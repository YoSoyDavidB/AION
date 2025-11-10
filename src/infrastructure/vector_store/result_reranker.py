"""
Result re-ranking for improved RAG relevance.

Implements multiple re-ranking strategies to improve
the quality of retrieved documents.
"""

import re
from typing import Any, Literal

from src.shared.logging import LoggerMixin


RerankStrategy = Literal["mmr", "keyword_boost", "recency", "hybrid"]


class ResultReranker(LoggerMixin):
    """
    Re-ranks search results to improve relevance.

    Strategies:
    - MMR (Maximal Marginal Relevance): Balances relevance and diversity
    - Keyword Boost: Boosts results with exact keyword matches
    - Recency: Favors newer documents
    - Hybrid: Combines multiple signals
    """

    def __init__(self):
        """Initialize result reranker."""
        super().__init__()

    def rerank(
        self,
        results: list[dict[str, Any]],
        query: str,
        strategy: RerankStrategy = "hybrid",
        top_k: int | None = None,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Re-rank search results.

        Args:
            results: Original search results from vector store
            query: Original search query
            strategy: Re-ranking strategy
            top_k: Return only top K results after re-ranking
            **kwargs: Strategy-specific parameters

        Returns:
            Re-ranked results
        """
        if not results:
            return []

        self.logger.info(
            "reranking_results",
            num_results=len(results),
            strategy=strategy
        )

        if strategy == "mmr":
            reranked = self._rerank_mmr(results, query, **kwargs)
        elif strategy == "keyword_boost":
            reranked = self._rerank_keyword_boost(results, query, **kwargs)
        elif strategy == "recency":
            reranked = self._rerank_recency(results, **kwargs)
        else:  # hybrid
            reranked = self._rerank_hybrid(results, query, **kwargs)

        # Apply top_k limit if specified
        if top_k:
            reranked = reranked[:top_k]

        self.logger.info(
            "reranking_complete",
            final_count=len(reranked)
        )

        return reranked

    def _rerank_mmr(
        self,
        results: list[dict[str, Any]],
        query: str,
        lambda_param: float = 0.5,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Maximal Marginal Relevance re-ranking.

        Balances relevance to query with diversity of results.

        Args:
            results: Search results
            query: Search query
            lambda_param: Balance between relevance (1.0) and diversity (0.0)

        Returns:
            Re-ranked results
        """
        if not results or len(results) <= 1:
            return results

        # Start with most relevant result
        selected = [results[0]]
        remaining = results[1:]

        # Iteratively select results that are relevant but diverse
        while remaining and len(selected) < len(results):
            best_score = float('-inf')
            best_idx = 0

            for idx, candidate in enumerate(remaining):
                # Relevance score (already from vector search)
                relevance = candidate.get("score", 0.5)

                # Diversity: minimum similarity to already selected
                max_similarity = 0.0
                for selected_result in selected:
                    # Approximate similarity based on keyword overlap
                    similarity = self._compute_text_similarity(
                        candidate.get("payload", {}).get("content", ""),
                        selected_result.get("payload", {}).get("content", "")
                    )
                    max_similarity = max(max_similarity, similarity)

                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            # Add best candidate
            selected.append(remaining.pop(best_idx))

        return selected

    def _rerank_keyword_boost(
        self,
        results: list[dict[str, Any]],
        query: str,
        boost_factor: float = 1.5,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Boost results with exact keyword matches.

        Args:
            results: Search results
            query: Search query
            boost_factor: Multiplier for keyword matches

        Returns:
            Re-ranked results
        """
        # Extract query keywords (simple approach)
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        query_keywords = query_keywords - stop_words

        reranked = []

        for result in results:
            content = result.get("payload", {}).get("content", "").lower()
            original_score = result.get("score", 0.5)

            # Count keyword matches
            matches = sum(1 for keyword in query_keywords if keyword in content)

            # Boost score based on matches
            if matches > 0:
                boost = 1.0 + (matches / len(query_keywords)) * (boost_factor - 1.0)
                new_score = min(1.0, original_score * boost)
            else:
                new_score = original_score

            # Create modified result
            modified = result.copy()
            modified["score"] = new_score
            modified["keyword_matches"] = matches

            reranked.append(modified)

        # Sort by new score
        reranked.sort(key=lambda x: x["score"], reverse=True)

        return reranked

    def _rerank_recency(
        self,
        results: list[dict[str, Any]],
        recency_weight: float = 0.3,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Favor more recent documents.

        Args:
            results: Search results
            recency_weight: Weight for recency score (0-1)

        Returns:
            Re-ranked results
        """
        reranked = []

        # Find newest and oldest timestamps
        timestamps = []
        for result in results:
            created_at = result.get("payload", {}).get("created_at")
            if created_at:
                # Assuming timestamp is in seconds
                if isinstance(created_at, (int, float)):
                    timestamps.append(created_at)

        if not timestamps:
            # No timestamps, return as-is
            return results

        min_time = min(timestamps)
        max_time = max(timestamps)
        time_range = max_time - min_time if max_time > min_time else 1

        for result in results:
            original_score = result.get("score", 0.5)
            created_at = result.get("payload", {}).get("created_at")

            if created_at and isinstance(created_at, (int, float)):
                # Normalize recency score (0-1, newer = higher)
                recency_score = (created_at - min_time) / time_range
            else:
                recency_score = 0.5  # Neutral

            # Combine scores
            new_score = (1 - recency_weight) * original_score + recency_weight * recency_score

            # Create modified result
            modified = result.copy()
            modified["score"] = new_score
            modified["recency_score"] = recency_score

            reranked.append(modified)

        # Sort by new score
        reranked.sort(key=lambda x: x["score"], reverse=True)

        return reranked

    def _rerank_hybrid(
        self,
        results: list[dict[str, Any]],
        query: str,
        keyword_weight: float = 0.3,
        recency_weight: float = 0.2,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Hybrid re-ranking combining multiple signals.

        Args:
            results: Search results
            query: Search query
            keyword_weight: Weight for keyword boost
            recency_weight: Weight for recency

        Returns:
            Re-ranked results
        """
        # Apply keyword boost
        results = self._rerank_keyword_boost(results, query, boost_factor=1.0 + keyword_weight)

        # Apply recency boost
        results = self._rerank_recency(results, recency_weight=recency_weight)

        return results

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        Compute simple text similarity based on word overlap.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Extract words
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
