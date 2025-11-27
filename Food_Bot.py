import requests
import time
import json
from threading import Thread
from datetime import datetime

class DragonCityBot:
    def __init__(self, code):
        self.code = code
        self.session = requests.Session()
        self.user_id = None
        self.session_id = None
        self.total_food_claimed = 0
        self.total_gold_claimed = 0
        self.total_xp_claimed = 0
        self.claim_count = 0
        self.is_running = False
        self.session_start_time = None
        self.current_mode = None  # 'gold' or 'food'
        
        # Base headers
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/json',
            'origin': 'https://gamemodshub.com',
            'referer': 'https://gamemodshub.com/game/dragoncity/Login',
            'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
    
    def login(self, silent=False):
        """Login to Dragon City Tool"""
        url = 'https://gamemodshub.com/game/dragoncity/Login'
        payload = {
            "type": "login",
            "code": self.code
        }
        
        try:
            response = self.session.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'user_id' in data:
                    self.user_id = data['user_id']
                if 'session_id' in data:
                    self.session_id = data['session_id']
                
                if not self.user_id and 'DragonCityToolUserid' in self.session.cookies:
                    self.user_id = self.session.cookies['DragonCityToolUserid']
                if not self.session_id and 'DragonCityToolSession' in self.session.cookies:
                    self.session_id = self.session.cookies['DragonCityToolSession']
                
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def claim_gold_xp(self):
        """Claim gold and XP"""
        if not self.user_id or not self.session_id:
            if not self.login(silent=True):
                return {"success": False, "relogin": True}
        
        url = 'https://gamemodshub.com/game/dragoncity/script/packet'
        
        claim_headers = self.headers.copy()
        claim_headers['content-type'] = 'application/x-www-form-urlencoded'
        claim_headers['accept'] = 'application/json, text/javascript, */*; q=0.01'
        claim_headers['referer'] = 'https://gamemodshub.com/game/dragoncity/tools'
        
        payload = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'cmds': 'auto-gold-and-xp-50k',
            'shop_value': '1',
            'tree_of_life_dragon_select': '0',
            'type_edit_send_json': 'undefined',
            'claim_all_reward_value': '99',
            'rescue_current_node_id': '0',
            'breed_id': '0',
            'hatch_eggs_to_habitat_id': '0',
            'Hatch_id': '0',
            'hatchery_uid': '0',
            'map_dragons_id': '0',
            'map_items_id': '0',
            'breed_eggs_to_hatch_id': '0',
            'breed_dragon_1': '0',
            'breed_dragon_2': '0',
            'breed_in_map_id': '0',
            'farm_food_id': '0',
            'farm_in_map_id': '0',
            'runner_value': '',
            'values_itemsx': '1',
            'map_change_name_dragon': 'GameMods',
            'map_level_up_dragon': '1',
            'map_value_gold_dragon': '',
            'Mapx': '',
            'Mapy': '',
            'verify': 'true'
        }
        
        try:
            response = self.session.post(url, headers=claim_headers, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'success' in result or 'gold' in str(result).lower() or 'xp' in str(result).lower():
                    self.claim_count += 1
                    self.total_gold_claimed += 249950
                    self.total_xp_claimed += 74985
                    return {"success": True}
                else:
                    if self.login(silent=True):
                        time.sleep(1)
                        return self.claim_gold_xp()
                    return {"success": False, "relogin": True}
            else:
                return {"success": False, "relogin": True}
                
        except Exception as e:
            if self.login(silent=True):
                time.sleep(1)
                return self.claim_gold_xp()
            return {"success": False, "relogin": True}
    
    def claim_food(self):
        """Claim 50k food"""
        if not self.user_id or not self.session_id:
            if not self.login(silent=True):
                return {"success": False, "relogin": True}
        
        url = 'https://gamemodshub.com/game/dragoncity/script/packet'
        
        claim_headers = self.headers.copy()
        claim_headers['content-type'] = 'application/x-www-form-urlencoded'
        claim_headers['accept'] = 'application/json, text/javascript, */*; q=0.01'
        claim_headers['referer'] = 'https://gamemodshub.com/game/dragoncity/tools'
        
        payload = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'cmds': 'auto-food-50k',
            'shop_value': '1',
            'tree_of_life_dragon_select': '0',
            'type_edit_send_json': 'undefined',
            'claim_all_reward_value': '99',
            'rescue_current_node_id': '0',
            'breed_id': '0',
            'hatch_eggs_to_habitat_id': '0',
            'Hatch_id': '0',
            'hatchery_uid': '0',
            'map_dragons_id': '0',
            'map_items_id': '0',
            'breed_eggs_to_hatch_id': '0',
            'breed_dragon_1': '0',
            'breed_dragon_2': '0',
            'breed_in_map_id': '0',
            'farm_food_id': '0',
            'farm_in_map_id': '0',
            'runner_value': '',
            'values_itemsx': '1',
            'map_change_name_dragon': 'GameMods',
            'map_level_up_dragon': '1',
            'map_value_gold_dragon': '',
            'Mapx': '',
            'Mapy': '',
            'verify': 'true'
        }
        
        try:
            response = self.session.post(url, headers=claim_headers, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'success' in result or 'food' in str(result).lower():
                    self.claim_count += 1
                    self.total_food_claimed += 50000
                    return {"success": True}
                else:
                    if self.login(silent=True):
                        time.sleep(1)
                        return self.claim_food()
                    return {"success": False, "relogin": True}
            else:
                return {"success": False, "relogin": True}
                
        except Exception as e:
            if self.login(silent=True):
                time.sleep(1)
                return self.claim_food()
            return {"success": False, "relogin": True}
    
    def get_stats(self):
        """Get current statistics"""
        return {
            'claims': self.claim_count,
            'food': self.total_food_claimed,
            'gold': self.total_gold_claimed,
            'xp': self.total_xp_claimed,
            'running': self.is_running,
            'started': self.session_start_time,
            'mode': self.current_mode
        }
    
    def start_claiming(self, chat_id, callback, mode='food'):
        """Start the claiming process
        
        Args:
            chat_id: Telegram chat ID
            callback: Callback function for updates
            mode: 'gold' for gold/XP or 'food' for food
        """
        self.is_running = True
        self.active_chat_id = chat_id
        self.claim_count = 0
        self.total_food_claimed = 0
        self.total_gold_claimed = 0
        self.total_xp_claimed = 0
        self.current_mode = mode
        self.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.login():
            return False
        
        def claim_loop():
            while self.is_running:
                if self.current_mode == 'gold':
                    result = self.claim_gold_xp()
                else:
                    result = self.claim_food()
                
                if result.get("success"):
                    # Report every 10 claims
                    if self.claim_count % 10 == 0:
                        callback()
                elif result.get("relogin"):
                    # Notify about re-login attempt
                    callback(relogin=True)
                    time.sleep(2)
                    self.login(silent=True)
                else:
                    time.sleep(2)
                    self.login(silent=True)
                
                time.sleep(0.5)
        
        thread = Thread(target=claim_loop, daemon=True)
        thread.start()
        return True
    
    def stop_claiming(self):
        """Stop the claiming process"""
        self.is_running = False
        self.active_chat_id = None


class TelegramBot:
    def __init__(self, token, dragon_code):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.dragon_bot = DragonCityBot(dragon_code)
        self.last_update_id = 0
        self.authorized_users = set()
        self.active_chat_id = None
        
    def send_claim_update(self, relogin=False):
        """Send statistics update to active chat"""
        if self.active_chat_id:
            if relogin:
                msg = "🔄 Re-logging in..."
                self.send_message(self.active_chat_id, msg)
            else:
                stats = self.dragon_bot.get_stats()
                if stats['mode'] == 'gold':
                    msg = f"""✅ Claim #{stats['claims']} successful!
💰 Total gold: {stats['gold']:,}
⭐ Total XP: {stats['xp']:,}"""
                else:
                    msg = f"""✅ Claim #{stats['claims']} successful!
🍖 Total food: {stats['food']:,}"""
                self.send_message(self.active_chat_id, msg)
    
    def send_message(self, chat_id, text, parse_mode='Markdown'):
        """Send a message to a chat"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def get_updates(self):
        """Get updates from Telegram"""
        url = f"{self.base_url}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': 30
        }
        try:
            response = requests.get(url, params=params, timeout=35)
            return response.json()
        except Exception as e:
            print(f"Error getting updates: {e}")
            return None
    
    def handle_command(self, chat_id, command, username):
        """Handle bot commands"""
        # Auto-authorize first user
        if not self.authorized_users:
            self.authorized_users.add(chat_id)
        
        if chat_id not in self.authorized_users:
            self.send_message(chat_id, "❌ Unauthorized access")
            return
        
        if command == '/start':
            welcome_msg = """🤖 *Welcome to Dragon City Auto Claimer!*

Commands:
• `/gold` - Start claiming gold & XP
• `/food` - Start claiming food
• `/stop` - Stop claiming
• `/stats` - View your stats
• `/help` - Show help

Ready to start! 🚀"""
            self.send_message(chat_id, welcome_msg)
        
        elif command == '/gold' or command == '1':
            if self.dragon_bot.is_running:
                self.send_message(chat_id, "⚠️ Bot is already running! Use /stop to stop it first.")
            else:
                self.send_message(chat_id, "🔐 Logging in...")
                
                if self.dragon_bot.start_claiming(chat_id, self.send_claim_update, mode='gold'):
                    self.active_chat_id = chat_id
                    self.send_message(chat_id, "✅ Login successful!\n💰 Starting gold & XP claims...")
                else:
                    self.send_message(chat_id, "❌ Login failed! Please check your code.")
        
        elif command == '/food' or command == '2':
            if self.dragon_bot.is_running:
                self.send_message(chat_id, "⚠️ Bot is already running! Use /stop to stop it first.")
            else:
                self.send_message(chat_id, "🔐 Logging in...")
                
                if self.dragon_bot.start_claiming(chat_id, self.send_claim_update, mode='food'):
                    self.active_chat_id = chat_id
                    self.send_message(chat_id, "✅ Login successful!\n🍖 Starting food claims...")
                else:
                    self.send_message(chat_id, "❌ Login failed! Please check your code.")
        
        elif command == '/stop':
            if self.dragon_bot.is_running:
                self.dragon_bot.stop_claiming()
                stats = self.dragon_bot.get_stats()
                
                if stats['mode'] == 'gold':
                    msg = f"""🛑 *Bot Stopped!*

📊 *Final Stats:*
• Claims: {stats['claims']}
• Gold earned: {stats['gold']:,}
• XP earned: {stats['xp']:,}
• Started: {stats.get('started', 'N/A')}"""
                else:
                    msg = f"""🛑 *Bot Stopped!*

📊 *Final Stats:*
• Claims: {stats['claims']}
• Food earned: {stats['food']:,}
• Started: {stats.get('started', 'N/A')}"""
                
                self.send_message(chat_id, msg)
                self.active_chat_id = None
            else:
                self.send_message(chat_id, "⚠️ Bot is not running")
        
        elif command == '/stats':
            stats = self.dragon_bot.get_stats()
            if not stats.get('started'):
                self.send_message(chat_id, "❌ No stats available. Start claiming first with /gold or /food")
                return
            
            status = "🟢 Active" if stats['running'] else "🔴 Stopped"
            mode_emoji = "💰" if stats['mode'] == 'gold' else "🍖"
            mode_name = "Gold & XP" if stats['mode'] == 'gold' else "Food"
            
            if stats['mode'] == 'gold':
                msg = f"""📊 *Your Stats*

Status: {status}
Mode: {mode_emoji} {mode_name}
• Claims: {stats['claims']}
• Gold earned: {stats['gold']:,}
• XP earned: {stats['xp']:,}
• Started: {stats.get('started', 'N/A')}"""
            else:
                msg = f"""📊 *Your Stats*

Status: {status}
Mode: {mode_emoji} {mode_name}
• Claims: {stats['claims']}
• Food earned: {stats['food']:,}
• Started: {stats.get('started', 'N/A')}"""
            
            self.send_message(chat_id, msg)
        
        elif command == '/help':
            help_msg = """🉐 *Dragon City Bot Help*

*Commands:*
/gold (or send '1') - Claim gold & XP
/food (or send '2') - Claim food
/stop - Stop the bot
/stats - View statistics
/help - Show this message

*Claim Rates:*
💰 Gold mode: 249,950 gold + 74,985 XP per claim
🍖 Food mode: 50,000 food per claim

*Features:*
• Auto claims continuously
• Updates every 10 claims
• Auto re-login on errors
• Real-time statistics"""
            self.send_message(chat_id, help_msg)
        
        else:
            self.send_message(chat_id, "❓ Unknown command. Use /help for available commands.")
    
    def run(self):
        """Run the bot"""
        print("🤖 Telegram bot started!")
        print("Send /start to your bot to begin\n")
        
        while True:
            try:
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            message = update['message']
                            chat_id = message['chat']['id']
                            username = message['from'].get('username', 'Unknown')
                            
                            if 'text' in message:
                                text = message['text']
                                if text.startswith('/') or text in ['1', '2']:
                                    self.handle_command(chat_id, text, username)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Bot stopped by user")
                if self.dragon_bot.is_running:
                    self.dragon_bot.stop_claiming()
                break
            except Exception as e:
                print(f"Error in bot loop: {e}")
                time.sleep(5)


# Configuration
if __name__ == "__main__":
    TELEGRAM_TOKEN = "8376059118:AAGPH_mO_Ftg6CBis8ZJjbKxMEhqpv5yVHM"
    DRAGON_CODE = "eaba7c88325347e0d8050ca295ec6948"
    
    # Create and run bot
    bot = TelegramBot(TELEGRAM_TOKEN, DRAGON_CODE)
    bot.run()