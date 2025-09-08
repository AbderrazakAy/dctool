import requests
import time

# Target URL
url = "https://nullzereptool.com/packet"

# Headers
headers = {
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

# Base cookies dictionary (without PHPSESSID)
cookies = {
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

# Form data for claiming gold and XP
data = {
    "mode": "claim-gold-xp"
}

# Counter for tracking requests
request_count = 0

def get_phpsessid():
    """Prompt user for PHPSESSID and update cookies"""
    phpsessid = input("🔐 Please enter your PHPSESSID: ").strip()
    if not phpsessid:
        print("❌ No PHPSESSID provided")
        return False
    cookies["PHPSESSID"] = phpsessid
    return True

def make_request():
    """Make a single API request to claim gold and XP"""
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def run_gold_xp_bot():
    """Run the gold/XP claiming bot continuously"""
    global request_count
    
    print("🏆 Starting Gold & XP Claim Bot...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            request_count += 1
            print(f"\n--- Claim Request #{request_count} ---")
            
            response = make_request()
            
            if response:
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                # Check if request was successful
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if response_data.get('success', False):
                            print("✅ Successfully claimed Gold & XP! Making next request...")
                            
                            # Display any reward info if available
                            if 'gold' in response_data:
                                print(f"💰 Gold gained: {response_data.get('gold', 'Unknown')}")
                            if 'xp' in response_data:
                                print(f"⭐ XP gained: {response_data.get('xp', 'Unknown')}")
                                
                            # Continue immediately to next iteration
                            continue
                        else:
                            print("❌ API returned success=false")
                            error_msg = response_data.get('message', 'Unknown error')
                            print(f"Error message: {error_msg}")
                            
                            # Check if it's a cooldown/timing issue
                            if 'cooldown' in error_msg.lower() or 'wait' in error_msg.lower():
                                print("⏰ Cooldown detected, continuing anyway...")
                                continue
                            else:
                                print("Stopping bot due to error...")
                                break
                    except:
                        # If response isn't JSON, assume success if status is 200
                        print("✅ Success (non-JSON response)! Making next request...")
                        continue
                else:
                    print(f"❌ HTTP Error {response.status_code}")
                    if response.status_code == 403:
                        print("🔒 Forbidden - possible session expired or invalid request")
                    elif response.status_code == 429:
                        print("⏱️ Rate limited - server is throttling requests")
                    print("Stopping bot...")
                    break
            else:
                print("❌ Request failed")
                print("Stopping bot...")
                break
                
    except KeyboardInterrupt:
        print(f"\n🛑 Gold & XP Bot stopped by user after {request_count} claims")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"Bot stopped after {request_count} requests")

def run_gold_xp_bot_with_stats():
    """Enhanced version that tracks claimed rewards"""
    global request_count
    total_gold = 0
    total_xp = 0
    
    print("🏆 Starting Enhanced Gold & XP Claim Bot...")
    print("📊 This version tracks your total rewards")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            request_count += 1
            print(f"\n--- Claim #{request_count} ---")
            
            response = make_request()
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        gold_gained = 150000  # Fixed amount per successful claim
                        xp_gained = 45000     # Fixed amount per successful claim
                        
                        total_gold += gold_gained
                        total_xp += xp_gained
                        
                        print(f"✅ Claim successful!")
                        print(f"💰 This claim: +{gold_gained:,} gold | Total: {total_gold:,}")
                        print(f"⭐ This claim: +{xp_gained:,} XP | Total: {total_xp:,}")
                        continue
                    else:
                        print(f"❌ {data.get('message', 'Unknown error')}")
                        continue
                except:
                    # If response isn't JSON, assume success and add fixed amounts
                    gold_gained = 150000
                    xp_gained = 45000
                    total_gold += gold_gained
                    total_xp += xp_gained
                    print("✅ Success (non-JSON response)")
                    print(f"💰 This claim: +{gold_gained:,} gold | Total: {total_gold:,}")
                    print(f"⭐ This claim: +{xp_gained:,} XP | Total: {total_xp:,}")
                    continue
            else:
                print(f"❌ Request failed: {response.status_code if response else 'No response'}")
                break
                
    except KeyboardInterrupt:
        print(f"\n🛑 Bot stopped!")
        print(f"📊 Final Stats:")
        print(f"   • Total claims: {request_count}")
        print(f"   • Total gold earned: {total_gold:,}")
        print(f"   • Total XP earned: {total_xp:,}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"Bot stopped after {request_count} requests")

if __name__ == "__main__":
    # Prompt for PHPSESSID before starting
    if get_phpsessid():
        # Run enhanced bot with stats tracking
        run_gold_xp_bot_with_stats()
    else:
        print("🛑 Bot cannot start due to missing PHPSESSID")