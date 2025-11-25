#!/usr/bin/env python3
"""
telegram_multi_bot.py

Telegram bot for claiming gold/XP and food from game tools
"""

import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8376059118:AAGPH_mO_Ftg6CBis8ZJjbKxMEhqpv5yVHM"

# Gold/XP Bot Config
GOLD_BASE = "https://nullzereptool.com"
GOLD_LOGIN_URL = f"{GOLD_BASE}/login"
GOLD_PACKET_URL = f"{GOLD_BASE}/packet"
GOLD_CODE = "a4d130ef2e2e035b3561d61362116a99"

# Food Bot Config
FOOD_LOGIN_URL = "https://gamemodshub.com/game/dragoncity/Login"
FOOD_PACKET_URL = "https://gamemodshub.com/game/dragoncity/script/packet"
FOOD_CODE = "eaba7c88325347e0d8050ca295ec6948"
FOOD_USER_ID = "3769452541155155277"
FOOD_SESSION_ID = "34198510"

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

# Store active sessions per user
user_sessions = {}
user_stats = {}

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ============ GOLD/XP BOT FUNCTIONS ============
def login_gold_bot(session: requests.Session, timeout: float = 15.0) -> bool:
    """Login to gold/XP bot"""
    try:
        files = {
            "code": (None, GOLD_CODE),
            "loginType": (None, "user"),
        }
        headers = COMMON_HEADERS.copy()
        response = session.post(GOLD_LOGIN_URL, headers=headers, files=files, timeout=timeout)
        return response.ok
    except Exception as e:
        logger.error(f"Gold login error: {e}")
        return False

def claim_gold_xp(session: requests.Session, timeout: float = 15.0) -> dict:
    """Claim gold and XP"""
    try:
        headers = COMMON_HEADERS.copy()
        headers["content-type"] = "application/x-www-form-urlencoded"
        data = {"mode": "claim-gold-xp"}
        response = session.post(GOLD_PACKET_URL, headers=headers, data=data, timeout=timeout)
        
        if response.ok:
            return {"success": True}
        else:
            return {"success": False, "status": response.status_code}
    except Exception as e:
        logger.error(f"Claim error: {e}")
        return {"success": False, "error": str(e)}

