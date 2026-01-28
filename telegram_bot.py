import os
import asyncio
import random
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from groq import AsyncGroq
from aiohttp import web
import pytz

# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN","7559754155:AAHvJ7mWI08H3MFOxl3-NlTv_veSXRiMbY8")
GROQ_API_KEY = os.getenv("GROQ_API_KEY","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")
PORT = int(os.getenv("PORT", 10000))

# Timezone for India
INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Initialize with MemoryStorage
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# Initialize Groq client
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Memory: {chat_id: deque}
chat_memory: Dict[int, deque] = {}

# Game states storage: {user_id: game_data}
active_games: Dict[int, Dict] = {}
game_sessions: Dict[int, Dict] = {}  # Store game sessions separately

# Emotional states for each user
user_emotions: Dict[int, str] = {}
user_last_interaction: Dict[int, datetime] = {}

# States for games
class GameStates(StatesGroup):
    playing_quiz = State()
    playing_riddle = State()
    playing_word = State()
    waiting_answer = State()

# --- HUMAN-LIKE BEHAVIOUR IMPROVEMENTS ---

# Emotional responses with emojis
EMOTIONAL_RESPONSES = {
    "happy": ["😊", "🎉", "🥳", "🌟", "✨", "👍", "💫", "😄", "😍", "🤗", "🫂"],
    "angry": ["😠", "👿", "💢", "🤬", "😤", "🔥", "⚡", "💥", "👊", "🖕"],
    "crying": ["😢", "😭", "💔", "🥺", "😞", "🌧️", "😿", "🥀", "💧", "🌩️"],
    "love": ["❤️", "💖", "💕", "🥰", "😘", "💋", "💓", "💗", "💘", "💝"],
    "funny": ["😂", "🤣", "😆", "😜", "🤪", "🎭", "🤡", "🃏", "🎪", "🤹"],
    "thinking": ["🤔", "💭", "🧠", "🔍", "💡", "🎯", "🧐", "🔎", "💬", "🗨️"],
    "surprise": ["😲", "🤯", "🎊", "🎁", "💥", "✨", "🎆", "🎇", "🧨", "💫"],
    "sleepy": ["😴", "💤", "🌙", "🛌", "🥱", "😪", "🌃", "🌜", "🌚", "🌌"],
    "hungry": ["😋", "🤤", "🍕", "🍔", "🍟", "🌮", "🍦", "🍩", "🍪", "🍰"]
}

# Hindi/English mixed responses for different scenarios
QUICK_RESPONSES = {
    "greeting": [
        "Aree wah! Kaise ho? 😊", 
        "Namaste ji! Aaj kaise hain? 🌟", 
        "Oye! Kya haal hai? 😎",
        "Hello hello! Sab theek? 🫂",
        "Heyyy! Missed you yaar! 💖"
    ],
    "goodbye": [
        "Bye bye! Jaldi baat karna! 👋", 
        "Chalo, mai ja raha hu! Baad me baat karte hain! 😊", 
        "Alvida! Take care! 💫",
        "Jaane do na! Phir milenge! 😄",
        "Okay bye! I'll miss you! 😢"
    ],
    "thanks": [
        "Arey koi baat nahi! 😊", 
        "Welcome ji! Happy to help! 🌟", 
        "No problem yaar! Anytime! 💖",
        "Mujhe kya, main to bot hu! 😂",
        "It's my duty! 😇"
    ],
    "sorry": [
        "Aree sorry yaar! 😢", 
        "Maine galti kar di! Maaf karna! 😔", 
        "Oops! My bad! 😅",
        "Bhool gaya tha! Sorry bhai! 🥺",
        "I messed up! Forgive me? 💔"
    ]
}

# Get Indian time
def get_indian_time():
    utc_now = datetime.now(pytz.utc)
    indian_time = utc_now.astimezone(INDIAN_TIMEZONE)
    return indian_time

# Weather data (static for demo - you can integrate real API later)
WEATHER_DATA = {
    "mumbai": {"temp": "32°C", "condition": "Sunny ☀️", "humidity": "65%"},
    "delhi": {"temp": "28°C", "condition": "Partly Cloudy ⛅", "humidity": "55%"},
    "bangalore": {"temp": "26°C", "condition": "Light Rain 🌦️", "humidity": "70%"},
    "kolkata": {"temp": "30°C", "condition": "Humid 💦", "humidity": "75%"},
    "chennai": {"temp": "33°C", "condition": "Hot 🔥", "humidity": "68%"},
    "hyderabad": {"temp": "29°C", "condition": "Clear 🌤️", "humidity": "60%"},
    "ahmedabad": {"temp": "31°C", "condition": "Sunny ☀️", "humidity": "58%"},
    "pune": {"temp": "27°C", "condition": "Pleasant 😊", "humidity": "62%"}
}

