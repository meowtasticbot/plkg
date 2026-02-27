from config import BOT_NAME, BOT_TOKEN
from Meowstric.plugins.admin import admin_commands, member_update, plp, welcome_new_member
from Meowstric.plugins.broadcast import gbroadcast, ubroadcast
from Meowstric.plugins.chatbot import chat_handler
from Meowstric.plugins.economy import bal, claim, daily, gift, give, inventory, rob, use
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

 