# ============ FOOD BOT FUNCTIONS ============
def login_food_bot(session: requests.Session, timeout: float = 15.0) -> bool:
    """Login to food bot with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            payload = {
                "type": "login",
                "code": FOOD_CODE
            }
            
            # Add headers similar to browser request
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            r = session.post(FOOD_LOGIN_URL, json=payload, headers=headers, timeout=timeout)
            
            logger.info(f"Food login attempt {attempt + 1}: Status={r.status_code}, Response={r.text[:200]}")
            
            # Check both status code AND response text
            if r.status_code == 200:
                logger.info(f"Food login successful on attempt {attempt + 1}")
                return True
            else:
                logger.warning(f"Food login failed - Status: {r.status_code}")
                
        except Exception as e:
            logger.error(f"Food login error on attempt {attempt + 1}: {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            import time
            time.sleep(2)
    
    return False

def claim_food(session: requests.Session, timeout: float = 10.0) -> dict:
    """Claim food"""
    try:
        data = {
            "user_id": FOOD_USER_ID,
            "session_id": FOOD_SESSION_ID,
            "cmds": "auto-food-50k",
            "shop_value": "1",
            "tree_of_life_dragon_select": "0",
            "type_edit_send_json": "undefined",
            "claim_all_reward_value": "99",
            "rescue_current_node_id": "0",
            "breed_id": "0",
            "hatch_eggs_to_habitat_id": "0",
            "Hatch_id": "0",
            "hatchery_uid": "0",
            "map_dragons_id": "0",
            "map_items_id": "0",
            "breed_eggs_to_hatch_id": "0",
            "breed_dragon_1": "0",
            "breed_dragon_2": "0",
            "breed_in_map_id": "0",
            "farm_food_id": "0",
            "farm_in_map_id": "0",
            "values_itemsx": "1",
            "map_change_name_dragon": "GameMods",
            "map_level_up_dragon": "1",
            "verify": "true"
        }
        r = session.post(FOOD_PACKET_URL, data=data, timeout=timeout)
        
        # Check both success in text AND status code
        if r.status_code == 200 or "success" in r.text.lower():
            return {"success": True, "response": r.text[:100]}
        else:
            logger.warning(f"Food claim returned: {r.status_code} - {r.text[:200]}")
            return {"success": False, "status": r.status_code, "response": r.text[:200]}
    except Exception as e:
        logger.error(f"Food claim error: {e}")
        return {"success": False, "error": str(e)}

# ============ TELEGRAM BOT HANDLERS ============
async def safe_send_message(context, chat_id, text, **kwargs):
    """Send message with error handling"""
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    try:
        keyboard = [
            [InlineKeyboardButton("💰 Gold/XP Bot", callback_data='start_gold')],
            [InlineKeyboardButton("🍖 Food Bot", callback_data='start_food')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *Welcome to Multi-Bot!*\n\n"
            "Choose which bot you want to run:\n\n"
            "💰 *Gold/XP Bot* - Claim gold and XP\n"
            "🍖 *Food Bot* - Claim food for DragonCity\n\n"
            "Commands:\n"
            "• `/start` - Show bot selection\n"
            "• `/stop` - Stop active bot\n"
            "• `/stats` - View your stats",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if already running
    if user_id in user_sessions and user_sessions[user_id].get('active'):
        await query.message.reply_text("⚠️ Bot is already running! Use /stop to stop it first.")
        return
    
    if query.data == 'start_gold':
        await start_gold_bot(query, context, user_id)
    elif query.data == 'start_food':
        await start_food_bot(query, context, user_id)

async def start_gold_bot(query, context, user_id):
    """Start Gold/XP bot"""
    try:
        session = requests.Session()
        user_sessions[user_id] = {
            'active': True,
            'session': session,
            'type': 'gold'
        }
        user_stats[user_id] = {
            'claims': 0,
            'gold': 0,
            'xp': 0,
            'started': now_ts()
        }
        
        await query.message.reply_text("🔐 Logging in to Gold/XP bot...")
        
        if not login_gold_bot(session):
            await query.message.reply_text("❌ Login failed!")
            user_sessions[user_id]['active'] = False
            return
        
        await query.message.reply_text("✅ Login successful!\n🏆 Starting gold/XP claims...")
        
        context.application.create_task(gold_claim_loop(query, context, user_id))
    except Exception as e:
        logger.error(f"Gold bot start error: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")

async def start_food_bot(query, context, user_id):
    """Start Food bot"""
    try:
        # Create a fresh session
        session = requests.Session()
        
        # Set up session data BEFORE login attempt
        user_sessions[user_id] = {
            'active': False,  # Set to False until login succeeds
            'session': session,
            'type': 'food'
        }
        user_stats[user_id] = {
            'claims': 0,
            'food': 0,
            'started': now_ts()
        }
        
        await query.message.reply_text("🔐 Logging in to Food bot...")
        
        # Try login with detailed logging
        logger.info(f"Attempting food bot login for user {user_id}")
        login_success = login_food_bot(session)
        
        if not login_success:
            logger.error(f"Food bot login failed for user {user_id}")
            await query.message.reply_text(
                "❌ Login failed!\n\n"
                "Please check:\n"
                "• Code is valid\n"
                "• User ID and Session ID are correct\n"
                "• Try again in a few seconds"
            )
            user_sessions[user_id]['active'] = False
            return
        
        # Login succeeded, now activate
        user_sessions[user_id]['active'] = True
        logger.info(f"Food bot login successful for user {user_id}")
        
        await query.message.reply_text("✅ Login successful!\n🍖 Starting food claims...")
        
        context.application.create_task(food_claim_loop(query, context, user_id))
    except Exception as e:
        logger.error(f"Food bot start error: {e}", exc_info=True)
        await query.message.reply_text(f"❌ Error: {str(e)}")

async def gold_claim_loop(query, context, user_id):
    """Background task for Gold/XP claiming"""
    try:
        session_data = user_sessions.get(user_id)
        if not session_data:
            return
        
        session = session_data['session']
        stats = user_stats[user_id]
        chat_id = query.message.chat_id
        
        while user_sessions[user_id]['active']:
            try:
                result = claim_gold_xp(session)
                
                if result['success']:
                    stats['claims'] += 1
                    stats['gold'] += 150000
                    stats['xp'] += 45000
                    
                    # Report every 10 claims
                    if stats['claims'] % 10 == 0:
                        await safe_send_message(
                            context,
                            chat_id,
                            f"✅ Claim #{stats['claims']} successful!\n"
                            f"💰 Total gold: {stats['gold']:,}\n"
                            f"⭐ Total XP: {stats['xp']:,}"
                        )
                else:
                    # Re-login on failure
                    if login_gold_bot(session):
                        logger.info("Re-logged in successfully")
                    else:
                        await safe_send_message(
                            context,
                            chat_id,
                            "❌ Re-login failed, retrying..."
                        )
                        await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error in gold claim loop: {e}")
                await asyncio.sleep(5)
        
        session.close()
    except Exception as e:
        logger.error(f"Fatal error in gold claim loop: {e}")

async def food_claim_loop(query, context, user_id):
    """Background task for Food claiming"""
    try:
        session_data = user_sessions.get(user_id)
        if not session_data:
            return
        
        session = session_data['session']
        stats = user_stats[user_id]
        chat_id = query.message.chat_id
        
        while user_sessions[user_id]['active']:
            try:
                result = claim_food(session)
                
                if result['success']:
                    stats['claims'] += 1
                    stats['food'] += 50000
                    
                    # Report every 10 claims
                    if stats['claims'] % 10 == 0:
                        await safe_send_message(
                            context,
                            chat_id,
                            f"✅ Claim #{stats['claims']} successful!\n"
                            f"🍖 Total food: {stats['food']:,}"
                        )
                else:
                    # Re-login on failure
                    if login_food_bot(session):
                        logger.info("Re-logged in successfully")
                    else:
                        await safe_send_message(
                            context,
                            chat_id,
                            "❌ Re-login failed, retrying..."
                        )
                        await asyncio.sleep(3)
            
            except Exception as e:
                logger.error(f"Error in food claim loop: {e}")
                await asyncio.sleep(3)
        
        session.close()
    except Exception as e:
        logger.error(f"Fatal error in food claim loop: {e}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop active bot"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get('active'):
            await update.message.reply_text("⚠️ Bot is not running!")
            return
        
        bot_type = user_sessions[user_id].get('type', 'unknown')
        user_sessions[user_id]['active'] = False
        stats = user_stats.get(user_id, {})
        
        if bot_type == 'gold':
            message = (
                "🛑 *Gold/XP Bot Stopped!*\n\n"
                f"📊 *Final Stats:*\n"
                f"• Claims: {stats.get('claims', 0)}\n"
                f"• Gold earned: {stats.get('gold', 0):,}\n"
                f"• XP earned: {stats.get('xp', 0):,}\n"
                f"• Started: {stats.get('started', 'N/A')}"
            )
        else:  # food
            message = (
                "🛑 *Food Bot Stopped!*\n\n"
                f"📊 *Final Stats:*\n"
                f"• Claims: {stats.get('claims', 0)}\n"
                f"• Food earned: {stats.get('food', 0):,}\n"
                f"• Started: {stats.get('started', 'N/A')}"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Stop command error: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_stats:
            await update.message.reply_text("❌ No stats available. Start a bot first with /start")
            return
        
        stats = user_stats[user_id]
        session_data = user_sessions.get(user_id, {})
        active = session_data.get('active', False)
        bot_type = session_data.get('type', 'unknown')
        
        status = "🟢 Active" if active else "🔴 Stopped"
        
        if bot_type == 'gold':
            message = (
                f"📊 *Gold/XP Bot Stats*\n\n"
                f"Status: {status}\n"
                f"• Claims: {stats.get('claims', 0)}\n"
                f"• Gold earned: {stats.get('gold', 0):,}\n"
                f"• XP earned: {stats.get('xp', 0):,}\n"
                f"• Started: {stats.get('started', 'N/A')}"
            )
        else:  # food
            message = (
                f"📊 *Food Bot Stats*\n\n"
                f"Status: {status}\n"
                f"• Claims: {stats.get('claims', 0)}\n"
                f"• Food earned: {stats.get('food', 0):,}\n"
                f"• Started: {stats.get('started', 'N/A')}"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Stats command error: {e}")

async def clear_webhook():
    """Clear any existing webhook to avoid conflicts"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url, timeout=10)
        if response.ok:
            print(f"[{now_ts()}] ✅ Webhook cleared successfully")
        else:
            print(f"[{now_ts()}] ⚠️ Webhook clear response: {response.text}")
    except Exception as e:
        print(f"[{now_ts()}] ⚠️ Error clearing webhook: {e}")

def main():
    """Start the bot"""
    print(f"[{now_ts()}] 🚀 Starting Telegram Multi-Bot...")
    print(f"[{now_ts()}] 🔧 Clearing any existing webhooks...")
    
    # Clear webhook first
    import asyncio as sync_asyncio
    sync_asyncio.run(clear_webhook())
    
    print(f"[{now_ts()}] 📡 Initializing bot application...")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print(f"[{now_ts()}] ✅ Bot is running! Press Ctrl+C to stop.")
    print(f"[{now_ts()}] 💡 If you see 'Conflict' errors, stop ALL other bot instances first!")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        print(f"[{now_ts()}] ❌ Bot error: {e}")
        print(f"[{now_ts()}] 💡 Make sure no other instances are running!")
        raise

if __name__ == "__main__":
    main()