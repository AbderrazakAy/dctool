import requests
import asyncio
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading
import time
import logging

# Telegram Bot Token
TELEGRAM_TOKEN = "8463777160:AAGj3hlXJcOQcFoX1XnY19PAmclKXYi00Rg"

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

# Global state for each user
user_states = {}  # Dictionary to store user-specific data: {chat_id: {"phpsessid": str, "mode": str, "running": bool, "totals": dict, "request_count": int, "message_id": int}}

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def make_request(data, user_cookies):
    """Make a single API request with specified form data"""
    try:
        response = requests.post(url, headers=headers, cookies=user_cookies, data=data)
        return response, None
    except requests.exceptions.RequestException as e:
        return None, str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    user_states[chat_id] = {
        "phpsessid": None,
        "mode": None,
        "running": False,
        "totals": {"gold": 0, "xp": 0, "food": 0},
        "request_count": 0,
        "message_id": None
    }
    await update.message.reply_text(
        "👋 Welcome to the Gold, XP, and Food Claim Bot!\n"
        "1. Use /setphpsessid to set your PHPSESSID.\n"
        "2. Use /setmode to choose a mode (Gold/XP, Food, or both).\n"
        "3. Use /run to start the bot.\n"
        "4. Use /stop to stop the bot.\n"
        "5. Use /stats to view current totals."
    )

async def set_phpsessid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setphpsessid command"""
    chat_id = update.effective_chat.id
    if chat_id not in user_states:
        user_states[chat_id] = {
            "phpsessid": None,
            "mode": None,
            "running": False,
            "totals": {"gold": 0, "xp": 0, "food": 0},
            "request_count": 0,
            "message_id": None
        }
    
    await update.message.reply_text("🔐 Please send your PHPSESSID.")
    context.user_data["awaiting_phpsessid"] = True

async def handle_phpsessid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PHPSESSID input"""
    chat_id = update.effective_chat.id
    if context.user_data.get("awaiting_phpsessid", False):
        phpsessid = update.message.text.strip()
        if not phpsessid:
            await update.message.reply_text("❌ No PHPSESSID provided. Please try again with /setphpsessid.")
        else:
            user_states[chat_id]["phpsessid"] = phpsessid
            context.user_data["awaiting_phpsessid"] = False
            await update.message.reply_text("✅ PHPSESSID set successfully! Use /setmode to choose a mode.")
    else:
        await update.message.reply_text("❌ Please use /setphpsessid first to set your PHPSESSID.")

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setmode command"""
    chat_id = update.effective_chat.id
    if chat_id not in user_states or not user_states[chat_id]["phpsessid"]:
        await update.message.reply_text("❌ Please set your PHPSESSID first with /setphpsessid.")
        return
    
    await update.message.reply_text(
        "Select bot mode:\n"
        "1. Claim Gold & XP\n"
        "2. Transfer Food\n"
        "3. Claim Gold, XP, and Food\n"
        "Reply with 1, 2, or 3."
    )
    context.user_data["awaiting_mode"] = True

async def handle_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mode selection input"""
    chat_id = update.effective_chat.id
    if context.user_data.get("awaiting_mode", False):
        choice = update.message.text.strip()
        if choice == "1":
            user_states[chat_id]["mode"] = "gold_xp"
            mode_text = "Gold & XP Claim Bot"
        elif choice == "2":
            user_states[chat_id]["mode"] = "food"
            mode_text = "Food Transfer Bot"
        elif choice == "3":
            user_states[chat_id]["mode"] = "both"
            mode_text = "Gold, XP, and Food Claim Bot"
        else:
            await update.message.reply_text("❌ Invalid choice. Please reply with 1, 2, or 3.")
            return
        
        context.user_data["awaiting_mode"] = False
        await update.message.reply_text(f"✅ Mode set to {mode_text}! Use /run to start the bot.")
    else:
        await update.message.reply_text("❌ Please use /setmode first to select a mode.")

