# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
# Final Start Plugin - Fixed Inline Keyboard Error

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import BOT_NAME, OWNER_LINK, START_IMG_URL
from Meowstric.utils import ensure_user_exists, track_group


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
        except Exception:
            pass
    else:
        await update.message.reply_photo(photo=START_IMG_URL, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)


async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "return_start":
        await start_handler(update, context)

    elif data == "talk_baka":
        talk_text = "💬 To talk to me, just send me any message!"
        try:
            await query.message.edit_caption(caption=talk_text, reply_markup=get_back_to_start(), parse_mode=ParseMode.HTML)
        except Exception:
            pass

    elif data == "game_features":
        game_text = (
            "🎮 <b>CATVERSE GAME MODE</b>\n\n"
            "⚔️ <b>Battle:</b> /rob, /kill, /protect\n"
            "💰 <b>Economy:</b> /daily, /claim, /bal, /give\n"
            "🛒 <b>Shop:</b> /shop, /inventory, /use\n"
            "🐟 <b>Fishing:</b> /fish, /fishlb\n"
            "📊 <b>Ranks:</b> /xp, /meow, /toprich, /topkill\n"
            "💣 <b>Mini Games:</b> /bomb, /join, /pass\n"
            "🌸 <b>Collection:</b> Waifu drops in active groups\n\n"
            "Use /games for full guide and start grinding coins! 🪙"
        )
        try:
            await query.message.edit_caption(caption=game_text, reply_markup=get_back_to_start(), parse_mode=ParseMode.HTML)
        except Exception:
            pass

    await query.answer()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛡 <b>Admin Commands:</b>\n"
        "/kick /ban /mute /unmute /unban (reply based)\n\n"
        "💰 <b>Economy:</b> /daily /claim /bal /give /gift /shop /inventory /use\n"
        "⚔️ <b>Combat:</b> /rob /kill /protect\n"
        "🎮 <b>Game:</b> /games /fish /fishlb /toprich /topkill /xp /meow\n"
    )
    await update.message.reply_text(text=help_text, parse_mode=ParseMode.HTML)


__all__ = ["start_handler", "start_callback", "help_command", "get_start_keyboard", "get_back_to_start"]