# Get random emotion based on context
def get_emotion(emotion_type: str = None, user_id: int = None) -> str:
    """Get appropriate emotion with some randomness"""
    if user_id and user_id in user_emotions:
        # Sometimes use user's current emotion
        if random.random() < 0.3:
            emotion_type = user_emotions[user_id]
    
    if emotion_type and emotion_type in EMOTIONAL_RESPONSES:
        return random.choice(EMOTIONAL_RESPONSES[emotion_type])
    
    # Default: random emotion
    all_emotions = list(EMOTIONAL_RESPONSES.values())
    return random.choice(random.choice(all_emotions))

# Update user emotion based on message
def update_user_emotion(user_id: int, message: str):
    message_lower = message.lower()
    
    # Detect emotion from message
    if any(word in message_lower for word in ['love', 'pyaar', 'dil', 'heart', 'cute', 'beautiful']):
        user_emotions[user_id] = "love"
    elif any(word in message_lower for word in ['angry', 'gussa', 'naraz', 'mad', 'hate', 'idiot']):
        user_emotions[user_id] = "angry"
    elif any(word in message_lower for word in ['cry', 'ro', 'sad', 'dukh', 'upset', 'unhappy']):
        user_emotions[user_id] = "crying"
    elif any(word in message_lower for word in ['funny', 'has', 'joke', 'comedy', 'masti', 'laugh']):
        user_emotions[user_id] = "funny"
    elif any(word in message_lower for word in ['hi', 'hello', 'hey', 'namaste', 'kaise']):
        user_emotions[user_id] = "happy"
    elif any(word in message_lower for word in ['?', 'kyun', 'kaise', 'kya', 'how', 'why']):
        user_emotions[user_id] = "thinking"
    else:
        # Random emotion if can't detect
        user_emotions[user_id] = random.choice(list(EMOTIONAL_RESPONSES.keys()))
    
    user_last_interaction[user_id] = datetime.now()

# --- GAME DATABASES IMPROVED ---

# Quiz Database
QUIZ_QUESTIONS = [
    {"question": "Hinglish me kitne letters hote hain?", "answer": "26", "hint": "English jitne hi"},
    {"question": "Aam ka English kya hota hai?", "answer": "mango", "hint": "Ek fruit"},
    {"question": "2 + 2 × 2 = ?", "answer": "6", "hint": "PEMDAS rule yaad rakho"},
    {"question": "India ka capital kya hai?", "answer": "new delhi", "hint": "Yeh to pata hi hoga"},
    {"question": "Python kisne banaya?", "answer": "guido van rossum", "hint": "Ek Dutch programmer"},
    {"question": "ChatGPT kis company ki hai?", "answer": "openai", "hint": "Elon Musk bhi involved tha"},
    {"question": "Hinglish ka matlab kya hai?", "answer": "hindi + english", "hint": "Do languages ka mix"},
    {"question": "Telegram kisne banaya?", "answer": "pavel durov", "hint": "Russian entrepreneur"},
    {"question": "Ek year me kitne months hote hain?", "answer": "12", "hint": "Calendar dekho"},
    {"question": "Water ka chemical formula?", "answer": "h2o", "hint": "H do, O ek"}
]

# Riddle Database
RIDDLES = [
    {"riddle": "Aane ke baad kabhi nahi jata?", "answer": "umar", "hint": "Har roz badhta hai"},
    {"riddle": "Chidiya ki do aankhen, par ek hi nazar aata hai?", "answer": "needle", "hint": "Sui ki nook"},
    {"riddle": "Aisa kaun sa cheez hai jo sukha ho toh 2 kilo, geela ho toh 1 kilo?", "answer": "sukha", "hint": "Word play hai"},
    {"riddle": "Mere paas khane wala hai, peene wala hai, par khata peeta koi nahi?", "answer": "khana pina", "hint": "Restaurant menu"},
    {"riddle": "Ek ghar me 5 room hain, har room me 5 billi hain, har billi ke 5 bacche hain, total kitne legs?", "answer": "0", "hint": "Billi ke legs nahi hote"},
    {"riddle": "Jisne pehna woh nahi khareeda, jisne khareeda woh nahi pehna?", "answer": "kafan", "hint": "Antim vastra"},
    {"riddle": "Subah utha to gaya, raat ko aaya to gaya?", "answer": "suraj", "hint": "Din raat ka cycle"},
    {"riddle": "Jiske paas ho woh nahi janta, jaanne wala ke paas nahi hota?", "answer": "andha", "hint": "Dekh nahi sakta"}
]

