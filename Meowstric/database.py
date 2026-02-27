from pymongo import MongoClient

from Meowstric.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["catverse"]

cats = db["cats"]
global_state = db["global"]
leaderboard_history = db["leaderboard_history"]
users = db["users"]
groups = db["groups"]
sudoers_collection = db["sudoers"]

# Compatibility aliases for modular handlers
users_collection = users
groups_collection = groups
chatbot_collection = db["chatbot"]
