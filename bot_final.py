"""
ربات فروشگاه کانفیگ تلگرام
"""

import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = "8873361153:AAHwPsFgrZoQcIyAPuYBQULuv5mJ3SKmQrA"
ADMIN_ID   = 8337667257

PRODUCTS = [
    {"id": "v2ray_1m", "name": "🚀 V2Ray — یک ماهه", "desc": "سرعت بالا | ترافیک نامحدود", "price": 50_000, "config": "کانفیگ-اول-اینجا"},
    {"id": "v2ray_3m", "name": "⚡ V2Ray — سه ماهه", "desc": "سرعت بالا | تخفیف ویژه", "price": 130_000, "config": "کانفیگ-دوم-اینجا"},
    {"id": "shadowsocks", "name": "🛡 Shadowsocks — یک ماهه", "desc": "پایدار و مطمئن", "price": 45_000, "config": "کانفیگ-سوم-اینجا"},
    {"id": "warp_plus", "name": "🌐 Warp+ — سه ماهه", "desc": "سرعت فوق‌العاده", "price": 80_000, "config": "کانفیگ-چهارم-اینجا"},
    {"id": "vip_bundle", "name": "💎 باندل VIP — شش ماهه", "desc": "دسترسی به همه سرورها", "price": 280_000, "config": "کانفیگ-پنجم-اینجا"},
]

PAYMENT_INFO = """
💳 *اطلاعات پرداخت*
🏦 بانک ملت
💳 شماره کارت: `6104-3378-XXXX-XXXX`
👤 به نام: نام صاحب کارت
⚠️ بعد از واریز، *رسید* یا *اسکرین‌شات* را ارسال کنید.
"""

ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def next_order_id():
    orders = load_orders()
    return f"ORD{len(orders) + 1:04d}"

