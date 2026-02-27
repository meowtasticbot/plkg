# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
# Final BAKA Chatbot - Simple Font - Short Replies

import asyncio
import random

import httpx
from telegram import Update
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import CODESTRAL_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY
from Meowstric.database import chatbot_collection

MODELS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama3-70b-8192",
        "key": GROQ_API_KEY,
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-large-latest",
        "key": MISTRAL_API_KEY,
    },
    "codestral": {
        "url": "https://codestral.mistral.ai/v1/chat/completions",
        "model": "codestral-latest",
        "key": CODESTRAL_API_KEY,
    },
}

STICKER_PACKS = [
    "https://t.me/addstickers/RandomByDarkzenitsu",
    "https://t.me/addstickers/Null_x_sticker_2",
    "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot",
    "https://t.me/addstickers/animation_0_8_Cat",
    "https://t.me/addstickers/vhelw_by_CalsiBot",
    "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
    "https://t.me/addstickers/MySet199",
    "https://t.me/addstickers/Quby741",
    "https://t.me/addstickers/Animalsasthegtjtky_by_fStikBot",
    "https://t.me/addstickers/a6962237343_by_Marin_Roxbot",
    "https://t.me/addstickers/cybercats_stickers",
]


async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        link = random.choice(STICKER_PACKS).replace("https://t.me/addstickers/", "")
        s = await context.bot.get_sticker_set(link)
        if s and s.stickers:
            await update.message.reply_sticker(random.choice(s.stickers).file_id)
    except Exception:
        pass


async def call_model_api(provider, messages, max_tokens):
    conf = MODELS.get(provider)
    if not conf or not conf["key"]:
        return None

    async with httpx.AsyncClient(timeout=25) as client:
        try:
            resp = await client.post(
                conf["url"],
                json={"model": conf["model"], "messages": messages, "max_tokens": max_tokens},
                headers={
                    "Authorization": f"Bearer {conf['key']}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"].get("content", "")
                if isinstance(content, list):
                    return "".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
                return str(content).strip()
        except Exception:
            return None


def pick_default_model() -> str:
    if GROQ_API_KEY:
        return "groq"
    if MISTRAL_API_KEY:
        return "mistral"
    if CODESTRAL_API_KEY:
        return "codestral"
    return "mistral"


async def get_ai_response(chat_id, user_input, user_name, model=None):
    model = model or pick_default_model()
    is_code = any(kw in user_input.lower() for kw in ["code", "python", "fix", "debug"])
    active_model = "codestral" if is_code and CODESTRAL_API_KEY else model
    tokens = 4096 if is_code else 50
    prompt = f"You are MEOWSTRIC CAT AI. Sweet Hinglish girl. Reply in 1 short sentence only. User: {user_name}"

    doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
    history = doc.get("history", [])
    msgs = [{"role": "system", "content": prompt}] + history[-6:] + [{"role": "user", "content": user_input}]

    reply = await call_model_api(active_model, msgs, tokens)
    if not reply and model != "groq" and GROQ_API_KEY:
        reply = await call_model_api("groq", msgs, tokens)
    if not reply and model != "mistral" and MISTRAL_API_KEY:
        reply = await call_model_api("mistral", msgs, tokens)
    if not reply and model != "codestral" and CODESTRAL_API_KEY:
        reply = await call_model_api("codestral", msgs, tokens)

    reply = reply or "Achha ji? 😊"
    chatbot_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "history": (history + [{"role": "user", "content": user_input}, {"role": "assistant", "content": reply}])[-10:]
            }
        },
        upsert=True,
    )
    return reply, is_code


async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    if msg.sticker and (
        update.effective_chat.type == ChatType.PRIVATE
        or (msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id)
    ):
        return await send_ai_sticker(update, context)

    if not msg.text or msg.text.startswith("/"):
        return

    should = (
        update.effective_chat.type == ChatType.PRIVATE
        or (msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id)
        or any(msg.text.lower().startswith(kw) for kw in ["hey", "hi", "meowstric", "meow", "cat", "billi", "kitty"])
    )

    if should:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(0.4)
        res, code = await get_ai_response(update.effective_chat.id, msg.text, msg.from_user.first_name)
        if code:
            await msg.reply_text(res, parse_mode=ParseMode.MARKDOWN)
        else:
            await msg.reply_text(res)
            if random.random() < 0.15:
                await send_ai_sticker(update, context)


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    res, code = await get_ai_response(
        update.effective_chat.id, " ".join(context.args), update.effective_user.first_name
    )
    await update.message.reply_text(res, parse_mode=ParseMode.MARKDOWN if code else None)


async def ask_mistral_raw(role_text: str, user_text: str):
    msgs = [
        {"role": "system", "content": role_text},
        {"role": "user", "content": user_text},
    ]
    return await call_model_api("mistral", msgs, 80)


# compatibility alias
chat_handler = ai_message_handler

__all__ = ["ai_message_handler", "ask_ai", "chat_handler", "get_ai_response", "ask_mistral_raw"]
