from catverse_bot import *

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    # Get current user and group stats
    u = users.count_documents({})
    g = groups.count_documents({})
    members = sum(x.get("members", 0) for x in groups.find())

    await update.message.reply_text(
        f"📊 *Catverse Stats* 😺\n\n"
        f"👤 Users: *{u}*\n"
        f"👥 Groups: *{g}*\n"
        f"🐾 Members: *{members}*",
        parse_mode="Markdown"
    )


__all__ = ["stats_cmd"]