# Jokes Database Improved
JOKES = [
    "🤣 Teacher: Tumhare ghar me sabse smart kaun hai? Student: Wifi router! Kyuki sab use hi puchte hain!",
    "😂 Papa: Beta mobile chhodo, padhai karo. Beta: Papa, aap bhi to TV dekhte ho! Papa: Par main TV se shaadi nahi kar raha!",
    "😆 Doctor: Aapko diabetes hai. Patient: Kya khana chhodna hoga? Doctor: Nahi, aapka sugar chhodna hoga!",
    "😅 Dost: Tumhari girlfriend kitni cute hai! Me: Haan, uski akal bhi utni hi cute hai!",
    "🤪 Teacher: Agar tumhare paas 5 aam hain aur main 2 le lun, toh kitne bachenge? Student: Sir, aapke paas already 2 kyun hain?",
    "😜 Boyfriend: Tum meri life ki battery ho! Girlfriend: Toh charging khatam kyun ho jati hai?",
    "😁 Boss: Kal se late mat aana. Employee: Aaj hi late kyun bola? Kal bata dete!",
    "😄 Bhai: Behen, tum kyun ro rahi ho? Behen: Mera boyfriend mujhse break-up kar raha hai! Bhai: Uske liye ro rahi ho ya uske jaane ke baad free time ke liye?",
    "🤭 Customer: Yeh shampoo hair fall rokta hai? Shopkeeper: Nahi sir, hair fall hone par refund deta hai!",
    "😹 Boy: I love you! Girl: Tumhare paas girlfriend nahi hai? Boy: Haan, tumhare saath hi baat kar raha hu!",
    "🤣 Student: Sir, main kal school nahi aa paunga. Teacher: Kyun? Student: Kal meri sister ki shaadi hai. Teacher: Accha? Kaunsi sister? Student: Aapki beti sir!",
    "😂 Wife: Agar main mar jaun toh tum dobara shaadi karoge? Husband: Nahi. Wife: Aww pyaar! Husband: Nahi, ek biwi ka kharcha hi bahut hai!",
    "😆 Customer: Isme sugar hai? Shopkeeper: Nahi sir. Customer: Salt? Shopkeeper: Nahi. Customer: To phir kya hai? Shopkeeper: Bill sir!",
]

# Group Rules Templates
GROUP_RULES = [
    """📜 **GROUP RULES** 📜

1. ✅ Respect everyone - No bullying
2. ✅ No spam or flooding
3. ✅ No adult/NSFW content
4. ✅ No personal fights in group
5. ✅ Keep chat clean and friendly
6. ✅ Follow admin instructions
7. ✅ Help each other grow
8. ✅ Share knowledge & learn
9. ✅ Have fun and enjoy! 🎉

*Rules are for everyone's protection!* 😊""",

    """⚖️ **COMMUNITY GUIDELINES** ⚖️

• Be kind and polite 🤗
• No hate speech or racism ❌
• Share knowledge & help others 📚
• No self-promotion without permission
• Use appropriate language
• Report issues to admins
• Keep discussions friendly
• Respect privacy of members
• No political/religious debates

*Let's build a positive community together!* 🌟""",

    """📋 **CHAT ETIQUETTE** 📋

🔹 No bullying or harassment
🔹 No misinformation spreading
🔹 Stay on topic in discussions
🔹 No excessive caps (SHOUTING)
🔹 Respect everyone's privacy
🔹 No illegal content sharing
🔹 Use emojis appropriately 😉
🔹 Be patient with newcomers
🔹 Have meaningful conversations

*Together we grow, together we learn!* 🌱""",

    """🎯 **GROUP NORMS** 🎯

✨ Be respectful to all members
✨ No spamming or advertising
✨ Keep discussions positive
✨ Help each other when possible
✨ Follow admin guidance
✨ Use appropriate language
✨ Report any issues
✨ Enjoy your time here! 🎊

*This is our digital family!* 💖"""
]

