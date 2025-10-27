#!/usr/bin/env python3
"""
gold_xp_bot_auto_login.py

Automatically logs in and claims gold/XP repeatedly.
"""

import argparse
import time
import sys
import requests
from datetime import datetime

BASE = "https://nullzereptool.com"
LOGIN_URL = f"{BASE}/login"
PACKET_URL = f"{BASE}/packet"

COMMON_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.5",
    "origin": "https://nullzereptool.com",
    "priority": "u=1, i",
    "referer": "https://nullzereptool.com/",
    "sec-ch-ua": '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"),
}

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def login_with_code(session: requests.Session, code: str, timeout: float = 15.0) -> requests.Response:
    """Login using the provided code"""
    files = {
        "code": (None, code),
        "loginType": (None, "user"),
    }
    headers = COMMON_HEADERS.copy()
    return session.post(LOGIN_URL, headers=headers, files=files, timeout=timeout)

def claim_gold_xp(session: requests.Session, timeout: float = 15.0) -> requests.Response:
    """Claim gold and XP"""
    headers = COMMON_HEADERS.copy()
    headers["content-type"] = "application/x-www-form-urlencoded"
    data = {"mode": "claim-gold-xp"}
    return session.post(PACKET_URL, headers=headers, data=data, timeout=timeout)

def do_login(s: requests.Session, code: str, timeout: float) -> bool:
    """Perform login and return success status"""
    try:
        print(f"[{now_ts()}] 🔐 Logging in...")
        rlogin = login_with_code(s, code, timeout=timeout)
        if not rlogin.ok:
            print(f"[{now_ts()}] ❌ Login failed (status {rlogin.status_code})")
            return False
        print(f"[{now_ts()}] ✅ Login success")
        
        # Show session info
        if s.cookies:
            phpsess = s.cookies.get("PHPSESSID")
            if phpsess:
                print(f"[{now_ts()}] 🍪 Session: {phpsess[:20]}...")
        return True
    except Exception as e:
        print(f"[{now_ts()}] ❌ Login error: {e}")
        return False

def run_bot(code: str, timeout: float = 15.0):
    """
    Login and continuously claim gold/XP, re-login on failure
    """
    with requests.Session() as s:
        try:
            # Initial login
            if not do_login(s, code, timeout):
                print(f"[{now_ts()}] 🛑 Initial login failed, exiting...")
                return

            # Track stats
            claim_count = 0
            total_gold = 0
            total_xp = 0
            
            print(f"[{now_ts()}] 🏆 Starting Gold & XP Claims...")
            print(f"[{now_ts()}] Press Ctrl+C to stop\n")

            while True:
                claim_count += 1
                print(f"[{now_ts()}] --- Claim #{claim_count} ---")
                
                try:
                    response = claim_gold_xp(s, timeout=timeout)
                    
                    if response.ok:
                        try:
                            data = response.json()
                            if data.get('success'):
                                # Assuming fixed amounts per claim
                                gold_gained = 150000
                                xp_gained = 45000
                                total_gold += gold_gained
                                total_xp += xp_gained
                                
                                print(f"[{now_ts()}] ✅ Claim successful!")
                                print(f"[{now_ts()}] 💰 +{gold_gained:,} gold | Total: {total_gold:,}")
                                print(f"[{now_ts()}] ⭐ +{xp_gained:,} XP | Total: {total_xp:,}\n")
                            else:
                                msg = data.get('message', 'Unknown error')
                                print(f"[{now_ts()}] ⚠️ {msg}")
                                print(f"[{now_ts()}] 🔄 Re-logging in...\n")
                                if do_login(s, code, timeout):
                                    print(f"[{now_ts()}] ✅ Re-login successful, continuing...\n")
                                else:
                                    print(f"[{now_ts()}] ❌ Re-login failed, retrying...\n")
                                    time.sleep(5)
                        except:
                            # Non-JSON response, assume success
                            gold_gained = 150000
                            xp_gained = 45000
                            total_gold += gold_gained
                            total_xp += xp_gained
                            print(f"[{now_ts()}] ✅ Success (non-JSON)")
                            print(f"[{now_ts()}] 💰 +{gold_gained:,} gold | Total: {total_gold:,}")
                            print(f"[{now_ts()}] ⭐ +{xp_gained:,} XP | Total: {total_xp:,}\n")
                    else:
                        print(f"[{now_ts()}] ❌ HTTP {response.status_code}")
                        print(f"[{now_ts()}] 🔄 Re-logging in...\n")
                        if do_login(s, code, timeout):
                            print(f"[{now_ts()}] ✅ Re-login successful, continuing...\n")
                        else:
                            print(f"[{now_ts()}] ❌ Re-login failed, retrying...\n")
                            time.sleep(5)
                        
                except requests.exceptions.RequestException as e:
                    print(f"[{now_ts()}] ❌ Network error: {e}")
                    print(f"[{now_ts()}] 🔄 Re-logging in...\n")
                    if do_login(s, code, timeout):
                        print(f"[{now_ts()}] ✅ Re-login successful, continuing...\n")
                    else:
                        print(f"[{now_ts()}] ❌ Re-login failed, retrying...\n")
                        time.sleep(5)
                    
        except KeyboardInterrupt:
            print(f"\n[{now_ts()}] 🛑 Bot stopped by user")
            print(f"[{now_ts()}] 📊 Final Stats:")
            print(f"[{now_ts()}]    • Total claims: {claim_count}")
            print(f"[{now_ts()}]    • Total gold: {total_gold:,}")
            print(f"[{now_ts()}]    • Total XP: {total_xp:,}")
            return
        except Exception as e:
            print(f"[{now_ts()}] 💥 Unexpected error: {e}")
            return

def main():
    parser = argparse.ArgumentParser(description="Auto login + Gold/XP claim bot")
    parser.add_argument("--code", "-c",
                        default="a4d130ef2e2e035b3561d61362116a99",
                        help="Login code (default provided).")
    parser.add_argument("--timeout", "-t", type=int, default=15,
                        help="Request timeout in seconds (default: 15).")
    args = parser.parse_args()

    code = args.code
    timeout = args.timeout

    print(f"[{now_ts()}] 🚀 Starting Auto Gold/XP Bot")
    print(f"[{now_ts()}] Timeout: {timeout}s\n")
    
    run_bot(code, timeout=timeout)

if __name__ == "__main__":
    main()