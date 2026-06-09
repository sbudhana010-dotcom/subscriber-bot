"""
🚀 Viral Subscriber Bot - Complete System
Features: Free/Paid subscribers, Referral system, Auto-promotion, Admin panel
"""

import logging
import asyncio
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# ─── CONVERSATION STATES ───────────────────────────────────────────────────────
ADMIN_BROADCAST = 1

# ─── /START ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_code = context.args[0] if context.args else None

    is_new = db.register_user(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name,
        ref_code=ref_code
    )

    if is_new and ref_code:
        referrer_id = db.get_user_by_ref(ref_code)
        if referrer_id and referrer_id != user.id:
            db.add_free_subscribers(referrer_id, Config.REFERRAL_REWARD)
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 *Congratulations!* A new user joined via your referral link!\n"
                         f"✅ You received *{Config.REFERRAL_REWARD} free subscribers!*",
                    parse_mode='Markdown'
                )
            except:
                pass

    user_data = db.get_user(user.id)
    text = (
        f"🌟 *Welcome, {user.first_name}!*\n\n"
        f"🤖 Welcome to *Subscriber Bot*!\n"
        f"Grow your channel fast with real subscribers.\n\n"
        f"📊 *Your Account:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"├ 💎 Paid Subscribers: `{user_data['paid_subs']}`\n"
        f"├ 👥 Referrals: `{user_data['referrals']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"👇 *Choose an option below:*"
    )

    keyboard = main_menu_keyboard(user.id)
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)


