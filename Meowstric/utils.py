import html
from datetime import datetime

from telegram import Chat, User
from telegram.constants import ChatType, ParseMode

from Meowstric.config import BOT_NAME, LOGGER_ID, OWNER_ID, SUDO_IDS
from Meowstric.database import groups, groups_collection, sudoers_collection, users, users_collection

# --- 👑 SUDO SYSTEM ---
SUDO_USERS = set()


def reload_sudoers():
    """Loads sudo users from both config and database."""
    try:
        SUDO_USERS.clear()
        SUDO_USERS.add(OWNER_ID)

        for sid in SUDO_IDS:
            SUDO_USERS.add(int(sid))

        for doc in sudoers_collection.find({}):
            uid = doc.get("user_id")
            if uid is not None:
                SUDO_USERS.add(int(uid))
    except Exception:
        pass


def is_owner_user(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_admin(user_id: int) -> bool:
    return user_id in SUDO_USERS


async def log(context, text):
    """Log messages to the logger group/channel."""
    await context.bot.send_message(LOGGER_ID, text, parse_mode="Markdown")


def ensure_user_exists(user):
    users.update_one(
        {"_id": user.id},
        {
            "$set": {"user_id": user.id, "name": user.first_name},
            "$setOnInsert": {"created": datetime.utcnow(), "bot": BOT_NAME, "partner_id": None, "balance": 0},
        },
        upsert=True,
    )
    doc = users.find_one({"_id": user.id}) or users.find_one({"user_id": user.id}) or {"_id": user.id, "user_id": user.id, "name": user.first_name, "partner_id": None, "balance": 0}
    if "balance" not in doc:
        users.update_one({"_id": user.id}, {"$set": {"balance": 0}})
        doc["balance"] = 0
    if "partner_id" not in doc:
        users.update_one({"_id": user.id}, {"$set": {"partner_id": None}})
        doc["partner_id"] = None
    return doc


def track_group(chat, user=None):
    """Tracks group activity and adds to database."""
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        groups_collection.update_one(
            {"chat_id": chat.id},
            {
                "$set": {"title": chat.title, "_id": chat.id},
                "$setOnInsert": {"claimed": False, "economy_enabled": True},
            },
            upsert=True,
        )
        if user:
            users_collection.update_one(
                {"user_id": user.id},
                {
                    "$set": {"name": user.first_name, "_id": user.id},
                    "$addToSet": {"seen_groups": chat.id},
                },
                upsert=True,
            )


def get_mention(user_data, custom_name=None):
    """Generates a clickable HTML link for a user."""
    if isinstance(user_data, (User, Chat)):
        uid = user_data.id
        name = getattr(user_data, "first_name", getattr(user_data, "title", "User"))
    elif isinstance(user_data, dict):
        uid = user_data.get("user_id") or user_data.get("_id")
        name = user_data.get("name", "User")
    else:
        return "Unknown"

    safe_name = html.escape(custom_name or name or "User")
    return f'<a href="tg://user?id={uid}"><b>{safe_name}</b></a>'


reload_sudoers()


def format_money(amount: int) -> str:
    return f"{int(amount):,} coins"



async def resolve_target(update, context, specific_arg=None):
    msg = update.message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        target_user = msg.reply_to_message.from_user
        target = ensure_user_exists(target_user)
        return target, None

    arg = specific_arg or (context.args[0] if getattr(context, "args", None) else None)
    if not arg:
        return None, "Reply to a user or pass @username/user_id"

    if arg.startswith('@'):
        try:
            member = await update.effective_chat.get_member(arg)
            target = ensure_user_exists(member.user)
            return target, None
        except Exception:
            return None, "User not found in this chat"

    try:
        uid = int(arg)
        target = users_collection.find_one({"$or": [{"user_id": uid}, {"_id": uid}]})
        if target:
            return target, None
        return None, "User not found"
    except Exception:
        return None, "Invalid target"



def is_catverse_enabled(chat) -> bool:
    if not chat or getattr(chat, "type", None) == "private":
        return True
    g = groups_collection.find_one({"chat_id": chat.id}) or groups_collection.find_one({"_id": chat.id}) or {}
    return g.get("economy_enabled", True)


async def log_to_channel(bot, event_type: str, details: dict):
    if not LOGGER_ID or LOGGER_ID == 0:
        return
    now = datetime.now().strftime("%I:%M:%S %p")
    text = f"📜 <b>{event_type.upper()}</b>\n━━━━━━━━━━━━━━━━━━\n"
    for k, v in details.items():
        text += f"<b>{k.title()}:</b> {v}\n"
    text += f"━━━━━━━━━━━━━━━━━━\n⌚ <code>{now}</code>"
    try:
        await bot.send_message(chat_id=LOGGER_ID, text=text, parse_mode=ParseMode.HTML)
    except Exception:
        pass
