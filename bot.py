"""
🚀 Viral Subscriber Bot — Updated
Changes: USDT TRC20, Dollar rates, EasyPaisa name, Channel-join task
"""

import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from database import Database
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def pkr(amount):
    return f"Rs. {amount:,}"

def usd(amount):
    return f"${amount:.2f}"

def dual_price(pkg):
    return f"`{pkr(pkg['price_pkr'])}` (~{usd(pkg['price_usd'])})"


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

    if is_new and ref_code and ref_code.startswith("ref_"):
        try:
            referrer_id = int(ref_code.split("_")[1])
            if referrer_id != user.id:
                db.add_free_subscribers(referrer_id, Config.REFERRAL_REWARD)
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 *Mubarak Ho!* Aapka referral join ho gaya!\n"
                        f"✅ *{Config.REFERRAL_REWARD} Free Subscribers* aapke account mein add ho gaye!"
                    ),
                    parse_mode='Markdown'
                )
        except Exception:
            pass

    user_data = db.get_user(user.id)
    text = (
        f"🌟 *Welcome, {user.first_name}!*\n\n"
        f"🤖 *Subscriber Bot* mein khush amdeed!\n"
        f"Apna YouTube channel fast grow karo!\n\n"
        f"📊 *Aapka Account:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"├ 💎 Paid Subscribers: `{user_data['paid_subs']}`\n"
        f"├ 👥 Referrals: `{user_data['referrals']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"👇 *Neeche se option select karo:*"
    )
    await update.message.reply_text(
        text, parse_mode='Markdown',
        reply_markup=main_menu_keyboard(user.id)
    )


