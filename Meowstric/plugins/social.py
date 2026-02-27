# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>
# Location: Supaul, Bihar

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
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def propose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = ensure_user_exists(update.effective_user)
    if sender.get("partner_id"):
        return await update.message.reply_text("❌ Married!", parse_mode=ParseMode.HTML)

    target_arg = context.args[0] if context.args else None
    target, error = await resolve_target(update, context, specific_arg=target_arg)
    if not target:
        return await update.message.reply_text(error or "Usage: <code>/propose @user</code>", parse_mode=ParseMode.HTML)
    if target.get("user_id") == sender.get("user_id") or target.get("partner_id"):
        return await update.message.reply_text("💔 Invalid.", parse_mode=ParseMode.HTML)

    s_id, t_id = sender["user_id"], target["user_id"]
    kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("💍 Accept", callback_data=f"marry_y|{s_id}|{t_id}"),
            InlineKeyboardButton("🗑️ Reject", callback_data=f"marry_n|{s_id}|{t_id}"),
        ]]
    )

    msg = await update.message.reply_text(
        "💘 <b>Proposal!</b>\n\n"
        f"👤 {get_mention(sender)} loves {get_mention(target)}!\n"
        f"<i>Will you marry them?</i>\n"
        f"⏳ 30s...",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )

    async def delete_later():
        await asyncio.sleep(30)
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text="❌ Expired.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

    asyncio.create_task(delete_later())


async def marry_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_arg = context.args[0] if context.args else None
    target, _ = await resolve_target(update, context, specific_arg=target_arg)
    user = target if target else ensure_user_exists(update.effective_user)

    pid = user.get("partner_id")
    if pid:
        p = users_collection.find_one({"$or": [{"user_id": pid}, {"_id": pid}]})
        status = f"💍 Married to {get_mention(p) if p else pid}"
    else:
        status = "🦅 Single"

    await update.message.reply_text(
        f"📊 <b>Status:</b>\n👤 {get_mention(user)}\n{status}",
        parse_mode=ParseMode.HTML,
    )


async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user_exists(update.effective_user)
    if not user.get("partner_id"):
        return await update.message.reply_text("🤷‍♂️ Single.", parse_mode=ParseMode.HTML)

    if user.get("balance", 0) < DIVORCE_COST:
        return await update.message.reply_text(
            f"❌ Cost: {format_money(DIVORCE_COST)}", parse_mode=ParseMode.HTML
        )

    pid = user["partner_id"]
    users_collection.update_one(
        {"$or": [{"user_id": user["user_id"]}, {"_id": user["user_id"]}]},
        {"$set": {"partner_id": None}, "$inc": {"balance": -DIVORCE_COST}},
    )
    users_collection.update_one(
        {"$or": [{"user_id": pid}, {"_id": pid}]},
        {"$set": {"partner_id": None}},
    )
    await update.message.reply_text(
        f"💔 <b>Divorced!</b> Paid {format_money(DIVORCE_COST)}.",
        parse_mode=ParseMode.HTML,
    )


async def proposal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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


__all__ = ["couple_game", "propose", "marry_status", "divorce", "proposal_callback"]