async def run_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /run command"""
    chat_id = update.effective_chat.id
    if chat_id not in user_states or not user_states[chat_id]["phpsessid"]:
        await update.message.reply_text("❌ Please set your PHPSESSID first with /setphpsessid.")
        return
    if not user_states[chat_id]["mode"]:
        await update.message.reply_text("❌ Please set a mode first with /setmode.")
        return
    if user_states[chat_id]["running"]:
        await update.message.reply_text("⚠️ Bot is already running! Use /stop to stop it.")
        return
    
    user_states[chat_id]["running"] = True
    user_states[chat_id]["totals"] = {"gold": 0, "xp": 0, "food": 0}
    user_states[chat_id]["request_count"] = 0
    
    mode_text = {
        "gold_xp": "Gold & XP Claim Bot",
        "food": "Food Transfer Bot",
        "both": "Gold, XP, and Food Claim Bot"
    }
    
    await update.message.reply_text(f"🏆 Starting {mode_text[user_states[chat_id]['mode']]}...")
    
    # Send initial status message
    status_line = f"Request #0 | "
    if user_states[chat_id]["mode"] in ["gold_xp", "both"]:
        status_line += f"Gold: 0 | XP: 0"
    if user_states[chat_id]["mode"] in ["food", "both"]:
        status_line += f"{' | ' if user_states[chat_id]['mode'] == 'both' else ''}Food: 0"
    status_message = await update.message.reply_text(status_line)
    user_states[chat_id]["message_id"] = status_message.message_id
    
    # Run bot loop in a separate thread
    loop = asyncio.get_event_loop()
    threading.Thread(
        target=bot_loop,
        args=(context.bot, loop, chat_id, user_states[chat_id]["mode"], user_states[chat_id]["phpsessid"]),
        daemon=True
    ).start()

def bot_loop(bot, loop, chat_id, mode, phpsessid):
    """Background loop for making API requests"""
    user_cookies = cookies.copy()
    user_cookies["PHPSESSID"] = phpsessid
    totals = user_states[chat_id]["totals"]
    
    while user_states[chat_id]["running"]:
        user_states[chat_id]["request_count"] += 1
        request_count = user_states[chat_id]["request_count"]
        
        status_line = f"Request #{request_count} | "
        if mode in ["gold_xp", "both"]:
            status_line += f"Gold: {totals['gold']:,} | XP: {totals['xp']:,}"
        if mode in ["food", "both"]:
            status_line += f"{' | ' if mode == 'both' else ''}Food: {totals['food']:,}"
        
        # Update status message
        try:
            asyncio.run_coroutine_threadsafe(
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=user_states[chat_id]["message_id"],
                    text=status_line
                ),
                loop
            ).result()
        except telegram.error.TelegramError as e:
            logger.error(f"Failed to update message: {e}")
            asyncio.run_coroutine_threadsafe(
                bot.send_message(chat_id=chat_id, text=f"💥 Failed to update status: {e}"),
                loop
            ).result()
        
        if mode == "gold_xp":
            response, error = make_request(data_gold_xp, user_cookies)
            if response and response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get('success', False):
                        totals["gold"] += 150000
                        totals["xp"] += 45000
                    else:
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(chat_id=chat_id, text=f"❌ API returned success=false: {response_data.get('message', 'Unknown error')}"),
                            loop
                        ).result()
                except:
                    totals["gold"] += 150000
                    totals["xp"] += 45000
            else:
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(chat_id=chat_id, text=f"❌ HTTP Error {response.status_code if response else 'No response'}: {error if error else ''}\nStopping bot..."),
                    loop
                ).result()
                user_states[chat_id]["running"] = False
                break
        
        elif mode == "food":
            response, error = make_request(data_food, user_cookies)
            if response and response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get('success', False):
                        totals["food"] += 45000
                    else:
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(chat_id=chat_id, text=f"❌ API returned success=false: {response_data.get('message', 'Unknown error')}"),
                            loop
                        ).result()
                except:
                    totals["food"] += 45000
            else:
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(chat_id=chat_id, text=f"❌ HTTP Error {response.status_code if response else 'No response'}: {error if error else ''}\nStopping bot..."),
                    loop
                ).result()
                user_states[chat_id]["running"] = False
                break
        
        elif mode == "both":
            gold_xp_success = False
            response_gold_xp, error_gold_xp = make_request(data_gold_xp, user_cookies)
            if response_gold_xp and response_gold_xp.status_code == 200:
                try:
                    response_data = response_gold_xp.json()
                    if response_data.get('success', False):
                        totals["gold"] += 150000
                        totals["xp"] += 45000
                        gold_xp_success = True
                    else:
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(chat_id=chat_id, text=f"❌ Gold/XP API returned success=false: {response_data.get('message', 'Unknown error')}"),
                            loop
                        ).result()
                except:
                    totals["gold"] += 150000
                    totals["xp"] += 45000
                    gold_xp_success = True
            
            food_success = False
            response_food, error_food = make_request(data_food, user_cookies)
            if response_food and response_food.status_code == 200:
                try:
                    response_data = response_food.json()
                    if response_data.get('success', False):
                        totals["food"] += 45000
                        food_success = True
                    else:
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(chat_id=chat_id, text=f"❌ Food API returned success=false: {response_data.get('message', 'Unknown error')}"),
                            loop
                        ).result()
                except:
                    totals["food"] += 45000
                    food_success = True
            
            if not (gold_xp_success or food_success):
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(chat_id=chat_id, text=f"❌ Both requests failed: {error_gold_xp or ''} {error_food or ''}\nStopping bot..."),
                    loop
                ).result()
                user_states[chat_id]["running"] = False
                break
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.05)  # 50ms delay

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    chat_id = update.effective_chat.id
    if chat_id not in user_states or not user_states[chat_id]["running"]:
        await update.message.reply_text("⚠️ Bot is not running!")
        return
    
    user_states[chat_id]["running"] = False
    totals = user_states[chat_id]["totals"]
    request_count = user_states[chat_id]["request_count"]
    mode = user_states[chat_id]["mode"]
    
    final_stats = f"🛑 Bot stopped after {request_count} requests\n📊 Final Stats:\n"
    if mode in ["gold_xp", "both"]:
        final_stats += f"   • Total gold earned: {totals['gold']:,}\n"
        final_stats += f"   • Total XP earned: {totals['xp']:,}\n"
    if mode in ["food", "both"]:
        final_stats += f"   • Total food transferred: {totals['food']:,}"
    
    await update.message.reply_text(final_stats)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    chat_id = update.effective_chat.id
    if chat_id not in user_states:
        await update.message.reply_text("⚠️ Bot has not been started. Use /start to begin.")
        return
    
    totals = user_states[chat_id]["totals"]
    request_count = user_states[chat_id]["request_count"]
    mode = user_states[chat_id]["mode"]
    
    stats_text = f"📊 Current Stats after {request_count} requests:\n"
    if mode in ["gold_xp", "both"]:
        stats_text += f"   • Total gold earned: {totals['gold']:,}\n"
        stats_text += f"   • Total XP earned: {totals['xp']:,}\n"
    if mode in ["food", "both"]:
        stats_text += f"   • Total food transferred: {totals['food']:,}"
    
    await update.message.reply_text(stats_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_chat:
        await update.effective_chat.send_message(f"💥 An error occurred: {context.error}")

def main():
    """Run the Telegram bot"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setphpsessid", set_phpsessid))
    app.add_handler(CommandHandler("setmode", set_mode))
    app.add_handler(CommandHandler("run", run_bot))
    app.add_handler(CommandHandler("stop", stop_bot))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phpsessid), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mode), group=2)
    app.add_error_handler(error_handler)
    
    app.run_polling()

if __name__ == "__main__":
    main()