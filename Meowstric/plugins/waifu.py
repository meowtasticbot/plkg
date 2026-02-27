# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>

import random
from datetime import datetime, timedelta

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import WAIFU_PROPOSE_COST
from Meowstric.database import users_collection
from Meowstric.plugins.chatbot import ask_mistral_raw
from Meowstric.utils import ensure_user_exists, format_money, get_mention, resolve_target

API_URL = "https://api.waifu.pics"
SFW_ACTIONS = ["kick", "happy", "wink", "poke", "dance", "cringe", "kill", "waifu", "neko", "shinobu", "bully", "cuddle", "cry", "hug", "awoo", "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive", "handhold", "nom", "bite", "glomp", "slap"]


async def waifu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_URL}/sfw/waifu")
            url = resp.json()["url"]
            await update.message.reply_photo(photo=url, caption="🌸 <b>Your Random Waifu</b>", parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text("Connection error!")


async def waifu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0].replace("/", "").lower()
    if cmd not in SFW_ACTIONS:
        return

    target_db, _ = await resolve_target(update, context)
    user = update.effective_user
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_URL}/sfw/{cmd}")
            url = resp.json()["url"]
    except Exception:
        return

    s_link = get_mention(user)
    t_link = get_mention(target_db) if target_db else "the air"
    caption = f"{s_link} {cmd}s {t_link}!"
    if cmd == "kill":
        caption = f"{s_link} murdered {t_link} 💀"
    if cmd == "kiss":
        caption = f"{s_link} kissed {t_link} 💋"
    await update.message.reply_animation(animation=url, caption=caption, parse_mode=ParseMode.HTML)


async def wpropose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    if user.get("balance", 0) < WAIFU_PROPOSE_COST:
        return await update.message.reply_text(f"Need {format_money(WAIFU_PROPOSE_COST)}.", parse_mode=ParseMode.HTML)

    users_collection.update_one({"$or": [{"user_id": user['user_id']}, {"_id": user['user_id']}]}, {"$inc": {"balance": -WAIFU_PROPOSE_COST}})
    success = random.random() < 0.3
    if success:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.waifu.im/search?tags=waifu")
            img_url = r.json()["images"][0]["url"]
        waifu_data = {"name": "Celestial Queen", "rarity": "Celestial", "date": datetime.utcnow()}
        users_collection.update_one({"$or": [{"user_id": user['user_id']}, {"_id": user['user_id']}]}, {"$push": {"waifus": waifu_data}})
        await update.message.reply_photo(img_url, caption="YES! Married a CELESTIAL WAIFU!", parse_mode=ParseMode.HTML)
    else:
        roast = await ask_mistral_raw("Savage Roaster", "Roast a user rejected by anime girl. Hinglish.")
        fail_gif = "https://media.giphy.com/media/pSpmPXdHQWZrcuJRq3/giphy.gif"
        await update.message.reply_animation(fail_gif, caption=f"REJECTED!\n{roast or 'Ouch!'}", parse_mode=ParseMode.HTML)


async def wmarry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    last = user.get("last_wmarry")
    if last and (datetime.utcnow() - last) < timedelta(hours=2):
        return await update.message.reply_text("Cooldown! Wait 2 hours.", parse_mode=ParseMode.HTML)

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/sfw/waifu")
        url = r.json()["url"]
    waifu_data = {"name": "Random Waifu", "rarity": "Rare", "date": datetime.utcnow()}
    users_collection.update_one({"$or": [{"user_id": user['user_id']}, {"_id": user['user_id']}]}, {"$push": {"waifus": waifu_data}, "$set": {"last_wmarry": datetime.utcnow()}})
    await update.message.reply_photo(url, caption="Married! Added to collection.", parse_mode=ParseMode.HTML)


__all__ = ["waifu_cmd", "waifu_action", "wpropose", "wmarry", "SFW_ACTIONS"]
