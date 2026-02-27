import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "7789325573"))
LOGGER_GROUP_ID = int(os.getenv("LOGGER_GROUP_ID", "-1003833185152"))
LOGGER_ID = int(os.getenv("LOGGER_ID", str(LOGGER_GROUP_ID)))
BOT_NAME = os.getenv("BOT_NAME", "Meowstric 😺")

if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

if not MONGO_URI:
    raise RuntimeError("Missing MONGO_URI environment variable")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATBOT_BOT_TOKEN = os.getenv("CHATBOT_BOT_TOKEN", BOT_TOKEN)
OWNER_LINK = os.getenv("OWNER_LINK", "https://t.me/btw_moon")

# Sudo ids from env, comma separated
_raw_sudo_ids = os.getenv("SUDO_IDS", "")
SUDO_IDS = [int(x.strip()) for x in _raw_sudo_ids.split(",") if x.strip().isdigit()]
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
CODESTRAL_API_KEY = os.getenv("CODESTRAL_API_KEY")
WELCOME_IMG_URL = os.getenv("WELCOME_IMG_URL", "https://img.sanishtech.com/u/7a53054460bf7f0318de8cb3e838412a.png")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/meowstric")
DIVORCE_COST = int(os.getenv("DIVORCE_COST", "5000"))
START_TIME = int(os.getenv("START_TIME", str(int(time.time()))))
WAIFU_PROPOSE_COST = int(os.getenv("WAIFU_PROPOSE_COST", "1500"))
MIN_CLAIM_MEMBERS = int(os.getenv("MIN_CLAIM_MEMBERS", "1000"))


# Chatbot settings
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "kitty")
CHATBOT_OWNER_USERNAME = os.getenv("CHATBOT_OWNER_USERNAME", "@Moon_m_5")
CHATBOT_OWNER_NAME = os.getenv("CHATBOT_OWNER_NAME", "Moon")
CHATBOT_USERNAME = os.getenv("BOT_USERNAME", "")
CHATBOT_TRIGGERS = tuple(
    x.strip().lower()
    for x in os.getenv("CHATBOT_TRIGGERS", "billi,cat,meow").split(",")
    if x.strip()
)
