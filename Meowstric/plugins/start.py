# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
# Final Start Plugin - Fixed Inline Keyboard Error

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from Meowstric.config import BOT_NAME, OWNER_LINK, START_IMG_URL
from Meowstric.utils import ensure_user_exists, log_to_channel, track_group


def get_start_keyboard(bot_username):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 𝚃𝙰𝙻𝙺 𝚃𝙾 𝙱𝙰𝙺𝙰", callback_data="talk_baka"),
            InlineKeyboardButton("𝙾𝚆𝙽𝙴𝚁 ⚡", url=OWNER_LINK),
        ],
        [
            InlineKeyboardButton("🧸 𝙵𝚁𝙸𝙴𝙽𝙳𝚂", url="https://t.me/+hvxrr2DudTs4ODU1"),
            InlineKeyboardButton("𝙶𝙰𝙼𝙴𝚂 🎮", callback_data="game_features"),
        ],
        [
            InlineKeyboardButton(
                "➕ 𝙰𝙳𝙳 𝙼𝙴 𝚃𝙾 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿 👥",
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
    ])


def get_back_to_start():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝙱𝚊𝚌𝚔", callback_data="return_start")]])


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
        f"✨ <b>𝙷𝚎𝚢 — {user.first_name} ~</b>\n"
        f"💌 𝚈𝚘𝚞'𝚛𝚎 𝚃𝚊𝚕𝚔𝚒𝚗𝚐 𝚃𝚘 {BOT_NAME}, 𝙰 𝚂𝚊𝚜𝚜𝚢 𝙲𝚞𝚝𝚒𝚎 💕\n\n"
        "➬ 𝙲𝚑𝚘𝚘𝚜𝚎 𝙰𝚗 𝙾𝚙𝚝𝚒𝚘𝚗 𝙱𝚎𝚕𝚘𝚠:"
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
            await update.message.reply_photo(
                photo=START_IMG_URL,
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
        await query.answer("Baka mode on 😼")
        text = (
            "😼 <b>Baka Chat Mode</b>\n\n"
            "Just send me any normal text message and I will reply.\n"
            "Use game/economy commands from menu too."
        )
    elif data == "game_features":
        await query.answer("Opening game guide 🎮")
        text = (
            "🎮 <b>Game Features</b>\n\n"
            "• /daily - Daily coins\n"
            "• /claim - Group claim reward\n"
            "• /bal - Check wallet\n"
            "• /rob, /kill, /protect - PvP actions\n"
            "• /shop, /inventory, /use - Items\n"
            "• /fish, /fishlb - Fishing system\n"
            "• /toprich, /topkill, /xp - Leaderboards"
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
