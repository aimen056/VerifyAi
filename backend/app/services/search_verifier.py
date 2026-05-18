import logging
import json
import re
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, title: str, snippet: str, url: str, source: str = "Web"):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.source = source

class SearchVerifier:
    """
    Uses Serper.dev or Google Custom Search to cross-reference claims against real-time news.
    """
    def __init__(self, google_api_key: str = "", google_cx: str = "", serper_api_key: str = "", groq_api_key: str = ""):
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        self.serper_api_key = serper_api_key
        self.groq_api_key = groq_api_key
        self.google_url = "https://www.googleapis.com/customsearch/v1"
        self.serper_url = "https://google.serper.dev/search"

    async def _search_serper(self, query: str, search_type: str = "search") -> List[SearchResult]:
        """Query Serper.dev API (supports search, news, etc.)"""
        if not self.serper_api_key:
            return []

        url = f"https://google.serper.dev/{search_type}"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"q": query})

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=payload, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    # Serper news results are in 'news' key, general search in 'organic'
                    items = data.get("news", []) if search_type == "news" else data.get("organic", [])
                    for item in items[:10]:
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source=item.get("source", "Web")
                        ))
                    return results
        except Exception as e:
            logger.error(f"Serper error: {e}")
        return []

    async def search(self, query: str) -> List[SearchResult]:
        """Search Serper (First choice), then Google, fallback to DuckDuckGo."""
        # Clean and truncate query to prevent search API errors from massive OCR text blocks
        clean_query = query.replace('\n', ' ').strip()
        search_query = ' '.join(clean_query.split()[:20])
        
        results = []

        # 1. Try Serper.dev (Most reliable)
        if self.serper_api_key:
            results = await self._search_serper(search_query)
            if results:
                return results

        # 2. Try Google Custom Search
        if self.google_api_key and self.google_cx:
            try:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cx,
                    "q": search_query,
                    "num": 5
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.google_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("items", []):
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                snippet=item.get("snippet", ""),
                                url=item.get("link", "")
                            ))
                        if results:
                            return results
            except Exception as e:
                logger.error(f"Google Custom Search error: {e}")

        # 3. Fallback to DuckDuckGo HTML scraping
        logger.info(f"Performing DuckDuckGo search for: {search_query}")
        try:
            return await self._search_ddg(search_query)
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def _search_ddg(self, query: str) -> List[SearchResult]:
        """Simple DuckDuckGo search scraper."""
        logger.info(f"Performing DuckDuckGo search for: {query}")
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                response = await client.post(url, data={"q": query})
                response.raise_for_status()
                
                # Simple parsing of DDG HTML (Result titles and snippets)
                results = []
                # Find result blocks (approximate)
                html = response.text
                # Extract titles and links
                # Note: This is a fragile regex-based parser for the DDG HTML version
                matches = re.findall(r'result__a" href="([^"]+)">([^<]+)</a>.*?result__snippet">([^<]+)</div>', html, re.S)
                
                for link, title, snippet in matches[:5]:
                    # Clean up DDG redirects if needed
                    url = link
                    if "duckduckgo.com/l/?uddg=" in url:
                        from urllib.parse import unquote
                        url = unquote(url.split("uddg=")[1].split("&")[0])
                    
                    results.append(SearchResult(
                        title=title.strip(),
                        snippet=snippet.strip(),
                        url=url
                    ))
                return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def verify_corroboration(self, claim: str, results: List[SearchResult]) -> tuple[float, str]:
        """
        Zero-Trust Corroboration:
        - If Groq API key is set, use Llama 3 for intelligent semantic comparison.
        - Otherwise, fallback to RegEx rule-based checks.
        """
        if not results:
            return 0.2, "Zero Evidence: No reputable news sources confirm this claim."

        # ── LLM Intelligent Corroboration (Llama 3 via Groq) ──
        if self.groq_api_key:
            try:
                snippets_text = "\n".join([f"- {r.title}: {r.snippet}" for r in results])
                prompt = f"""
You are a STRICT and UNFORGIVING fact-checker. Compare this extracted CLAIM with the SEARCH RESULTS.
Your job is to determine if the search results corroborate the claim, contradict the claim, or are ambiguous.

CRITICAL INSTRUCTIONS:
1. You MUST extract and verify every single proper noun, location, organization, number, and date from the claim.
2. Compare these specific entities against the search results. If the search results describe the same core event but feature DIFFERENT entities (e.g., a different country, a different person's name, or a different statistic), that is a MASSIVE CONTRADICTION.
3. If ANY key entity in the claim is contradicted by the search results, you MUST return a score of 0.2 (Likely False) and explicitly state what the mismatch is in your reason.
4. Do not assume minor discrepancies are "close enough". You are a zero-trust auditor. Only return 0.95 if ALL details perfectly align.
5. If the search results are FACT-CHECK articles that explicitly DEBUNK, DENY, or label the claim as "Fake", "False", or "Hoax", you MUST return a score of 0.1 (Debunked) immediately.

CLAIM:
{claim}

SEARCH RESULTS:
{snippets_text}

Reply strictly with JSON format exactly like this:
{{
  "chain_of_thought": "Step 1: Extract entities from claim (e.g. Fidan, US, Iran, Pakistan, India). Step 2: Check if ALL these entities exist in the search results. Step 3: Identify mismatches...",
  "score": <float between 0.0 and 1.0>,
  "reason": "<string explanation>"
}}

- 0.95: Verified True (broad consensus confirms exact details)
- 0.75: Likely True (majority support)
- 0.5: Mixed/Ambiguous (reports exist but don't confirm exact details)
- 0.2: Likely False (contradicts details, like wrong numbers or countries)
- 0.1: Debunked (sources explicitly call it fake)

IMPORTANT: Do not use line breaks or unescaped quotes inside the JSON string values.
"""
                headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.1-8b-instant", 
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0
                }
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code != 200:
                        logger.error(f"Groq API Error: {resp.text}")
                    resp.raise_for_status()
                    data = resp.json()
                    content_str = data["choices"][0]["message"]["content"]
                    # Clean the string in case it has markdown code blocks
                    content_str = content_str.strip().strip("`").removeprefix("json").strip()
                    
                    # strict=False allows unescaped control characters (like newlines) inside strings
                    content = json.loads(content_str, strict=False)
                    logger.info(f"Llama 3 Output: {content}")
                    return float(content.get("score", 0.5)), content.get("reason", "Analyzed by AI.")
            except Exception as e:
                logger.error(f"Groq LLM verification failed, falling back to regex: {e}")

        # ── Fallback Rule-Based Corroboration ──

        claim_lower = claim.lower()
        text_pool = " ".join([(r.title + " " + r.snippet).lower() for r in results])
        
        # 1. Hard Debunk Check
        debunk_keywords = ["fact check", "false", "hoax", "misleading", "fake", "incorrect", "debunked", "untrue"]
        
        # Check if any results explicitly debunk the claim
        for r in results:
            text = (r.title + " " + r.snippet).lower()
            if any(k in text for k in debunk_keywords):
                return 0.1, f"Debunked: A source ('{r.title}') explicitly identifies this as a hoax or fake news."

        # 2. Extract Entities and Action Verbs
        entities = re.findall(r'\b[A-Z][a-z]+\b', claim)
        # Clean punctuation to avoid matching "talks," instead of "talks"
        clean_claim = re.sub(r'[^\w\s]', '', claim_lower)
        # Identify core action (e.g., assassinated, won, discovered)
        actions = [w for w in clean_claim.split() if w.endswith(('ed', 'ing', 's')) and len(w) > 4]

        # 3. Consensus Analysis
        supporting_sources = 0
        contradicting_sources = 0
        trusted_hits = 0
        
        trusted_domains = [
            "reuters.com", "apnews.com", "bbc.co.uk", "nytimes.com", "theguardian.com", 
            "cnn.com", "wsj.com", "aljazeera.com", "bloomberg.com", "nasa.gov", "who.int"
        ]

        for r in results:
            text = (r.title + " " + r.snippet).lower()
            is_trusted = any(d in r.url for d in trusted_domains)
            if is_trusted: trusted_hits += 1

            # Check if snippets support the action or contradict it
            # (e.g. if claim is 'died' but result says 'survived')
            supports = any(a in text for a in actions) if actions else True
            
            # Detect common contradictions
            contradicts = any(c in text for c in ["attempt", "failed", "false", "hoax", "fake", "rumor", "survived"])
            
            if is_trusted and contradicts:
                contradicting_sources += 2 # Weighted heavier
            elif is_trusted and supports:
                supporting_sources += 2
            elif contradicts:
                contradicting_sources += 1
            elif supports:
                supporting_sources += 1

        # 4. Final Verdict Logic (Consensus)
        total_signals = supporting_sources + contradicting_sources
        if total_signals == 0:
            return 0.4, "Ambiguous: We found reports about these entities, but they don't confirm or deny the specific action."

        consensus_ratio = supporting_sources / total_signals

        if contradicting_sources > supporting_sources:
            if trusted_hits > 0:
                return 0.1, "Contradicted by Trusted Sources: Reputable news organizations are reporting a different version of this story."
            return 0.2, "Likely False: Most available reports contradict the details of this claim."

        if consensus_ratio > 0.8 and trusted_hits > 0:
            return 0.95, "Verified: Broad consensus among trusted news organizations."
            
        if consensus_ratio > 0.6:
            return 0.75, "Likely True: The majority of reports align with this claim."

        return 0.5, "Mixed Reports: We found conflicting information from various sources."
