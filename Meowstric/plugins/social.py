import asyncio
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import DIVORCE_COST
from Meowstric.database import users_collection
from Meowstric.plugins.chatbot import ask_mistral_raw
from Meowstric.utils import ensure_user_exists, format_money, get_mention, resolve_target


def get_progress_bar(percent):
    filled = int(percent / 10)
    return "█" * filled + "▒" * (10 - filled)


def get_love_comment(percent):
    if percent < 30:
        return "💔 Terrible!"
    if percent < 80:
        return "💖 Cute!"
    return "🔥 Soulmates!"


def get_random_message(love_percentage):
    if love_percentage <= 30:
        return random.choice([
            "Love is in the air but needs a little spark.",
            "A good start but there's room to grow.",
            "It's just the beginning of something beautiful.",
        ])
    if love_percentage <= 70:
        return random.choice([
            "A strong connection is there. Keep nurturing it.",
            "You've got a good chance. Work on it.",
            "Love is blossoming, keep going.",
        ])
    return random.choice([
        "Wow! It's a match made in heaven!",
        "Perfect match! Cherish this bond.",
        "Destined to be together. Congratulations!",
    ])


async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if len(args) < 2:
        parts = (update.message.text or "").split()
        args = parts[1:] if len(parts) > 1 else []
    if len(args) < 2:
        return await update.message.reply_text("Please enter two names after /love command.")

    name1 = args[0].strip()
    name2 = args[1].strip()
    love_percentage = random.randint(10, 100)
    love_message = get_random_message(love_percentage)

    response = f"{name1}💕 + {name2}💕 = {love_percentage}%\n\n{love_message}"
    await update.message.reply_text(response)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡️ <b>Admin Commands (. or / both)</b>\n"
        "<code>.warn [reply]</code> - Warn a user (3 = ban)\n"
        "<code>.unwarn [reply]</code> - Remove 1 warning\n"
        "<code>.mute [reply]/[user id] [time]</code> - Mute temporarily/permanently\n"
        "<code>.unmute [reply]/[user id]</code> - Unmute the user\n"
        "<code>.ban [reply]/[user id]</code> - Ban user\n"
        "<code>.unban [reply]/[user id]</code> - Unban user\n"
        "<code>.kick [reply]/[user id]</code> - Kick from group\n"
        "<code>.promote [reply]/[user id] 1/2/3</code> - Promote user to admin\n"
        "<code>.demote [reply]/[user id]</code> - Demote admin\n"
        "<code>.title [reply]/[user id] [tag]</code> - Set custom title\n"
        "<code>.pin [reply]</code> - Pin a message\n"
        "<code>.unpin</code> - Unpin the current message\n"
        "<code>.d</code> - Delete a message\n"
        "<code>.help</code> - Show this help\n\n"
        "💘 <b>Fun</b>\n"
        "<code>/love name1 name2</code> - Love calculator\n"
        "<code>/hug /bite /slap /punch /kiss /truth /dare</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def couple_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("❌ Group Only!", parse_mode=ParseMode.HTML)

    user1 = ensure_user_exists(user)
    target, _ = await resolve_target(update, context)
    if target:
        user2 = target
    else:
        pipeline = [{"$match": {"seen_groups": chat.id, "user_id": {"$ne": user.id}}}, {"$sample": {"size": 1}}]
        results = list(users_collection.aggregate(pipeline))
        if not results:
            return await update.message.reply_text("😔 Forever Alone.", parse_mode=ParseMode.HTML)
        user2 = results[0]

    percent = random.randint(0, 100)
    text = (
        "💘 <b>Couple Matcher</b>\n\n"
        f"🔻 {get_mention(user1)}\n"
        f"🔺 {get_mention(user2)}\n\n"
        f"💟 <b>Score:</b> {percent}%\n"
        f"<code>{get_progress_bar(percent)}</code>\n"
        f"💭 <i>{get_love_comment(percent)}</i>"
async def proposal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action, p_id, t_id = query.data.split("|")
    p_id, t_id = int(p_id), int(t_id)

    if query.from_user.id != t_id:
        return await query.answer("❌ Not for you!", show_alert=True)

    if action == "marry_y":
        users_collection.update_one({"$or": [{"user_id": p_id}, {"_id": p_id}]}, {"$set": {"partner_id": t_id}}, upsert=True)
        users_collection.update_one({"$or": [{"user_id": t_id}, {"_id": t_id}]}, {"$set": {"partner_id": p_id}}, upsert=True)
        await query.message.edit_text(
            "💍 <b>Just Married!</b>\n"
            f"<a href='tg://user?id={p_id}'>P1</a> ❤️ <a href='tg://user?id={t_id}'>P2</a>\n"
            f"✨ 5% Tax Perk Active!",
            parse_mode=ParseMode.HTML,
        )
    elif action == "marry_n":
        roast = await ask_mistral_raw("Roaster", "Roast a rejected proposal.")
        await query.message.edit_text(
            f"❌ <b>Rejected!</b>\n🔥 {roast or 'Ouch.'}",
            parse_mode=ParseMode.HTML,
        )

    await query.answer()



__all__ = [
    "couple_game",
    "propose",
    "marry_status",
    "divorce",
    "proposal_callback",
    "love_command",
    "help_command",
]
