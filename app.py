from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import telebot
import requests
import os
import uuid
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, Set

# Load environment variables from .env file
load_dotenv()

# Get Telegram bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Get Telegram bot username from environment variable
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME")

# Set your ngrok URL here (or use environment variable)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-ngrok-url.ngrok.io")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///drooble.db")  # Fallback to SQLite
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tournament model
class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(String, primary_key=True)  # UUID
    chat_id = Column(String)
    num_players = Column(Integer)
    players = Column(String)  # JSON string of player data
    status = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

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

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create the bot
bot = telebot.TeleBot(TOKEN)

# Tournament state storage
tournaments = {}  # chat_id -> tournament info

# WebSocket connection management
class ConnectionManager:
    def __init__(self):
        # Store connections by tournament_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store user info by connection
        self.connection_users: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, tournament_id: str, user_info: dict):
        await websocket.accept()
        if tournament_id not in self.active_connections:
            self.active_connections[tournament_id] = set()
        self.active_connections[tournament_id].add(websocket)
        self.connection_users[websocket] = user_info
        
        # Broadcast updated user list to all connections in this tournament
        await self.broadcast_users(tournament_id)
    
    def disconnect(self, websocket: WebSocket, tournament_id: str):
        if tournament_id in self.active_connections:
            self.active_connections[tournament_id].discard(websocket)
            if not self.active_connections[tournament_id]:
                del self.active_connections[tournament_id]
        
        if websocket in self.connection_users:
            del self.connection_users[websocket]
    
    async def broadcast_users(self, tournament_id: str):
        if tournament_id not in self.active_connections:
            return
        
        # Get all users in this tournament
        users = []
        for connection in self.active_connections[tournament_id]:
            if connection in self.connection_users:
                users.append(self.connection_users[connection])
        
        # Broadcast to all connections
        for connection in self.active_connections[tournament_id]:
            try:
                await connection.send_json({
                    "type": "users_update",
                    "users": users
                })
            except:
                # Connection might be broken, remove it
                self.active_connections[tournament_id].discard(connection)

manager = ConnectionManager()

# Handler for /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command with welcome message and buttons"""
    chat_type = message.chat.type
    
    # Check if the message is from a group chat
    if chat_type in ['group', 'supergroup']:
        # Group chat welcome message
        welcome_text = "🏆 Welcome to Drooble! Ready to start a tournament?"
        
        # Create inline keyboard for group
        markup = telebot.types.InlineKeyboardMarkup()
        create_tournament_btn = telebot.types.InlineKeyboardButton("Create tournament", callback_data="create_tournament")
        markup.add(create_tournament_btn)
        
        bot.reply_to(message, welcome_text, reply_markup=markup)
    else:
        # Private chat welcome message
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
    elif call.data == "create_tournament":
        bot.answer_callback_query(call.id, "Creating tournament!")
        show_player_selection(call.message.chat.id, call.message.message_id)
    elif call.data.startswith("players_"):
        # Extract the number of players from callback data
        num_players = int(call.data.split("_")[1])
        bot.answer_callback_query(call.id, f"Selected {num_players} players!")
        create_tournament(call.message.chat.id, call.message.message_id, num_players)
    elif call.data == "join_tournament":
        bot.answer_callback_query(call.id, "Joining tournament!")
        join_tournament(call.message.chat.id, call.from_user, call.message.message_id)

def show_player_selection(chat_id, message_id):
    """Show player/slot selection buttons"""
    text = "🎯 How many players/slots for the tournament?"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("2", callback_data="players_2"),
        telebot.types.InlineKeyboardButton("4", callback_data="players_4")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("6", callback_data="players_6"),
        telebot.types.InlineKeyboardButton("8", callback_data="players_8")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("10", callback_data="players_10")
    )
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

def create_tournament(chat_id, message_id, num_players):
    """Create a new tournament and show join button"""
    # Initialize tournament state
    tournaments[chat_id] = {
        'num_players': num_players,
        'players': [],
        'status': 'waiting'
    }
    
    text = f"🏆 Tournament created!\n\nSlots: {num_players}\nJoined: 0/{num_players}\n\nClick below to join:"
    
    markup = telebot.types.InlineKeyboardMarkup()
    join_btn = telebot.types.InlineKeyboardButton("Join Tournament", callback_data="join_tournament")
    markup.add(join_btn)
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

