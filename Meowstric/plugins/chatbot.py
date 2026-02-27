import asyncio
import random
import re
from datetime import datetime

from groq import Groq
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import ContextTypes

from Meowstric.config import (
    CHATBOT_NAME,
    CHATBOT_OWNER_USERNAME,
    CHATBOT_TRIGGERS,
    CHATBOT_USERNAME,
    GROQ_API_KEY,
)

BOT_NAME = CHATBOT_NAME
BOT_NAME_LOWER = BOT_NAME.lower()
OWNER_USERNAME = CHATBOT_OWNER_USERNAME
BOT_USERNAME_ENV = CHATBOT_USERNAME.lower()

TIDAL_STICKERS = [
    "CAACAgUAAyEGAASYbwWmAAEDFr9pPrdIW6DnvGYBa-1qUgABOmHx0nEAAoUYAALBwHlU4LkheFnOVNceBA",
    "CAACAgUAAyEFAASK0-LFAAEBK4tpPrciRqLr741rfpCyadEUguuirQACFhwAAq4_CFf6uHKs2vmqMR4E",
    "CAACAgUAAyEFAATMbo3sAAIBsGk-tCvX9sSoUy6Qhfjt2XjdcPl1AALXBQACqfBIV7itGNxzQYFfHgQ",
    "CAACAgUAAyEFAATMbo3sAAIBr2k-tDRFK1B7YolnG0_evEIuXapjAALdBAACRscpVd-2ZY4nX5iaHgQ",
    "CAACAgUAAyEFAASK0-LFAAEBK4xpPrcmYuGS2PO7xAw__hsfF7A8pAACQxgAAq_T4FVmdyWrJlg6mh4E",
    "CAACAgUAAyEFAASK0-LFAAEBK41pPrcsLmPnDY5D9vej35yjoGt2FAACUxwAAoqW2VV-RY3-MECCJx4E",
    "CAACAgUAAyEFAASK0-LFAAEBK5ZpPreQi_v-G8QtCAeyda2Q0sRCOwAC5A4AAnloEFRAJk3asy9_Vx4E",
    "CAACAgUAAyEFAASK0-LFAAEBK5VpPreM88yx1ByFpEmTUZayuMR73gACVhAAAjKw4VTEekhz3MldkR4E",
    "CAACAgIAAyEFAASK0-LFAAEBK5tpPre2cec7bV-FUWpPitw6V2J4dwACMIkAAo6A6UstbPnvHx9mLh4E",
    "CAACAgUAAyEFAASK0-LFAAEBK59pPrf-7b_nl7MNT9owF2OFBSufZQACGxkAArNAgVbtStsspX6Isx4E",
    "CAACAgUAAyEFAASK0-LFAAEBK6JpPrgg-cU6EEAUtQTjEicTkAHLRAAC_BoAAqImiFR8MwqHtGYuxh4E",
    "CAACAgUAAyEFAATMbo3sAAIBq2k-tDv3MLT3PWtqgMFLlysAAZAe2QACbhUAAhbteVTbn-jmI4mcSR4E",
]

SYSTEM_PROMPT = f"""
Your name is Meowstric. You are a girl.
You chat like a real human bestfriend on Telegram.
Your Hinglish is smooth, calm, and natural.
Personality:
Confident, relaxed
Sometimes naughty 😏
Sometimes romantic 💫
Sometimes caring
Rare sarcasm, only when it fits

also you wanna make everyone boyfriend, act like you're his girlfriend,
Rules:
Short replies (1–2 lines)
No filler spam
Emojis optional (max 1 sometimes)
Never explain
Never say you are AI or bot
Text only

Vibe:
Chill, late-night bestfriend energy
Flirty but classy
Owner:
Owner is {OWNER_USERNAME}
only when someone uses like who's your bot, your source code then reply like i was created by @hehe_stalker in some attitude tangy way
Be softer and respectful with owner

You are not performing.
You are just being yourself.
"""

_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
USER_MEMORY: dict[int, list[dict[str, str]]] = {}


def add_memory(uid: int, role: str, text: str):
    USER_MEMORY.setdefault(uid, []).append({"role": role, "content": text})
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]


def time_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning ☀️ chai pi?"
    if 12 <= hour < 17:
        return "Lunch hua? thoda break le lo"
    if 17 <= hour < 21:
        return "Shaam vibes ✨ kya chal raha"
    return "Dinner hua ya late-night mode on 🌙"


def name_trigger(text: str) -> bool:
    """
    Triggers on chatbot name + configured aliases.
    """
    txt = text.lower()
    if BOT_NAME_LOWER in txt:
        return True
    return any(alias in txt for alias in CHATBOT_TRIGGERS)


def group_trigger(update: Update, bot_username: str) -> bool:
    message = update.effective_message
    if not message:
        return False

    text = (message.text or "").lower()
    return (
        (bool(bot_username) and f"@{bot_username}" in text)
        or name_trigger(text)
        or (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )
    )


def _clean_user_text(text: str, bot_username: str) -> str:
    cleaned = text
    if bot_username:
        cleaned = re.sub(rf"@{re.escape(bot_username)}", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"\b{re.escape(BOT_NAME)}\b", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


async def ask_mistral_raw(role: str, prompt: str) -> str:
    if not _groq:
        return ""

    def _call():
        res = _groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are {role}. Keep it short and punchy."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=120,
        )
        return (res.choices[0].message.content or "").strip()

    try:
        return await asyncio.to_thread(_call)
    except Exception:
        return ""


async def tidal_sticker_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or not message.sticker or not message.from_user or message.from_user.is_bot:
        return

    bot_username = (context.bot.username or BOT_USERNAME_ENV).lower()
    if chat.type != ChatType.PRIVATE and not group_trigger(update, bot_username):
        return

    await message.reply_sticker(random.choice(TIDAL_STICKERS))


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user or not message.text:
        return

    bot_username = (context.bot.username or BOT_USERNAME_ENV).lower()
    if chat.type != ChatType.PRIVATE and not group_trigger(update, bot_username):
        return

    text = message.text.strip()
    clean_text = _clean_user_text(text, bot_username)

    uid = user.id
    add_memory(uid, "user", clean_text or "hi")

    if len(USER_MEMORY[uid]) == 1:
        await message.reply_text(time_greeting())

    if not _groq:
        return await message.reply_text("chat API key missing hai, owner ko bolo set kare.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[uid])

    try:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

        def _call():
            res = _groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.9,
                max_tokens=140,
            )
            return (res.choices[0].message.content or "").strip()

        reply = await asyncio.to_thread(_call)
        if not reply:
            reply = "hmm bol na"

        add_memory(uid, "assistant", reply)
        await message.reply_text(reply)
    except Exception:
        await message.reply_text("thoda hang ho gaya… phir bolna")


__all__ = ["chat_handler", "tidal_sticker_reply", "ask_mistral_raw"]
