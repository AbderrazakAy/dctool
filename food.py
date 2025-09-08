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
    "xp": "48598795",
    "user_id": "3769452541155155277",
    "user_name": "Abdou",
    "level": "30",
    "gold": "17521937",
    "food": "24874031",
    "cash": "16",
    "premium_expired_at": "2025-10-06 00:08:04",
    "uniqueDragons": "63",
    "dragonPoints": "7373"
}

# Form data
data = {
    "mode": "transfer-food"
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
    """Make a single API request"""
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def run_bot():
    """Run the bot continuously and track food"""
    global request_count
    total_food = 0
    
    print("🍲 Starting Food Transfer Bot...")
    print("📊 This version tracks your total food")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            request_count += 1
            print(f"\n--- Request #{request_count} ---")
            
            response = make_request()
            
            if response:
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                # Check if request was successful
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if response_data.get('success', False):
                            food_gained = 45000
                            total_food += food_gained
                            print(f"✅ Success! Transferred food.")
                            print(f"🍲 This request: +{food_gained:,} food | Total: {total_food:,}")
                            # Continue immediately to next iteration
                            continue
                        else:
                            print("❌ API returned success=false")
                            print(f"Error message: {response_data.get('message', 'Unknown error')}")
                            print("Stopping bot...")
                            break
                    except:
                        # If response isn't JSON, assume success if status is 200
                        food_gained = 45000
                        total_food += food_gained
                        print("✅ Success (non-JSON response)!")
                        print(f"🍲 This request: +{food_gained:,} food | Total: {total_food:,}")
                        continue
                else:
                    print(f"❌ HTTP Error {response.status_code}")
                    print("Stopping bot...")
                    break
            else:
                print("❌ Request failed")
                print("Stopping bot...")
                break
                
    except KeyboardInterrupt:
        print(f"\n🛑 Bot stopped by user after {request_count} requests")
        print(f"📊 Final Stats:")
        print(f"   • Total food transferred: {total_food:,}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"Bot stopped after {request_count} requests")
        print(f"📊 Final Stats:")
        print(f"   • Total food transferred: {total_food:,}")

def run_bot_with_minimal_delay(delay_ms=10):
    """Run bot with minimal delay between requests and track food"""
    global request_count
    total_food = 0
    
    print(f"🍲 Starting Food Transfer Bot with {delay_ms}ms delay between requests...")
    print("📊 This version tracks your total food")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            request_count += 1
            print(f"\n--- Request #{request_count} ---")
            
            response = make_request()
            
            if response:
                print(f"Status: {response.status_code} | Response: {response.text[:100]}...")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if response_data.get('success', False):
                            food_gained = 45000
                            total_food += food_gained
                            print(f"✅ Success! Transferred food.")
                            print(f"🍲 This request: +{food_gained:,} food | Total: {total_food:,}")
                            # Minimal delay to prevent overwhelming the server
                            time.sleep(delay_ms / 1000)
                            continue
                        else:
                            print(f"❌ API returned success=false")
                            print(f"Error message: {response_data.get('message', 'Unknown error')}")
                            print("Stopping bot...")
                            break
                    except:
                        # If response isn't JSON, assume success if status is 200
                        food_gained = 45000
                        total_food += food_gained
                        print("✅ Success (non-JSON response)!")
                        print(f"🍲 This request: +{food_gained:,} food | Total: {total_food:,}")
                        time.sleep(delay_ms / 1000)
                        continue
                else:
                    print(f"❌ HTTP Error {response.status_code}")
                    print("Stopping bot...")
                    break
            else:
                print("❌ Request failed, stopping...")
                break
                
    except KeyboardInterrupt:
        print(f"\n🛑 Bot stopped after {request_count} requests")
        print(f"📊 Final Stats:")
        print(f"   • Total food transferred: {total_food:,}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"Bot stopped after {request_count} requests")
        print(f"📊 Final Stats:")
        print(f"   • Total food transferred: {total_food:,}")

if __name__ == "__main__":
    # Prompt for PHPSESSID before starting
    if get_phpsessid():
        # Choose which version to run:
        
        # Option 1: No delay between successful requests
        run_bot()
        
        # Option 2: Minimal delay (uncomment to use instead)
        # run_bot_with_minimal_delay(50)  # 50ms delay
    else:
        print("🛑 Bot cannot start due to missing PHPSESSID")