def join_tournament(chat_id, user, message_id):
    """Add a player to the tournament"""
    if chat_id not in tournaments:
        bot.send_message(chat_id, "No active tournament in this group!")
        return
    
    tournament = tournaments[chat_id]
    
    # Check if tournament is full
    if len(tournament['players']) >= tournament['num_players']:
        bot.answer_callback_query("Tournament is full!")
        return
    
    # Check if user already joined
    for player in tournament['players']:
        if player['id'] == user.id:
            bot.answer_callback_query("You already joined!")
            return
    
    # Add player to tournament
    tournament['players'].append({
        'id': user.id,
        'name': user.first_name
    })
    
    print(f"Player {user.first_name} joined. Total players: {len(tournament['players'])}/{tournament['num_players']}")
    
    # Update the message
    current_players = len(tournament['players'])
    total_players = tournament['num_players']
    
    if current_players >= total_players:
        # Tournament is full - create database entry and generate link
        tournament['status'] = 'full'
        tournament_id = str(uuid.uuid4())
        
        # Save to database
        session = SessionLocal()
        try:
            db_tournament = Tournament(
                id=tournament_id,
                chat_id=str(chat_id),
                num_players=total_players,
                players=json.dumps(tournament['players']),
                status='full'
            )
            session.add(db_tournament)
            session.commit()
            print(f"Tournament {tournament_id} saved to database")
        except Exception as e:
            print(f"Database error: {e}")
            session.rollback()
        finally:
            session.close()
        
        # Update group message with Mini App launch link
        webapp_url = f"https://t.me/PlayDroobleBot/Drooble?startapp={tournament_id}"
        text = f"🏆 Tournament is full!\n\nPlayers: {current_players}/{total_players}\n\nTournament started! Click below to view the bracket:"
        
        markup = telebot.types.InlineKeyboardMarkup()
        webapp_btn = telebot.types.InlineKeyboardButton(
            text="🎮 View Bracket",
            url=webapp_url
        )
        markup.add(webapp_btn)
    else:
        text = f"🏆 Tournament created!\n\nSlots: {total_players}\nJoined: {current_players}/{total_players}\n\nClick below to join:"
        markup = telebot.types.InlineKeyboardMarkup()
        join_btn = telebot.types.InlineKeyboardButton("Join Tournament", callback_data="join_tournament")
        markup.add(join_btn)
    
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        print("Message updated successfully")
    except Exception as e:
        print(f"Error updating message: {e}")

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
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Root endpoint - serves the tournament page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the tournament page as the main WebApp entry point"""
    return templates.TemplateResponse("tournament.html", {
        "request": request
    })

# Tournament page endpoint
@app.get("/tournament/{tournament_id}", response_class=HTMLResponse)
async def tournament_page(request: Request, tournament_id: str):
    """Serve the tournament page"""
    return templates.TemplateResponse("tournament.html", {
        "request": request
    })

# Tournament API endpoint (returns JSON data)
@app.get("/api/tournament/{tournament_id}")
async def tournament_api(tournament_id: str):
    """Return tournament data as JSON"""
    session = SessionLocal()
    try:
        tournament = session.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            return {"error": "Tournament not found"}, 404
        
        players = json.loads(tournament.players)
        
        # Create matchups (simple pairing)
        matchups = []
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                matchups.append({
                    'player1': players[i]['name'],
                    'player2': players[i+1]['name']
                })
        
        return {
            "tournament_id": tournament_id,
            "matchups": matchups,
            "players": players
        }
    finally:
        session.close()

# WebSocket endpoint for real-time user status
@app.websocket("/ws/{tournament_id}")
async def websocket_endpoint(websocket: WebSocket, tournament_id: str):
    """Handle WebSocket connections for tournament participants"""
    # Get user info from query parameters
    user_name = websocket.query_params.get("user_name", "Anonymous")
    user_id = websocket.query_params.get("user_id", str(uuid.uuid4()))
    
    user_info = {
        "id": user_id,
        "name": user_name,
        "online": True
    }
    
    await manager.connect(websocket, tournament_id, user_info)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # You can handle client messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, tournament_id)
        await manager.broadcast_users(tournament_id)

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=8000)
