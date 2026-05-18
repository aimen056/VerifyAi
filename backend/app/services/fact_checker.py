"""
Google Fact Check Tools API integration.

Queries Google's ClaimReview API for existing fact-check articles
related to a given claim. Returns structured results that feed
into the verification pipeline.

API docs: https://developers.google.com/fact-check/tools/api/reference/rest
"""

import asyncio
import logging
from typing import Optional, List
from urllib.parse import quote_plus

import httpx

from app.services.base import (
    BaseFactChecker,
    FactCheckResult,
    FactCheckClaim,
)

logger = logging.getLogger(__name__)

GOOGLE_FACTCHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


class GoogleFactChecker(BaseFactChecker):
    """
    Google Fact Check Tools API client.

    Usage:
        checker = GoogleFactChecker(api_key="YOUR_KEY")
        result = await checker.check("COVID vaccines cause autism")
        for claim in result.claims:
            print(claim.rating, claim.source_name)
    """

    def __init__(
        self,
        api_key: str,
        language_code: str = "en",
        max_results: int = 5,
        timeout: float = 10.0,
    ):
        """
        Args:
            api_key:       Google API key with Fact Check API enabled.
            language_code: BCP-47 language code for results.
            max_results:   Maximum number of claims to return.
            timeout:       HTTP request timeout in seconds.
        """
        self.api_key = api_key
        self.language_code = language_code
        self.max_results = max_results
        self.timeout = timeout

    # ── Interface Implementation ──────────────────────────────

    async def check(self, claim: str) -> FactCheckResult:
        """
        Search for existing fact-checks related to the given claim.

        Returns a FactCheckResult containing any matching claims
        from Google's ClaimReview database.
        """
        if not self.api_key or self.api_key == "your_google_api_key_here":
            logger.warning(
                "Google Fact Check API key not configured — "
                "returning empty results"
            )
            return FactCheckResult(query=claim, claims=[])

        try:
            return await self._search(claim)
        except Exception as e:
            logger.error(f"Fact check API error: {e}", exc_info=True)
            return FactCheckResult(query=claim, claims=[])

    async def _search(self, claim: str) -> FactCheckResult:
        """Execute the HTTP request to Google Fact Check API."""
        params = {
            "key": self.api_key,
            "query": claim,
            "languageCode": self.language_code,
            "pageSize": self.max_results,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(GOOGLE_FACTCHECK_URL, params=params)
            response.raise_for_status()
            data = response.json()

        claims = self._parse_response(data)

        logger.info(
            f"Fact check for \"{claim[:60]}...\" returned {len(claims)} results"
        )

        return FactCheckResult(query=claim, claims=claims)

    def _parse_response(self, data: dict) -> List[FactCheckClaim]:
        """Parse the API JSON response into FactCheckClaim objects."""
        claims: List[FactCheckClaim] = []

        for item in data.get("claims", []):
            claim_text = item.get("text", "")
            claimant = item.get("claimant")

            # Each claim may have multiple reviews
            for review in item.get("claimReview", []):
                claims.append(
                    FactCheckClaim(
                        claim_text=claim_text,
                        claimant=claimant,
                        rating=review.get("textualRating"),
                        source_name=review.get("publisher", {}).get("name"),
                        source_url=review.get("url"),
                    )
                )

        return claims[: self.max_results]
