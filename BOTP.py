import requests
import time
import sys

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

# Form data for different modes
data_gold_xp = {"mode": "claim-gold-xp"}
data_food = {"mode": "transfer-food"}

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

def make_request(data):
    """Make a single API request with specified form data"""
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return None

def run_combined_bot(mode):
    """Run the bot with the selected mode (gold_xp, food, or both)"""
    global request_count
    total_gold = 0
    total_xp = 0
    total_food = 0
    
    mode_text = {
        "gold_xp": "Gold & XP Claim Bot",
        "food": "Food Transfer Bot",
        "both": "Gold, XP, and Food Claim Bot"
    }
    
    print(f"🏆 Starting {mode_text[mode]}...")
    print("📊 Tracking your total rewards")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            request_count += 1
            
            # Initialize status line based on mode
            status_line = f"\rRequest #{request_count} | "
            if mode in ["gold_xp", "both"]:
                status_line += f"Gold: {total_gold:,} | XP: {total_xp:,}"
            if mode in ["food", "both"]:
                status_line += f"{' | ' if mode == 'both' else ''}Food: {total_food:,}"
            
            # Print initial status line
            sys.stdout.write(status_line)
            sys.stdout.flush()
            
            # Handle the selected mode
            if mode == "gold_xp":
                response = make_request(data_gold_xp)
                if response and response.status_code == 200:
                    try:
                        response_data = response.json()
                        if response_data.get('success', False):
                            total_gold += 150000
                            total_xp += 45000
                        else:
                            print(f"\n❌ API returned success=false: {response_data.get('message', 'Unknown error')}")
                            continue
                    except:
                        total_gold += 150000
                        total_xp += 45000
                else:
                    print(f"\n❌ HTTP Error {response.status_code if response else 'No response'}")
                    print("Stopping bot...")
                    break
            
            elif mode == "food":
                response = make_request(data_food)
                if response and response.status_code == 200:
                    try:
                        response_data = response.json()
                        if response_data.get('success', False):
                            total_food += 45000
                        else:
                            print(f"\n❌ API returned success=false: {response_data.get('message', 'Unknown error')}")
                            continue
                    except:
                        total_food += 45000
                else:
                    print(f"\n❌ HTTP Error {response.status_code if response else 'No response'}")
                    print("Stopping bot...")
                    break
            
            elif mode == "both":
                gold_xp_success = False
                response_gold_xp = make_request(data_gold_xp)
                if response_gold_xp and response_gold_xp.status_code == 200:
                    try:
                        response_data = response_gold_xp.json()
                        if response_data.get('success', False):
                            total_gold += 150000
                            total_xp += 45000
                            gold_xp_success = True
                        else:
                            print(f"\n❌ Gold/XP API returned success=false: {response_data.get('message', 'Unknown error')}")
                    except:
                        total_gold += 150000
                        total_xp += 45000
                        gold_xp_success = True
                
                food_success = False
                response_food = make_request(data_food)
                if response_food and response_food.status_code == 200:
                    try:
                        response_data = response_food.json()
                        if response_data.get('success', False):
                            total_food += 45000
                            food_success = True
                        else:
                            print(f"\n❌ Food API returned success=false: {response_data.get('message', 'Unknown error')}")
                    except:
                        total_food += 45000
                        food_success = True
                
                if not (gold_xp_success or food_success):
                    print(f"\n❌ Both requests failed, stopping bot...")
                    break
            
            # Update status line with new totals
            status_line = f"\rRequest #{request_count} | "
            if mode in ["gold_xp", "both"]:
                status_line += f"Gold: {total_gold:,} | XP: {total_xp:,}"
            if mode in ["food", "both"]:
                status_line += f"{' | ' if mode == 'both' else ''}Food: {total_food:,}"
            sys.stdout.write(status_line)
            sys.stdout.flush()
                
    except KeyboardInterrupt:
        print(f"\n🛑 Bot stopped by user after {request_count} requests")
        print(f"📊 Final Stats:")
        if mode in ["gold_xp", "both"]:
            print(f"   • Total gold earned: {total_gold:,}")
            print(f"   • Total XP earned: {total_xp:,}")
        if mode in ["food", "both"]:
            print(f"   • Total food transferred: {total_food:,}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"Bot stopped after {request_count} requests")
        print(f"📊 Final Stats:")
        if mode in ["gold_xp", "both"]:
            print(f"   • Total gold earned: {total_gold:,}")
            print(f"   • Total XP earned: {total_xp:,}")
        if mode in ["food", "both"]:
            print(f"   • Total food transferred: {total_food:,}")

def select_mode():
    """Prompt user to select the bot mode"""
    print("Select bot mode:")
    print("1. Claim Gold & XP")
    print("2. Transfer Food")
    print("3. Claim Gold, XP, and Food")
    choice = input("Enter 1, 2, or 3: ").strip()
    
    if choice == "1":
        return "gold_xp"
    elif choice == "2":
        return "food"
    elif choice == "3":
        return "both"
    else:
        print("❌ Invalid choice, defaulting to Gold & XP mode")
        return "gold_xp"

if __name__ == "__main__":
    # Prompt for PHPSESSID before starting
    if get_phpsessid():
        # Prompt for mode selection
        mode = select_mode()
        # Run the combined bot with the selected mode
        run_combined_bot(mode)
    else:
        print("🛑 Bot cannot start due to missing PHPSESSID")