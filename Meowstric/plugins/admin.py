
from datetime import datetime, timedelta, timezone

from telegram import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from Meowstric.config import SUPPORT_GROUP, WELCOME_IMG_URL
from Meowstric.database import groups_collection, sudoers_collection

from Meowstric.utils import SUDO_USERS, get_mention, log_to_channel, reload_sudoers


def get_emotion(mood: str = "happy") -> str:
    emotions = {
        "happy": "😺",
        "angry": "😾",
        "thinking": "🤔",
        "crying": "😿",
        "funny": "😹",
    }
    return emotions.get(mood, "😺")


def _extract_command(text: str) -> str:
    head = (text or "").split()[0]
    return head.replace("/", "").replace(".", "").split("@")[0].lower()


def _parse_duration(raw: str):
    if not raw:
        return None
    raw = raw.strip().lower()
    if raw in {"perm", "permanent", "forever"}:
        return None
    try:
        if raw.endswith("m"):
            return datetime.now(timezone.utc) + timedelta(minutes=int(raw[:-1]))
        if raw.endswith("h"):
            return datetime.now(timezone.utc) + timedelta(hours=int(raw[:-1]))
        if raw.endswith("d"):
            return datetime.now(timezone.utc) + timedelta(days=int(raw[:-1]))
    except ValueError:
        return None
    return None


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


async def welcome_new_members_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.new_chat_members:
        return

    chat = update.effective_chat
    group_data = groups_collection.find_one({"chat_id": chat.id}) or {}
    if not group_data.get("welcome_enabled", True):
        return
    base_messages = [
        "🎉 <b>Welcome {name}!</b> Khush aamdeed! 😊",
        "🌟 <b>Aao ji {name}!</b> Group me warm welcome! 🫂",
        "✨ <b>Hey {name}!</b> Great to have you here! 💖",
        "😺 <b>{name}</b> joined the cat gang! Warm welcome!",
        "🌈 <b>Welcome aboard, {name}!</b> Masti shuru karo!",
    ]

    for idx, member in enumerate(update.message.new_chat_members):
        if member.id == context.bot.id:
            continue
        msg_template = base_messages[idx % len(base_messages)]
        text = (
            f"{msg_template.format(name=get_mention(member))}\n\n"
            "🤖 I'm here to help with games, economy & smart chat replies."
        )

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP)]])
        try:
            await context.bot.send_photo(
                chat_id=chat.id,
                photo=WELCOME_IMG_URL,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        except Exception:
            await context.bot.send_message(chat.id, text, parse_mode=ParseMode.HTML)
            



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

    command = _extract_command(message.text or "")
    raw_parts = (message.text or "").split()
    raw_args = raw_parts[1:] if len(raw_parts) > 1 else []
    if context.args:
        raw_args = context.args
    target_user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user

    elif raw_args:
        first_arg = raw_args[0]
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
                target_user = None

    if command in {"unpin"}:
        await chat.unpin_all_messages()
        return await message.reply_text("📌 Current pinned message removed.")

    if command in {"d"}:
        if not message.reply_to_message:
            return await message.reply_text("Reply to a message for delete.")
        await message.reply_to_message.delete()
        await message.delete()
        return

    if command in {"pin"}:
        if not message.reply_to_message:
            return await message.reply_text("Reply to a message to pin.")
        await chat.pin_message(message.reply_to_message.message_id, disable_notification=True)
        return await message.reply_text("📌 Message pinned.")

    if command in {"warn", "unwarn", "kick", "ban", "unban", "mute", "unmute", "promote", "demote", "title"} and not target_user:
        return await message.reply_text("Reply karo ya valid @username/user_id do.")

    if target_user and target_user.id == sender.id:
        return await message.reply_text("Khud pe admin action allowed nahi hai.")

    if target_user:
        target_member = await chat.get_member(target_user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and command not in {"title"}:
            return await message.reply_text("Admin/owner par ye action allowed nahi hai.")

    try:
        if command == "kick":
            await chat.unban_member(target_user.id)
            await message.reply_text(f"{get_emotion('angry')} Kicked {target_user.first_name}.")

        elif command == "ban":
            await chat.ban_member(target_user.id)
            await message.reply_text(f"🚫 Banned {target_user.first_name}.")

        elif command == "mute":
            until = _parse_duration(raw_args[1] if len(raw_args) > 1 else "") if raw_args else None
            await chat.restrict_member(
                target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
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

        elif command == "warn":
            key = f"warnings.{target_user.id}"
            groups_collection.update_one({"chat_id": chat.id}, {"$inc": {key: 1}, "$setOnInsert": {"chat_id": chat.id}}, upsert=True)
            data = groups_collection.find_one({"chat_id": chat.id}) or {}
            count = (((data.get("warnings") or {}).get(str(target_user.id))) or 0)
            if count >= 3:
                await chat.ban_member(target_user.id)
                groups_collection.update_one({"chat_id": chat.id}, {"$set": {key: 0}})
                await message.reply_text(f"🚫 {target_user.first_name} banned (3 warnings).")
            else:
                await message.reply_text(f"⚠️ {target_user.first_name} warned. Total: {count}/3")

        elif command == "unwarn":
            key = f"warnings.{target_user.id}"
            data = groups_collection.find_one({"chat_id": chat.id}) or {}
            current = (((data.get("warnings") or {}).get(str(target_user.id))) or 0)
            new_count = max(0, current - 1)
            groups_collection.update_one({"chat_id": chat.id}, {"$set": {key: new_count}, "$setOnInsert": {"chat_id": chat.id}}, upsert=True)
            await message.reply_text(f"✅ Warning removed. {target_user.first_name}: {new_count}/3")

        elif command == "promote":
            level = 1
            if len(raw_args) > 1:
                try:
                    level = int(raw_args[1])
                except ValueError:
                    level = 1
            level = 1 if level not in {1, 2, 3} else level
            perms = {
                "can_manage_chat": True,
                "can_delete_messages": True,
                "can_restrict_members": level >= 2,
                "can_invite_users": True,
                "can_pin_messages": True,
                "can_promote_members": level >= 3,
                "can_change_info": level >= 2,
                "can_manage_video_chats": level >= 2,
            }
            await chat.promote_member(target_user.id, **perms)
            await message.reply_text(f"✅ Promoted {target_user.first_name} to admin level {level}.")

        elif command == "demote":
            await chat.promote_member(
                target_user.id,
                can_manage_chat=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_change_info=False,
                can_manage_video_chats=False,
            )
            await message.reply_text(f"⬇️ Demoted {target_user.first_name}.")

        elif command == "title":
            if len(raw_args) < 2:
                return await message.reply_text("Usage: .title [reply]/[user_id] [tag]")
            title = " ".join(raw_args[1:]).strip()
            await chat.set_administrator_custom_title(target_user.id, title)
            await message.reply_text(f"🏷️ Title set for {target_user.first_name}: {title}")

    except BadRequest as exc:
        await message.reply_text(f"⚠️ Action failed: {exc.message}")
    except TelegramError:
        await message.reply_text("⚠️ Telegram API error aayi, dobara try karo.")


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

    if len(context.args) < 2
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


__all__ = ["welcome_new_member", "welcome_new_members_message", "admin_commands", "plp"]