def main_menu_keyboard(user_id):
    is_admin = user_id in Config.ADMIN_IDS
    buttons = [
        [InlineKeyboardButton("🆓 Free Subscribers",  callback_data="free_menu"),
         InlineKeyboardButton("💎 Paid Subscribers",  callback_data="paid_menu")],
        [InlineKeyboardButton("👥 Referral System",   callback_data="referral_menu"),
         InlineKeyboardButton("📊 My Account",        callback_data="my_account")],
        [InlineKeyboardButton("📋 Order History",     callback_data="orders"),
         InlineKeyboardButton("ℹ️ Help",              callback_data="help")],
        [InlineKeyboardButton("💱 Dollar Rate",       callback_data="dollar_rate")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)


# ─── DOLLAR RATE INFO ──────────────────────────────────────────────────────────
async def dollar_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        f"💱 *CURRENT DOLLAR RATE*\n\n"
        f"🇺🇸 1 USD = `Rs. {Config.USD_TO_PKR}`\n\n"
        f"Tamam packages ka price PKR aur USD dono mein show hota hai.\n"
        f"USDT payment ke liye dollar wala amount bhejein.\n\n"
        f"_Rate time ke sath change ho sakta hai_"
    )
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── FREE SUBSCRIBERS MENU ─────────────────────────────────────────────────────
async def free_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = db.get_user(query.from_user.id)

    text = (
        f"🆓 *FREE SUBSCRIBER SYSTEM*\n\n"
        f"📌 *Free Subscribers kaise milenge?*\n\n"
        f"*Method 1 — Channel Task:*\n"
        f"├ {Config.TASK_REQUIRED} channels join karo\n"
        f"└ *{Config.TASK_REWARD} Free Subscribers* milenge! 🎁\n\n"
        f"*Method 2 — Referral:*\n"
        f"├ Apna referral link share karo\n"
        f"└ Har new user = *{Config.REFERRAL_REWARD} Free Subscribers* 🔗\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Aapka Status:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"└ 👥 Total Referrals: `{user_data['referrals']}`"
    )
    buttons = [
        [InlineKeyboardButton(
            f"✅ {Config.TASK_REQUIRED} Channels Join → {Config.TASK_REWARD} Free Subs",
            callback_data="task_channels"
        )],
        [InlineKeyboardButton("🔗 Referral Link Lo",    callback_data="get_referral")],
        [InlineKeyboardButton("📤 Free Subs Redeem Karo", callback_data="use_free_subs")],
        [InlineKeyboardButton("🔙 Back",                callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── CHANNEL JOIN TASK ─────────────────────────────────────────────────────────
async def task_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    channels = Config.TASK_CHANNELS

    # Channels abhi set nahi hue — coming soon message
    if not channels:
        await query.edit_message_text(
            "⏳ *Channel Task Coming Soon!*\n\n"
            "Abhi yeh feature available nahi hai.\n"
            "Referral system se free subscribers earn karo! 🔗",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Referral Link Lo", callback_data="get_referral")],
                [InlineKeyboardButton("🔙 Back", callback_data="free_menu")],
            ])
        )
        return

    text = (
        f"📋 *CHANNEL TASK*\n\n"
        f"🎯 *Neeche diye {Config.TASK_REQUIRED} channels join karo*\n"
        f"Phir ✅ *Check karo* button dabao — *{Config.TASK_REWARD} free subscribers* milenge!\n\n"
    )
    for i, ch in enumerate(channels, 1):
        text += f"{i}. @{ch['username']} — *{ch['name']}*\n"

    text += f"\n⚠️ *Sabhi channels join karne zaroori hain*"

    buttons = []
    row = []
    for i, ch in enumerate(channels):
        row.append(InlineKeyboardButton(
            f"📢 {ch['name'][:18]}",
            url=f"https://t.me/{ch['username']}"
        ))
        if len(row) == 2 or i == len(channels) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(
        "✅ Maine Sab Join Kar Liye — Check Karo!",
        callback_data="check_channels"
    )])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="free_menu")])

    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Check ho raha hai...")
    user_id = query.from_user.id
    channels = Config.TASK_CHANNELS

    not_joined = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception:
            # If bot is not in channel or can't check, skip
            not_joined.append(ch)

    if not_joined:
        missing_text = "\n".join([f"❌ @{ch['username']} — {ch['name']}" for ch in not_joined])
        text = (
            f"⚠️ *Aap yeh channels join nahi kiye:*\n\n"
            f"{missing_text}\n\n"
            f"Sab join karke dobara check karo!"
        )
        buttons = [
            [InlineKeyboardButton("🔙 Channels Dekhain", callback_data="task_channels")]
        ]
        await query.edit_message_text(text, parse_mode='Markdown',
                                       reply_markup=InlineKeyboardMarkup(buttons))
        return

    # All joined — award reward
    task_status = db.get_task_status(user_id)
    if task_status.get("completed", 0) > 0:
        text = (
            f"✅ *Aap pehle hi yeh task kar chuke hain!*\n\n"
            f"Referral system se aur subscribers earn karo! 🔗"
        )
    else:
        db.complete_task(user_id)
        text = (
            f"🎉 *TASK COMPLETE!*\n\n"
            f"✅ Aapne tamam {Config.TASK_REQUIRED} channels join kar liye!\n"
            f"🎁 *{Config.TASK_REWARD} Free Subscribers* aapke account mein add!\n\n"
            f"Referral link share karo aur aur earn karo! 🚀"
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
    ref_link  = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"🔗 *REFERRAL SYSTEM*\n\n"
        f"💰 *Har referral par earn karo:*\n"
        f"└ New user join kare → *{Config.REFERRAL_REWARD} Free Subscribers*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Aapki Stats:*\n"
        f"├ 👥 Total Referrals: `{user_data['referrals']}`\n"
        f"├ 🆓 Free Subs Earned: `{user_data['free_subs']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"🔗 *Aapka Personal Link:*\n"
        f"`{ref_link}`"
    )
    buttons = [
        [InlineKeyboardButton("📤 WhatsApp Share",
                               url=f"https://wa.me/?text=🚀 Free subscribers lo! {ref_link}"),
         InlineKeyboardButton("📢 Telegram Share",
                               url=f"https://t.me/share/url?url={ref_link}&text=🚀+Free+Subscribers!")],
        [InlineKeyboardButton("🏆 Leaderboard",   callback_data="leaderboard")],
        [InlineKeyboardButton("🔙 Back",          callback_data="main_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def get_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id  = query.from_user.id
    ref_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"🔗 *AAPKA REFERRAL LINK*\n\n"
        f"`{ref_link}`\n\n"
        f"💰 Har referral: *{Config.REFERRAL_REWARD} Free Subscribers*\n\n"
        f"📤 *Yahan share karo:*\n"
        f"• WhatsApp groups\n"
        f"• Telegram channels\n"
        f"• Facebook / Instagram\n\n"
        f"Jitne zyada share — utna zyada earn! 🚀"
    )
    buttons = [
        [InlineKeyboardButton("📤 WhatsApp",
                               url=f"https://wa.me/?text=🚀 Join karo aur free subscribers pao! {ref_link}"),
         InlineKeyboardButton("📢 Telegram",
                               url=f"https://t.me/share/url?url={ref_link}&text=🚀+Free+Subscribers!")],
        [InlineKeyboardButton("🔙 Back", callback_data="referral_menu")],
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
        name = (u['full_name'] or "User")[:15]
        text += f"{medals[i]} *{name}* — `{u['referrals']}` referrals\n"

    text += "\n💪 Zyada refer karo, leaderboard par aao!"
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
        f"✅ 100% Real & Genuine\n"
        f"✅ Fast Delivery\n"
        f"✅ No Drop Guarantee\n"
        f"💱 Rate: 1 USD = Rs. {Config.USD_TO_PKR}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Available Packages:*\n\n"
    )

    buttons = []
    for pkg in packages:
        text += (
            f"*{pkg['name']}*\n"
            f"├ 👥 Subscribers: `{pkg['subs']:,}`\n"
            f"├ 💰 Price: {dual_price(pkg)}\n"
            f"└ ⚡ Delivery: `{pkg['delivery']}`\n\n"
        )
        buttons.append([InlineKeyboardButton(
            f"🛒 {pkg['name']} — {pkr(pkg['price_pkr'])} / {usd(pkg['price_usd'])}",
            callback_data=f"buy_pkg_{pkg['id']}"
        )])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def buy_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pkg_id = int(query.data.split("_")[-1])
    pkg    = db.get_package(pkg_id)

    text = (
        f"🛒 *ORDER CONFIRM KARO*\n\n"
        f"📦 Package: *{pkg['name']}*\n"
        f"👥 Subscribers: `{pkg['subs']:,}`\n"
        f"💰 Price: {dual_price(pkg)}\n"
        f"⚡ Delivery: `{pkg['delivery']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 *Payment Options:*\n\n"
        f"🟢 *EasyPaisa:*\n"
        f"├ Number: `{Config.EASYPAISA_NUM}`\n"
        f"└ Name: *{Config.EASYPAISA_NAME}*\n\n"
        f"🔵 *JazzCash:*\n"
        f"├ Number: `{Config.JAZZCASH_NUM}`\n"
        f"└ Name: *{Config.JAZZCASH_NAME}*\n\n"
        f"🟡 *USDT TRC20:*\n"
        f"└ `{Config.USDT_TRC20}`\n"
        f"   Amount: `{usd(pkg['price_usd'])}`\n\n"
        f"📸 *Payment karo phir screenshot bhejo!*"
    )

    buttons = [
        [InlineKeyboardButton("📱 EasyPaisa / JazzCash", callback_data=f"pay_pkr_{pkg_id}"),
         InlineKeyboardButton("🟡 USDT TRC20",          callback_data=f"pay_usdt_{pkg_id}")],
        [InlineKeyboardButton("💬 Contact Admin",       url=f"https://t.me/{Config.ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Back",                callback_data="paid_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def pay_pkr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    pkg_id = int(query.data.split("_")[-1])
    pkg    = db.get_package(pkg_id)
    context.user_data['pending_pkg']    = pkg_id
    context.user_data['pending_method'] = 'easypaisa'

    text = (
        f"📱 *EASYPAISA / JAZZCASH PAYMENT*\n\n"
        f"💰 Amount: `{pkr(pkg['price_pkr'])}`\n\n"
        f"🟢 *EasyPaisa:* `{Config.EASYPAISA_NUM}`\n"
        f"   Name: *{Config.EASYPAISA_NAME}*\n\n"
        f"🔵 *JazzCash:* `{Config.JAZZCASH_NUM}`\n"
        f"   Name: *{Config.JAZZCASH_NAME}*\n\n"
        f"📸 *Payment karo aur screenshot yahan bhejo 👇*"
    )
    buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="paid_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def pay_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    pkg_id = int(query.data.split("_")[-1])
    pkg    = db.get_package(pkg_id)
    context.user_data['pending_pkg']    = pkg_id
    context.user_data['pending_method'] = 'usdt'

    text = (
        f"🟡 *USDT TRC20 PAYMENT*\n\n"
        f"💰 Amount: `{usd(pkg['price_usd'])}` USDT\n\n"
        f"📍 *Wallet Address (TRC20):*\n"
        f"`{Config.USDT_TRC20}`\n\n"
        f"⚠️ *Sirf TRC20 network use karo!*\n"
        f"ERC20 ya koi aur network mat use karna.\n\n"
        f"📸 *Transaction screenshot yahan bhejo 👇*"
    )
    buttons = [[InlineKeyboardButton("❌ Cancel", callback_data="paid_menu")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def handle_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'pending_pkg' not in context.user_data:
        return

    user       = update.effective_user
    pkg_id     = context.user_data['pending_pkg']
    pay_method = context.user_data.get('pending_method', 'easypaisa')
    pkg        = db.get_package(pkg_id)
    order_id   = db.create_order(user.id, pkg_id, pay_method)

    method_label = "USDT TRC20" if pay_method == 'usdt' else "EasyPaisa/JazzCash"
    price_label  = usd(pkg['price_usd']) if pay_method == 'usdt' else pkr(pkg['price_pkr'])

    for admin_id in Config.ADMIN_IDS:
        try:
            caption = (
                f"💰 *NEW ORDER!*\n\n"
                f"👤 User: {user.full_name} (@{user.username or 'N/A'})\n"
                f"🆔 ID: `{user.id}`\n"
                f"📦 Package: {pkg['name']}\n"
                f"👥 Subscribers: {pkg['subs']:,}\n"
                f"💳 Method: *{method_label}*\n"
                f"💰 Amount: {price_label}\n"
                f"🔢 Order ID: #{order_id}"
            )
            await context.bot.forward_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await context.bot.send_message(
                chat_id=admin_id, text=caption,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_order_{order_id}"),
                    InlineKeyboardButton("❌ Reject",  callback_data=f"reject_order_{order_id}")
                ]])
            )
        except Exception as e:
            logger.error(f"Admin notify error: {e}")

    await update.message.reply_text(
        f"✅ *Payment Screenshot Receive Ho Gaya!*\n\n"
        f"🔢 Order ID: `#{order_id}`\n"
        f"⏰ 1–2 ghante mein process hoga.\n\n"
        f"Admin approve karne par notification aayega!",
        parse_mode='Markdown'
    )
    context.user_data.pop('pending_pkg', None)
    context.user_data.pop('pending_method', None)


# ─── MY ACCOUNT ────────────────────────────────────────────────────────────────
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    user_data = db.get_user(user_id)
    ref_link  = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"

    text = (
        f"👤 *MY ACCOUNT*\n\n"
        f"📛 Name: *{user_data['full_name']}*\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Joined: `{user_data['joined_date']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Statistics:*\n"
        f"├ 🆓 Free Subscribers: `{user_data['free_subs']}`\n"
        f"├ 💎 Paid Subscribers: `{user_data['paid_subs']}`\n"
        f"├ 👥 Referrals: `{user_data['referrals']}`\n"
        f"└ 🏆 Total Earned: `{user_data['total_earned']}`\n\n"
        f"🔗 *Referral Link:*\n"
        f"`{ref_link}`"
    )
    buttons = [
        [InlineKeyboardButton("📋 Order History",    callback_data="orders")],
        [InlineKeyboardButton("🔗 Referral Link",    callback_data="get_referral")],
        [InlineKeyboardButton("🔙 Back",             callback_data="main_menu")],
    ]
    kb = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)


async def orders_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    orders  = db.get_user_orders(user_id)

    if not orders:
        text = "📋 *ORDER HISTORY*\n\nAbhi tak koi order nahi!\n\n💎 Paid packages dekhain!"
    else:
        text = "📋 *ORDER HISTORY*\n\n"
        for o in orders[-10:]:
            emoji  = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(o['status'], "❓")
            method = "🟡 USDT" if o['pay_method'] == 'usdt' else "📱 PKR"
            price  = usd(o['price_usd']) if o['pay_method'] == 'usdt' else pkr(o['price_pkr'])
            text += (
                f"{emoji} Order `#{o['id']}`\n"
                f"├ {o['pkg_name']}\n"
                f"├ {method}: {price}\n"
                f"├ Status: *{o['status'].upper()}*\n"
                f"└ {o['created_at']}\n\n"
            )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="my_account")]]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


