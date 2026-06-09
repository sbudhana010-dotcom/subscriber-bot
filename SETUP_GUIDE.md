# 🚀 Subscriber Bot — Setup Guide

## Step 1: Create Your Bot on Telegram
1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Enter a name (e.g. `Subscriber Pro Bot`)
4. Enter a username ending in `bot` (e.g. `SubscriberProBot`)
5. Copy the **API Token** you receive

---

## Step 2: Get Your Telegram User ID
1. Open Telegram → search **@userinfobot**
2. Send `/start`
3. Copy your **ID number**

---

## Step 3: Edit config.py
Open `config.py` and fill in:

```python
BOT_TOKEN      = "paste your token here"
BOT_USERNAME   = "YourBotUsername"   # without @
ADMIN_IDS      = [123456789]         # your ID number
ADMIN_USERNAME = "YourUsername"      # without @
EASYPAISA_NUM  = "0300-XXXXXXX"
JAZZCASH_NUM   = "0300-XXXXXXX"
BANK_ACCOUNT   = "Bank Name: Account Number"
```

---

## Step 4: Install & Run

### Option A — Run on your PC/Laptop
```bash
# Install Python 3.10+ first from python.org

# Install dependencies
pip install python-telegram-bot==20.7

# Run the bot
python bot.py
```

### Option B — Run 24/7 on a Server (Recommended)
Use any cheap VPS (DigitalOcean, Hostinger VPS, etc.)
```bash
pip install python-telegram-bot==20.7
nohup python bot.py &    # runs in background
```

---

## Step 5: Edit Package Prices
Open `database.py` and find this section to change prices:

```python
("🥉 Starter Pack",   100,   200,  "1-2 Hours"),
("🥈 Basic Pack",     500,   800,  "2-4 Hours"),
("🥇 Standard Pack", 1000,  1400,  "4-6 Hours"),
("💎 Premium Pack",  5000,  5500,  "1 Day"),
("👑 VIP Pack",     10000, 10000,  "1-2 Days"),
#  ^ name           ^ subs ^ price ^ delivery time
```

---

## Bot Features Summary

| Feature | Details |
|---|---|
| Free Subscribers | Invite 10 people → Get 5 free subs |
| Referral System | Each referral = 2 free subscribers |
| Paid Packages | 5 packages, prices editable |
| Payment | EasyPaisa / JazzCash / Bank |
| Admin Panel | Stats, broadcast, approve orders |
| Leaderboard | Top referrers ranking |
| Viral Design | Every user auto-promotes the bot |

---

## Files Overview
```
telegram_bot/
├── bot.py          ← Main bot logic
├── database.py     ← All data storage (SQLite)
├── config.py       ← YOUR SETTINGS GO HERE
└── requirements.txt
```

---

## 💡 Tips to Make Your Bot Go Viral
1. Make a short video showing the bot working
2. Share in WhatsApp groups & Telegram channels
3. The referral system does the rest automatically!
