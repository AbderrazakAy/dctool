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
        self.claim_count = 0
        self.is_running = False
        
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
    
    def login(self):
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
    
    def claim_food(self):
        """Claim 50k food"""
        if not self.user_id or not self.session_id:
            if not self.login():
                return False
        
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
                    return True
                else:
                    if self.login():
                        time.sleep(1)
                        return self.claim_food()
                    return False
            else:
                return False
                
        except Exception as e:
            if self.login():
                time.sleep(1)
                return self.claim_food()
            return False
    
    def get_stats(self):
        """Get current statistics"""
        return {
            'claims': self.claim_count,
            'food': self.total_food_claimed,
            'running': self.is_running
        }
    
    def start_claiming(self):
        """Start the claiming process"""
        self.is_running = True
        
        if not self.login():
            return False
        
        def claim_loop():
            while self.is_running:
                success = self.claim_food()
                if not success:
                    time.sleep(2)
                    self.login()
        
        thread = Thread(target=claim_loop, daemon=True)
        thread.start()
        return True
    
    def stop_claiming(self):
        """Stop the claiming process"""
        self.is_running = False


class TelegramBot:
    def __init__(self, token, dragon_code):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.dragon_bot = DragonCityBot(dragon_code)
        self.last_update_id = 0
        self.authorized_users = set()
        
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
            welcome_msg = """🐉 *Dragon City Auto Claimer Bot*

Welcome! Available commands:

/startclaim - Start claiming food
/stop - Stop claiming
/stats - Show current statistics
/help - Show this message

Ready to start! 🚀"""
            self.send_message(chat_id, welcome_msg)
        
        elif command == '/startclaim':
            if self.dragon_bot.is_running:
                self.send_message(chat_id, "⚠️ Bot is already running!")
            else:
                if self.dragon_bot.start_claiming():
                    self.send_message(chat_id, "✅ *Started claiming food!*\n\nUse /stats to check progress")
                else:
                    self.send_message(chat_id, "❌ Failed to login. Check your code.")
        
        elif command == '/stop':
            if self.dragon_bot.is_running:
                self.dragon_bot.stop_claiming()
                stats = self.dragon_bot.get_stats()
                msg = f"""✅ *Bot Stopped*

📊 Final Statistics:
• Claims: {stats['claims']:,}
• Total Food: {stats['food']:,}"""
                self.send_message(chat_id, msg)
            else:
                self.send_message(chat_id, "⚠️ Bot is not running")
        
        elif command == '/stats':
            stats = self.dragon_bot.get_stats()
            status = "🟢 Running" if stats['running'] else "🔴 Stopped"
            msg = f"""📊 *Current Statistics*

Status: {status}
Claims: {stats['claims']:,}
Total Food: {stats['food']:,}
Time: {datetime.now().strftime('%H:%M:%S')}"""
            self.send_message(chat_id, msg)
        
        elif command == '/help':
            help_msg = """🐉 *Dragon City Bot Help*

*Commands:*
/startclaim - Start auto-claiming
/stop - Stop the bot
/stats - View statistics
/help - Show this message

*Features:*
• Auto claims 50k food continuously
• No delays between claims
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
                                if text.startswith('/'):
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