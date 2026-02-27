# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>
# Location: Supaul, Bihar

import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from Meowstric.database import groups_collection, users_collection
from Meowstric.utils import SUDO_USERS


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_USERS:
        return

    args = context.args
    reply = update.message.reply_to_message

    if not args and not reply:
        return await update.message.reply_text(
            "📢 <b>𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐚𝐧𝐚𝐠𝐞𝐫</b>\n\n"
            "<b>Usage:</b>\n"
            "‣ /broadcast -user (Reply to msg)\n"
            "‣ /broadcast -group (Reply to msg)\n\n"
            "<b>Flags:</b>\n"
            "‣ -clean : Copy msg (Use for Buttons)",
            parse_mode=ParseMode.HTML,
        )

    target_type = "user" if "-user" in args else "group" if "-group" in args else None
    if not target_type:
        return await update.message.reply_text(
            "⚠️ Missing flag: <code>-user</code> or <code>-group</code>",
            parse_mode=ParseMode.HTML,
        )

    is_clean = "-clean" in args

    msg_text = None
    if not reply:
        clean_args = [a for a in args if a not in ["-user", "-group", "-clean"]]
        if not clean_args:
            return await update.message.reply_text(
                "⚠️ Give me a message or reply to one.", parse_mode=ParseMode.HTML
            )
        msg_text = " ".join(clean_args)

    status_msg = await update.message.reply_text(
        f"⏳ <b>Broadcasting to {target_type}s...</b>", parse_mode=ParseMode.HTML
    )

    count = 0
    targets = users_collection.find({}) if target_type == "user" else groups_collection.find({})

    for doc in targets:
        cid = (
            doc.get("user_id") or doc.get("_id")
            if target_type == "user"
            else doc.get("chat_id") or doc.get("_id")
        )
        if not cid:
            continue

        try:
            if reply:
                if is_clean:
                    await reply.copy(cid)
                else:
                    await reply.forward(cid)
            else:
                await context.bot.send_message(chat_id=cid, text=msg_text, parse_mode=ParseMode.HTML)

            count += 1
            if count % 20 == 0:
                await asyncio.sleep(1)

        except Forbidden:
            if target_type == "user":
                users_collection.delete_one({"$or": [{"user_id": cid}, {"_id": cid}]})
            else:
                groups_collection.delete_one({"$or": [{"chat_id": cid}, {"_id": cid}]})
        except Exception:
            pass

    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\nSent to {count} {target_type}s.",
        parse_mode=ParseMode.HTML,
    )


# Legacy compatibility commands
async def ubroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["-user", *context.args]
    await broadcast(update, context)


async def gbroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["-group", *context.args]
    await broadcast(update, context)


def get_all_chats():
    """Sabhi group chat IDs."""
    return [g.get("chat_id") or g.get("_id") for g in groups_collection.find({}, {"chat_id": 1, "_id": 1})]


def get_all_users():
    """Sabhi user IDs."""
    return [u.get("user_id") or u.get("_id") for u in users_collection.find({}, {"user_id": 1, "_id": 1})]


__all__ = ["broadcast", "ubroadcast", "gbroadcast", "get_all_chats", "get_all_users"]
