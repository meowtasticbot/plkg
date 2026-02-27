# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>
# Location: Supaul, Bihar

import os
import time

import psutil
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import BOT_NAME, START_TIME


def get_readable_time(seconds: int) -> str:
    count = 0
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        time_list.pop()

    time_list.reverse()
    return ":".join(time_list)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks API Latency and System Stats."""
    if not update.message:
        return

    try:
        start_time = time.time()
        msg = await update.message.reply_text("⚡ <b>Pinging...</b>", parse_mode=ParseMode.HTML)
        end_time = time.time()
        latency = round((end_time - start_time) * 1000)

        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📡 System Stats", callback_data="sys_stats")]]
        )

        await msg.edit_text(
            f"🏓 <b>Pong!</b>\n\n"
            f"📶 <b>Latency:</b> <code>{latency}ms</code>\n"
            f"🤖 <b>Status:</b> 🟢 Online\n"
            f"<i>Click below for server details!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception:
        pass


async def ping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.data != "sys_stats":
        return

    try:
        uptime = get_readable_time(int(time.time() - START_TIME))
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.getcwd()).percent

        text = (
            f"📊 {BOT_NAME} Stats 📊\n\n"
            f"⏰ Uptime: {uptime}\n"
            f"🧠 RAM: {ram}%\n"
            f"⚙️ CPU: {cpu}%\n"
            f"💾 Disk: {disk}%"
        )

        await query.answer(text, show_alert=True)
    except Exception:
        await query.answer("❌ Error fetching stats", show_alert=True)


__all__ = ["ping", "ping_callback", "get_readable_time"]
