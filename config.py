"""
⚙️ Bot Configuration — Fill in your details here
"""

class Config:
    # ══════════════════════════════════════════════
    # 🤖 BOT SETTINGS — REQUIRED
    # ══════════════════════════════════════════════

    # Paste the token you got from @BotFather
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

    # Your bot's username (without @)
    BOT_USERNAME = "YourBotUsername"

    # ══════════════════════════════════════════════
    # 👑 ADMIN SETTINGS
    # ══════════════════════════════════════════════

    # Your Telegram User ID (get it from @userinfobot)
    # You can add multiple admin IDs separated by commas
    ADMIN_IDS = [123456789]  # <-- Put your ID here

    # Admin username (without @)
    ADMIN_USERNAME = "YourAdminUsername"

    # ══════════════════════════════════════════════
    # 💰 PAYMENT SETTINGS
    # ══════════════════════════════════════════════

    EASYPAISA_NUM = "0300-1234567"
    JAZZCASH_NUM  = "0300-1234567"
    BANK_ACCOUNT  = "HBL: 1234-5678-9012"

    # ══════════════════════════════════════════════
    # 🎁 REWARD SETTINGS
    # ══════════════════════════════════════════════

    # Free subscribers awarded per referral
    REFERRAL_REWARD = 2

    # Task reward: invite TASK_REQUIRED people → get TASK_REWARD free subs
    TASK_REWARD    = 5
    TASK_REQUIRED  = 10
