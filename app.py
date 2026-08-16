from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio

# Replace with your Telegram bot token from BotFather
TOKEN = "8881016785:AAHduCchY7a7cD912X2Jt8UZ0LytOo8Eaws"

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

# Startup event to initialize the application
@app.on_event("startup")
async def startup_event():
    """Initialize the telegram application on startup"""
    await application.initialize()
    await application.start()

# Shutdown event to cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the telegram application on shutdown"""
    await application.stop()
    await application.shutdown()

# Set up webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook updates from Telegram"""
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}

# Health check endpoint
@app.get("/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