def main_menu_keyboard(user_id):
    is_admin = user_id in Config.ADMIN_IDS
    buttons = [
        [InlineKeyboardButton("🆓 Free Subscribers", callback_data="free_menu"),
         InlineKeyboardButton("💎 Paid Subscribers", callback_data="paid_menu")],
        [InlineKeyboardButton("👥 Referral System", callback_data="referral_menu"),
         InlineKeyboardButton("📊 My Account", callback_data="my_account")],
        [InlineKeyboardButton("📋 Order History", callback_data="orders"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)


# ─── FREE SUBSCRIBERS MENU ─────────────────────────────────────────────────────
async def free_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    text = (
        f"🆓 *FREE SUBSCRIBER SYSTEM*\n\n"
        f"📌 *How to get Free Subscribers?*\n\n"
        f"*Method 1 — Task:*\n"
        f"├ Invite 10 people to join this bot\n"
        f"└ Get *5 free subscribers* as reward! 🎁\n\n"
        f"*Method 2 — Referral:*\n"
        f"├ Share your referral link\n"
        f"└ Get *{Config.REFERRAL_REWARD} subscribers* per new user! 🔗\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Your Current Status:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"└ 👥 Total Referrals: `{user_data['referrals']}`\n\n"
        f"👇 *What would you like to do?*"
    )

    buttons = [
        [InlineKeyboardButton("✅ Invite 10 → Get 5 Free Subs", callback_data="task_subscribe")],
        [InlineKeyboardButton("🔗 Get Referral Link", callback_data="get_referral")],
        [InlineKeyboardButton("📤 Use Free Subscribers", callback_data="use_free_subs")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def task_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    task_status = db.get_task_status(user_id)
    subscribed_count = task_status['subscribed'] if task_status else 0
    needed = Config.TASK_REQUIRED

    filled = subscribed_count if subscribed_count <= needed else needed
    text = (
        f"📋 *TASK: Invite 10 People*\n\n"
        f"🎯 *Your Progress:* `{subscribed_count}/{needed}`\n"
        f"{'█' * filled}{'░' * (needed - filled)} {min(subscribed_count, needed)*10}%\n\n"
        f"*Steps:*\n"
        f"1️⃣ Copy your special task link below\n"
        f"2️⃣ Send it to 10 friends\n"
        f"3️⃣ They join the bot\n"
        f"4️⃣ You automatically get *5 free subscribers!* 🎁\n\n"
        f"⚠️ *Note:* Only new users are counted\n\n"
        f"🔗 *Your Task Link:*\n"
        f"`https://t.me/{Config.BOT_USERNAME}?start=task_{user_id}`"
    )

    buttons = [
        [InlineKeyboardButton("📋 Copy & Share Link",
                               url=f"https://t.me/{Config.BOT_USERNAME}?start=task_{user_id}")],
        [InlineKeyboardButton("📊 Check My Progress", callback_data="check_task_progress")],
        [InlineKeyboardButton("🔙 Back", callback_data="free_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def check_task_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_status = db.get_task_status(user_id)
    subscribed_count = task_status['subscribed'] if task_status else 0

    if subscribed_count >= Config.TASK_REQUIRED:
        db.complete_task(user_id)
        text = (
            f"🎉 *TASK COMPLETE!*\n\n"
            f"✅ You successfully invited {Config.TASK_REQUIRED} users!\n"
            f"🎁 *5 Free Subscribers* have been added to your account!\n\n"
            f"Want more? Share your link again and repeat! 🚀"
        )
    else:
        remaining = Config.TASK_REQUIRED - subscribed_count
        text = (
            f"⏳ *Task Progress Update*\n\n"
            f"✅ Joined so far: `{subscribed_count}/{Config.TASK_REQUIRED}`\n"
            f"⏳ Still needed: `{remaining}` more\n\n"
            f"{'█' * subscribed_count}{'░' * (Config.TASK_REQUIRED - subscribed_count)} "
            f"{subscribed_count * 10}%\n\n"
            f"Keep sharing — your reward is waiting! 🚀"
        )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="free_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── REFERRAL MENU ─────────────────────────────────────────────────────────────
async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    ref_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"🔗 *REFERRAL SYSTEM*\n\n"
        f"💰 *Earn with every referral:*\n"
        f"├ 👤 New user joins → *{Config.REFERRAL_REWARD} Free Subscribers*\n"
        f"├ 💎 They place a paid order → *Bonus!*\n"
        f"└ 🔥 More referrals = more rewards!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Your Stats:*\n"
        f"├ 👥 Total Referrals: `{user_data['referrals']}`\n"
        f"├ 🆓 Free Subs Earned: `{user_data['free_subs']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"🔗 *Your Personal Link:*\n"
        f"`{ref_link}`\n\n"
        f"📢 *Share and earn!*"
    )

    share_url = f"https://t.me/share/url?url={ref_link}&text=🚀+Join+this+bot+and+get+free+subscribers!"

    buttons = [
        [InlineKeyboardButton("📤 Share on WhatsApp",
                               url=f"https://wa.me/?text=🚀 Join this Subscriber Bot and get free subs! {ref_link}"),
         InlineKeyboardButton("📢 Share on Telegram", url=share_url)],
        [InlineKeyboardButton("🏆 Referral Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top_users = db.get_leaderboard()

    medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    text = "🏆 *TOP REFERRERS*\n\n"
    for i, u in enumerate(top_users[:5]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = (u['full_name'] or "User")[:15]
        text += f"{medal} *{name}* — `{u['referrals']}` referrals\n"

    text += "\n💪 Refer more people and climb the leaderboard!"
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="referral_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── PAID SUBSCRIBERS MENU ─────────────────────────────────────────────────────
async def paid_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    packages = db.get_packages()

    text = (
        f"💎 *PAID SUBSCRIBER PACKAGES*\n\n"
        f"🌟 *Real & High Quality Subscribers*\n"
        f"✅ 100% Genuine\n"
        f"✅ Fast Delivery\n"
        f"✅ No Drop Guarantee\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Available Packages:*\n\n"
    )

    buttons = []
    for pkg in packages:
        text += (
            f"*{pkg['name']}*\n"
            f"├ 👥 Subscribers: `{pkg['subs']}`\n"
            f"├ 💰 Price: `Rs. {pkg['price']}`\n"
            f"└ ⚡ Delivery: `{pkg['delivery']}`\n\n"
        )
        buttons.append([InlineKeyboardButton(
            f"🛒 {pkg['name']} — Rs.{pkg['price']}",
            callback_data=f"buy_pkg_{pkg['id']}"
        )])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def buy_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pkg_id = int(query.data.split("_")[-1])
    pkg = db.get_package(pkg_id)

    text = (
        f"🛒 *CONFIRM YOUR ORDER*\n\n"
        f"📦 Package: *{pkg['name']}*\n"
        f"👥 Subscribers: `{pkg['subs']}`\n"
        f"💰 Price: `Rs. {pkg['price']}`\n"
        f"⚡ Delivery: `{pkg['delivery']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 *Payment Methods:*\n"
        f"├ EasyPaisa: `{Config.EASYPAISA_NUM}`\n"
        f"├ JazzCash: `{Config.JAZZCASH_NUM}`\n"
        f"└ Bank: `{Config.BANK_ACCOUNT}`\n\n"
        f"📸 *Send payment and upload screenshot!*\n"
        f"Order will be processed within 1–2 hours ✅"
    )

    buttons = [
        [InlineKeyboardButton("✅ Submit Payment Screenshot",
                               callback_data=f"submit_payment_{pkg_id}")],
        [InlineKeyboardButton("💬 Contact Admin",
                               url=f"https://t.me/{Config.ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="paid_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def submit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pkg_id = int(query.data.split("_")[-1])
    context.user_data['pending_pkg'] = pkg_id

    text = (
        f"📸 *SUBMIT PAYMENT SCREENSHOT*\n\n"
        f"Please send your payment screenshot below.\n"
        f"Admin will verify and process your order!\n\n"
        f"⏰ Processing time: 1–2 hours"
    )
    buttons = [[InlineKeyboardButton("🔙 Cancel", callback_data="paid_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def handle_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'pending_pkg' not in context.user_data:
        return

    user = update.effective_user
    pkg_id = context.user_data['pending_pkg']
    pkg = db.get_package(pkg_id)
    order_id = db.create_order(user.id, pkg_id)

    for admin_id in Config.ADMIN_IDS:
        try:
            caption = (
                f"💰 *NEW ORDER RECEIVED!*\n\n"
                f"👤 User: {user.full_name} (@{user.username})\n"
                f"🆔 User ID: `{user.id}`\n"
                f"📦 Package: {pkg['name']}\n"
                f"👥 Subscribers: {pkg['subs']}\n"
                f"💰 Amount: Rs. {pkg['price']}\n"
                f"🔢 Order ID: #{order_id}\n\n"
                f"Please approve or reject:"
            )
            approve_btn = [[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_order_{order_id}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"reject_order_{order_id}")
            ]]
            await context.bot.forward_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await context.bot.send_message(
                chat_id=admin_id, text=caption,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(approve_btn)
            )
        except Exception as e:
            logger.error(f"Admin notify error: {e}")

    await update.message.reply_text(
        f"✅ *Payment Screenshot Received!*\n\n"
        f"🔢 Order ID: `#{order_id}`\n"
        f"⏰ Will be processed within 1–2 hours.\n\n"
        f"You'll get a notification once admin approves it!",
        parse_mode='Markdown'
    )
    del context.user_data['pending_pkg']


# ─── MY ACCOUNT ────────────────────────────────────────────────────────────────
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    ref_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"👤 *MY ACCOUNT*\n\n"
        f"📛 Name: *{user_data['full_name']}*\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Joined: `{user_data['joined_date']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Statistics:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"├ 💎 Paid Subscribers: `{user_data['paid_subs']}`\n"
        f"├ 👥 Referrals Done: `{user_data['referrals']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *Your Referral Link:*\n"
        f"`{ref_link}`"
    )

    buttons = [
        [InlineKeyboardButton("📋 Order History", callback_data="orders")],
        [InlineKeyboardButton("🔗 My Referral Link", callback_data="get_referral")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def orders_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    orders = db.get_user_orders(user_id)

    if not orders:
        text = "📋 *ORDER HISTORY*\n\nYou haven't placed any orders yet!\n\n💎 Check out our paid packages!"
    else:
        text = "📋 *ORDER HISTORY*\n\n"
        for order in orders[-10:]:
            status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌",
                            "completed": "🎉"}.get(order['status'], "❓")
            text += (
                f"{status_emoji} Order `#{order['id']}`\n"
                f"├ Package: {order['pkg_name']}\n"
                f"├ Status: *{order['status'].upper()}*\n"
                f"└ Date: {order['created_at']}\n\n"
            )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="my_account")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── ADMIN PANEL ───────────────────────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return

    stats = db.get_stats()
    text = (
        f"⚙️ *ADMIN PANEL*\n\n"
        f"📊 *Bot Statistics:*\n"
        f"├ 👥 Total Users: `{stats['total_users']}`\n"
        f"├ 🆕 Joined Today: `{stats['today_users']}`\n"
        f"├ 💎 Total Orders: `{stats['total_orders']}`\n"
        f"├ ⏳ Pending Orders: `{stats['pending_orders']}`\n"
        f"└ 💰 Total Revenue: `Rs. {stats['total_revenue']}`\n\n"
    )

    buttons = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"),
         InlineKeyboardButton("⏳ Pending Orders",    callback_data="admin_pending")],
        [InlineKeyboardButton("💰 Edit Package Rates", callback_data="admin_packages"),
         InlineKeyboardButton("👥 All Users",          callback_data="admin_users")],
        [InlineKeyboardButton("🎁 Give Free Subs",     callback_data="admin_give_subs"),
         InlineKeyboardButton("📊 Full Stats",         callback_data="admin_full_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def admin_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    orders = db.get_pending_orders()
    if not orders:
        text = "✅ No pending orders!"
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    await query.edit_message_text(f"⏳ *{len(orders)} Pending Orders:*", parse_mode='Markdown')
    for order in orders[:5]:
        text = (
            f"⏳ *PENDING ORDER #{order['id']}*\n\n"
            f"👤 User: {order['full_name']}\n"
            f"📦 Package: {order['pkg_name']}\n"
            f"👥 Subscribers: {order['subs']}\n"
            f"💰 Amount: Rs. {order['price']}\n"
            f"📅 Date: {order['created_at']}"
        )
        buttons = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_order_{order['id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"reject_order_{order['id']}")
        ]]
        await query.message.reply_text(text, parse_mode='Markdown',
                                        reply_markup=InlineKeyboardMarkup(buttons))


async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    order_id = int(query.data.split("_")[-1])
    order = db.approve_order(order_id)

    try:
        await context.bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"🎉 *ORDER APPROVED!*\n\n"
                f"✅ Your Order `#{order_id}` has been approved!\n"
                f"📦 Package: {order['pkg_name']}\n"
                f"👥 {order['subs']} subscribers will be delivered soon!\n\n"
                f"Thank you for your purchase! 🙏"
            ),
            parse_mode='Markdown'
        )
    except:
        pass

    await query.edit_message_text(f"✅ Order #{order_id} Approved!")


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    order_id = int(query.data.split("_")[-1])
    db.reject_order(order_id)

    try:
        order = db.get_order(order_id)
        await context.bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"❌ *Order Rejected*\n\n"
                f"Order `#{order_id}` was rejected.\n"
                f"For any issue, please contact admin: @{Config.ADMIN_USERNAME}"
            ),
            parse_mode='Markdown'
        )
    except:
        pass

    await query.edit_message_text(f"❌ Order #{order_id} Rejected!")


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    context.user_data['awaiting_broadcast'] = True
    await query.edit_message_text(
        "📢 *BROADCAST MESSAGE*\n\nType the message you want to send to all users:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")
        ]])
    )


async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_broadcast'):
        return
    if update.effective_user.id not in Config.ADMIN_IDS:
        return

    message = update.message.text
    users = db.get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text("📢 Broadcasting...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 *ANNOUNCEMENT*\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await status_msg.edit_text(
        f"✅ *Broadcast Complete!*\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )
    context.user_data['awaiting_broadcast'] = False


# ─── GET REFERRAL LINK ──────────────────────────────────────────────────────────
async def get_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ref_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"🔗 *YOUR REFERRAL LINK*\n\n"
        f"`{ref_link}`\n\n"
        f"💰 Per referral: *{Config.REFERRAL_REWARD} Free Subscribers*\n\n"
        f"📤 *Share it on:*\n"
        f"• WhatsApp groups\n"
        f"• Telegram channels\n"
        f"• Facebook posts\n"
        f"• Instagram bio\n\n"
        f"More shares = more earnings! 🚀"
    )
    buttons = [
        [InlineKeyboardButton("📤 WhatsApp",
                               url=f"https://wa.me/?text=🚀 Join this bot and get free subscribers! {ref_link}"),
         InlineKeyboardButton("📢 Telegram",
                               url=f"https://t.me/share/url?url={ref_link}&text=🚀+Get+free+subscribers!")],
        [InlineKeyboardButton("🔙 Back", callback_data="referral_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── HELP ──────────────────────────────────────────────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        f"ℹ️ *HELP & GUIDE*\n\n"
        f"*How to get Free Subscribers?*\n"
        f"1. Invite 10 people to this bot\n"
        f"2. Or share your referral link\n\n"
        f"*What are Paid Subscribers?*\n"
        f"Real, genuine subscribers added to your channel/group.\n\n"
        f"*How to pay?*\n"
        f"EasyPaisa / JazzCash / Bank Transfer\n\n"
        f"*Need help?*\n"
        f"Contact Admin: @{Config.ADMIN_USERNAME}\n\n"
        f"*Commands:*\n"
        f"/start — Start the bot\n"
        f"/account — View your account\n"
        f"/referral — Get your referral link"
    )
    buttons = [
        [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{Config.ADMIN_USERNAME}"),
         InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_data = db.get_user(user.id)

    text = (
        f"🌟 *Main Menu*\n\n"
        f"📊 *Your Account:*\n"
        f"├ 🆓 Free: `{user_data['free_subs']}`\n"
        f"├ 💎 Paid: `{user_data['paid_subs']}`\n"
        f"└ 👥 Referrals: `{user_data['referrals']}`\n\n"
        f"👇 *Choose an option:*"
    )
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=main_menu_keyboard(user.id))


async def use_free_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    text = (
        f"📤 *USE FREE SUBSCRIBERS*\n\n"
        f"You have *{user_data['free_subs']} free subscribers* available.\n\n"
        f"To redeem them, please contact admin with your:\n"
        f"• Channel/Group link\n"
        f"• Number of subscribers to add\n\n"
        f"Admin: @{Config.ADMIN_USERNAME}"
    )
    buttons = [
        [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{Config.ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="free_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("account", my_account))

    handlers = {
        "free_menu":            free_menu,
        "paid_menu":            paid_menu,
        "referral_menu":        referral_menu,
        "my_account":           my_account,
        "orders":               orders_history,
        "help":                 help_menu,
        "main_menu":            main_menu,
        "task_subscribe":       task_subscribe,
        "check_task_progress":  check_task_progress,
        "get_referral":         get_referral,
        "use_free_subs":        use_free_subs,
        "leaderboard":          leaderboard,
        "admin_panel":          admin_panel,
        "admin_pending":        admin_pending_orders,
        "admin_broadcast":      admin_broadcast_start,
    }

    for data, handler in handlers.items():
        app.add_handler(CallbackQueryHandler(handler, pattern=f"^{data}$"))

    app.add_handler(CallbackQueryHandler(buy_package,    pattern=r"^buy_pkg_\d+$"))
    app.add_handler(CallbackQueryHandler(submit_payment, pattern=r"^submit_payment_\d+$"))
    app.add_handler(CallbackQueryHandler(approve_order,  pattern=r"^approve_order_\d+$"))
    app.add_handler(CallbackQueryHandler(reject_order,   pattern=r"^reject_order_\d+$"))

    app.add_handler(MessageHandler(
        filters.PHOTO & filters.ChatType.PRIVATE, handle_payment_photo
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, send_broadcast
    ))

    logger.info("🚀 Bot is running!")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
