#!/usr/bin/env python3
"""
nullzerep_auto_bot_clean.py

Automates:
  1) login (multipart form with code + loginType=user)
  2) packet -> mode=puzzle-crazy
  3) packet -> mode=puzzle-claim

Clean output version - shows only success/failure status.
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
    files = {
        "code": (None, code),
        "loginType": (None, "user"),
    }
    headers = COMMON_HEADERS.copy()
    return session.post(LOGIN_URL, headers=headers, files=files, timeout=timeout)

def post_packet(session: requests.Session, mode: str, timeout: float = 15.0) -> requests.Response:
    headers = COMMON_HEADERS.copy()
    headers["content-type"] = "application/x-www-form-urlencoded"
    data = {"mode": mode}
    return session.post(PACKET_URL, headers=headers, data=data, timeout=timeout)

def run_cycle(code: str, attempt_timeout: float = 15.0) -> bool:
    """
    Perform login + puzzle-crazy + puzzle-claim once.
    Returns True if full cycle succeeded, False otherwise.
    """
    with requests.Session() as s:
        try:
            # Login
            rlogin = login_with_code(s, code, timeout=attempt_timeout)
            if not rlogin.ok:
                print(f"[{now_ts()}] ❌ Login failed")
                return False
            print(f"[{now_ts()}] ✅ Login success")

            # Puzzle-crazy
            r1 = post_packet(s, "puzzle-crazy", timeout=attempt_timeout)
            if not r1.ok:
                print(f"[{now_ts()}] ❌ Crazy failed")
                return False
            print(f"[{now_ts()}] ✅ Crazy success")

            # Puzzle-claim
            r2 = post_packet(s, "puzzle-claim", timeout=attempt_timeout)
            if not r2.ok:
                print(f"[{now_ts()}] ❌ Claim failed")
                return False
            print(f"[{now_ts()}] ✅ Claim success")

            return True

        except requests.exceptions.RequestException as e:
            print(f"[{now_ts()}] ❌ Network error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Auto bot for nullzereptool (clean output).")
    parser.add_argument("--code", "-c",
                        default="a4d130ef2e2e035b3561d61362116a99",
                        help="Login code (default provided).")
    parser.add_argument("--max", "-m", type=int, default=0,
                        help="Max cycles to run (0 = unlimited).")
    parser.add_argument("--timeout", "-t", type=int, default=15,
                        help="Request timeout in seconds (default: 15).")
    parser.add_argument("--backoff", type=int, default=5,
                        help="Base backoff seconds after a failed cycle before retrying (default: 5).")
    args = parser.parse_args()

    code = args.code
    max_cycles = args.max
    timeout = args.timeout
    backoff = args.backoff

    print(f"[{now_ts()}] Bot started | max={max_cycles or '∞'} | timeout={timeout}s")
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n[{now_ts()}] === Cycle {cycle} ===")
            success = run_cycle(code, attempt_timeout=timeout)
            
            if success:
                print(f"[{now_ts()}] 🎯 Cycle {cycle} complete - starting next cycle")
            else:
                wait = min(backoff * (2 ** (cycle - 1)), 300)
                print(f"[{now_ts()}] ⏳ Backing off {wait}s before retry...")
                time.sleep(wait)

            if max_cycles and cycle >= max_cycles:
                print(f"[{now_ts()}] Reached max cycles ({max_cycles}). Exiting.")
                break

    except KeyboardInterrupt:
        print(f"\n[{now_ts()}] Interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()