from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import telebot
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Telegram bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Get Telegram bot username from environment variable
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")

# Set your ngrok URL here (or use environment variable)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-ngrok-url.ngrok.io")

# Lifespan context manager for startup events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Set the Telegram webhook on startup"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    response = requests.get(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook",
        params={"url": webhook_url}
    )
    if response.status_code == 200:
        print(f"Webhook set successfully to {webhook_url}")
    else:
        print(f"Failed to set webhook: {response.text}")
    yield
    # Cleanup code here if needed

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Create the bot
bot = telebot.TeleBot(TOKEN)

# Handler for /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command with welcome message and buttons"""
    user_name = message.from_user.first_name
    if message.from_user.last_name:
        user_name += f" {message.from_user.last_name}"
    
    welcome_text = f"Welcome {user_name}! 🎮\n\nChoose how you want to play:"
    
    # Create inline keyboard
    markup = telebot.types.InlineKeyboardMarkup()
    single_player_btn = telebot.types.InlineKeyboardButton("Single Player", callback_data="single_player")
    
    # URL button that opens Telegram's add to group feature
    if BOT_USERNAME:
        add_to_group_btn = telebot.types.InlineKeyboardButton(
            "Add Drooble to group", 
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    else:
        # Fallback if username not set
        add_to_group_btn = telebot.types.InlineKeyboardButton("Add Drooble to group", callback_data="add_to_group")
    
    markup.add(single_player_btn, add_to_group_btn)
    
    bot.reply_to(message, welcome_text, reply_markup=markup)

# Handler for button clicks
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    """Handle button clicks"""
    if call.data == "single_player":
        bot.answer_callback_query(call.id, "You chose Single Player mode!")
        bot.send_message(call.message.chat.id, "Starting Single Player mode... 🎯")
    elif call.data == "add_to_group":
        bot.answer_callback_query(call.id, "Add me to a group!")
        bot.send_message(call.message.chat.id, "To add me to a group:\n\n1. Open your group chat\n2. Click the group name\n3. Go to 'Members'\n4. Click 'Add Member'\n5. Search for @DroobleBot\n6. Select me and add! 🤖")

# Handler for other messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle any message and respond with 'hi'"""
    bot.reply_to(message, "hi")

# Set up webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook updates from Telegram"""
    json_string = await request.json()
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return {"status": "ok"}

# Health check endpoint
@app.get("/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=8000)
