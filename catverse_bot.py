import random
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import *
from database import *
from utils import *


LEVELS = [
    ("🐱 Kitten", 0),
    ("😺 Teen", 1200),
    ("😼 Rogue", 3500),
    ("🐯 Alpha", 7000),
    ("👑 Legend", 14000),
]

UPGRADE_COSTS = {
    "aggression": 120,
    "intelligence": 120,
    "luck": 120,
    "charm": 120,
}

SHOP_ITEMS = {
    "shield": {"price": 500, "desc": "Blocks robbery/attacks once."},
    "shield_breaker": {"price": 700, "desc": "Breaks target shield during rob."},
    "luck_boost": {"price": 450, "desc": "Boosted luck on next robbery."},
    "bail_pass": {"price": 350, "desc": "Auto-used when jailed in events."},
    "fish_bait": {"price": 250, "desc": "Improves fish rewards and rare chance."},
    "vip_shield": {"price": 2000, "desc": "Consumes to block one robbery/attack."},
}

GIFT_ITEMS = {
    "rose": {"price": 180, "emoji": "🌹"},
    "chocolate": {"price": 260, "emoji": "🍫"},
    "kiss": {"price": 420, "emoji": "💋"},
    "ring": {"price": 1200, "emoji": "💍"},
}


def evolve(cat: dict) -> dict:
    xp = int(cat.get("xp", 0))
    level_name = LEVELS[0][0]
    for name, required_xp in LEVELS:
        if xp >= required_xp:
            level_name = name
    cat["level"] = level_name
    return cat


def _new_cat(user) -> dict:
    now = datetime.utcnow()
    return {
        "_id": user.id,
        "user_id": user.id,
        "name": user.first_name,
        "coins": 1000,
        "xp": 0,
        "level": LEVELS[0][0],
        "fish": 0,
        "kills": 0,
        "deaths": 0,
        "health": 100,
        "inventory": {},
        "dna": {"aggression": 0, "intelligence": 0, "luck": 0, "charm": 0},
        "created": now,
        "last_daily": None,
        "last_claim": None,
        "protected_until": None,
    }


def get_cat(user):
    cat = cats.find_one({"_id": user.id})
    if not cat:
        cat = _new_cat(user)
        cats.insert_one(cat)

    # backfill missing keys for old docs
    changed = False
    defaults = _new_cat(user)
    for key, value in defaults.items():
        if key not in cat:
            cat[key] = value
            changed = True
    if changed:
        cats.update_one({"_id": user.id}, {"$set": cat})

    return cat


def is_protected(cat: dict) -> bool:
    until = cat.get("protected_until")
    if not until:
        return False
    if getattr(until, "tzinfo", None) is None:
        until = until.replace(tzinfo=timezone.utc)
    return until > datetime.now(timezone.utc)


def calculate_global_rank(user_id: int) -> int:
    cursor = cats.find({}, {"_id": 1, "coins": 1}).sort("coins", -1)
    for idx, row in enumerate(cursor, start=1):
        if row.get("_id") == user_id:
            return idx
    return 0


from Meowstric.plugins.admin import admin_commands, plp, welcome_new_member, welcome_new_members_message
from Meowstric.plugins.broadcast import gbroadcast, ubroadcast
from Meowstric.plugins.ping import ping, ping_callback
from Meowstric.plugins.chatbot import chat_handler, tidal_sticker_reply
from Meowstric.plugins.economy import bal, claim, daily, gift, give, inventory, rob, use
from Meowstric.plugins.events import (
    chat_member_update as member_update,
    close_economy,
    economy_switch,
    open_economy,
)
from Meowstric.plugins.game import (
    fish,
    fishlb,
    fun,
    games,
    kill,
    leaderboard_callback,
    lobu,
    moon_mere_papa,
    protect,
    topkill,
    toprich,
    upgrade,
)
from Meowstric.plugins.profile import meow, xp
from Meowstric.plugins.shop import shop, shop_system
from Meowstric.plugins.start import start_callback, start_handler
from Meowstric.plugins.stats import stats_cmd
from Meowstric.plugins.waifu import SFW_ACTIONS, waifu_action, waifu_cmd, wmarry, wpropose


async def button_handler(update, context):
    """Fallback callback router for generic callback queries."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    if data in {"return_start", "talk_baka", "game_features"}:
        await start_callback(update, context)
        return

    await query.answer()
