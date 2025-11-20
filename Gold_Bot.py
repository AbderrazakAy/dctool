#!/usr/bin/env python3
"""
telegram_gold_xp_bot.py

Telegram bot for claiming gold/XP from nullzereptool
"""

import requests
import time
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8376059118:AAGPH_mO_Ftg6CBis8ZJjbKxMEhqpv5yVHM"

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

# Store active sessions per user
user_sessions = {}
user_stats = {}

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def login_with_code(session: requests.Session, code: str, timeout: float = 15.0) -> bool:
    """Login using the provided code"""
    try:
        files = {
            "code": (None, code),
            "loginType": (None, "user"),
        }
        headers = COMMON_HEADERS.copy()
        response = session.post(LOGIN_URL, headers=headers, files=files, timeout=timeout)
        return response.ok
    except Exception as e:
        logger.error(f"Login error: {e}")
        return False

def claim_gold_xp(session: requests.Session, timeout: float = 15.0) -> dict:
    """Claim gold and XP, return result"""
    try:
        headers = COMMON_HEADERS.copy()
        headers["content-type"] = "application/x-www-form-urlencoded"
        data = {"mode": "claim-gold-xp"}
        response = session.post(PACKET_URL, headers=headers, data=data, timeout=timeout)
        
        if response.ok:
            try:
                return {"success": True, "data": response.json()}
            except:
                return {"success": True, "data": None}
        else:
            return {"success": False, "status": response.status_code}
    except Exception as e:
        logger.error(f"Claim error: {e}")
        return {"success": False, "error": str(e)}

async def safe_send_message(context, chat_id, text, **kwargs):
    """Send message with error handling"""
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    try:
        await update.message.reply_text(
            "🤖 *Welcome to Gold/XP Claim Bot!*\n\n"
            "Commands:\n"
            "• `/claim <code>` - Start claiming gold/XP\n"
            "• `/stop` - Stop claiming\n"
            "• `/stats` - View your stats\n\n"
            "Example: `/claim a4d130ef2e2e035b3561d61362116a98`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start claiming gold/XP"""
    try:
        user_id = update.effective_user.id
        
        # Check if already running
        if user_id in user_sessions and user_sessions[user_id].get('active'):
            await update.message.reply_text("⚠️ Bot is already running! Use /stop to stop it first.")
            return
        
        # Get code from command
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide your login code!\n\n"
                "Usage: `/claim <your_code>`",
                parse_mode='Markdown'
            )
            return
        
        code = context.args[0]
        
        # Initialize session
        session = requests.Session()
        user_sessions[user_id] = {
            'active': True,
            'session': session,
            'code': code
        }
        user_stats[user_id] = {
            'claims': 0,
            'gold': 0,
            'xp': 0,
            'started': now_ts()
        }
        
        await update.message.reply_text("🔐 Logging in...")
        
        # Initial login
        if not login_with_code(session, code):
            await update.message.reply_text("❌ Login failed! Please check your code.")
            user_sessions[user_id]['active'] = False
            return
        
        await update.message.reply_text("✅ Login successful!\n🏆 Starting claims...")
        
        # Start claiming loop in background
        context.application.create_task(claim_loop(update, context, user_id))
    except Exception as e:
        logger.error(f"Claim command error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def claim_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Background task for claiming"""
    try:
        session_data = user_sessions.get(user_id)
        if not session_data:
            return
        
        session = session_data['session']
        code = session_data['code']
        stats = user_stats[user_id]
        
        chat_id = update.effective_chat.id
        
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
                    if login_with_code(session, code):
                        logger.info("Re-logged in successfully")
                    else:
                        await safe_send_message(
                            context,
                            chat_id,
                            "❌ Re-login failed, retrying in 5s..."
                        )
                        await asyncio.sleep(5)
                
                # Small delay between claims
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error in claim loop: {e}")
                await asyncio.sleep(5)
        
        # Cleanup
        session.close()
    except Exception as e:
        logger.error(f"Fatal error in claim loop: {e}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop claiming"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_sessions or not user_sessions[user_id].get('active'):
            await update.message.reply_text("⚠️ Bot is not running!")
            return
        
        user_sessions[user_id]['active'] = False
        stats = user_stats.get(user_id, {})
        
        await update.message.reply_text(
            "🛑 *Bot Stopped!*\n\n"
            f"📊 *Final Stats:*\n"
            f"• Claims: {stats.get('claims', 0)}\n"
            f"• Gold earned: {stats.get('gold', 0):,}\n"
            f"• XP earned: {stats.get('xp', 0):,}\n"
            f"• Started: {stats.get('started', 'N/A')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Stop command error: {e}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_stats:
            await update.message.reply_text("❌ No stats available. Start claiming first with /claim")
            return
        
        stats = user_stats[user_id]
        active = user_sessions.get(user_id, {}).get('active', False)
        status = "🟢 Active" if active else "🔴 Stopped"
        
        await update.message.reply_text(
            f"📊 *Your Stats*\n\n"
            f"Status: {status}\n"
            f"• Claims: {stats.get('claims', 0)}\n"
            f"• Gold earned: {stats.get('gold', 0):,}\n"
            f"• XP earned: {stats.get('xp', 0):,}\n"
            f"• Started: {stats.get('started', 'N/A')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Stats command error: {e}")

def main():
    """Start the bot"""
    print(f"[{now_ts()}] 🚀 Starting Telegram Bot...")
    
    # Create application with longer timeout
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
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    print(f"[{now_ts()}] ✅ Bot is running! Press Ctrl+C to stop.")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()