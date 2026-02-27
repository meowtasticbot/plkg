# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>

from telegram import ChatMember, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import MIN_CLAIM_MEMBERS
from Meowstric.database import groups_collection, users_collection
from Meowstric.utils import ensure_user_exists, format_money


async def open_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Use in groups only.")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        return await update.message.reply_text("Only admins can use this.")

    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"economy_enabled": True}}, upsert=True)
    await update.message.reply_text("Economy and games enabled.")


async def close_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Use in groups only.")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        return await update.message.reply_text("Only admins can use this.")

    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"economy_enabled": False}}, upsert=True)
    await update.message.reply_text("Economy and catverse game disabled.")


async def claim_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Claim in groups only.")

    members_count = await context.bot.get_chat_member_count(chat.id)
    if members_count < MIN_CLAIM_MEMBERS:
        return await update.message.reply_text(f"Need {MIN_CLAIM_MEMBERS} members to claim!")

    group_data = groups_collection.find_one({"chat_id": chat.id}) or {}
    if group_data.get("reward_claimed"):
        return await update.message.reply_text("Reward already claimed here.")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        return await update.message.reply_text("Only admins can claim this.")

    reward = 10000 if members_count < 500 else 25000
    ensure_user_exists(user)
    users_collection.update_one({"$or": [{"user_id": user.id}, {"_id": user.id}]}, {"$inc": {"balance": reward}})
    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"reward_claimed": True}}, upsert=True)

    await update.message.reply_text(f"Reward claimed: {format_money(reward)}", parse_mode=ParseMode.HTML)


async def group_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == ChatType.PRIVATE:
        return
    groups_collection.update_one(
        {"chat_id": update.effective_chat.id},
        {"$set": {"title": update.effective_chat.title, "active": True}, "$inc": {"activity_score": 1}},
        upsert=True,
    )


async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.my_chat_member:
        return
    new, old = update.my_chat_member.new_chat_member, update.my_chat_member.old_chat_member
    chat = update.my_chat_member.chat

    if new.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR] and old.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"title": chat.title, "active": True}}, upsert=True)
    elif new.status in [ChatMember.LEFT, ChatMember.BANNED]:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"active": False}})


__all__ = ["open_economy", "close_economy", "claim_group", "group_tracker", "chat_member_update"]
