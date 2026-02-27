# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>

import random
from datetime import datetime

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Meowstric.database import groups_collection, users_collection
from Meowstric.utils import ensure_user_exists, get_mention

active_drops = {}
DROP_MESSAGE_COUNT = 100

WAIFU_NAMES = [
    ("Rem", "rem"), ("Ram", "ram"), ("Emilia", "emilia"), ("Asuna", "asuna"),
    ("Zero Two", "zero two"), ("Makima", "makima"), ("Nezuko", "nezuko"),
    ("Hinata", "hinata"), ("Sakura", "sakura"), ("Mikasa", "mikasa"),
    ("Yor", "yor"), ("Anya", "anya"), ("Power", "power"),
]


async def check_drops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat:
        return
    chat = update.effective_chat
    if chat.type == "private":
        return

    group = groups_collection.find_one_and_update(
        {"chat_id": chat.id}, {"$inc": {"msg_count": 1}}, upsert=True, return_document=True
    ) or {}

    if not group.get("economy_enabled", True):
        return

    if group.get("msg_count", 0) % DROP_MESSAGE_COUNT == 0:
        name, slug = random.choice(WAIFU_NAMES)
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"https://api.waifu.im/search?included_tags={slug}")
                url = r.json()["images"][0]["url"] if r.status_code == 200 else "https://telegra.ph/file/5e5480760e412bd402e88.jpg"
        except Exception:
            url = "https://telegra.ph/file/5e5480760e412bd402e88.jpg"

        active_drops[chat.id] = name.lower()
        caption = "👧 <b>A Waifu Appeared!</b>\nGuess her name to collect her!"
        await update.message.reply_photo(photo=url, caption=caption, parse_mode=ParseMode.HTML)


async def collect_waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    if not msg or not msg.text:
        return
    if chat.id not in active_drops:
        return

    guess = msg.text.lower().strip()
    correct = active_drops[chat.id]
    if guess == correct:
        user = ensure_user_exists(msg.from_user)
        del active_drops[chat.id]

        rarity = random.choice(["Common"] * 50 + ["Rare"] * 30 + ["Epic"] * 15 + ["Legendary"] * 5)
        waifu_data = {"name": correct.title(), "rarity": rarity, "date": datetime.utcnow()}
        users_collection.update_one({"$or": [{"user_id": user['user_id']}, {"_id": user['user_id']}]}, {"$push": {"waifus": waifu_data}})

        await msg.reply_text(
            f"🎉 <b>Collected!</b>\n👤 {get_mention(user)} caught <b>{correct.title()}</b>!\n🌟 <b>Rarity:</b> {rarity}",
            parse_mode=ParseMode.HTML,
        )


__all__ = ["check_drops", "collect_waifu"]
