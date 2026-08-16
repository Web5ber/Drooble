import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your Telegram bot token from BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Define a message handler that responds with "hi"
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message and respond with 'hi'"""
    await update.message.reply_text("hi")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add message handler
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
