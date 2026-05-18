
import asyncio
import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.fact_checker import GoogleFactChecker

load_dotenv("backend/.env")

async def test():
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    checker = GoogleFactChecker(api_key=api_key)
    
    # Test with a known fake claim
    claim = "COVID vaccines cause autism"
    print(f"Checking claim: {claim}")
    result = await checker.check(claim)
    
    print(f"Found {len(result.claims)} claims:")
    for c in result.claims:
        print(f"- Source: {c.source_name}, Rating: {c.rating}, URL: {c.source_url}")

if __name__ == "__main__":
    asyncio.run(test())