async def use_free_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = db.get_user(query.from_user.id)

    text = (
        f"📤 *FREE SUBSCRIBERS USE KARO*\n\n"
        f"Aapke paas *{user_data['free_subs']} free subscribers* hain.\n\n"
        f"Redeem karne ke liye admin ko bhejain:\n"
        f"• Apne channel/group ka link\n"
        f"• Kitne subscribers add karne hain\n\n"
        f"Admin: @{Config.ADMIN_USERNAME}"
    )
    buttons = [
        [InlineKeyboardButton("💬 Admin Se Contact Karo", url=f"https://t.me/{Config.ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Back", callback_data="free_menu")],
    ]
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=InlineKeyboardMarkup(buttons))


# ─── HELP ──────────────────────────────────────────────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        f"ℹ️ *HELP & GUIDE*\n\n"
        f"*Free Subscribers kaise milein?*\n"
        f"1. {Config.TASK_REQUIRED} channels join karo → {Config.TASK_REWARD} free subs\n"
        f"2. Referral link share karo → har user = {Config.REFERRAL_REWARD} subs\n\n"
        f"*Paid Subscribers kya hain?*\n"
        f"Real genuine subscribers aapke channel mein add hote hain.\n\n"
        f"*Payment Methods:*\n"
        f"📱 EasyPaisa / JazzCash\n"
        f"🟡 USDT TRC20 (crypto)\n\n"
        f"*Dollar Rate:* 1 USD = Rs. {Config.USD_TO_PKR}\n\n"
        f"*Help chahiye?*\n"
        f"Admin: @{Config.ADMIN_USERNAME}"
    )
    buttons = [
        [InlineKeyboardButton("💬 Admin", url=f"https://t.me/{Config.ADMIN_USERNAME}"),
         InlineKeyboardButton("🔙 Back",  callback_data="main_menu")]
    ]
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
        f"├ 🆕 Aaj Join: `{stats['today_users']}`\n"
        f"├ 💎 Total Orders: `{stats['total_orders']}`\n"
        f"├ ⏳ Pending Orders: `{stats['pending_orders']}`\n"
        f"└ 💰 Total Revenue: `{pkr(stats['total_revenue'])}`\n\n"
        f"💱 Dollar Rate: 1 USD = Rs. {Config.USD_TO_PKR}"
    )
    buttons = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton("⏳ Pending",   callback_data="admin_pending")],
        [InlineKeyboardButton("🔙 Back",      callback_data="main_menu")],
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
        await query.edit_message_text(
            "✅ Koi pending orders nahi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
        return

    await query.edit_message_text(f"⏳ *{len(orders)} Pending Orders:*",
                                   parse_mode='Markdown')
    for o in orders[:5]:
        method = "🟡 USDT" if o['pay_method'] == 'usdt' else "📱 PKR"
        price  = usd(o['price_usd']) if o['pay_method'] == 'usdt' else pkr(o['price_pkr'])
        text = (
            f"⏳ *ORDER #{o['id']}*\n\n"
            f"👤 {o['full_name']} (ID: `{o['user_id']}`)\n"
            f"📦 {o['pkg_name']} — {o['subs']:,} subs\n"
            f"💳 {method}: {price}\n"
            f"📅 {o['created_at']}"
        )
        await query.message.reply_text(
            text, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_order_{o['id']}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"reject_order_{o['id']}")
            ]])
        )


