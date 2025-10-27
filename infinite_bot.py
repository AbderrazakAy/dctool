#!/usr/bin/env python3
"""
Single burst bot — makes 10 simultaneous API calls once and exits.
"""
import asyncio
import aiohttp
from datetime import datetime

# ------------- CONFIG -------------
URL = "https://nullzereptool.com/packet"
CALL_COUNT = 10              # number of simultaneous calls
REQUEST_TIMEOUT = 30         # seconds

# Headers (adapted from working script)
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.8",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://nullzereptool.com",
    "priority": "u=1, i",
    "referer": "https://nullzereptool.com/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

# Cookies (you'll need to enter your PHPSESSID)
COOKIES = {
    "user_id": "3769452541155155277",
    "user_name": "Abdou",
    "level": "31",
    "gold": "31728714",
    "food": "52904949",
    "cash": "53",
    "xp": "53786995",
    "premium_expired_at": "2025-10-06 00:08:04",
    "uniqueDragons": "67",
    "dragonPoints": "7782"
}

PAYLOAD = {"mode": "claim-gold-xp"}
# -----------------------------------

def get_phpsessid():
    """Prompt user for PHPSESSID"""
    phpsessid = input("🔐 Please enter your PHPSESSID: ").strip()
    if not phpsessid:
        print("❌ No PHPSESSID provided")
        return False
    COOKIES["PHPSESSID"] = phpsessid
    return True

async def make_call(call_id: int, session: aiohttp.ClientSession):
    try:
        async with session.post(URL, data=PAYLOAD, timeout=REQUEST_TIMEOUT) as resp:
            text = await resp.text()
            status = resp.status
            print(f"[{datetime.utcnow().isoformat()}] call-{call_id} status={status}")
            
            # Try to parse response
            try:
                import json
                data = json.loads(text)
                if data.get('success'):
                    print(f"  ✅ Call-{call_id}: Success! Gold/XP claimed")
                else:
                    print(f"  ❌ Call-{call_id}: {data.get('message', 'Unknown error')}")
            except:
                print(f"  📄 Call-{call_id}: Response: {text[:100]}")
            
            return status
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] call-{call_id} ERROR: {e}")
        return None

async def main():
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    connector = aiohttp.TCPConnector(limit_per_host=0, limit=0)
    
    async with aiohttp.ClientSession(headers=HEADERS, cookies=COOKIES, timeout=timeout, connector=connector) as session:
        print(f"\n🚀 Making {CALL_COUNT} simultaneous API calls...")
        print(f"⏱️  This should take ~5 seconds instead of ~50 seconds\n")
        
        start_time = datetime.utcnow()
        tasks = [make_call(i+1, session) for i in range(CALL_COUNT)]
        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*50}")
        print(f"✅ Completed {CALL_COUNT} calls in {elapsed:.2f} seconds!")
        print(f"📊 Results: {results}")
        print(f"{'='*50}")

if __name__ == "__main__":
    print("🏆 Gold & XP Claim Bot - Burst Mode (10 simultaneous calls)")
    print("="*60)
    
    if get_phpsessid():
        asyncio.run(main())
        print("\n✅ Bot finished.")
    else:
        print("🛑 Bot cannot start without PHPSESSID")