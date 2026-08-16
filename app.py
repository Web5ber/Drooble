from fastapi import FastAPI, Request
import telebot

# Replace with your Telegram bot token from BotFather
TOKEN = "8881016785:AAHduCchY7a7cD912X2Jt8UZ0LytOo8Eaws"

# Initialize FastAPI app
app = FastAPI()

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