SELECTING_PRODUCT, WAITING_RECEIPT = range(2)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛍 مشاهده محصولات", callback_data="show_products")],
        [InlineKeyboardButton("📦 سفارش‌های من", callback_data="my_orders")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
    ]
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n\nبه فروشگاه کانفیگ خوش آمدید.\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for p in PRODUCTS:
        keyboard.append([InlineKeyboardButton(f"{p['name']}  —  {p['price']:,} تومان", callback_data=f"buy_{p['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("📦 *محصولات موجود:*\n\nروی محصول مورد نظر کلیک کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_PRODUCT

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data.replace("buy_", "")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        await query.edit_message_text("❌ محصول یافت نشد.")
        return ConversationHandler.END
    context.user_data["selected_product"] = product
    text = f"*{product['name']}*\n\n📝 {product['desc']}\n\n💰 قیمت: *{product['price']:,} تومان*\n\nبرای خرید روی «ادامه» کلیک کنید:"
    keyboard = [
        [InlineKeyboardButton("✅ ادامه و پرداخت", callback_data="proceed_payment")],
        [InlineKeyboardButton("🔙 بازگشت به محصولات", callback_data="show_products")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_PRODUCT

async def proceed_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = context.user_data.get("selected_product")
    if not product:
        await query.edit_message_text("❌ لطفاً دوباره از منو محصول انتخاب کنید.")
        return ConversationHandler.END
    order_id = next_order_id()
    context.user_data["order_id"] = order_id
    orders = load_orders()
    orders[order_id] = {"order_id": order_id, "user_id": query.from_user.id, "user_name": query.from_user.full_name, "username": query.from_user.username, "product_id": product["id"], "product_name": product["name"], "price": product["price"], "status": "pending", "created_at": datetime.now().isoformat()}
    save_orders(orders)
    await query.edit_message_text(f"🧾 *شماره سفارش: `{order_id}`*\n\n" + PAYMENT_INFO + f"\n\n💰 مبلغ قابل پرداخت: *{product['price']:,} تومان*\n\n📸 بعد از پرداخت، رسید یا اسکرین‌شات را *همین‌جا* ارسال کنید:", parse_mode="Markdown")
    return WAITING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = context.user_data.get("order_id")
    product = context.user_data.get("selected_product")
    if not order_id or not product:
        await update.message.reply_text("❌ سفارشی یافت نشد. لطفاً /start را بزنید.")
        return ConversationHandler.END
    await update.message.reply_text(f"✅ رسید شما دریافت شد!\n\n🧾 شماره سفارش: `{order_id}`\n⏳ در حال بررسی توسط ادمین...\n\nپس از تأیید، کانفیگ برایتان ارسال می‌شود.", parse_mode="Markdown")
    admin_text = f"🔔 *سفارش جدید!*\n\n📋 شماره سفارش: `{order_id}`\n👤 کاربر: {user.full_name} (ID: `{user.id}`)\n🔗 یوزرنیم: @{user.username or 'ندارد'}\n📦 محصول: {product['name']}\n💰 مبلغ: {product['price']:,} تومان\n\nبرای تأیید یا رد سفارش:"
    admin_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید و ارسال کانفیگ", callback_data=f"admin_approve_{order_id}"), InlineKeyboardButton("❌ رد سفارش", callback_data=f"admin_reject_{order_id}")]])
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=admin_text, parse_mode="Markdown", reply_markup=admin_keyboard)
    elif update.message.document:
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=admin_text, parse_mode="Markdown", reply_markup=admin_keyboard)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text + f"\n\n📄 متن رسید:\n{update.message.text}", parse_mode="Markdown", reply_markup=admin_keyboard)
    return ConversationHandler.END

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ دسترسی ندارید.", show_alert=True)
        return
    order_id = query.data.replace("admin_approve_", "")
    orders = load_orders()
    order = orders.get(order_id)
    if not order:
        await query.edit_message_text("❌ سفارش یافت نشد.")
        return
    product = next((p for p in PRODUCTS if p["id"] == order["product_id"]), None)
    orders[order_id]["status"] = "approved"
    orders[order_id]["approved_at"] = datetime.now().isoformat()
    save_orders(orders)
    await context.bot.send_message(chat_id=order["user_id"], text=f"🎉 *سفارش شما تأیید شد!*\n\n🧾 شماره سفارش: `{order_id}`\n📦 محصول: {product['name']}\n\n🔑 *کانفیگ شما:*\n`{product['config']}`\n\nبرای راهنمای اتصال پیام دهید.", parse_mode="Markdown")
    try:
        await query.edit_message_caption(query.message.caption + "\n\n✅ *تأیید شد* — کانفیگ ارسال گردید.", parse_mode="Markdown")
    except:
        await query.edit_message_text(f"✅ سفارش `{order_id}` تأیید و کانفیگ ارسال شد.", parse_mode="Markdown")

async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ دسترسی ندارید.", show_alert=True)
        return
    order_id = query.data.replace("admin_reject_", "")
    orders = load_orders()
    order = orders.get(order_id)
    if not order:
        await query.edit_message_text("❌ سفارش یافت نشد.")
        return
    orders[order_id]["status"] = "rejected"
    orders[order_id]["rejected_at"] = datetime.now().isoformat()
    save_orders(orders)
    await context.bot.send_message(chat_id=order["user_id"], text=f"❌ *سفارش شما رد شد.*\n\n🧾 شماره سفارش: `{order_id}`\n\nاگر مشکلی پیش آمده، لطفاً با پشتیبانی تماس بگیرید.", parse_mode="Markdown")
    try:
        await query.edit_message_caption(query.message.caption + "\n\n❌ *رد شد.*", parse_mode="Markdown")
    except:
        await query.edit_message_text(f"❌ سفارش `{order_id}` رد شد.", parse_mode="Markdown")

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    orders = load_orders()
    my = [o for o in orders.values() if o["user_id"] == user_id]
    if not my:
        text = "📭 شما هنوز سفارشی ثبت نکرده‌اید."
    else:
        lines = ["📦 *سفارش‌های شما:*\n"]
        STATUS_EMOJI = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        for o in my[-5:]:
            em = STATUS_EMOJI.get(o["status"], "❓")
            lines.append(f"{em} `{o['order_id']}` — {o['product_name']}")
        text = "\n".join(lines)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await query.edit_message_text("📞 *پشتیبانی*\n\nبرای ارتباط با ما پیام دهید:\n@YourSupportUsername", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🛍 مشاهده محصولات", callback_data="show_products")],
        [InlineKeyboardButton("📦 سفارش‌های من", callback_data="my_orders")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
    ]
    await query.edit_message_text("منوی اصلی — یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد. برای شروع مجدد /start بزنید.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_products, pattern="^show_products$")],
        states={
            SELECTING_PRODUCT: [
                CallbackQueryHandler(product_detail, pattern="^buy_"),
                CallbackQueryHandler(proceed_payment, pattern="^proceed_payment$"),
                CallbackQueryHandler(show_products, pattern="^show_products$"),
            ],
            WAITING_RECEIPT: [
                MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT, receive_receipt),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^admin_approve_"))
    app.add_handler(CallbackQueryHandler(admin_reject, pattern="^admin_reject_"))
    app.add_handler(CallbackQueryHandler(my_orders, pattern="^my_orders$"))
    app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    print("✅ ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
