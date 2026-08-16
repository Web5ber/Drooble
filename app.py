from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Replace with your Telegram bot token from BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Initialize FastAPI app
app = FastAPI()

# Create Telegram application
application = Application.builder().token(TOKEN).build()

# Define message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message and respond with 'hi'"""
    await update.message.reply_text("hi")

# Add handler to the application
application.add_handler(MessageHandler(filters.ALL, handle_message))

# Set up webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook updates from Telegram"""
    update = Update.de_json(await request.json(), application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

# Health check endpoint
@app.get("/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
