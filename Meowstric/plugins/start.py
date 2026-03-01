# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
# Final Start Plugin - Fixed Inline Keyboard Error

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from pathlib import Path

from Meowstric.config import BOT_NAME, OWNER_LINK, SUPPORT_GROUP
from Meowstric.utils import ensure_user_exists, log_to_channel, track_group

START_IMAGE_PATH = Path(__file__).resolve().parent.parent / "assets" / "123344.jpeg"

def get_start_keyboard(bot_username):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("💬 Chat with Meow", callback_data="talk_baka"),
            InlineKeyboardButton("🔥 Cool Features", callback_data="show_features"),
        ],
        [
            InlineKeyboardButton("🎮 Game Zone", callback_data="game_features"),
            InlineKeyboardButton("🛟 Support", url=SUPPORT_GROUP)
        ],
    ])


def get_back_to_start():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="return_start")]])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    ensure_user_exists(user)
    track_group(chat, user)

    if chat and chat.type == "private":
        await log_to_channel(
            context.bot,
            "bot_start",
            {
                "user": f"{user.first_name} ({user.id})",
                "username": f"@{user.username}" if user.username else "N/A",
            },
        )

    caption = (
        "💫 <b>Welcome to the Meowverse!</b>\n"
        f"Hey <b>{user.first_name}</b> — I am <b>{BOT_NAME}</b>, your premium AI + group power bot. 😺\n\n"
        "⚡ <b>Why people love me:</b>\n"
        "• Smooth AI chat with smart replies\n"
        "• Addictive games, economy & leaderboards\n"
        "• Powerful moderation and utility toolsn\n\n"
        "🎯 <b>Tap a button below to explore.</b>"
    )

    kb = get_start_keyboard(context.bot.username)

    if update.callback_query:
        query = update.callback_query
        try:
            await query.message.edit_caption(caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
        except BadRequest:
            try:
                await query.message.edit_text(text=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
            except BadRequest:
                pass
    else:       
        try:
            photo = START_IMAGE_PATH if START_IMAGE_PATH.exists() else "https://img.sanishtech.com/u/7a53054460bf7f0318de8cb3e838412a.png"
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
            )
        except BadRequest:
            await update.message.reply_text(
                caption,
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
            )


async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    data = query.data or ""

    if data == "return_start":
        await query.answer()
        return await start_handler(update, context)

    if data == "talk_baka":
        await query.answer("Meowstric is ready 😼")
        text = (
            "😼 <b>Chat Mode Activated</b>\n\n"
            "Drop any message and I'll answer instantly with smart AI style.\n"
            "In groups, reply to my message or start with hi/hey/meow for best response."
        )
    elif data == "show_features":
        await query.answer("Loading top features ✨")
        text = (
            "🔥 <b>Top Features</b>\n\n"
            "• AI replies with personality\n"
            "• Welcome + moderation support\n"
            "• Couple/profile/social commands\n"
            "• Fun events, voice & utility tools\n"
            "• Fast inline menus for easy use"
        )
    elif data == "game_features":
        await query.answer("Opening game menu 🎮")
        text = (
            "🎮 <b>Game & Economy Highlights</b>\n\n"
            "• <code>/daily</code> - Daily coins\n"
            "• <code>/claim</code> - Group claim reward\n"
            "• <code>/bal</code> - Wallet check\n"
            "• <code>/rob</code>, <code>/kill</code>, <code>/protect</code> - PvP actions\n"
            "• <code>/shop</code>, <code>/inventory</code>, <code>/use</code> - Items\n"
            "• <code>/fish</code>, <code>/fishlb</code> - Fishing system\n"
            "• <code>/toprich</code>, <code>/topkill</code>, <code>/xp</code> - Leaderboards"
        )
    else:
        await query.answer()
        return

    try:
        await query.message.edit_caption(
            caption=text,
            reply_markup=get_back_to_start(),
            parse_mode=ParseMode.HTML,
        )
    except BadRequest:
        await query.message.edit_text(
            text=text,
            reply_markup=get_back_to_start(),
            parse_mode=ParseMode.HTML,
        )


__all__ = ["start_handler", "start_callback"]
