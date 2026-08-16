import logging
import telebot

# Replace with your Telegram bot token from BotFather
TOKEN = "8881016785:AAHduCchY7a7cD912X2Jt8UZ0LytOo8Eaws"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Create the bot
bot = telebot.TeleBot(TOKEN)

# Define a message handler that responds with "hi"
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle any message and respond with 'hi'"""
    bot.reply_to(message, "hi")

def main():
    """Start the bot."""
    logging.info("Starting bot...")
    bot.polling()

if __name__ == "__main__":
    main()
