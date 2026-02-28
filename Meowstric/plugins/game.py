from catverse_bot import *

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level_text = "\n".join([f"{lvl} → {req} XP" for lvl, req in LEVELS])
    text = (
        "🐱 *CATVERSE GUIDE*\n\n"

        "💰 Economy:\n"
        "  /daily — Daily coins (DM only)\n"
        "  /claim — Group reward (1000+ members)\n"
        "  /bal — Check balance\n"
        "  /give <amount> — Gift coins (reply)\n\n"

        "⚔️ Combat:\n"
        "  /rob <amount> — Rob a cat\n"
        "  /kill — Attack a cat\n"
        "  /protect — 24h protection\n\n"

        "🛒 Shop & Items:\n"
        "  /shop — Shop items\n"
        "     🐟 Fish Bait, 🚔 Bail Pass, 🍀 Luck Boost, 🛡 Shield, 💣 Shield Breaker\n"
        "  /inventory — Your items\n"
        "  /use <item> — Activate item (shield, shield_breaker, luck_boost, bail_pass, fish_bait)\n\n"

        "🐟 Fishing & Events:\n"
        "  Chat to gain XP & trigger fish events\n"
        "  /fish — Catch fish, rare boosted by Fish Bait\n\n"

        "📊 Profile & Stats:\n"
        "  /meow — Profile\n"
        "  /toprich — Richest cats\n"
        "  /topkill — Top fighters\n"
        "  /xp — Check XP & DNA stats\n"
        "  Levels: 🐱 Kitten → 😺 Teen → 😼 Rogue → 🐯 Alpha → 👑 Legend\n"
        f"📈 Levels:\n{level_text}"
    )
    await update.message.reply_text(text)

async def fish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cat = get_cat(user)
    inventory = cat.get("inventory", {})
    now = datetime.now(timezone.utc)

    today = now.date().isoformat()
    last_date = cat.get("last_fish_date")
    streak = cat.get("fish_streak", 0)

    if last_date == today:
        streak += 1
    else:
        streak = 1

    streak_bonus = min(streak * 20, 200)

    bait_bonus = 0
    bait_msg = ""
    if inventory.get("fish_bait", 0) > 0:
        bait_bonus = random.randint(50, 150)
        inventory["fish_bait"] -= 1
        bait_msg = "🐟 Magic bait boosted your luck!\n"

    roll = random.randint(1, 100)

    jackpot_msgs = [
        "💎 LEGENDARY DRAGON FISH!",
        "🐉 Mythical sea beast with treasure!",
        "🌟 Ancient glowing fish surfaced!",
    ]

    profit_msgs = [
        "🎣 Smooth catch!",
        "🐠 Coin-filled fish!",
        "🌊 Lucky wave reward!",
        "🏝️ Pirate fish haul!",
    ]

    loss_msgs = [
        "🦈 Sharks robbed you!",
        "🌪️ Storm destroyed net!",
        "🐙 Octopus tax taken!",
        "🏴‍☠️ Pirates stole catch!",
    ]

    coins_change = 0
    msg = ""

    # 🎉 JACKPOT
    if roll == 1:
        base = random.randint(5000, 10000)
        total = base + bait_bonus + streak_bonus
        coins_change = total
        msg = (
            f"{bait_msg}{random.choice(jackpot_msgs)}\n"
            f"💰 Base Catch: {base}\n"
            f"🎁 Streak Bonus: {streak_bonus}\n"
            f"✨ Bait Bonus: {bait_bonus}\n"
            f"🔥 JACKPOT TOTAL: +🪙 {total}"
        )

    # 🟢 NORMAL PROFIT
    elif 2 <= roll <= 71:
        base = random.randint(400, 1000)
        total = base + bait_bonus + streak_bonus
        coins_change = total
        msg = (
            f"{bait_msg}{random.choice(profit_msgs)}\n"
            f"💰 Base Catch: {base}\n"
            f"🎁 Streak Bonus: {streak_bonus}\n"
            f"✨ Bait Bonus: {bait_bonus}\n"
            f"🪙 TOTAL GAIN: +{total}"
        )

    # 🔴 LOSS
    else:
        loss = random.randint(1000, 2000)
        current = cat.get("coins", 0)

        if current < loss:
            loss = max(50, int(current * 0.5))

        coins_change = -loss
        msg = f"{random.choice(loss_msgs)}\n💸 Lost 🪙 {loss}"

    new_balance = max(0, cat.get("coins", 0) + coins_change)

    update_data = {
        "coins": new_balance,
        "fish_streak": streak,
        "last_fish_date": today,
        "inventory": inventory,
    }

    if coins_change > 0:
        update_data["fish_total_earned"] = cat.get("fish_total_earned", 0) + coins_change

    cats.update_one({"_id": user.id}, {"$set": update_data})

    await update.message.reply_text(msg)

