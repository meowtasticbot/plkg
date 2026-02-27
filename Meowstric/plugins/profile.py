from catverse_bot import *

async def xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)

    # 👑 OWNER GOD MODE XP
    if is_owner_user(update.effective_user.id):
        text = (
            f"👑 *OWNER GOD STATS*\n\n"
            f"Level: 👑 Legend Cat\n"
            f"XP: ∞\n\n"
            f"🧬 DNA Stats:\n"
            f"▫️ Aggression: 100\n"
            f"▫️ Intelligence: 100\n"
            f"▫️ Luck: 100\n"
            f"▫️ Charm: 100\n"
            f"🐟 Fish: ∞"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    # 👤 NORMAL USER
    stats = cat["dna"]
    text = (
        f"📊 *Your Cat Stats*\n"
        f"Level: {cat['level']}\n"
        f"XP: {cat['xp']}\n\n"
        f"🧬 DNA Stats:\n"
        f"▫️ Aggression: {stats['aggression']}\n"
        f"▫️ Intelligence: {stats['intelligence']}\n"
        f"▫️ Luck: {stats['luck']}\n"
        f"▫️ Charm: {stats['charm']}\n"
        f"🐟 Fish: {cat['fish']}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def meow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    cat = get_cat(target_user)

    # 👑 OWNER PROFILE (GOD MODE)
    if is_owner_user(target_user.id):
        # Owner ke liye stats hardcode + infinite coins
        mention = f"<a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>"
        await update.message.reply_text(
            f"👑 {mention} — <b>CATVERSE OWNER</b>\n\n"
            f"<b>🐾 Level:</b> 👑 Legend Cat\n"
            f"<b>💰 Money:</b> ∞\n"
            f"<b>🏆 Rank:</b> #∞\n"
            f"<b>🐟 Fish:</b> ∞\n"
            f"<b>⚔️ Wins:</b> ∞ | <b>💀 Deaths:</b> 0\n\n"
            f"<b>DNA →</b> 😼 100 | 🧠 100 | 🍀 100 | 💖 100\n"
            f"✨ <i>The one who rules Catverse</i>",
            parse_mode="HTML"
        )
        return

    # 🐱 Normal users
    d = cat["dna"]
    rank = calculate_global_rank(cat["_id"])
    mention = f"<a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>"

    # Agar owner ne recently /lobu ya /give se coins diye, wo DB me update ho chuke honge, yahan latest show hoga
    await update.message.reply_text(
        f"🐾 {mention} — \n\n<b>🐾 Level:</b> {cat['level']}\n"
        f"<b>💰 Money:</b> ${cat['coins']}\n"
        f"<b>🏆 Rank:</b> #{rank}\n"
        f"<b>🐟 Fish:</b> {cat['fish']}\n"
        f"<b>⚔️ Wins:</b> {cat['kills']} | <b>💀 Deaths:</b> {cat['deaths']}\n\n"
        f"<b>DNA →</b> 😼 {d['aggression']} | 🧠 {d['intelligence']} | 🍀 {d['luck']} | 💖 {d['charm']}",
        parse_mode="HTML"
    )

__all__ = ["xp", "meow"]
