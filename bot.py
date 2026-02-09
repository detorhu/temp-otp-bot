import random
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ================== TEMP DATABASE ==================
users = {}
numbers = {
    "IN": {"number": "+91 9835765310", "price": 10, "points": 10},
    "US": {"number": "+1 805-861-1180", "price": 15, "points": 15}
}
# ==================================================

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "points": 0,
            "number": None,
            "deposit": 0
        }
    return users[uid]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    text = (
        "📲 *Virtual Number OTP Bot*\n\n"
        "This bot provides virtual numbers for OTP verification, "
        "allowing users to receive verification codes quickly and easily.\n\n"
        "Use the buttons below to continue."
    )

    kb = [
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📲 Buy Numbers", callback_data="buy")],
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="refer")]
    ]

    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

# ================= PROFILE =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    u = get_user(q.from_user.id)

    text = (
        f"👤 *Your Profile*\n\n"
        f"💰 Balance: {u['balance']}\n"
        f"🎁 Points: {u['points']}\n"
        f"📱 Active Number: {u['number'] or 'None'}\n"
        f"💳 Total Deposit: {u['deposit']}"
    )

    await q.answer()
    await q.edit_message_text(text, parse_mode="Markdown")

# ================= BUY =================
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    kb = []

    for c, d in numbers.items():
        flag = "🇮🇳" if c == "IN" else "🇺🇸"
        kb.append([
            InlineKeyboardButton(
                f"{flag} {c} - ₹{d['price']} / {d['points']} pts",
                callback_data=f"select_{c}"
            )
        ])

    await q.answer()
    await q.edit_message_text(
        "📲 *Choose a number:*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def confirm_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    country = q.data.split("_")[1]
    context.user_data["buy"] = country

    kb = [
        [InlineKeyboardButton("✅ Buy Number", callback_data="buy_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="start")]
    ]

    await q.answer()
    await q.edit_message_text(
        f"Confirm purchase for {country} number?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    u = get_user(uid)
    c = context.user_data["buy"]

    u["number"] = numbers[c]["number"]

    kb = [
        [InlineKeyboardButton("📩 Get OTP", callback_data="otp")]
    ]

    await q.answer()
    await q.edit_message_text(
        f"✅ *Number Purchased*\n\n📱 `{u['number']}`",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# ================= OTP =================
async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    otp = random.randint(100000, 999999)

    await q.answer()
    await q.edit_message_text(
        f"📩 *Your OTP*\n\n`{otp}`",
        parse_mode="Markdown"
    )

# ================= DEPOSIT =================
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    text = (
        "💰 *Deposit Balance*\n\n"
        "Pay via UPI:\n"
        "`yourupi@upi`\n\n"
        "After payment, click *I Have Paid*"
    )

    kb = [
        [InlineKeyboardButton("✅ I Have Paid", callback_data="paid")]
    ]

    await q.answer()
    await q.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("📸 Please send payment screenshot.")

    context.user_data["awaiting_ss"] = True

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_ss"):
        await context.bot.forward_message(
            ADMIN_ID,
            update.message.chat_id,
            update.message.message_id
        )
        await update.message.reply_text(
            "✅ Screenshot sent to admin. Waiting for approval."
        )
        context.user_data["awaiting_ss"] = False

# ================= REFER =================
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    link = f"https://t.me/{context.bot.username}?start={uid}"

    await q.answer()
    await q.edit_message_text(
        f"🎁 *Refer & Earn*\n\n"
        f"1 Referral = 1 Point\n\n"
        f"Your link:\n{link}",
        parse_mode="Markdown"
    )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(profile, pattern="profile"))
    app.add_handler(CallbackQueryHandler(buy_menu, pattern="buy"))
    app.add_handler(CallbackQueryHandler(confirm_buy, pattern="select_"))
    app.add_handler(CallbackQueryHandler(buy_confirm, pattern="buy_confirm"))
    app.add_handler(CallbackQueryHandler(get_otp, pattern="otp"))
    app.add_handler(CallbackQueryHandler(deposit, pattern="deposit"))
    app.add_handler(CallbackQueryHandler(paid, pattern="paid"))
    app.add_handler(CallbackQueryHandler(refer, pattern="refer"))
    app.add_handler(MessageHandler(filters.PHOTO, screenshot))

    app.run_polling()

if __name__ == "__main__":
    main()
