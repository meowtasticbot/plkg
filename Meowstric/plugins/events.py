# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>

from telegram import ChatMember, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import MIN_CLAIM_MEMBERS
from Meowstric.database import groups_collection, users_collection
from Meowstric.utils import ensure_user_exists, format_money, log_to_channel


async def open_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Use in groups only.")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        return await update.message.reply_text("Only admins can use this.")

    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"economy_enabled": True}}, upsert=True)
    await log_to_channel(
        context.bot,
        "economy_opened",
        {
            "chat": f"{chat.title} ({chat.id})",
            "by": f"{user.first_name} ({user.id})",
        },
    )
    await update.message.reply_text("Economy and games enabled.")


async def close_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Use in groups only.")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        return await update.message.reply_text("Only admins can use this.")

    groups_collection.update_one({"chat_id": chat.id}, {"$set": {"economy_enabled": False}}, upsert=True)
    await log_to_channel(
        context.bot,
        "economy_closed",
        {
            "chat": f"{chat.title} ({chat.id})",
            "by": f"{user.first_name} ({user.id})",
        },
    )
    await update.message.reply_text("Economy and games disabled.")


async def claim_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, user = update.effective_chat, update.effective_user
    if chat.type == ChatType.PRIVATE:
        return await update.message.reply_text("Use this in group only.")

    members_count = await chat.get_member_count()
    if members_count < MIN_CLAIM_MEMBERS:
        return await update.message.reply_text(
            f"Need at least {MIN_CLAIM_MEMBERS} members to claim reward.\nCurrent: {members_count}"
        )

    group = groups_collection.find_one({"chat_id": chat.id}) or {}
    if group.get("reward_claimed"):
        return await update.message.reply_text("This group reward is already claimed.")

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

    joined_statuses = [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]
    left_statuses = [ChatMember.LEFT, ChatMember.BANNED]

    if new.status in joined_statuses and old.status in left_statuses:
        await context.bot.send_message(
            chat_id=chat.id,
            text="😺 Thanks for adding me! I'm online and ready to help.\nUse /start to begin.",
        )
        await log_to_channel(
            context.bot,
            "bot_added",
            {
                "chat": f"{chat.title} ({chat.id})",
                "status": new.status,
            },
        )
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"title": chat.title, "active": True}}, upsert=True)
    elif new.status in left_statuses and old.status not in left_statuses:
        groups_collection.update_one({"chat_id": chat.id}, {"$set": {"active": False}}, upsert=True)
        await log_to_channel(
            context.bot,
            "bot_removed",
            {
                "chat": f"{chat.title} ({chat.id})",
                "status": new.status,
            },
        )


__all__ = ["open_economy", "close_economy", "claim_group", "group_tracker", "chat_member_update"]
