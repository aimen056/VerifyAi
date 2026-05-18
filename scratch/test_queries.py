
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
    
    claims = [
        "India says US troop withdrawal 'foreseeable' as Nato seeks clarification",
        "US troop withdrawal 'foreseeable' as Nato seeks clarification",
        "Germany says US troop withdrawal 'foreseeable' as Nato seeks clarification"
    ]
    
    for claim in claims:
        print(f"\nChecking claim: {claim}")
        result = await checker.check(claim)
        print(f"Found {len(result.claims)} claims.")
        for c in result.claims:
            print(f"- Source: {c.source_name}, Rating: {c.rating}")

if __name__ == "__main__":
    asyncio.run(test())
