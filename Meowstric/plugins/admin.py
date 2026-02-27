from Meowstric.config import OWNER_ID, SUDO_IDS
from Meowstric.database import groups_collection, sudoers_collection, users_collection
from Meowstric.utils import reload_sudoers
from catverse_bot import *

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_status = update.chat_member.new_chat_member.status
    if new_status == ChatMemberStatus.MEMBER:
        member = update.chat_member.new_chat_member.user
        messages = [
            f"🎉 Welcome {member.first_name}! Khush aamdeed! 😊",
            f"🌟 Aao ji {member.first_name}! Group me welcome! 🫂",
            f"✨ Hey {member.first_name}! Great to have you here! 💖"
        ]
        await context.bot.send_message(update.effective_chat.id, random.choice(messages))

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    bot = context.bot

    target_user = None

    # ================= TARGET USER =================
    # Reply case
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    # @username case
    elif context.args:
        username = context.args[0]
        if username.startswith("@"):
            try:
                member = await bot.get_chat_member(message.chat.id, username)
                target_user = member.user
            except:
                target_user = None

    if not target_user:
        responses = [
            f"{get_emotion('thinking')} Kisi ke message par reply karke command do! 👆",
            f"{get_emotion()} Reply to user's message first! 📩",
            f"{get_emotion('angry')} Bhai kisko? Reply karo na! 😠"
        ]
        await message.reply_text(random.choice(responses))
        return

    cmd = message.text.split()[0][1:]  # Remove '/'

    try:
        if cmd == "kick":
            await bot.ban_chat_member(message.chat.id, target_user.id)
            await bot.unban_chat_member(message.chat.id, target_user.id)
            responses = [
                f"{get_emotion('angry')} {target_user.first_name} ko nikal diya! 🏃💨",
                f"{get_emotion()} Bye bye {target_user.first_name}! 👋",
                f"{get_emotion('happy')} {target_user.first_name} removed! 🚪"
            ]
            await message.reply_text(random.choice(responses))

        elif cmd == "ban":
            await bot.ban_chat_member(message.chat.id, target_user.id)
            responses = [
                f"{get_emotion('angry')} {target_user.first_name} BANNED! 🚫",
                f"{get_emotion()} Permanent ban for {target_user.first_name}! 🔨",
                f"{get_emotion('crying')} Sorry {target_user.first_name}, rules are rules! 😔"
            ]
            await message.reply_text(random.choice(responses))

        elif cmd == "mute":
            mute_until = datetime.now() + timedelta(hours=1)
            await bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                ),
                until_date=mute_until
            )
            responses = [
                f"{get_emotion()} {target_user.first_name} muted for 1 hour! 🔇",
                f"{get_emotion('thinking')} {target_user.first_name} ko chup kara diya! 🤫",
                f"{get_emotion('angry')} {target_user.first_name}, ab 1 ghante tak bolna band! ⚠️"
            ]
            await message.reply_text(random.choice(responses))

        elif cmd == "unmute":
            await bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False
                )
            )
            responses = [
                f"{get_emotion('happy')} {target_user.first_name} unmuted! 🔊",
                f"{get_emotion()} {target_user.first_name} ab bol sakta hai! 🎤",
                f"{get_emotion('funny')} {target_user.first_name}, ab bol lo! 😄"
            ]
            await message.reply_text(random.choice(responses))

        elif cmd == "unban":
            await bot.unban_chat_member(message.chat.id, target_user.id)
            await message.reply_text(
                f"{get_emotion('happy')} {target_user.first_name} unbanned! 🐾"
            )

    except:
        error_responses = [
            f"{get_emotion('crying')} I don't have permission! ❌",
            f"{get_emotion('angry')} Make me admin first! 👑",
            f"{get_emotion('thinking')} Can't do that! Need admin rights! 🔒"
        ]
        await message.reply_text(random.choice(error_responses))

