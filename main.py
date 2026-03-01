
# MAIN.PY — CATVERSE BOT (SYNCED MENU + STABLE STARTUP)

import logging

from telegram.constants import ChatType
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

def _economy_enabled_only(handler):
    async def wrapped(update, context):
        chat = update.effective_chat

        if not chat or chat.type == ChatType.PRIVATE:
            return await handler(update, context)

        group = core.groups_collection.find_one({"chat_id": chat.id}) or core.groups_collection.find_one({"_id": chat.id}) or {}
        if not group.get("economy_enabled", True):
            return await update.message.reply_text(
                "🚫 Group economy/games abhi OFF hai.\n"
                "Admin se bolo: /eco on"
            )

        return await handler(update, context)

    return wrapped


# ─── BOT COMMAND MENU (SYNCED WITH HANDLERS) ──────────────────────────────────
async def _notify_startup(application):
    me = await application.bot.get_me()
    try:
        await application.bot.send_message(
            chat_id=core.LOGGER_GROUP_ID,
            text=(
                "🟢 <b>Bot Started</b>\n"
                f"• Name: {me.first_name}\n"
                f"• Username: @{me.username or 'N/A'}\n"
                "• Status: Deploy/startup successful"
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Failed to send startup log message: %s", exc)


async def post_init(application):
    commands = [
        ("start", "✨ Catverse start + quick intro"),
        ("help", "📘 All commands and usage guide"),
        ("games", "🎮 Economy/game commands guide"),
        ("meow", "😺 Your profile card"),
        ("xp", "🧬 Check your XP + DNA"),
        ("bal", "💰 Wallet balance"),
        ("daily", "🎁 Claim daily reward (DM)"),
        ("claim", "🏆 Claim group reward"),
        ("give", "🤝 Gift coins to a user"),
        ("gift", "🎉 Send gift items/coins"),
        ("rob", "🦹 Try to rob someone"),
        ("protect", "🛡️ Protect from robbery"),
        ("kill", "⚔️ Attack a player"),
        ("fish", "🎣 Catch fish (bait boosts rares)"),
        ("use", "🧪 Use an item from inventory"),
        ("shop", "🛒 Open item shop"),
        ("inventory", "🎒 View your inventory"),
        ("upgrade", "⬆️ Upgrade game stats/items"),
        ("toprich", "👑 Richest players leaderboard"),
        ("topkill", "💀 Top killers leaderboard"),
        ("fishlb", "🐟 Fishing leaderboard"),
        ("fun", "🎲 Random fun mini commands"),
        ("hug", "🤗 Hug someone"),
        ("kiss", "😘 Kiss someone"),
        ("waifu", "💞 Waifu profile + relationship menu"),
        ("wpropose", "💍 Propose to your waifu"),
        ("wmarry", "💒 Marry your waifu"),
        ("couple", "💕 Couple system (coming soon)"),
        ("love", "❤️ Love calculator"),
        ("voice", "🔊 Convert text to voice"),
        ("ping", "📡 Bot latency + server stats"),
        ("eco", "🛠️ Open/close group economy"),
        ("stats", "📊 Owner stats panel"),
    ]
    await application.bot.set_my_commands(commands)
    await _notify_startup(application)
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
    app.add_handler(CommandHandler(["open_economy", "openeconomy", "openeco"], core.open_economy))
    app.add_handler(CommandHandler(["close_economy", "closeeconomy", "closeeco"], core.close_economy))
    app.add_handler(CommandHandler("eco", core.economy_switch))

    gated_handlers = [
        ("games", core.games),
        ("xp", core.xp),
        ("meow", core.meow),
        ("lobu", core.lobu),
        ("daily", core.daily),
        ("claim", core.claim),
        ("bal", core.bal),
        ("give", core.give),
        ("gift", core.gift),
        ("use", core.use),
        ("rob", core.rob),
        ("fish", core.fish),
        ("moon_mere_papa", core.moon_mere_papa),
        ("kill", core.kill),
        ("protect", core.protect),
        ("toprich", core.toprich),
        ("topkill", core.topkill),
        ("shop", core.shop),
        ("inventory", core.inventory),
        ("fun", core.fun),
        ("upgrade", core.upgrade),
        ("fishlb", core.fishlb),
    ]
    for name, fn in gated_handlers:
        app.add_handler(CommandHandler(name, _economy_enabled_only(fn)))

    # START / CHAT / CALLBACKS
    app.add_handler(CommandHandler("start", core.start_handler))
    app.add_handler(CommandHandler("help", core.help_command))
    app.add_handler(CommandHandler("love", core.love_command))
    app.add_handler(CommandHandler(["waifu", "wifu"], core.waifu_cmd))
    app.add_handler(CommandHandler("wpropose", core.wpropose))
    app.add_handler(CommandHandler("voice", core.voice_command))
    app.add_handler(CommandHandler("wmarry", core.wmarry))
    app.add_handler(CommandHandler(core.SFW_ACTIONS, core.waifu_action))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, core.chat_handler))
    app.add_handler(CommandHandler("ping", core.ping))
    app.add_handler(MessageHandler(filters.Sticker.ALL, core.tidal_sticker_reply))
    app.add_handler(CallbackQueryHandler(core.shop_system, pattern="shop|giftshop"))
    app.add_handler(CallbackQueryHandler(core.leaderboard_callback, pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(core.shop_system, pattern="^shop:"))
    app.add_handler(CallbackQueryHandler(core.button_handler))

    # GROUP / ADMIN / LOGGER
    app.add_handler(ChatMemberHandler(core.welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, core.welcome_new_members_message))
    app.add_handler(CommandHandler("plp", core.plp))
    app.add_handler(CallbackQueryHandler(core.ping_callback, pattern="^sys_stats$"))
    app.add_handler(CommandHandler("stats", core.stats_cmd))
    app.add_handler(CommandHandler("ubroadcast", core.ubroadcast))
    app.add_handler(CommandHandler("gbroadcast", core.gbroadcast))
    app.add_handler(ChatMemberHandler(core.member_update))
    app.add_handler(CommandHandler(["kick", "ban", "mute", "unmute", "unban", "warn", "unwarn", "promote", "demote", "title", "pin", "unpin", "d"], core.admin_commands))

    # Dot-prefixed command support (.cmd)
    app.add_handler(MessageHandler(filters.Regex(r"^\.(help)(?:\s|$)"), core.help_command))
    app.add_handler(MessageHandler(filters.Regex(r"^\.(love)(?:\s|$)"), core.love_command))
    app.add_handler(MessageHandler(filters.Regex(r"^\.(hug|bite|slap|punch|kiss|truth|dare)(?:\s|$)"), core.waifu_action))
    app.add_handler(MessageHandler(filters.Regex(r"^\.(kick|ban|mute|unmute|unban|warn|unwarn|promote|demote|title|pin|unpin|d)(?:\s|$)"), core.admin_commands))

    print(f"🚀 {core.BOT_NAME} main engine online")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