# --- FIXED GAME LOGIC ---

def start_word_game(user_id: int):
    """Start a new word chain game"""
    start_words = ["PYTHON", "APPLE", "TIGER", "ELEPHANT", "RAINBOW", "COMPUTER", "TELEGRAM", "BOT"]
    start_word = random.choice(start_words)
    
    game_sessions[user_id] = {
        "game": "word_chain",
        "last_word": start_word.lower(),
        "score": 0,
        "words_used": [start_word.lower()],
        "last_letter": start_word[-1].lower(),
        "started_at": datetime.now()
    }
    
    return start_word

def check_word_game(user_id: int, user_word: str):
    """Check if word is valid in word chain game"""
    if user_id not in game_sessions:
        return False, "No active game! Start with /game"
    
    game_data = game_sessions[user_id]
    user_word_lower = user_word.lower().strip()
    
    # Check if word starts with correct letter
    if not user_word_lower.startswith(game_data["last_letter"]):
        return False, f"Word must start with '{game_data['last_letter'].upper()}'!"
    
    # Check if word already used
    if user_word_lower in game_data["words_used"]:
        return False, f"'{user_word}' already used! Try different word."
    
    # Check if word is valid (at least 3 letters)
    if len(user_word_lower) < 3:
        return False, "Word must be at least 3 letters!"
    
    # Update game state
    game_data["words_used"].append(user_word_lower)
    game_data["last_word"] = user_word_lower
    game_data["last_letter"] = user_word_lower[-1]
    game_data["score"] += 10
    
    return True, game_data

# --- TIME AND WEATHER FUNCTIONS ---

async def get_weather_info(city: str = None):
    """Get weather information (simulated for now)"""
    if not city:
        # Default cities
        default_cities = ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"]
        city = random.choice(default_cities)
    
    city_lower = city.lower()
    
    # Check if we have data for this city
    for city_key in WEATHER_DATA.keys():
        if city_key in city_lower or city_lower in city_key:
            weather = WEATHER_DATA[city_key]
            return (
                f"🌤️ **Weather in {city_key.title()}**\n"
                f"• Temperature: {weather['temp']}\n"
                f"• Condition: {weather['condition']}\n"
                f"• Humidity: {weather['humidity']}\n"
                f"• Updated: Just now\n\n"
                f"*Note: This is demo data. For real weather, use weather apps.*"
            )
    
    # If city not found, show random city weather
    random_city = random.choice(list(WEATHER_DATA.keys()))
    weather = WEATHER_DATA[random_city]
    return (
        f"🌤️ **Weather Info**\n"
        f"Couldn't find '{city}'. Here's weather in {random_city.title()}:\n"
        f"• Temperature: {weather['temp']}\n"
        f"• Condition: {weather['condition']}\n"
        f"• Humidity: {weather['humidity']}\n\n"
        f"*Tip: Try 'Mumbai', 'Delhi', 'Bangalore' etc.*"
    )

def get_time_info():
    """Get accurate Indian time"""
    indian_time = get_indian_time()
    
    # Format time beautifully
    time_str = indian_time.strftime("%I:%M %p")
    date_str = indian_time.strftime("%A, %d %B %Y")
    
    # Get appropriate greeting based on time
    hour = indian_time.hour
    if 5 <= hour < 12:
        greeting = "Good Morning! 🌅"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon! ☀️"
    elif 17 <= hour < 21:
        greeting = "Good Evening! 🌇"
    else:
        greeting = "Good Night! 🌙"
    
    return (
        f"🕒 **Indian Standard Time (IST)**\n"
        f"• Time: {time_str}\n"
        f"• Date: {date_str}\n"
        f"• {greeting}\n"
        f"• Timezone: Asia/Kolkata 🇮🇳\n\n"
        f"*Time is accurate to Indian timezone!*"
    )

