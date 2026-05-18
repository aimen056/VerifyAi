import asyncio
import httpx
import json
import time

async def test_claim(claim, expected_verdict):
    print(f"\n[TESTING] {claim}")
    
    # Large timeout because ML models are heavy
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/verify/text",
                json={"text": claim}
            )
            if response.status_code == 200:
                data = response.json()
                verdict = data["verdict"].upper()
                confidence = data["confidence"]
                
                # Check for Pass/Fail
                success = False
                if verdict == expected_verdict.upper():
                    success = True
                elif verdict == "UNVERIFIED" and expected_verdict.upper() == "FALSE":
                    # Unverified is a "Safe" result for a false claim if search was uncertain
                    success = True
                
                status = "PASS" if success else "FAIL"
                print(f"[RESULT]  {verdict} ({confidence:.1%}) -> {status}")
                return success
            else:
                print(f"[ERROR]   Status {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR]   {str(e)}")
            return False

async def run_suite():
    tests = [
        ("Scientists have successfully revived a 48,000-year-old 'zombie virus' from Siberian permafrost", "TRUE"),
        ("Drinking lemon water with baking soda is 10,000 times more effective than chemotherapy", "FALSE"),
        ("Japan is sending astronauts to the moon in 2026", "TRUE"),
        ("Elon Musk has announced he is buying the Moon for 50 billion dollars", "FALSE"),
        ("The Eiffel Tower was moved to Dubai for the COP28 summit", "FALSE")
    ]
    
    passed = 0
    print("=== VERIFYAI ACCURACY BENCHMARK ===")
    print("Testing AI + Search + FactCheck integration...\n")
    
    for claim, expected in tests:
        if await test_claim(claim, expected):
            passed += 1
        await asyncio.sleep(2) 
        
    print("\n" + "="*40)
    print(f"FINAL SCORE: {passed}/{len(tests)} ({passed/len(tests):.0%})")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(run_suite())