async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    order_id = int(query.data.split("_")[-1])
    order    = db.approve_order(order_id)

    try:
        await context.bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"🎉 *ORDER APPROVE HO GAYA!*\n\n"
                f"✅ Order `#{order_id}` approve!\n"
                f"📦 {order['pkg_name']}\n"
                f"👥 {order['subs']:,} subscribers jald add honge!\n\n"
                f"Shukriya! 🙏"
            ),
            parse_mode='Markdown'
        )
    except Exception:
        pass

    await query.edit_message_text(f"✅ Order #{order_id} Approved!")


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    order_id = int(query.data.split("_")[-1])
    order    = db.get_order(order_id)
    db.reject_order(order_id)

    try:
        await context.bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"❌ *Order Reject Ho Gaya*\n\n"
                f"Order `#{order_id}` reject hua.\n"
                f"Help ke liye admin se contact karo: @{Config.ADMIN_USERNAME}"
            ),
            parse_mode='Markdown'
        )
    except Exception:
        pass

    await query.edit_message_text(f"❌ Order #{order_id} Rejected!")


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in Config.ADMIN_IDS:
        return

    context.user_data['awaiting_broadcast'] = True
    await query.edit_message_text(
        "📢 *BROADCAST*\n\nJo message sab users ko bhejna hai woh type karo:",
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

    message  = update.message.text
    users    = db.get_all_users()
    sent     = 0
    failed   = 0
    status   = await update.message.reply_text("📢 Broadcasting...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 *ANNOUNCEMENT*\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status.edit_text(f"✅ *Broadcast Complete!*\n\n✅ Sent: {sent}\n❌ Failed: {failed}")
    context.user_data['awaiting_broadcast'] = False


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user  = query.from_user
    ud    = db.get_user(user.id)

    text = (
        f"🌟 *Main Menu*\n\n"
        f"├ 🆓 Free: `{ud['free_subs']}`\n"
        f"├ 💎 Paid: `{ud['paid_subs']}`\n"
        f"└ 👥 Referrals: `{ud['referrals']}`\n\n"
        f"👇 Option select karo:"
    )
    await query.edit_message_text(text, parse_mode='Markdown',
                                   reply_markup=main_menu_keyboard(user.id))


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("account", my_account))

    simple = {
        "free_menu":       free_menu,
        "paid_menu":       paid_menu,
        "referral_menu":   referral_menu,
        "my_account":      my_account,
        "orders":          orders_history,
        "help":            help_menu,
        "main_menu":       main_menu,
        "task_channels":   task_channels,
        "check_channels":  check_channels,
        "get_referral":    get_referral,
        "use_free_subs":   use_free_subs,
        "leaderboard":     leaderboard,
        "admin_panel":     admin_panel,
        "admin_pending":   admin_pending_orders,
        "admin_broadcast": admin_broadcast_start,
        "dollar_rate":     dollar_rate,
    }
    for data, fn in simple.items():
        app.add_handler(CallbackQueryHandler(fn, pattern=f"^{data}$"))

    app.add_handler(CallbackQueryHandler(buy_package,    pattern=r"^buy_pkg_\d+$"))
    app.add_handler(CallbackQueryHandler(pay_pkr,        pattern=r"^pay_pkr_\d+$"))
    app.add_handler(CallbackQueryHandler(pay_usdt,       pattern=r"^pay_usdt_\d+$"))
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
