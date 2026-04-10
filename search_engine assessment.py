from database import search_policies, get_categories
from pdf_indexer import indexer


class HybridSearchEngine:
    def __init__(self):
        indexer.load_and_index()

    def search(self, query, category=None, status="Active", date_from=None, top_k=10):
        """Hybrid search combining DB + PDF results"""
        results = []

        db_results = search_policies(query, category, status, date_from)

        for row in db_results:
            policy_id, policy_name, cat, eff_date, stat, desc, _ = row

            score = self._calculate_db_score(query, policy_name, desc)

            results.append(
                {
                    "source": "Database",
                    "policy_id": policy_id,
                    "title": policy_name,
                    "category": cat,
                    "effective_date": eff_date,
                    "status": stat,
                    "snippet": desc[:150] + "..." if len(desc) > 150 else desc,
                    "score": score,
                    "page": None,
                }
            )

        pdf_results = indexer.search(query)

        for pdf_result in pdf_results:
            results.append(pdf_result)

        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _calculate_db_score(self, query, title, description):
        """Calculate relevance score for DB results"""
        query_lower = query.lower()
        title_lower = title.lower()
        desc_lower = description.lower()

        score = 0

        if query_lower in title_lower:
            score += 80

        if query_lower in desc_lower:
            score += 40

        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 3:
                if word in title_lower:
                    score += 10
                if word in desc_lower:
                    score += 5

        return min(100, score)


search_engine = HybridSearchEngine()

if __name__ == "__main__":
    results = search_engine.search("maternity leave eligibility", top_k=5)
    for r in results:
        print(f"{r['source']} | {r['title']} ({r['score']}%) | {r['snippet'][:80]}")