async def fishlb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = cats.find().sort("fish_total_earned", -1).limit(5)

    text = "🏆 Top Fishing Legends 🏆\n\n"
    for i, u in enumerate(top_users, start=1):
        text += f"{i}. {u.get('name','Cat')} — 🪙 {u.get('fish_total_earned',0)}\n"

    await update.message.reply_text(text)

async def moon_mere_papa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)
    inventory = cat.get("inventory", {})

    rare_bonus = 0
    if inventory.get("fish_bait", 0) > 0:
        rare_bonus = 15
        inventory["fish_bait"] -= 1
        await update.message.reply_text("🐟 Fish Bait used! +15% rare chance")

    if random.randint(1, 100) <= 10 + rare_bonus:
        reward = 500
        await update.message.reply_text(f"🎉 You caught a rare fish! +${reward}")
    else:
        reward = 100
        await update.message.reply_text(f"🐟 You caught a normal fish. +${reward}")

    cat["coins"] += reward
    cat["inventory"] = inventory
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ❌ OWNER PROTECTION: Agar target owner hai
    if update.message.reply_to_message and is_owner_user(update.message.reply_to_message.from_user.id):
        await update.message.reply_text(
            "👑 Hold up!\n"
            "Ye koi normal cat nahi 😼\n"
            "✨ This is the OWNER of the bot.\n"
            "⚠️ Tumhari command yahin khatam hoti hai.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to attack someone.")

    attacker_user = update.effective_user
    victim_user = update.message.reply_to_message.from_user

    # Khud ko attack na kar sake
    if attacker_user.id == victim_user.id:
        return await update.message.reply_text("You can't attack yourself 😹")

    attacker = get_cat(attacker_user)
    victim = get_cat(victim_user)

    # Clickable mentions
    attacker_mention = f"<a href='tg://user?id={attacker_user.id}'>{attacker_user.first_name}</a>"
    victim_mention = f"<a href='tg://user?id={victim_user.id}'>{victim_user.first_name}</a>"

    # 🛡 PROTECTION CHECK
    if victim["inventory"].get("vip_shield", 0) > 0:
        return await update.message.reply_text(
            f"👑 {victim_mention} is protected by a VIP Shield!",
            parse_mode="HTML"
        )

    if victim["inventory"].get("shield", 0) > 0 or is_protected(victim):
        return await update.message.reply_text(
            f"🛡 {victim_mention} is protected right now!",
            parse_mode="HTML"
        )

    # 🪦 Already dead check
    if victim.get("health", 100) <= 0:
        return await update.message.reply_text(
            f"☠️ {victim_mention} is already dead!\nNo need to attack again 😼",
            parse_mode="HTML"
        )

    # 🎁 Reward
    reward = random.randint(80, 160)

    attacker["kills"] += 1
    victim["deaths"] += 1
    attacker["coins"] += reward

    # Victim health zero
    victim["health"] = 0

    cats.update_one({"_id": attacker["_id"]}, {"$set": attacker})
    cats.update_one({"_id": victim["_id"]}, {"$set": victim})

    # ✅ Group message
    await update.message.reply_text(
        f"⚔️ {attacker_mention} attacked {victim_mention} and won!\n"
        f"💰 Reward: ${reward}",
        parse_mode="HTML"
    )

    # 📩 DM to victim
    try:
        await context.bot.send_message(
            chat_id=victim_user.id,
            text=(
                f"🚨 <b>You were attacked!</b>\n"
                f"⚔️ Attacker: {attacker_mention}\n"
                f"💀 You lost the fight and are now dead.\n"
                f"❤️ Health: 0"
            ),
            parse_mode="HTML"
        )
    except:
        pass

async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = get_cat(update.effective_user)
    now = datetime.now(timezone.utc)

    # ❗ Show usage if no argument
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /protection 1d")

    # ❌ Only 1d allowed
    if context.args[0].lower() != "1d":
        return await update.message.reply_text("❗ Users can only use: 1d")

    # 🛡 Already protected check
    protected_until = cat.get("protected_until")
    if protected_until and protected_until.tzinfo is None:
        protected_until = protected_until.replace(tzinfo=timezone.utc)

    if protected_until and protected_until > now:
        remaining = protected_until - now
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        days = remaining.days

        time_text = ""
        if days > 0:
            time_text += f"{days}d "
        if hours > 0:
            time_text += f"{hours}h "
        if minutes > 0:
            time_text += f"{minutes}m"

        return await update.message.reply_text(
            f"🛡 You are already protected!\n⏳ Time left: {time_text.strip()}"
        )

    # 💰 Cost check
    cost = 600
    if cat["coins"] < cost:
        return await update.message.reply_text(f"Need ${cost} for protection.")

    # ✅ Activate protection
    cat["coins"] -= cost
    cat["protected_until"] = now + timedelta(days=1)

    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

    await update.message.reply_text("🛡 Protection enabled for 1 day.")

def leaderboard_buttons():
    keyboard = [[
        InlineKeyboardButton("🏆 Richest Cats", callback_data="lb_rich"),
        InlineKeyboardButton("⚔️ Top Fighters", callback_data="lb_kill"),
    ]]
    return InlineKeyboardMarkup(keyboard)

def rank_decor(rank: int) -> str:
    return ["👑", "🥈", "🥉"][rank-1] if rank <= 3 else "🎖"

def get_rank_arrow(user_id: int, board_type: str, new_rank: int) -> str:
    key = f"{board_type}_{user_id}"
    prev = leaderboard_history.find_one({"_id": key})

    if not prev:
        leaderboard_history.insert_one({"_id": key, "rank": new_rank})
        return "🆕"

    old_rank = prev["rank"]
    leaderboard_history.update_one({"_id": key}, {"$set": {"rank": new_rank}})

    if new_rank < old_rank:
        return "🔼"
    elif new_rank > old_rank:
        return "🔽"
    return "➖"

def build_rich_board():
    top = cats.find({"_id": {"$ne": OWNER_ID}}).sort("coins", -1).limit(10)  # exclude owner
    msg = "<b>🏆 Top Rich Cats</b>\n\n"

    for i, c in enumerate(top, 1):  
        user_id = c["_id"]  
        name = c.get("name", "Cat")  
        coins = c.get("coins", 0)  

        badge = rank_decor(i)  
        arrow = get_rank_arrow(user_id, "rich", i)  
        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"  

        msg += f"{badge} {i}. {mention} {arrow} — ${coins}\n"  

    return msg

def build_kill_board():
    top = cats.find({"_id": {"$ne": OWNER_ID}}).sort("kills", -1).limit(10)  # exclude owner
    msg = "<b>⚔️ Top Fighters</b>\n\n"

    for i, c in enumerate(top, 1):  
        user_id = c["_id"]  
        name = c.get("name", "Cat")  
        kills = c.get("kills", 0)  

        badge = rank_decor(i)  
        arrow = get_rank_arrow(user_id, "kill", i)  
        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"  

        msg += f"{badge} {i}. {mention} {arrow} — {kills} wins\n"  

    return msg

async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = build_rich_board()
    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=leaderboard_buttons()
    )

async def topkill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = build_kill_board()
    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=leaderboard_buttons()
    )

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lb_rich":
        msg = build_rich_board()
    else:
        msg = build_kill_board()

    await query.edit_message_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=leaderboard_buttons()
    )

async def lobu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ Sirf owner use kar sakta
    if not is_owner_user(update.effective_user.id):
        return await update.message.reply_text(
            "🚫 Sorry! Only the OWNER can use this command!"
        )

    # ✅ Reply aur amount check
    if not update.message.reply_to_message or not context.args:
        return await update.message.reply_text(
            "Usage: /lobu <amount> (reply to a user)"
        )

    # ✅ Amount parse karna
    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("❌ Enter a valid number!")

    # ✅ Target user
    target_user = update.message.reply_to_message.from_user
    target = get_cat(target_user)

    # ✅ Owner coins = infinite
    cat_owner = get_cat(update.effective_user)
    cat_owner["coins"] = float("inf")
    cats.update_one({"_id": cat_owner["_id"]}, {"$set": cat_owner})  # DB update

    # ✅ Target ko coins add karna
    target["coins"] += amount
    cats.update_one({"_id": target["_id"]}, {"$set": target})  # DB update

    # ✅ Mention
    mention = f"<a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>"

    # ✅ Reply message (proper indentation inside function)
    await update.message.reply_text(
        f"👑 Owner Power Activated!\n\n"
        f"✨ {mention} just received ${amount} instantly!\n"
        f"💰 Owner's magic never fails!",
        parse_mode="HTML"  # HTML mode for clickable mentions
    )

async def fun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    responses = [
        "😹 You found a hidden treasure! +$120",
        "🐟 A fish jumps into your inventory! +1 fish",
        "💤 You took a nap, nothing happened...",
        "🍀 Lucky day! Gain +2 luck",
        "😼 Mischievous cat almost stole your money!",
    ]
    msg = random.choice(responses)
    cat = get_cat(update.effective_user)

    if "$120" in msg:
        cat["coins"] += 120
    if "fish" in msg:
        cat["fish"] += 1
    if "luck" in msg:
        cat["dna"]["luck"] += 2

    cats.update_one({"_id": cat["_id"]}, {"$set": cat})
    await update.message.reply_text(msg)

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(
            "Usage: /upgrade <stat> <amount>\nStats: aggression, intelligence, luck, charm"
        )

    cat = get_cat(update.effective_user)
    stat = context.args[0].lower()
    amount = int(context.args[1]) if len(context.args) > 1 else 1

    if stat not in UPGRADE_COSTS:
        return await update.message.reply_text("❌ Invalid stat!")

    cost = UPGRADE_COSTS[stat] * amount
    if cat["coins"] < cost:
        return await update.message.reply_text(f"❌ Not enough money! Costs ${cost}")

    cat["coins"] -= cost
    cat["dna"][stat] += amount
    evolve(cat)
    cats.update_one({"_id": cat["_id"]}, {"$set": cat})

    await update.message.reply_text(
        f"✅ {stat.capitalize()} increased by {amount}! Spent ${cost}\n"
        f"New {stat.capitalize()}: {cat['dna'][stat]}\n"
        f"Current Level: {cat['level']}"
    )

__all__ = ["games", "fish", "fishlb", "moon_mere_papa", "kill", "protect", "leaderboard_buttons", "rank_decor", "get_rank_arrow", "build_rich_board", "build_kill_board", "toprich", "topkill", "leaderboard_callback", "lobu", "fun", "upgrade"]
