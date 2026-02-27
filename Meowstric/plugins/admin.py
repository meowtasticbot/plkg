import random
from datetime import datetime, timedelta

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.database import groups, groups_collection, sudoers_collection, users, users_collection
from Meowstric.utils import log, reload_sudoers


def get_emotion(mood: str = "happy") -> str:
    emotions = {
        "happy": "😺",
        "angry": "😾",
        "thinking": "🤔",
        "crying": "😿",
        "funny": "😹",
    }
    return emotions.get(mood, "😺")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_status = update.chat_member.new_chat_member.status
    if new_status == ChatMemberStatus.MEMBER:
        member = update.chat_member.new_chat_member.user
        messages = [
            f"🎉 Welcome {member.first_name}! Khush aamdeed! 😊",
            f"🌟 Aao ji {member.first_name}! Group me welcome! 🫂",
            f"✨ Hey {member.first_name}! Great to have you here! 💖"
        ]
        await context.bot.send_message(update.effective_chat.id, random.choice(messages))

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    bot = context.bot

    target_user = None

    # ================= TARGET USER =================
    # Reply case
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    # @username case
    elif context.args:
