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

 
