import asyncio
import io

from gtts import gTTS
from langdetect import detect
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes


def _generate_audio_sync(text: str):
    """Blocking TTS generation function for executor thread."""
    try:
        lang_code = detect(text)
    except Exception:
        lang_code = "en"

    lowered = text.lower()
    if lang_code == "hi" or any(x in lowered for x in ["kaise", "kya", "hai", "nhi", "haan", "bol", "sun"]):
        selected_lang = "hi"
        tld = "co.in"
        voice_name = "Indian Girl"
    elif lang_code == "ja":
        selected_lang = "ja"
        tld = "co.jp"
        voice_name = "Anime Girl"
    else:
        selected_lang = "en"
        tld = "us"
        voice_name = "English Girl"

    audio_fp = io.BytesIO()
    gTTS(text=text, lang=selected_lang, tld=tld, slow=False).write_to_fp(audio_fp)
    audio_fp.seek(0)

    return audio_fp, voice_name


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart non-blocking text-to-speech command."""
    text = " ".join(context.args).strip()

    if not text and update.message.reply_to_message:
        text = (
            update.message.reply_to_message.text
            or update.message.reply_to_message.caption
            or ""
        ).strip()

    if not text:
        return await update.message.reply_text(
            "🗣️ <b>Usage:</b> <code>/voice Hello</code>",
            parse_mode=ParseMode.HTML,
        )

    if len(text) > 500:
        return await update.message.reply_text("❌ Text too long!", parse_mode=ParseMode.HTML)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)

    try:
        loop = asyncio.get_running_loop()
        audio_bio, voice_name = await loop.run_in_executor(None, _generate_audio_sync, text)

        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=audio_bio,
            caption=(
                f"🗣️ <b>Voice:</b> {voice_name}\n"
                f"📝 <i>{text[:50]}{'...' if len(text) > 50 else ''}</i>"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(
            f"❌ <b>Audio Error:</b> <code>{exc}</code>",
            parse_mode=ParseMode.HTML,
        )
