from catverse_bot import *

from catverse_bot import (
    ContextTypes,
    ParseMode,
    Update,
    SHOP_ITEMS,
    GIFT_ITEMS,
    cats,
    get_cat,
    is_owner_user,
    is_protected,
)

async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)
    await update.message.reply_text(f"💰 Balance: ${cat['coins']}")

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ❌ OWNER PROTECTION: Agar reply kiya gaya user OWNER hai
    if update.message.reply_to_message and is_owner_user(update.message.reply_to_message.from_user.id):
        await update.message.reply_text(
            "👑 Hold on! This cat is the OWNER of the bot 😼\n"
            "💰 You can't give or take money from them.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if not update.message.reply_to_message or not context.args:
        return await update.message.reply_text("❗ Reply with /give <amount>")

    sender = get_cat(update.effective_user)
    receiver = get_cat(update.message.reply_to_message.from_user)

    try:
        amount = int(context.args[0])
        if amount <= 0:
            return await update.message.reply_text("Enter a valid amount.")
    except:
        return await update.message.reply_text("Enter a valid number.")

    if sender["coins"] < amount:
        return await update.message.reply_text("Not enough money.")

    tax = int(amount * 0.05)
    final = amount - tax

    sender["coins"] -= amount
    receiver["coins"] += final

    cats.update_one({"_id": sender["_id"]}, {"$set": sender})
    cats.update_one({"_id": receiver["_id"]}, {"$set": receiver})

    await update.message.reply_text(f"🐾 Sent ${final} after tax!")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ Only in DM
    if update.effective_chat.type != "private":
        return await update.message.reply_text("⚠️ Daily reward DM only.")

    cat = get_cat(update.effective_user)
    now = datetime.utcnow()  # ✅ FIXED

    last = cat.get("last_daily")
    if last and (now - last) < timedelta(hours=24):
        return await update.message.reply_text("⏳ Already claimed today!")

    cat["coins"] += 400
    cat["last_daily"] = now
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

    await update.message.reply_text("🎁 You got $400!")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # ❌ Not allowed in private chat
    if chat.type == "private":
        return await update.message.reply_text("❌ Use /daily in DM for personal reward.")

    # 👥 Check group size
    try:
        members = await context.bot.get_chat_member_count(chat.id)
    except:
        return await update.message.reply_text("⚠️ Unable to verify group size.")

    if members < 1000:
        return await update.message.reply_text("🚫 This command works only in groups with 1000+ members.")

    cat = get_cat(update.effective_user)
    now = datetime.utcnow()  # ✅ FIXED

    last = cat.get("last_claim")
    if last and (now - last) < timedelta(hours=24):
        return await update.message.reply_text("⏳ You already claimed a group reward today!")

    reward = 250  # Group reward amount

    cat["coins"] += reward
    cat["last_claim"] = now
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

    await update.message.reply_text(f"🏆 Group reward claimed! You received ${reward}")

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = get_cat(update.effective_user)

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to someone to gift 🎁")

    if not context.args:
        return await update.message.reply_text("Usage: /gift <item>")

    item = context.args[0].lower()
    if item not in GIFT_ITEMS:
        return await update.message.reply_text("Invalid gift item.")

    if sender.get("inventory", {}).get(item, 0) <= 0:
        return await update.message.reply_text("You don't own this gift.")

    receiver_user = update.message.reply_to_message.from_user
    receiver = get_cat(receiver_user)

    # Deduct from sender
    sender["inventory"][item] -= 1
    if sender["inventory"][item] <= 0:
        del sender["inventory"][item]

    # Add to receiver
    receiver.setdefault("inventory", {})
    receiver["inventory"][item] = receiver["inventory"].get(item, 0) + 1

    # Update DB
    cats.update_one({"_id": sender["_id"]}, {"$set": {"inventory": sender["inventory"]}})
    cats.update_one({"_id": receiver["_id"]}, {"$set": {"inventory": receiver["inventory"]}})

    # Prepare reply
    if item == "kiss":
        # Clickable user link
        user_link = f"[{receiver_user.first_name}](tg://user?id={receiver_user.id})"
        text = f"{GIFT_ITEMS[item]['emoji']} Gift sent to {user_link} 💖"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"{GIFT_ITEMS[item]['emoji']} Gift sent to {receiver_user.first_name} 💖")

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)
    inv = cat.get("inventory", {})

    msg = "🎒 *Your Inventory*\n\n"

    # ----- Normal Items -----
    normal_items = [f"▫️ {k.replace('_',' ').title()} × {v}" for k, v in inv.items() if k in SHOP_ITEMS and v > 0]
    if normal_items:
        msg += "🛒 *Shop Items:*\n" + "\n".join(normal_items) + "\n\n"
    else:
        msg += "🛒 *Shop Items:* Empty 😿\n\n"

    # ----- Gift Items -----
    gift_items = [f"{GIFT_ITEMS[k]['emoji']} {k.title()} × {v}" for k, v in inv.items() if k in GIFT_ITEMS and v > 0]
    if gift_items:
        msg += "🎁 *Gift Items:*\n" + "\n".join(gift_items)
    else:
        msg += "🎁 *Gift Items:* Empty 😿"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)  # get user data

    if not context.args:
        return await update.message.reply_text(
            "Usage: /use <item>\nExample: /use shield"
        )

    item = context.args[0].lower()
    inventory = cat.get("inventory", {})

    # ------------------- SHIELD -------------------
    if item == "shield":
        if inventory.get("shield", 0) <= 0:
            return await update.message.reply_text("❌ You don't own a shield.")

        inventory["shield"] -= 1
        cat["shield_until"] = datetime.now(timezone.utc) + timedelta(days=1)
        await update.message.reply_text("🛡 Shield activated for 24 hours!")

    # ------------------- SHIELD BREAKER -------------------
    elif item == "shield_breaker":
        if inventory.get("shield_breaker", 0) <= 0:
            return await update.message.reply_text("❌ You don't own a Shield Breaker.")
        # For shield breaker, it is consumed automatically in rob command
        return await update.message.reply_text("ℹ️ Use a Shield Breaker during a robbery!")

    # ------------------- LUCK BOOST -------------------
    elif item == "luck_boost":
        if inventory.get("luck_boost", 0) <= 0:
            return await update.message.reply_text("❌ You don't own a Luck Boost.")
        # For luck boost, it is consumed automatically in rob command
        return await update.message.reply_text("ℹ️ Luck Boost will be applied automatically on next robbery!")

    # ------------------- BAIL PASS -------------------
    elif item == "bail_pass":
        if inventory.get("bail_pass", 0) <= 0:
            return await update.message.reply_text("❌ You don't own a Bail Pass.")
        # Used automatically when jailed
        return await update.message.reply_text("ℹ️ Bail Pass will be used automatically if jailed!")

    # ------------------- FISH BAIT -------------------
    elif item == "fish_bait":
        if inventory.get("fish_bait", 0) <= 0:
            return await update.message.reply_text("❌ You don't own Fish Bait.")
        # Consumed automatically in fishing
        return await update.message.reply_text("ℹ️ Fish Bait will be consumed automatically in next fishing event!")

    else:
        return await update.message.reply_text("❌ Unknown item!")

    # Update cat inventory & db
    cat["inventory"] = inventory
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

