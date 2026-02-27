# Copyright (c) 2026 Telegram:- @WTF_Phantom <DevixOP>
# MAIN.PY — CATVERSE BOT (SYNCED MENU + STABLE STARTUP)

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
)
from telegram.request import HTTPXRequest

import catverse_bot as core

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─── BOT COMMAND MENU (SYNCED WITH HANDLERS) ──────────────────────────────────
async def post_init(application):
    commands = [
        ("start", "Start catverse system"),
        ("bal", "Wallet balance"),
        ("kill", "Attack someone"),
        ("rob", "Steal coins"),
        ("daily", "Claim daily bonus"),
        ("toprich", "Richest players"),
        ("claim", "Claim group reward"),
        ("games", "Game guide"),
        ("xp", "Check XP + DNA"),
        ("shop", "Open item shop"),
        ("inventory", "View inventory"),
        ("fish", "Catch fish"),
        ("stats", "Owner stats panel"),
    ]
    await application.bot.set_my_commands(commands)
    print(f"✅ {core.BOT_NAME} menu synchronized")


# ─── MAIN ENGINE ──────────────────────────────────────────────────────────────
def main():
    if not core.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing in environment")

    request = HTTPXRequest(connection_pool_size=30, read_timeout=40.0)

    app = (
        ApplicationBuilder()
        .token(core.BOT_TOKEN)
        .request(request)
        .post_init(post_init)
        .build()
    )

    # GAME / ECONOMY
    app.add_handler(CommandHandler("games", core.games))
    app.add_handler(CommandHandler("xp", core.xp))
    app.add_handler(CommandHandler("meow", core.meow))
    app.add_handler(CommandHandler("lobu", core.lobu))
    app.add_handler(CommandHandler("daily", core.daily))
    app.add_handler(CommandHandler("claim", core.claim))
    app.add_handler(CommandHandler("bal", core.bal))
    app.add_handler(CommandHandler("give", core.give))
    app.add_handler(CommandHandler("gift", core.gift))
    app.add_handler(CommandHandler("use", core.use))
    app.add_handler(CommandHandler("rob", core.rob))
    app.add_handler(CommandHandler("fish", core.fish))
    app.add_handler(CommandHandler("moon_mere_papa", core.moon_mere_papa))
    app.add_handler(CommandHandler("kill", core.kill))
    app.add_handler(CommandHandler("protect", core.protect))
    app.add_handler(CommandHandler("toprich", core.toprich))
    app.add_handler(CommandHandler("topkill", core.topkill))
    app.add_handler(CommandHandler("shop", core.shop))
    app.add_handler(CommandHandler("inventory", core.inventory))
    app.add_handler(CommandHandler("fun", core.fun))
    app.add_handler(CommandHandler("upgrade", core.upgrade))
    app.add_handler(CommandHandler("fishlb", core.fishlb))

    # START / CHAT / CALLBACKS
    app.add_handler(CommandHandler("start", core.start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, core.chat_handler))
    app.add_handler(CallbackQueryHandler(core.shop_system, pattern="shop|giftshop"))
    app.add_handler(CallbackQueryHandler(core.leaderboard_callback, pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(core.shop_system, pattern="^shop:"))
    app.add_handler(CallbackQueryHandler(core.button_handler))

    # GROUP / ADMIN / LOGGER
    app.add_handler(ChatMemberHandler(core.welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("plp", core.plp))
    app.add_handler(CommandHandler("stats", core.stats_cmd))
    app.add_handler(CommandHandler("ubroadcast", core.ubroadcast))
    app.add_handler(CommandHandler("gbroadcast", core.gbroadcast))
    app.add_handler(ChatMemberHandler(core.member_update))
    app.add_handler(CommandHandler(["kick", "ban", "mute", "unmute", "unban"], core.admin_commands))

    print(f"🚀 {core.BOT_NAME} main engine online")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
