import requests
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import asyncio
import threading
import time
from typing import Dict, Optional

TOKEN = os.getenv("BOT_TOKEN")

# Store user sessions
user_sessions: Dict[int, requests.Session] = {}
# Store automation tasks
automation_tasks: Dict[int, Dict[str, bool]] = {}
# Store bot application reference
bot_app: Optional[Application] = None

# Check if arena response indicates no stamina
def check_arena_stamina(response_text: str) -> bool:
    """Check if arena response indicates no stamina"""
    try:
        result_json = json.loads(response_text)
        return (result_json.get("success") is False and 
                result_json.get("status") == 403 and 
                "Not enough stamina" in result_json.get("message", ""))
    except json.JSONDecodeError:
        return False

# Wait for stamina to regenerate (25 minutes)
def wait_for_stamina(user_id: int):
    """Wait 25 minutes for stamina to regenerate"""
    send_message_safe(user_id, "⚡ Arena paused - Not enough stamina! Waiting 25 minutes...")
    time.sleep(1500)  # Wait 25 minutes (1500 seconds)
    send_message_safe(user_id, "🔄 Arena resumed - Stamina should be restored!")

# Create main menu keyboard based on login status
def get_main_menu_keyboard(is_logged_in: bool) -> InlineKeyboardMarkup:
    if is_logged_in:
        keyboard = [
            [
                InlineKeyboardButton("🍎 Auto Food", callback_data="food"),
                InlineKeyboardButton("⚔️ Auto Arena", callback_data="arena")
            ],
            [
                InlineKeyboardButton("📺 Auto TV", callback_data="tv"),
                InlineKeyboardButton("⏹️ Stop All", callback_data="stop")
            ],
            [
                InlineKeyboardButton("🚪 Logout", callback_data="logout")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("🔑 Generate Code", callback_data="generate_code"),
                InlineKeyboardButton("🚪 Login", callback_data="login_help")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    welcome_text = """
🐉 **Welcome to Dragon City Tool Bot!**
*Developed by Abdou*

**Available Features:**
1️⃣ **Generate Code** - Get your login code
2️⃣ **Login** - Login with your code
3️⃣ **Auto Food** - 100k Food Collection (after login)
4️⃣ **Auto Arena** - Arena Fight automation (after login)
5️⃣ **Auto TV** - Dragon TV automation (after login)
6️⃣ **Stop All** - Stop all automation (after login)

⚠️ **Note:** You need to login first before using automation features!

Choose an option below:
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

# Callback for start (used for Back to Menu)
async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    welcome_text = """
🐉 **Welcome to Dragon City Tool Bot!**
*Developed by Abdou*

**Available Features:**
1️⃣ **Generate Code** - Get your login code
2️⃣ **Login** - Login with your code
3️⃣ **Auto Food** - 100k Food Collection (after login)
4️⃣ **Auto Arena** - Arena Fight automation (after login)
5️⃣ **Auto TV** - Dragon TV automation (after login)
6️⃣ **Stop All** - Stop all automation (after login)

⚠️ **Note:** You need to login first before using automation features!

Choose an option below:
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

# Handle callback queries (button presses)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    if query.data == "generate_code":
        await generate_code_callback(update, context)
    elif query.data == "login_help":
        await show_login_help(update, context)
    elif query.data == "food":
        await auto_food_callback(update, context)
    elif query.data == "arena":
        await auto_arena_callback(update, context)
    elif query.data == "tv":
        await auto_tv_callback(update, context)
    elif query.data == "stop":
        await stop_automation_callback(update, context)
    elif query.data == "logout":
        await logout_callback(update, context)
    elif query.data == "start":
        await start_callback(update, context)

# Callback for login help
async def show_login_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    instructions = """
❌ **Login Code Required!**

**Usage:** `/login YOUR_CODE_HERE`

**Example:** `/login abc123def456`

💡 **Don't have a code?** Use "Generate Code" button first!
    """
    keyboard = get_main_menu_keyboard(is_logged_in(update.effective_user.id))
    await query.edit_message_text(instructions, parse_mode='Markdown', reply_markup=keyboard)

# Callback for generate code
async def generate_code_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    facebook_url = "https://graph.facebook.com/oauth/authorize?type=user_agent&client_id=302826159782423&redirect_uri=https://apps.facebook.com/dragoncity/&scope=offline_access"
    
    instructions = f"""
🌐 **Code Generation Instructions:**

1. Click this link: [Dragon City Login]({facebook_url})
2. Login to Facebook and authorize Dragon City
3. Copy the redirected URL from your browser
4. Send the URL back to this bot as a message

**What to look for:**
The redirected URL should contain `access_token` parameter.

⏳ **Waiting for your URL...**
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instructions, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=reply_markup)
    context.user_data['expecting_url'] = True

# Callback for auto food
async def auto_food_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    global main_loop
    
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("❌ Please login first using `/login YOUR_CODE`", reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('food'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("⚠️ Food collection is already running! Use 'Stop All' to stop it.", reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['food'] = True
    
    success_message = """
🍎 **Auto 100K Food Collection Started!**

✅ Running in background...
⏹️ Use 'Stop All' to stop automation
📊 Status updates will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    def food_worker():
        collect_url = "https://vinafull.com/packet"
        collect_data = {"mode": "free-food-100k"}
        
        while automation_tasks.get(user_id, {}).get('food', False):
            try:
                response = session.post(collect_url, data=collect_data, timeout=30)
                result = response.text
                
                if "You can only claim 10 times every 12 hours." in result:
                    limit_message = """
⚠️ **Limit Reached!**

You can only claim 10 times every 12 hours.

💎 **Want Unlimited?** Contact:
• Telegram: @dralop
• Discord: @Abdou6322

🔄 Food collection stopped.
                    """
                    send_message_safe(user_id, limit_message)
                    break
                
                send_message_safe(user_id, "✅ +100K Food Added!")
                time.sleep(2)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ Food collection error: {str(e)}")
                break
        
        if user_id in automation_tasks:
            automation_tasks[user_id]['food'] = False
            send_message_safe(user_id, "🔄 Food collection stopped.")
    
    threading.Thread(target=food_worker, daemon=True).start()

# Callback for auto arena
async def auto_arena_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    global main_loop
    
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("❌ Please login first using `/login YOUR_CODE`", reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('arena'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("⚠️ Arena fight is already running! Use 'Stop All' to stop it.", reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['arena'] = True
    
    success_message = """
⚔️ **Auto Arena Fight Started!**

🥊 Fighting in background...
⏹️ Use 'Stop All' to stop automation
🏆 Victory notifications will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    def arena_worker():
        arena_url = "https://vinafull.com/packet"
        arena_data = {"mode": "arena-fight"}
        arena_win_data = {"mode": "arena-win"}
        
        while automation_tasks.get(user_id, {}).get('arena', False):
            try:
                response = session.post(arena_url, data=arena_data, timeout=30)
                result = response.text
                
                if check_arena_stamina(result):
                    wait_for_stamina(user_id)
                    continue
                
                try:
                    result_json = json.loads(result)
                    if result_json.get("success") is True:
                        try:
                            session.post(arena_url, data=arena_win_data, timeout=10)
                        except:
                            pass
                        
                        send_message_safe(user_id, "🏆 Arena fight won!")
                    else:
                        message = result_json.get('message', 'Arena fight completed')
                        send_message_safe(user_id, f"⚔️ {message}")
                except json.JSONDecodeError:
                    send_message_safe(user_id, f"⚔️ Arena response: {result}")
                
                time.sleep(3)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ Arena error: {str(e)}")
                break
        
        if user_id in automation_tasks:
            automation_tasks[user_id]['arena'] = False
            send_message_safe(user_id, "🔄 Arena fights stopped.")
    
    threading.Thread(target=arena_worker, daemon=True).start()

# Callback for auto TV
async def auto_tv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    global main_loop
    
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("❌ Please login first using `/login YOUR_CODE`", reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('tv'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await query.edit_message_text("⚠️ Dragon TV is already running! Use 'Stop All' to stop it.", reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['tv'] = True
    
    success_message = """
📺 **Auto Watch Dragon TV Started!**

🔄 Watching in background...
⏹️ Use 'Stop All' to stop automation
✨ Updates will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    def tv_worker():
        tv_url = "https://vinafull.com/packet"
        tv_data = {"mode": "watch-tv"}
        
        while automation_tasks.get(user_id, {}).get('tv', False):
            try:
                response = session.post(tv_url, data=tv_data, timeout=30)
                result = response.text
                
                try:
                    result_json = json.loads(result)
                    if result_json.get("success") is True:
                        send_message_safe(user_id, "📺 Dragon TV watched successfully!")
                    else:
                        message = result_json.get('message', 'TV watch completed')
                        send_message_safe(user_id, f"📺 {message}")
                except json.JSONDecodeError:
                    send_message_safe(user_id, f"📺 TV response: {result}")
                
                time.sleep(5)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ TV error: {str(e)}")
                break
        
        if user_id in automation_tasks:
            automation_tasks[user_id]['tv'] = False
            send_message_safe(user_id, "🔄 Dragon TV watching stopped.")
    
    threading.Thread(target=tv_worker, daemon=True).start()

# Callback for stop automation
async def stop_automation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id in automation_tasks:
        stopped_tasks = []
        
        if automation_tasks[user_id].get('food'):
            automation_tasks[user_id]['food'] = False
            stopped_tasks.append("🍎 Food Collection")
            
        if automation_tasks[user_id].get('arena'):
            automation_tasks[user_id]['arena'] = False
            stopped_tasks.append("⚔️ Arena Fight")
            
        if automation_tasks[user_id].get('tv'):
            automation_tasks[user_id]['tv'] = False
            stopped_tasks.append("📺 Dragon TV")
        
        if stopped_tasks:
            stopped_text = "\n".join(f"• {task}" for task in stopped_tasks)
            message = f"⏹️ **Stopped Automation:**\n\n{stopped_text}\n\n✅ All tasks stopped successfully!"
        else:
            message = "ℹ️ No automation tasks were running."
    else:
        message = "ℹ️ No automation tasks were running."
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=keyboard)

# Callback for logout
async def logout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Stop all automation tasks
    if user_id in automation_tasks:
        automation_tasks[user_id]['food'] = False
        automation_tasks[user_id]['arena'] = False
        automation_tasks[user_id]['tv'] = False
        del automation_tasks[user_id]
    
    # Remove user session
    if user_id in user_sessions:
        user_sessions[user_id].close()
        del user_sessions[user_id]
    
    message = """
🚪 **Logged Out Successfully!**

You have been logged out.
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=keyboard)

# Generate code command
async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facebook_url = "https://graph.facebook.com/oauth/authorize?type=user_agent&client_id=302826159782423&redirect_uri=https://apps.facebook.com/dragoncity/&scope=offline_access"
    
    instructions = f"""
🌐 **Code Generation Instructions:**

1. Click this link: [Dragon City Login]({facebook_url})
2. Login to Facebook and authorize Dragon City
3. Copy the redirected URL from your browser
4. Send the URL back to this bot as a message

**What to look for:**
The redirected URL should contain `access_token` parameter.

⏳ **Waiting for your URL...**
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(instructions, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=reply_markup)
    
    # Set user state to expect URL
    context.user_data['expecting_url'] = True

# Handle URL input for code generation
async def handle_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('expecting_url'):
        return
    
    redirected_url = update.message.text.strip()
    
    if not redirected_url.startswith('http'):
        await update.message.reply_text("❌ Please provide a valid URL!")
        return
    
    try:
        await update.message.reply_text("⏳ Generating code...")
        
        # Make request to create code
        create_code_url = "https://vinafull.com/find"
        create_code_data = {
            "request": "create_code",
            "url": redirected_url
        }
        
        response = requests.post(create_code_url, data=create_code_data)
        response.raise_for_status()
        
        # Parse JSON response
        try:
            result = json.loads(response.text)
            if "code" in result:
                code = result['code']
                success_message = f"""
✅ **Code Generated Successfully!**

🔑 **Your Code:** `{code}`

**Next Steps:**
1. Copy the code above
2. Use `/login {code}` to login

**Note:** Keep your code private and secure!
                """
                keyboard = get_main_menu_keyboard(is_logged_in(update.effective_user.id))
                await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
            else:
                keyboard = get_main_menu_keyboard(is_logged_in(update.effective_user.id))
                await update.message.reply_text(f"⚠️ Response: {response.text}", reply_markup=keyboard)
        except json.JSONDecodeError:
            keyboard = get_main_menu_keyboard(is_logged_in(update.effective_user.id))
            await update.message.reply_text(f"⚠️ Response: {response.text}", reply_markup=keyboard)
        
    except Exception as e:
        keyboard = get_main_menu_keyboard(is_logged_in(update.effective_user.id))
        await update.message.reply_text(f"❌ Error generating code: {str(e)}", reply_markup=keyboard)
    
    # Reset state
    context.user_data['expecting_url'] = False

# Login command
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await update.message.reply_text("""
❌ **Login Code Required!**

**Usage:** `/login YOUR_CODE_HERE`

**Example:** `/login abc123def456`

💡 **Don't have a code?** Use "Generate Code" button first!
        """, parse_mode='Markdown', reply_markup=keyboard)
        return
    
    login_code = ' '.join(context.args)
    
    try:
        await update.message.reply_text("⏳ Logging in...")
        
        login_url = "https://vinafull.com/login"
        login_data = {"code": login_code}
        
        # Create a new session for this user
        session = requests.Session()
        login_response = session.post(login_url, data=login_data)
        login_response.raise_for_status()
        
        # Store session
        user_sessions[user_id] = session
        
        success_message = """
✅ **Login Successful!**

🎮 **Automation Features Now Available:**
• **Auto Food** - 100k Food Collection
• **Auto Arena** - Arena Fight automation
• **Auto TV** - Dragon TV automation
• **Stop All** - Stop all automation
• **Logout** - Log out and return to initial menu

🔥 **Ready to dominate Dragon City!**
        """
        
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
        
    except Exception as e:
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        await update.message.reply_text(f"❌ Login failed: {str(e)}", reply_markup=keyboard)

# Logout command
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Stop all automation tasks
    if user_id in automation_tasks:
        automation_tasks[user_id]['food'] = False
        automation_tasks[user_id]['arena'] = False
        automation_tasks[user_id]['tv'] = False
        del automation_tasks[user_id]
    
    # Remove user session
    if user_id in user_sessions:
        user_sessions[user_id].close()
        del user_sessions[user_id]
    
    message = """
🚪 **Logged Out Successfully!**

You have been logged out. Please generate a new code or login again to continue.
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)

# Check if user is logged in
def is_logged_in(user_id: int) -> bool:
    return user_id in user_sessions

# Store the main event loop
main_loop = None

# Safe way to send messages from background threads
def send_message_safe(chat_id: int, message: str):
    """Send message from background thread safely"""
    try:
        if bot_app and bot_app.bot:
            # Try to get the running loop or use the stored one
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop in this thread, try to get the main loop
                loop = main_loop
            
            if loop:
                # Schedule the message to be sent in the main event loop
                future = asyncio.run_coroutine_threadsafe(
                    bot_app.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'),
                    loop
                )
                # Wait for completion with timeout
                future.result(timeout=5)
            else:
                print(f"No event loop available to send message: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")  # Log error but don't crash

# Auto food collection
async def auto_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global main_loop
    user_id = update.effective_user.id
    
    # Set the main loop when first command is called
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "❌ Please login first using `/login YOUR_CODE`"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_ORDER_BYtext(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('food'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "⚠️ Food collection is already running! Use 'Stop All' to stop it."
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    # Initialize automation tracking
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['food'] = True
    
    success_message = """
🍎 **Auto 100K Food Collection Started!**

✅ Running in background...
⏹️ Use 'Stop All' to stop automation
📊 Status updates will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.message.edit_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    # Start food collection in background
    def food_worker():
        collect_url = "https://vinafull.com/packet"
        collect_data = {"mode": "free-food-100k"}
        
        while automation_tasks.get(user_id, {}).get('food', False):
            try:
                response = session.post(collect_url, data=collect_data, timeout=30)
                result = response.text
                
                if "You can only claim 10 times every 12 hours." in result:
                    limit_message = """
⚠️ **Limit Reached!**

You can only claim 10 times every 12 hours.

💎 **Want Unlimited?** Contact:
• Telegram: @dralop
• Discord: @Abdou6322

🔄 Food collection stopped.
                    """
                    send_message_safe(user_id, limit_message)
                    break
                
                send_message_safe(user_id, "✅ +100K Food Added!")
                
                # Add delay between requests
                time.sleep(2)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ Food collection error: {str(e)}")
                break
        
        # Clean up
        if user_id in automation_tasks:
            automation_tasks[user_id]['food'] = False
            send_message_safe(user_id, "🔄 Food collection stopped.")
    
    # Start in background thread
    threading.Thread(target=food_worker, daemon=True).start()

# Auto arena fight
async def auto_arena(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global main_loop
    user_id = update.effective_user.id
    
    # Set the main loop when first command is called
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "❌ Please login first using `/login YOUR_CODE`"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('arena'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "⚠️ Arena fight is already running! Use 'Stop All' to stop it."
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    # Initialize automation tracking
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['arena'] = True
    
    success_message = """
⚔️ **Auto Arena Fight Started!**

🥊 Fighting in background...
⏹️ Use 'Stop All' to stop automation
🏆 Victory notifications will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.message.edit_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    def arena_worker():
        arena_url = "https://vinafull.com/packet"
        arena_data = {"mode": "arena-fight"}
        arena_win_data = {"mode": "arena-win"}
        
        while automation_tasks.get(user_id, {}).get('arena', False):
            try:
                response = session.post(arena_url, data=arena_data, timeout=30)
                result = response.text
                
                # Check for stamina depletion (only for arena fights)
                if check_arena_stamina(result):
                    wait_for_stamina(user_id)
                    continue  # Continue the loop after waiting
                
                try:
                    result_json = json.loads(result)
                    if result_json.get("success") is True:
                        # Call arena-win silently
                        try:
                            session.post(arena_url, data=arena_win_data, timeout=10)
                        except:
                            pass
                        
                        send_message_safe(user_id, "🏆 Arena fight won!")
                    else:
                        message = result_json.get('message', 'Arena fight completed')
                        send_message_safe(user_id, f"⚔️ {message}")
                except json.JSONDecodeError:
                    send_message_safe(user_id, f"⚔️ Arena response: {result}")
                
                # Add delay between fights
                time.sleep(3)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ Arena error: {str(e)}")
                break
        
        # Clean up
        if user_id in automation_tasks:
            automation_tasks[user_id]['arena'] = False
            send_message_safe(user_id, "🔄 Arena fights stopped.")
    
    threading.Thread(target=arena_worker, daemon=True).start()

# Auto watch dragon TV
async def auto_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global main_loop
    user_id = update.effective_user.id
    
    # Set the main loop when first command is called
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
    
    if not is_logged_in(user_id):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "❌ Please login first using `/login YOUR_CODE`"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    if user_id in automation_tasks and automation_tasks[user_id].get('tv'):
        keyboard = get_main_menu_keyboard(is_logged_in(user_id))
        message_text = "⚠️ Dragon TV is already running! Use 'Stop All' to stop it."
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard)
        return
    
    session = user_sessions[user_id]
    
    # Initialize automation tracking
    if user_id not in automation_tasks:
        automation_tasks[user_id] = {}
    automation_tasks[user_id]['tv'] = True
    
    success_message = """
📺 **Auto Watch Dragon TV Started!**

🔄 Watching in background...
⏹️ Use 'Stop All' to stop automation
✨ Updates will be sent here
    """
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.message.edit_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=keyboard)
    
    def tv_worker():
        tv_url = "https://vinafull.com/packet"
        tv_data = {"mode": "watch-tv"}
        
        while automation_tasks.get(user_id, {}).get('tv', False):
            try:
                response = session.post(tv_url, data=tv_data, timeout=30)
                result = response.text
                
                try:
                    result_json = json.loads(result)
                    if result_json.get("success") is True:
                        send_message_safe(user_id, "📺 Dragon TV watched successfully!")
                    else:
                        message = result_json.get('message', 'TV watch completed')
                        send_message_safe(user_id, f"📺 {message}")
                except json.JSONDecodeError:
                    send_message_safe(user_id, f"📺 TV response: {result}")
                
                # Add delay between TV watches
                time.sleep(5)
                
            except Exception as e:
                send_message_safe(user_id, f"❌ TV error: {str(e)}")
                break
        
        # Clean up
        if user_id in automation_tasks:
            automation_tasks[user_id]['tv'] = False
            send_message_safe(user_id, "🔄 Dragon TV watching stopped.")
    
    threading.Thread(target=tv_worker, daemon=True).start()

# Stop all automation
async def stop_automation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in automation_tasks:
        stopped_tasks = []
        
        if automation_tasks[user_id].get('food'):
            automation_tasks[user_id]['food'] = False
            stopped_tasks.append("🍎 Food Collection")
            
        if automation_tasks[user_id].get('arena'):
            automation_tasks[user_id]['arena'] = False
            stopped_tasks.append("⚔️ Arena Fight")
            
        if automation_tasks[user_id].get('tv'):
            automation_tasks[user_id]['tv'] = False
            stopped_tasks.append("📺 Dragon TV")
        
        if stopped_tasks:
            stopped_text = "\n".join(f"• {task}" for task in stopped_tasks)
            message = f"⏹️ **Stopped Automation:**\n\n{stopped_text}\n\n✅ All tasks stopped successfully!"
        else:
            message = "ℹ️ No automation tasks were running."
    else:
        message = "ℹ️ No automation tasks were running."
    
    keyboard = get_main_menu_keyboard(is_logged_in(user_id))
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.message.edit_text(message, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)

def main():
    global bot_app, main_loop
    
    app = Application.builder().token(TOKEN).build()
    bot_app = app  # Store reference for background threads

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_code", generate_code))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("food", auto_food))
    app.add_handler(CommandHandler("arena", auto_arena))
    app.add_handler(CommandHandler("tv", auto_tv))
    app.add_handler(CommandHandler("stop", stop_automation))
    
    # Add callback query handler for button presses
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for URL input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_input))

    print("🤖 Dragon City Bot is running...")
    print("🔥 Ready to automate Dragon City!")
    
    # Store the event loop after the bot starts running
    async def set_loop():
        global main_loop
        main_loop = asyncio.get_running_loop()
    
    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()