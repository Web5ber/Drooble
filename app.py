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

# Define a message handler that responds with "hi"
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
