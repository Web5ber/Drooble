# Drooble - Telegram Bot

A simple Telegram bot that responds "hi" to any message, built with Python and FastAPI.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get your Telegram bot token:**
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow the instructions
   - Copy the bot token you receive

3. **Configure the bot:**
   - Replace `YOUR_BOT_TOKEN_HERE` in both `main.py` and `app.py` with your actual bot token

## Running the Bot

### Option 1: Standalone Polling (Simple)
```bash
python main.py
```

### Option 2: FastAPI Webhook (Production)
```bash
python app.py
```
The FastAPI server will run on `http://0.0.0.0:8000` with:
- Webhook endpoint: `/webhook`
- Health check: `/`

## Auto-Commit Feature

To enable automatic git commits when you save files:

1. **Run the auto-commit watcher:**
   ```bash
   python auto_commit.py
   ```

2. **How it works:**
   - Watches for file changes in the project directory
   - Waits 5 seconds after the last change before committing
   - Automatically commits and pushes to GitHub
   - Skips `venv/`, `.git/`, and temporary files

3. **Stop the watcher:**
   - Press `Ctrl+C`

## Project Structure

- `main.py` - Standalone Telegram bot using polling
- `app.py` - FastAPI integration with webhook support
- `auto_commit.py` - Auto-commit script for git
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore patterns

## Development

Always use the virtual environment:
```bash
.\venv\Scripts\activate
```

Deactivate when done:
```bash
deactivate
```
