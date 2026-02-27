from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ChatMemberHandler, CommandHandler, MessageHandler, filters

from Meowstric.config import CHATBOT_BOT_TOKEN
from Meowstric.plugins.admin import addsudo, admin_commands, cleandb, member_update, plp, rmsudo, sudo_help, sudolist, welcome_new_member
from Meowstric.plugins.broadcast import broadcast, gbroadcast, ubroadcast
from Meowstric.plugins.stats import stats_cmd
from Meowstric.plugins.economy import bal, claim, daily, gift, give, rob, use
from Meowstric.plugins.game import fish, fishlb, fun, games, kill, lobu, moon_mere_papa, protect, topkill, toprich, upgrade
from Meowstric.plugins.profile import meow, xp
from Meowstric.plugins.shop import inventory, shop, shop_system
from Meowstric.plugins.chatbot import ask_ai, chat_handler
from Meowstric.plugins.start import help_command, start_callback, start_handler
from Meowstric.plugins.welcome import new_member, welcome_command
from Meowstric.plugins.social import couple_game, divorce, marry_status, proposal_callback, propose
from Meowstric.plugins.ping import ping, ping_callback
from Meowstric.plugins.events import chat_member_update, claim_group, close_economy, group_tracker, open_economy
from Meowstric.plugins.waifu import SFW_ACTIONS, waifu_action, waifu_cmd, wmarry, wpropose
from Meowstric.plugins.collection import check_drops, collect_waifu
from Meowstric.plugins.bomb import bomb_cancel, bomb_leaders, bomb_myrank, join_bomb, pass_bomb, start_bomb
from Meowstric.utils import is_catverse_enabled
from Meowstric.plugins.game import leaderboard_callback


def guard(handler):
    async def wrapped(update, context):
        if not is_catverse_enabled(update.effective_chat):
            if update.message:
                await update.message.reply_text("Catverse game is OFF in this group. Use /openeco to enable.")
            return
        return await handler(update, context)
    return wrapped


def main():
    app = ApplicationBuilder().token(CHATBOT_BOT_TOKEN).build()

    app.add_handler(CommandHandler("games", guard(games)))
    app.add_handler(CommandHandler("xp", guard(xp)))
    app.add_handler(CommandHandler("meow", guard(meow)))
    app.add_handler(CommandHandler("lobu", guard(lobu)))
    app.add_handler(CommandHandler("daily", guard(daily)))
    app.add_handler(CommandHandler("claim", guard(claim)))
    app.add_handler(CommandHandler("bal", guard(bal)))
    app.add_handler(CommandHandler("give", guard(give)))
    app.add_handler(CommandHandler("gift", guard(gift)))
    app.add_handler(CommandHandler("use", guard(use)))
    app.add_handler(CallbackQueryHandler(shop_system, pattern="shop|giftshop"))
    app.add_handler(CommandHandler("rob", guard(rob)))
    app.add_handler(CommandHandler("fish", guard(fish)))
    app.add_handler(CommandHandler("moon_mere_papa", guard(moon_mere_papa)))
    app.add_handler(CommandHandler("kill", guard(kill)))
    app.add_handler(CommandHandler("protect", guard(protect)))
    app.add_handler(CommandHandler("toprich", guard(toprich)))
    app.add_handler(CommandHandler("topkill", guard(topkill)))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^lb_"))
    app.add_handler(CommandHandler("shop", guard(shop)))
    app.add_handler(CommandHandler("inventory", guard(inventory)))
    app.add_handler(CallbackQueryHandler(shop_system, pattern="^shop:"))
    app.add_handler(CommandHandler("fun", guard(fun)))
    app.add_handler(CommandHandler("upgrade", guard(upgrade)))
    app.add_handler(CommandHandler("fishlb", guard(fishlb)))
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("ask", ask_ai))
    app.add_handler(CommandHandler("welcome", welcome_command))
    app.add_handler(CommandHandler("openeco", open_economy))
    app.add_handler(CommandHandler("closeeco", close_economy))
    app.add_handler(CommandHandler("claimgroup", claim_group))
    app.add_handler(CommandHandler("waifu", guard(waifu_cmd)))
    app.add_handler(CommandHandler("wpropose", guard(wpropose)))
    app.add_handler(CommandHandler("wmarry", guard(wmarry)))
    app.add_handler(CommandHandler("bomb", guard(start_bomb)))
    app.add_handler(CommandHandler("join", guard(join_bomb)))
    app.add_handler(CommandHandler("pass", guard(pass_bomb)))
    app.add_handler(CommandHandler("bleaders", guard(bomb_leaders)))
    app.add_handler(CommandHandler("bmyrank", guard(bomb_myrank)))
    app.add_handler(CommandHandler("bcancel", bomb_cancel))
    for action in SFW_ACTIONS:
        app.add_handler(CommandHandler(action, guard(waifu_action)))
    app.add_handler(CommandHandler("sudopanel", sudo_help))
    app.add_handler(CommandHandler("sudolist", sudolist))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("rmsudo", rmsudo))
    app.add_handler(CommandHandler("cleandb", cleandb))
    app.add_handler(CommandHandler("couple", guard(couple_game)))
    app.add_handler(CommandHandler("propose", guard(propose)))
    app.add_handler(CommandHandler("mstatus", guard(marry_status)))
    app.add_handler(CommandHandler("divorce", guard(divorce)))
    app.add_handler(CallbackQueryHandler(proposal_callback, pattern=r"^marry_[yn]\|"))
    app.add_handler(CallbackQueryHandler(start_callback, pattern="^(return_start|talk_baka|game_features)$"))
    app.add_handler(CallbackQueryHandler(ping_callback, pattern="^sys_stats$"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.ALL, group_tracker), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_waifu), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_drops), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler), group=2)
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("plp", plp))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("ubroadcast", ubroadcast))
    app.add_handler(CommandHandler("gbroadcast", gbroadcast))
    app.add_handler(ChatMemberHandler(member_update))
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler(["kick", "ban", "mute", "unmute", "unban"], admin_commands))

    print("🐱 CATVERSE FULLY UPGRADED & RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
