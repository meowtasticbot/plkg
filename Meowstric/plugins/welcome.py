# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import SUPPORT_GROUP, WELCOME_IMG_URL
from Meowstric.database import groups_collection
from Meowstric.utils import ensure_user_exists, get_mention


async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/Disable Welcomes via /welcome on/off."""
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("🍼 Grp only baby!")

    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("❌ Admin only!")

    if not context.args:
        return await update.message.reply_text(
            "⚠️ Usage: <code>/welcome on</code> or <code>off</code>", parse_mode=ParseMode.HTML
        )

    state = context.args[0].lower()
    enabled = state in ["on", "enable", "yes"]
    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"welcome_enabled": enabled}}, upsert=True)
    status = "Enabled ✅" if enabled else "Disabled ❌"
    await update.message.reply_text(f"🌹 <b>Welcome Messages {status}</b>", parse_mode=ParseMode.HTML)


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Naye users ko welcome karta hai."""
    chat = update.effective_chat
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            txt = (
                f"🌹 <b>Welcome {get_mention(update.message.from_user)}!</b>\n\n"
                "Thanks for adding me! ✨\nType <code>/claim</code> for bonus!"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Support", url=SUPPORT_GROUP)]])
            try:
                await update.message.reply_photo(
                    WELCOME_IMG_URL, caption=txt, parse_mode=ParseMode.HTML, reply_markup=kb
                )
            except Exception:
                await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            ensure_user_exists(member)
            group_data = groups_collection.find_one({"chat_id": chat.id})
            if group_data and group_data.get("welcome_enabled", True):
                welcome_text = f"Welcome {get_mention(member)} 🌹"
                try:
                    await update.message.reply_photo(
                        WELCOME_IMG_URL, caption=welcome_text, parse_mode=ParseMode.HTML
                    )
                except Exception:
                    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


__all__ = ["welcome_command", "new_member"]
