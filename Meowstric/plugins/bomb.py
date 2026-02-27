# Copyright (c) 2025 Telegram:- @WTF_Phantom <DevixOP>

import asyncio
import html
import random

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Meowstric.config import OWNER_ID
from Meowstric.database import users_collection
from Meowstric.utils import ensure_user_exists, format_money

GAMES = {}


async def start_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in GAMES:
        return await update.message.reply_text("A game is already running in this group!")
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("Usage: /bomb <amount>")

    entry_fee = int(context.args[0])
    if entry_fee < 100:
        return await update.message.reply_text("Minimum entry fee is 100 coins.")

    user_db = ensure_user_exists(user)
    if user_db.get("balance", 0) < entry_fee:
        return await update.message.reply_text("You don't have enough balance to start!")

    users_collection.update_one({"$or": [{"user_id": user.id}, {"_id": user.id}]}, {"$inc": {"balance": -entry_fee}})
    GAMES[chat_id] = {"fee": entry_fee, "players": [{"id": user.id, "name": user.first_name}], "pot": entry_fee, "status": "joining", "holder_idx": 0}

    await update.message.reply_text(
        f"💣 <b>BOMB GAME STARTED</b>\nHost: {html.escape(user.first_name)}\nEntry Fee: <code>{format_money(entry_fee)}</code>\nTo Join: <code>/join {entry_fee}</code>",
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(60)
    await run_game(update, context, chat_id)


async def join_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in GAMES or GAMES[chat_id]["status"] != "joining":
        return await update.message.reply_text("No active joining phase found.")

    game = GAMES[chat_id]
    if any(p["id"] == user.id for p in game["players"]):
        return await update.message.reply_text("You already joined!")
    if not context.args or not context.args[0].isdigit() or int(context.args[0]) != game["fee"]:
        return await update.message.reply_text(f"Usage: /join {game['fee']}")

    user_db = ensure_user_exists(user)
    if user_db.get("balance", 0) < game["fee"]:
        return await update.message.reply_text("Low balance!")

    users_collection.update_one({"$or": [{"user_id": user.id}, {"_id": user.id}]}, {"$inc": {"balance": -game['fee']}})
    game["players"].append({"id": user.id, "name": user.first_name})
    game["pot"] += game["fee"]
    await update.message.reply_text(f"{html.escape(user.first_name)} joined! Pot: {format_money(game['pot'])}")


async def pass_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in GAMES or GAMES[chat_id]["status"] != "running":
        return
    game = GAMES[chat_id]
    if user.id != game["players"][game["holder_idx"]]["id"]:
        return await update.message.reply_text("You don't have the bomb!")
    game["holder_idx"] = (game["holder_idx"] + 1) % len(game["players"])
    new_holder = game["players"][game["holder_idx"]]
    await update.message.reply_text(f"{html.escape(user.first_name)} passed to {html.escape(new_holder['name'])}!")


async def run_game(update, context, chat_id):
    game = GAMES.get(chat_id)
    if not game:
        return
    if len(game["players"]) < 2:
        for p in game["players"]:
            users_collection.update_one({"$or": [{"user_id": p['id']}, {"_id": p['id']}]}, {"$inc": {"balance": game['fee']}})
        del GAMES[chat_id]
        return await update.effective_chat.send_message("Not enough players. Fees refunded.")

    game["status"] = "running"
    await update.effective_chat.send_message(f"Game started! {len(game['players'])} players.")
    while len(game["players"]) > 1:
        holder = game["players"][game["holder_idx"]]
        await update.effective_chat.send_message(f"💣 {html.escape(holder['name'])} has the bomb! Use /pass")
        await asyncio.sleep(random.randint(5, 10))
        exploded = game["players"].pop(game["holder_idx"])
        await update.effective_chat.send_message(f"💥 BOOM on {html.escape(exploded['name'])}!")
        if len(game["players"]) > 0:
            game["holder_idx"] %= len(game["players"])

    winner = game["players"][0]
    users_collection.update_one({"$or": [{"user_id": winner['id']}, {"_id": winner['id']}]}, {"$inc": {"balance": game['pot'], "bomb_wins": 1}})
    await update.effective_chat.send_message(f"🏆 WINNER {html.escape(winner['name'])}! Won {format_money(game['pot'])}")
    del GAMES[chat_id]


async def bomb_leaders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = users_collection.find({"bomb_wins": {"$gt": 0}}).sort("bomb_wins", -1).limit(10)
    msg = "💣 <b>BOMB GAME RANKINGS</b>\n"
    for i, u in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        msg += f"{medal} <b>{i}.</b> {html.escape(u.get('name', 'User'))} — <code>{u.get('bomb_wins', 0)} Wins</code>\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def bomb_myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    u = ensure_user_exists(target)
    wins = u.get("bomb_wins", 0)
    rank = users_collection.count_documents({"bomb_wins": {"$gt": wins}}) + 1
    await update.message.reply_text(f"💣 <b>{html.escape(target.first_name)} Stats</b>\n🏆 Wins: <code>{wins}</code>\n📊 Rank: <code>#{rank}</code>", parse_mode=ParseMode.HTML)


async def bomb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    chat_id = update.effective_chat.id
    if chat_id in GAMES:
        for p in GAMES[chat_id]["players"]:
            users_collection.update_one({"$or": [{"user_id": p['id']}, {"_id": p['id']}]}, {"$inc": {"balance": GAMES[chat_id]['fee']}})
        del GAMES[chat_id]
        await update.message.reply_text("Game cancelled, fees refunded.")


__all__ = ["start_bomb", "join_bomb", "pass_bomb", "bomb_leaders", "bomb_myrank", "bomb_cancel"]