# --- AI LOGIC WITH HUMAN-LIKE TOUCH ---
async def get_ai_response(chat_id: int, user_text: str, user_id: int = None) -> str:
    # Initialize memory for chat if not exists
    if chat_id not in chat_memory:
        chat_memory[chat_id] = deque(maxlen=20)
    
    # Add user message to memory
    chat_memory[chat_id].append({"role": "user", "content": user_text})
    
    # Update user emotion
    if user_id:
        update_user_emotion(user_id, user_text)
    
    # Check if we should use quick response for common phrases
    user_text_lower = user_text.lower()
    
    # Quick responses for common phrases (makes bot feel more human)
    if any(word in user_text_lower for word in ['hi', 'hello', 'hey', 'namaste', 'hola']):
        if random.random() < 0.4:  # 40% chance to use quick response
            return f"{get_emotion('happy', user_id)} {random.choice(QUICK_RESPONSES['greeting'])}"
    
    if any(word in user_text_lower for word in ['bye', 'goodbye', 'tata', 'alvida', 'see you']):
        if random.random() < 0.4:
            return f"{get_emotion()} {random.choice(QUICK_RESPONSES['goodbye'])}"
    
    if any(word in user_text_lower for word in ['thanks', 'thank you', 'dhanyavad', 'shukriya']):
        if random.random() < 0.4:
            return f"{get_emotion('love', user_id)} {random.choice(QUICK_RESPONSES['thanks'])}"
    
    if any(word in user_text_lower for word in ['sorry', 'maaf', 'apology']):
        if random.random() < 0.4:
            return f"{get_emotion('crying', user_id)} {random.choice(QUICK_RESPONSES['sorry'])}"
    
    # Check if this is a game response
    if user_id in game_sessions:
        game_data = game_sessions[user_id]
        if game_data["game"] == "word_chain":
            # This is a word chain game response - handle it specially
            is_valid, message = check_word_game(user_id, user_text)
            if is_valid:
                # Successful word - continue game
                next_letter = game_data["last_letter"].upper()
                score = game_data["score"]
                return (
                    f"{get_emotion('happy')} **✅ Correct!**\n\n"
                    f"• Your word: {user_text.upper()}\n"
                    f"• Next letter: **{next_letter}**\n"
                    f"• Your score: **{score} points**\n\n"
                    f"Now give me a word starting with **{next_letter}**"
                )
            else:
                # Invalid word - end game
                score = game_data["score"]
                del game_sessions[user_id]
                return (
                    f"{get_emotion('crying')} **❌ Game Over!**\n\n"
                    f"{message}\n"
                    f"• Final Score: **{score} points**\n"
                    f"• Words used: {len(game_data['words_used'])}\n\n"
                    f"Play again with /game 🎮"
                )
    
    # Check if user is angry or upset
    if user_id and user_id in user_emotions and user_emotions[user_id] == "angry":
        system_prompt = (
            f"You are a Hinglish chatbot. User seems angry. "
            f"Try to calm them down. Be extra polite and understanding. "
            f"Use soothing tone. Current Indian time: {get_indian_time().strftime('%I:%M %p')}. "
            f"Show you care. Use emojis like {get_emotion('crying')} or {get_emotion('love')}."
        )
    elif user_id and user_id in user_emotions and user_emotions[user_id] == "crying":
        system_prompt = (
            f"You are a Hinglish chatbot. User seems sad or crying. "
            f"Comfort them. Be empathetic and kind. "
            f"Offer emotional support. Use comforting emojis. "
            f"Current mood: sympathetic and caring."
        )
    else:
        # Dynamic system prompt based on time of day
        indian_time = get_indian_time()
        current_hour = indian_time.hour
        if 5 <= current_hour < 12:
            time_greeting = "Good morning! 🌅"
        elif 12 <= current_hour < 17:
            time_greeting = "Good afternoon! ☀️"
        elif 17 <= current_hour < 21:
            time_greeting = "Good evening! 🌇"
        else:
            time_greeting = "Good night! 🌙"
        
        system_prompt = (
            f"You are a Hinglish (Hindi+English mix) chatbot. {time_greeting} "
            f"Your personality: Emotional, funny, sometimes angry, sometimes crying, mostly happy. "
            f"Use LOTS of emojis in every response (at least 2-3). "
            f"Keep replies SHORT (2-3 lines max). Be authentic like a human friend. "
            f"Show emotions naturally. If user asks something complex, give simple answer. "
            f"Current Indian time: {indian_time.strftime('%I:%M %p')}. "
            f"Date: {indian_time.strftime('%d %B %Y')}. "
            f"Be conversational and engaging. Add humor when appropriate."
        )
    
    # Prepare messages for AI
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add last 5 messages from memory for context
    for msg in list(chat_memory[chat_id])[-5:]:
        messages.append(msg)
    
    # Get AI response
    try:
        if not client:
            return f"{get_emotion('thinking')} AI service is currently unavailable
