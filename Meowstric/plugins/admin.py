import random

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import ContextTypes

from Meowstric.database import sudoers_collection
from Meowstric.utils import SUDO_USERS, log, reload_sudoers


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

    new_status = update.chat_member.new_chat_member.status
    if new_status == ChatMemberStatus.MEMBER:
        member = update.chat_member.new_chat_member.user
        messages = [
            f"🎉 Welcome {member.first_name}! Khush aamdeed! 😊",
            f"🌟 Aao ji {member.first_name}! Group me welcome! 🫂",
            f"✨ Hey {member.first_name}! Great to have you here! 💖",
        ]
        await context.bot.send_message(update.effective_chat.id, random.choice(messages))


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
        raw = context.args[0]
        if raw.startswith("@"):
            try:
                member = await chat.get_member(raw)
                target_user = member.user
            except Exception:
                target_user = None
        else:
            try:
                uid = int(raw)
                member = await chat.get_member(uid)
                target_user = member.user
            except Exception:
                target_user = None

    if not target_user:
        return await message.reply_text("Reply to a user or pass user_id.")

    if target_user.id == sender.id:
        return await message.reply_text("Khud pe command mat chalao 😂")

    if target_user.id == context.bot.id:
        return await message.reply_text("Mujhe kyun target kar rahe ho? 😾")

    try:
        target_member = await chat.get_member(target_user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("I cannot perform admin action on another admin.")
    except Exception:
        pass

    if command == "kick":
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await context.bot.unban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"{get_emotion('angry')} Kicked {target_user.first_name}")

    elif command == "ban":
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"⛔ Banned {target_user.first_name}")

    elif command == "mute":
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        await message.reply_text(f"🔇 Muted {target_user.first_name}")

    elif command == "unmute":
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            ),
        )
        await message.reply_text(f"🔊 Unmuted {target_user.first_name}")

    elif command == "unban":
        await context.bot.unban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"✅ Unbanned {target_user.first_name}")

    else:
        return await message.reply_text("Unknown admin command.")

    await log(context, f"#admin\nby: {sender.id}\ncmd: {command}\ntarget: {target_user.id}\nchat: {chat.id}")


async def plp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS:
        return

    message = update.message
    if not message or not context.args:
        return await message.reply_text("Usage: /plp add|del <user_id>")

    action = context.args[0].lower()
    if action not in {"add", "del", "rem", "remove"}:
        return await message.reply_text("Use: add or del")

    if len(context.args) < 2:
        return await message.reply_text("Give me user_id")

    try:
        user_id = int(context.args[1])
    except ValueError:
        return await message.reply_text("Invalid user_id")

    if action == "add":
        sudoers_collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
        text = f"✅ Added {user_id} to sudo users"
    else:
        sudoers_collection.delete_one({"user_id": user_id})
        text = f"🗑 Removed {user_id} from sudo users"

    reload_sudoers()
    await message.reply_text(text)


__all__ = ["admin_commands", "welcome_new_member", "get_emotion", "plp"]
