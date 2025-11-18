#!/usr/bin/env python3
"""
telegram_gold_xp_bot.py

Telegram bot for claiming gold/XP from nullzereptool
"""

import requests
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Bot configuration
BOT_TOKEN = "8211838996:AAFRegUpOsZhvXd2TGXjWPxvIvHd-mecD1I"

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
    except:
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
        return {"success": False, "error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text(
        "🤖 *Welcome to Gold/XP Claim Bot!*\n\n"
        "Commands:\n"
        "• `/claim <code>` - Start claiming gold/XP\n"
        "• `/stop` - Stop claiming\n"
        "• `/stats` - View your stats\n\n"
        "Example: `/claim a4d130ef2e2e035b3561d61362116a98`",
        parse_mode='Markdown'
    )

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start claiming gold/XP"""
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

async def claim_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Background task for claiming"""
    session_data = user_sessions.get(user_id)
    if not session_data:
        return
    
    session = session_data['session']
    code = session_data['code']
    stats = user_stats[user_id]
    
    last_report_time = time.time()
    
    while user_sessions[user_id]['active']:
        result = claim_gold_xp(session)
        
        if result['success']:
            stats['claims'] += 1
            stats['gold'] += 150000
            stats['xp'] += 45000
            
            # Report every 10 claims
            if stats['claims'] % 10 == 0:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ Claim #{stats['claims']} successful!\n"
                         f"💰 Total gold: {stats['gold']:,}\n"
                         f"⭐ Total XP: {stats['xp']:,}"
                )
        else:
            # Re-login on failure
            if login_with_code(session, code):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🔄 Re-logged in, continuing..."
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Re-login failed, retrying in 5s..."
                )
                await asyncio.sleep(5)
        
        # Small delay between claims
        await asyncio.sleep(0.5)
    
    # Cleanup
    session.close()

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop claiming"""
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

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats"""
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

def main():
    """Start the bot"""
    print(f"[{now_ts()}] 🚀 Starting Telegram Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    print(f"[{now_ts()}] ✅ Bot is running! Press Ctrl+C to stop.")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    main()