def has_active_shield(cat):
    """Check if the cat has an active shield protection"""
    return cat.get("shield_until") and cat["shield_until"] > datetime.now(timezone.utc)

async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ❌ OWNER PROTECTION: Agar reply kiya gaya user OWNER hai
    if update.message.reply_to_message and is_owner_user(update.message.reply_to_message.from_user.id):
        await update.message.reply_text(
            "👑 Stop right there!\n"
            "Ye koi normal cat nahi 😼\n"
            "✨ This is the OWNER of the bot.\n"
            "⚠️ Tumhari robbery yahin fail hoti hai.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if update.effective_chat.type == "private":
        return await update.message.reply_text("❌ Rob works in groups only.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ Reply to a cat and use /rob <amount>")

    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("💸 Use like: /rob <amount>")

    if amount < 1 or amount > 1000:
        return await update.message.reply_text("❗ You can only rob between 1 - 1000.")

    thief_user = update.effective_user
    victim_user = update.message.reply_to_message.from_user

    if victim_user.id == thief_user.id:
        return await update.message.reply_text("🙀 You can't rob yourself!")

    if victim_user.is_bot:
        return await update.message.reply_text("🤖 That's a bot!")

    thief = get_cat(thief_user)
    victim = get_cat(victim_user)

    # Clickable mentions
    thief_mention = f"<a href='tg://user?id={thief_user.id}'>{thief_user.first_name}</a>"
    victim_mention = f"<a href='tg://user?id={victim_user.id}'>{victim_user.first_name}</a>"

    # 👑 VIP SHIELD CHECK
    if victim["inventory"].get("vip_shield", 0) > 0:
        victim["inventory"]["vip_shield"] -= 1
        cats.update_one({"_id": victim["_id"]}, {"$set": victim})
        return await update.message.reply_text(
            f"👑 VIP SHIELD activated! {victim_mention} blocked the robbery!",
            parse_mode="HTML"
        )

    # 🛡 NORMAL PROTECTION CHECK
    if is_protected(victim) or victim["inventory"].get("shield", 0) > 0:
        if thief["inventory"].get("shield_breaker", 0) > 0:
            thief["inventory"]["shield_breaker"] -= 1
            cats.update_one({"_id": thief["_id"]}, {"$set": thief})
            await update.message.reply_text("💣 Shield Breaker used! Protection destroyed!")
        else:
            return await update.message.reply_text(
                f"🛡 {victim_mention} is protected by a magic shield!",
                parse_mode="HTML"
            )

    steal = min(amount, victim["coins"])

    if steal <= 0:
        return await update.message.reply_text(
            f"😿 {victim_mention} is broke! Has $0",
            parse_mode="HTML"
        )

    if steal < amount:
        await update.message.reply_text(
            f"⚠️ {victim_mention} has only ${victim['coins']}! You stole ${steal} instead.",
            parse_mode="HTML"
        )

    victim["coins"] -= steal
    thief["coins"] += steal

    cats.update_one({"_id": thief["_id"]}, {"$set": thief})
    cats.update_one({"_id": victim["_id"]}, {"$set": victim})

    # ✅ Group success message with mentions
    await update.message.reply_text(
        f"😼 {thief_mention} robbed {victim_mention} and stole ${steal}!",
        parse_mode="HTML"
    )

    # 📩 DM to victim
    try:
        await context.bot.send_message(
            chat_id=victim_user.id,
            text=f"🚨 You were robbed by {thief_mention}!\n💸 Lost: ${steal}",
            parse_mode="HTML"
        )
    except:
        pass  # user may have DMs closed

__all__ = ["bal", "give", "daily", "claim", "gift", "inventory", "use", "has_active_shield", "rob"]
