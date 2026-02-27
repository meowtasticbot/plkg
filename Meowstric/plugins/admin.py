import random

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import ContextTypes

from Meowstric.database import sudoers_collection
from Meowstric.utils import SUDO_USERS, log, log_to_channel, reload_sudoers


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
    if not update.chat_member:
        return

    chat = update.effective_chat
    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status
    member = update.chat_member.new_chat_member.user

    joined_statuses = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    left_statuses = {ChatMemberStatus.LEFT, ChatMemberStatus.BANNED}

    if new_status in joined_statuses and old_status not in joined_statuses:
        messages = [
            f"🎉 Welcome {member.first_name}! Khush aamdeed! 😊",
            f"🌟 Aao ji {member.first_name}! Group me welcome! 🫂",
            f"✨ Hey {member.first_name}! Great to have you here! 💖",
        ]
        await context.bot.send_message(chat.id, random.choice(messages))
        await log_to_channel(
            context.bot,
            "member_added",
            {
                "chat": f"{chat.title} ({chat.id})",
                "user": f"{member.first_name} ({member.id})",
                "username": f"@{member.username}" if member.username else "N/A",
            },
        )
    elif new_status in left_statuses and old_status not in left_statuses:
        await log_to_channel(
            context.bot,
            "member_removed",
            {
                "chat": f"{chat.title} ({chat.id})",
                "user": f"{member.first_name} ({member.id})",
                "username": f"@{member.username}" if member.username else "N/A",
            },
        )


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat
    sender = update.effective_user

    if not message or not chat or not sender:
        return

    if chat.type == ChatType.PRIVATE:
        return await message.reply_text("This command works only in groups.")

    me = await chat.get_member(sender.id)
    if me.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and sender.id not in SUDO_USERS:
        return await message.reply_text("Only admins can use this command.")

    command = (message.text or "").split()[0].replace("/", "").split("@")[0].lower()
    target_user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user

    # @username case
    elif context.args:
