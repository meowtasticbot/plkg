from catverse_bot import *

def is_owner(query, context):
    return context.chat_data.get("shop_owner") == query.from_user.id

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["shop_owner"] = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("🧪 Items Shop", callback_data="shop:items")],
        [InlineKeyboardButton("🎁 Gift Shop", callback_data="giftshop:open")]
    ]

    await update.message.reply_text(
        "🛒 *Catverse Black Market*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def shop_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_owner(query, context):
        return await query.answer("🚫 This shop isn't yours!", show_alert=True)

    cat = get_cat(query.from_user)

    if "inventory" not in cat or not isinstance(cat["inventory"], dict):
        cat["inventory"] = {}

    data = query.data

    # ===== MAIN MENU =====
    if data == "shop:main":
        keyboard = [
            [InlineKeyboardButton("🧪 Items Shop", callback_data="shop:items")],
            [InlineKeyboardButton("🎁 Gift Shop", callback_data="giftshop:open")]
        ]
        await query.edit_message_text("🛒 *Catverse Black Market*", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== OPEN ITEMS SHOP =====
    elif data == "shop:items":
        keyboard = [[InlineKeyboardButton(i.replace('_',' ').title(), callback_data=f"shop:view:{i}")] for i in SHOP_ITEMS]
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="shop:main")])
        await query.edit_message_text("🧪 *Black Market Items*", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== OPEN GIFT SHOP =====
    elif data == "giftshop:open":
        keyboard = [[InlineKeyboardButton(f"{v['emoji']} {k.title()} - ${v['price']}",
                                          callback_data=f"giftshop:view:{k}")] for k, v in GIFT_ITEMS.items()]
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="shop:main")])
        await query.edit_message_text("🎁 *Gift Shop*", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== VIEW NORMAL ITEM =====
    elif data.startswith("shop:view:"):
        item = data.split(":")[2]
        info = SHOP_ITEMS[item]
        owned = cat["inventory"].get(item, 0)

        text = f"🧾 *{item.replace('_',' ').title()}*\n\n{info['desc']}\n\n💰 Price: *${info['price']}*\n📦 Owned: *{owned}*"
        keyboard = [
            [InlineKeyboardButton("🛒 Purchase", callback_data=f"shop:buy:{item}")],
            [InlineKeyboardButton("⬅ Back", callback_data="shop:items")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== BUY NORMAL ITEM =====
    elif data.startswith("shop:buy:"):
        item = data.split(":")[2]
        price = SHOP_ITEMS[item]["price"]

        if cat["coins"] < price:
            return await query.answer("💸 You don't have enough coins!", show_alert=True)

        cat["coins"] -= price
        cat["inventory"][item] = cat["inventory"].get(item, 0) + 1
        cats.update_one({"_id": cat["_id"]}, {"$set": {"coins": cat["coins"], "inventory": cat["inventory"]}})

        await query.edit_message_text(
            f"✅ Purchased *{item.replace('_',' ').title()}*\n💰 Balance: ${cat['coins']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="shop:items")]])
        )

    # ===== VIEW GIFT =====
    elif data.startswith("giftshop:view:"):
        item = data.split(":")[2]
        info = GIFT_ITEMS[item]
        owned = cat["inventory"].get(item, 0)

        text = f"{info['emoji']} *{item.title()}*\n\n💰 Price: *${info['price']}*\n📦 Owned: *{owned}*"
        keyboard = [
            [InlineKeyboardButton("🛒 Buy Gift", callback_data=f"giftshop:buy:{item}")],
            [InlineKeyboardButton("⬅ Back", callback_data="giftshop:open")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== BUY GIFT =====
    elif data.startswith("giftshop:buy:"):
        item = data.split(":")[2]
        price = GIFT_ITEMS[item]["price"]

        if cat["coins"] < price:
            return await query.answer("💸 You don't have enough coins!", show_alert=True)

        cat["coins"] -= price
        cat["inventory"][item] = cat["inventory"].get(item, 0) + 1
        cats.update_one({"_id": cat["_id"]}, {"$set": {"coins": cat["coins"], "inventory": cat["inventory"]}})

        await query.edit_message_text(
            f"🎁 Gift Purchased: {GIFT_ITEMS[item]['emoji']} *{item.title()}*\n💰 Balance: ${cat['coins']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="giftshop:open")]])
        )

__all__ = ["is_owner", "shop", "shop_system"]
