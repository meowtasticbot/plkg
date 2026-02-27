import random

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import ContextTypes

from Meowstric.database import sudoers_collection
from telegram.error import BadRequest, TelegramError
from Meowstric.utils import SUDO_USERS, log_to_channel, reload_sudoers


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
        first_arg = context.args[0]
        if first_arg.startswith("@"):
            try:
                member = await chat.get_member(first_arg)
                target_user = member.user
            except Exception:
                return await message.reply_text("User not found in this chat.")
        else:
            try:
                member = await chat.get_member(int(first_arg))
                target_user = member.user
            except Exception:
                return await message.reply_text("Reply to a user or pass a valid @username/user_id.")

    if target_user.id == sender.id:
        return await message.reply_text("Khud pe admin action allowed nahi hai.")

    target_member = await chat.get_member(target_user.id)
    if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text("Admin/owner par ye action allowed nahi hai.")

    try:
        if command == "kick":
            await chat.unban_member(target_user.id)
            await message.reply_text(f"{get_emotion('angry')} Kicked {target_user.first_name}.")
        elif command == "ban":
            await chat.ban_member(target_user.id)
            await message.reply_text(f"🚫 Banned {target_user.first_name}.")
        elif command == "mute":
            await chat.restrict_member(
                target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await message.reply_text(f"🔇 Muted {target_user.first_name}.")
        elif command == "unmute":
            await chat.restrict_member(
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
            await message.reply_text(f"🔊 Unmuted {target_user.first_name}.")
        elif command == "unban":
            await chat.unban_member(target_user.id)
            await message.reply_text(f"✅ Unbanned {target_user.first_name}.")
    except BadRequest as exc:
        await message.reply_text(f"⚠️ Action failed: {exc.message}")
    except TelegramError:
        await message.reply_text("⚠️ Telegram API error aayi, dobara try karo."

async def plp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = update.effective_user

    if not message or not user:
        return

    if user.id not in SUDO_USERS:
        return await message.reply_text("Only owner/sudo can manage sudoers.")

    if not context.args:
        sudo_list = sorted(SUDO_USERS)
        text = "👑 Sudo users:\n" + "\n".join([f"• <code>{uid}</code>" for uid in sudo_list])
        return await message.reply_text(text, parse_mode="HTML")

    action = context.args[0].lower()
    if action not in {"add", "del", "remove", "list"}:
        return await message.reply_text("Usage: /plp [add|del|remove|list] <user_id>")

    if action == "list":
        sudo_list = sorted(SUDO_USERS)
        text = "👑 Sudo users:\n" + "\n".join([f"• <code>{uid}</code>" for uid in sudo_list])
        return await message.reply_text(text, parse_mode="HTML")

    if len(context.args) < 2:
        return await message.reply_text("Pass a user_id too. Example: /plp add 123456")

    try:
        target_id = int(context.args[1])
    except ValueError:
        return await message.reply_text("Invalid user_id.")

    if action == "add":
        sudoers_collection.update_one({"user_id": target_id}, {"$set": {"user_id": target_id}}, upsert=True)
        reload_sudoers()
        return await message.reply_text(f"✅ Added <code>{target_id}</code> to sudoers.", parse_mode="HTML")

    sudoers_collection.delete_one({"user_id": target_id})
    reload_sudoers()
    await message.reply_text(f"✅ Removed <code>{target_id}</code> from sudoers.", parse_mode="HTML")


__all__ = ["welcome_new_member", "admin_commands", "plp"]