async def plp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = users.find_one({"_id": user.id})

    # Insert a new user if not already present
    users.update_one(
        {"_id": user.id},
        {"$setOnInsert": {
            "name": user.first_name,
            "first_open_logged": True
        }},
        upsert=True
    )

    # If new user, log it in the logger GC
    if not existing:
        await log(
            context,
            f"🐾 *New Cat Opened Bot*\n"
            f"👤 {user.first_name}\n"
            f"🆔 `{user.id}`"
        )

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    actor = update.chat_member.from_user
    new = update.chat_member.new_chat_member
    old = update.chat_member.old_chat_member

    # Ensure only group chats are logged
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if new.user.id != context.bot.id:
        return

    # Get the group privacy (public/private) and invite link if available
    if chat.type == ChatType.GROUP:
        group_info = await context.bot.get_chat(chat.id)
        try:
            invite_link = await context.bot.export_chat_invite_link(chat.id)
            group_privacy = "Public" if group_info.invite_link else "Private"
        except:
            invite_link = "No invite link available"
            group_privacy = "Private"  # If we cannot fetch link, assume private

        # Update group member count and log the action
        count = await context.bot.get_chat_member_count(chat.id)
        groups.update_one(
            {"_id": chat.id},
            {"$set": {"title": chat.title, "members": count, "privacy": group_privacy, "invite_link": invite_link}},
            upsert=True
        )

        # Log the bot being added to the group with invite link and privacy info
        await log(
            context,
            f"🐱 *Bot Added*\n"
            f"📛 {chat.title}\n"
            f"👥 Members: {count}\n"
            f"👤 By: {actor.first_name}\n"
            f"🔗 Invite Link: {invite_link}\n"
            f"🌐 Privacy: {group_privacy}"
        )

    # Log if the bot is removed from a group
    if old.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR) and new.status in (
        ChatMemberStatus.LEFT, ChatMemberStatus.KICKED
    ):
        groups.delete_one({"_id": chat.id})
        await log(
            context,
            f"😿 *Bot Removed*\n"
            f"📛 {chat.title}\n"
            f"👤 By: {actor.first_name}"
        )

__all__ = ["plp", "member_update", "welcome_new_member", "admin_commands", "sudo_help", "sudolist", "addsudo", "rmsudo", "cleandb"]


# ===== SUDO MANAGEMENT PANEL =====
def is_authorized(user_id: int) -> bool:
    db_sudos = [s.get("user_id") for s in sudoers_collection.find()]
    return user_id == OWNER_ID or user_id in SUDO_IDS or user_id in db_sudos


async def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        return {"user_id": u.id, "name": u.full_name}
    if context.args:
        arg = context.args[0]
        if arg.isdigit():
            return {"user_id": int(arg), "name": arg}
        if arg.startswith("@"):
            try:
                chat = await context.bot.get_chat(arg)
                return {"user_id": chat.id, "name": chat.full_name or arg}
            except Exception:
                return None
    return None



async def sudo_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    msg = (
        "🔐 <b>Sudo Panel</b>\n\n"
        "💰 <b>Economy</b>\n"
        "• /addcoins amt\n"
        "• /rmcoins amt\n"
        "• /freerevive\n"
        "• /unprotect\n\n"
        "👑 <b>Sudo Management</b>\n"
        "• /addsudo | /rmsudo\n"
        "• /sudolist | /cleandb"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    sudos = list(sudoers_collection.find())
    msg = f"🛡️ <b>Sudoers List</b>\n\n👑 OWNER: <code>{OWNER_ID}</code>\n"
    for sdoc in sudos:
        if sdoc.get("user_id") != OWNER_ID:
            msg += f"• <code>{sdoc.get('user_id')}</code>\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    target = await get_target(update, context)
    if not target:
        return await update.message.reply_text("User not found.")
    sudoers_collection.update_one({"user_id": target["user_id"]}, {"$set": {"user_id": target["user_id"]}}, upsert=True)
    reload_sudoers()
    await update.message.reply_text(f"✅ {target['name']} added as sudo.")


async def rmsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    target = await get_target(update, context)
    if not target:
        return await update.message.reply_text("User not found.")
    sudoers_collection.delete_one({"user_id": target["user_id"]})
    reload_sudoers()
    await update.message.reply_text(f"❌ {target['name']} removed from sudo.")


async def cleandb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    users_collection.delete_many({})
    groups_collection.delete_many({})
    await update.message.reply_text("💥 Database wiped.")


__all__ = ["plp", "member_update", "welcome_new_member", "admin_commands", "sudo_help", "sudolist", "addsudo", "rmsudo", "cleandb"]
