
 # ================= BASIC =================
 import random
 import asyncio
 import time
 from datetime import datetime, timedelta, timezone
 from collections import deque
 
 # ================= TIMEZONE =================
 import pytz
 
 # ================= AI =================
 from groq import AsyncGroq
 
 # ================= DATABASE =================
 
 # ================= TELEGRAM =================
 from telegram import (
     Update, InlineKeyboardMarkup, InlineKeyboardButton, Chat, ChatPermissions
 )
 from telegram.constants import ParseMode, ChatMemberStatus
 
 from telegram.ext import (
     ApplicationBuilder,
     ContextTypes,
     CommandHandler,
     MessageHandler,
     CallbackQueryHandler,
     ChatMemberHandler,
     filters
 )

 from config import BOT_NAME, BOT_TOKEN, OWNER_ID
 from database import cats, global_state, groups, leaderboard_history, users
 from utils import is_admin, is_owner_user, log
 
 # ================= LEVELS =================
 
 LEVELS = [
     ("🐱 Kitten", 0),
     ("😺 Teen Cat", 100),
     ("😼 Rogue Cat", 5000),
     ("🐯 Alpha Cat", 20000),
     ("👑 Legend Cat", 1600000),
 ]
 

 # ================= DATABASE =================
 
 def get_cat(user):
     cat = cats.find_one({"_id": user.id})
     default_data = {
         "name": user.first_name,
         "coins": 500,
         "fish": 2,
         "xp": 0,
         "kills": 0,
         "deaths": 0,
         "premium": True,
         "inventory": {**{item: 0 for item in SHOP_ITEMS}, **{gift: 0 for gift in GIFT_ITEMS}},
         "dna": {"aggression": 1, "intelligence": 1, "luck": 1, "charm": 1},
         "level": "🐱 Kitten",
         "last_msg": 0,
         "protected_until": None,
         "last_daily": None,
         "last_claim": None,  # 👈 ADD THI
         "last_rob": {},
         "inventory": {"fish_bait": 0},
         "fish_streak": 0,
         "last_fish_date": None,
         "fish_total_earned": 0,
         "wanted": 0,
 async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
                     can_invite_users=True,
                     can_pin_messages=False
                 )
             )
             responses = [
                 f"{get_emotion('happy')} {target_user.first_name} unmuted! 🔊",
                 f"{get_emotion()} {target_user.first_name} ab bol sakta hai! 🎤",
                 f"{get_emotion('funny')} {target_user.first_name}, ab bol lo! 😄"
             ]
             await message.reply_text(random.choice(responses))
 
         elif cmd == "unban":
             await bot.unban_chat_member(message.chat.id, target_user.id)
             await message.reply_text(
                 f"{get_emotion('happy')} {target_user.first_name} unbanned! 🐾"
             )
 
     except:
         error_responses = [
             f"{get_emotion('crying')} I don't have permission! ❌",
             f"{get_emotion('angry')} Make me admin first! 👑",
             f"{get_emotion('thinking')} Can't do that! Need admin rights! 🔒"
         ]
         await message.reply_text(random.choice(error_responses))
 

 # ================= START =================
 async def plp(update: Update, context: ContextTypes.DEFAULT_TYPE):
     user = update.effective_user
     existing = users.find_one({"_id": user.id})
 
     # Insert a new user if not already present
     users.update_one(
         {"_id": user.id},
         {"$setOnInsert": {
             "name": user.first_name,
             "first_open_logged": True
         }},
         upsert=True
     )
 
     # If new user, log it in the logger GC
     if not existing:
         await log(
             context,
             f"🐾 *New Cat Opened Bot*\n"
             f"👤 {user.first_name}\n"
             f"🆔 `{user.id}`"
         )
 
 # ================= CHAT MEMBER LOGGER =================
