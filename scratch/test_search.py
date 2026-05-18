
import asyncio
import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.search_verifier import SearchVerifier

load_dotenv("backend/.env")

async def test():
    api_key = os.getenv("CUSTOM_SEARCH_API")
    cx = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
    
    print(f"Testing Search with Key: {api_key[:10]}... and CX: {cx}")
    
    verifier = SearchVerifier(api_key=api_key, search_engine_id=cx)
    
    query = "India says US troop withdrawal foreseeable Nato"
    print(f"\nSearching for: {query}")
    results = await verifier.search(query)
    
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"- {r.title}")
        print(f"  URL: {r.url}")
        print(f"  Snippet: {r.snippet[:100]}...")

    score, reason = verifier.verify_corroboration(query, results)
    print(f"\nVerification Results:")
    print(f"Score: {score}")
    print(f"Reasoning: {reason}")

if __name__ == "__main__":
    asyncio.run(test())
