import os
import random
import time
from datetime import datetime, timedelta

from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["catverse"]
cats = db["cats"]
global_state = db["global"]

# ================= LEVELS =================
LEVELS = [
    ("🐱 Kitten", 0),
    ("😺 Teen", 30),
    ("😼 Rogue", 60),
    ("🐯 Alpha", 100),
    ("👑 Legend", 160),
]

# ================= HELPERS =================
def get_cat(user):
    cat = cats.find_one({"_id": user.id})
    if not cat:
        cat = {
            "_id": user.id,
            "name": user.first_name,
            "coins": 500,
            "fish": 2,
            "xp": 0,
            "kills": 0,
            "premium": False,
            "inventory": {"fish_bait": 0, "shield": 0},
            "dna": {"aggression": 1, "intelligence": 1, "luck": 1, "charm": 1},
            "level": "🐱 Kitten",
            "last_msg": 0,
            "protected_until": None,
            "last_daily": None,
            "created": datetime.utcnow()
        }
        cats.insert_one(cat)
    return cat


def evolve(cat):
    total = sum(cat["dna"].values())
    for name, req in reversed(LEVELS):
        if total >= req:
            cat["level"] = name
            break


def dark_night_active():
    state = global_state.find_one({"_id": "dark"})
    return state and state["until"] > datetime.utcnow()


def calculate_global_rank(user_id):
    all_cats = list(cats.find().sort("coins", -1))
    for idx, c in enumerate(all_cats, 1):
        if c["_id"] == user_id:
            return idx
    return 0


# ================= CHAT GAME LOOP =================
async def on_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    cat = get_cat(user)

    now = time.time()
    if now - cat["last_msg"] < 4:
        return

    cat["last_msg"] = now
    cat["xp"] += random.randint(1, 3)
    stat = random.choice(list(cat["dna"]))
    cat["dna"][stat] += 1

    old_level = cat["level"]
    evolve(cat)

    if old_level != cat["level"]:
        await update.message.reply_text(f"✨ EVOLVED! You are now {cat['level']} 😼")

    # Fish event
    if random.random() < 0.05:
        context.chat_data["fish_event"] = True
        await update.message.reply_text("🐟 A glowing fish appeared!\nType: eat | save | share")

    # Dark night
    if random.random() < 0.01 and not dark_night_active():
        global_state.update_one(
            {"_id": "dark"},
            {"$set": {"until": datetime.utcnow() + timedelta(minutes=5)}},
            upsert=True
        )
        await update.message.reply_text("🌑 DARK NIGHT HAS FALLEN! Rare boosts active 👑")

    cats.update_one({"_id": user.id}, {"$set": cat})


# ================= FISH ACTION =================
async def fish_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.chat_data.get("fish_event"):
        return

    cat = get_cat(update.effective_user)
    text = update.message.text.lower()

    if "eat" in text:
        cat["fish"] += 2
        cat["dna"]["aggression"] += 1
        msg = "😻 You ate the fish. Power up!"
    elif "save" in text:
        cat["dna"]["intelligence"] += 2
        msg = "🧠 Smart choice. Brain boosted."
    elif "share" in text:
        cat["dna"]["charm"] += 2
        msg = "💖 Shared fish. Charm increased."
    else:
        return

    evolve(cat)
    context.chat_data.pop("fish_event")
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})
    await update.message.reply_text(msg)


# ================= INVENTORY =================
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)
    inv = cat["inventory"]
    await update.message.reply_text(
        f"🎒 Inventory\n"
        f"🐟 Fish Bait: {inv['fish_bait']}\n"
        f"🛡 Shields: {inv['shield']}"
    )


# ================= SHOP =================
SHOP_ITEMS = {
    "fish_bait": {"price": 300, "name": "🐟 Fish Bait"},
    "shield": {"price": 800, "name": "🛡 Shield (Auto Protect)"},
}

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛒 Cat Shop\n"
    buttons = []

    for key, item in SHOP_ITEMS.items():
        text += f"{item['name']} — ${item['price']}\n"
        buttons.append([InlineKeyboardButton(f"Buy {item['name']}", callback_data=f"buy_{key}")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_key = query.data.split("_")[1]
    cat = get_cat(query.from_user)
    item = SHOP_ITEMS[item_key]

    if cat["coins"] < item["price"]:
        return await query.edit_message_text("❌ Not enough coins.")

    cat["coins"] -= item["price"]
    cat["inventory"][item_key] += 1
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

    await query.edit_message_text(f"✅ Purchased {item['name']}!")


# ================= LEADERBOARD BUTTONS =================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("💰 Richest Cats", callback_data="lb_rich")],
        [InlineKeyboardButton("💀 Top Killers", callback_data="lb_kill")],
    ]
    await update.message.reply_text("🏆 Leaderboards", reply_markup=InlineKeyboardMarkup(buttons))


async def leaderboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lb_rich":
        top = cats.find().sort("coins", -1).limit(10)
        text = "💰 Top Rich Cats\n"
        for i, c in enumerate(top, 1):
            text += f"{i}. {c['name']} — {c['coins']}\n"
    else:
        top = cats.find().sort("kills", -1).limit(10)
        text = "💀 Top Killer Cats\n"
        for i, c in enumerate(top, 1):
            text += f"{i}. {c['name']} — {c['kills']} kills\n"

    await query.edit_message_text(text)


# ================= GAME GUIDE =================
GAME_TEXT = (
    "🐱 **CATVERSE GUIDE**\n\n"
    "• Game always ON, just chat!\n"
    "• Fish events = eat | save | share\n"
    "• /me — view your cat stats & ranking\n"
    "• Reply + /kill — attack another cat\n"
    "• /toprich — top rich cats\n"
    "• /topkill — top killer cats\n"
    "• /give — gift coins\n"
    "• /rob — rob coins\n"
    "• /protect — buy 1 day protection\n"
    "• /shop — buy items\n"
    "• /inventory — view items\n"
    "• /leaderboard — rankings with buttons\n"
    "• Dark Night 🌑 = rare power boost\n\n"
    "Enjoy your cat life! 😼"
)

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GAME_TEXT, parse_mode="Markdown")

async def game_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await games(update, context)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("game", game_alias))
    app.add_handler(CommandHandler("games", games))
    app.add_handler(CommandHandler("inventory", inventory))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    app.add_handler(CallbackQueryHandler(buy_item, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(leaderboard_buttons, pattern="^lb_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fish_action))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_chat))

    print("🐱 CatVerse Ultimate Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
