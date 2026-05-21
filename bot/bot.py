import os
import requests
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

# Flask app for webhook
flask_app = Flask(__name__)

# Telegram bot
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "MySecretKey2024")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

NAME_AR, NAME_EN, NATIONAL_ID, HOSPITAL, DOCTOR_AR, DOCTOR_EN, DATE_G, DATE_H = range(8)
user_data = {}

# ==================== دوال البوت ====================
async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton("📝 إجازة جديدة", callback_data="new_leave")],
                [InlineKeyboardButton("💰 رصيد النقاط", callback_data="points")],
                [InlineKeyboardButton("❓ المساعدة", callback_data="help")]]
    await update.message.reply_text("🏥 مرحبا بك في نظام الإجازات المرضية\n\nاختر أحد الخيارات:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "new_leave":
        await query.edit_message_text("📝 أدخل اسم المريض بالعربي:")
        return NAME_AR
    elif query.data == "points":
        try:
            response = requests.get(f"https://medical-leave-bot.onrender.com/points/{query.from_user.id}")
            if response.status_code == 200:
                await query.edit_message_text(f"💰 رصيدك: {response.json()['points']} نقطة")
            else:
                await query.edit_message_text("⚠️ خطأ في جلب الرصيد")
        except:
            await query.edit_message_text("❌ خطأ في الاتصال")
        return ConversationHandler.END
    elif query.data == "help":
        await query.edit_message_text("📋 أرسل /start للبدء")
        return ConversationHandler.END

async def name_ar(update: Update, context):
    uid = update.effective_user.id
    user_data[uid] = {"telegram_id": uid, "full_name": update.effective_user.full_name}
    user_data[uid]["name_ar"] = update.message.text
    await update.message.reply_text("📝 أدخل الاسم بالإنجليزي:")
    return NAME_EN

async def name_en(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["name_en"] = update.message.text
    await update.message.reply_text("🆔 أدخل رقم الهوية:")
    return NATIONAL_ID

async def national_id(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["national_id"] = update.message.text
    await update.message.reply_text("🏥 أدخل اسم المستشفى:")
    return HOSPITAL

async def hospital(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["hospital"] = update.message.text
    await update.message.reply_text("👨‍⚕️ أدخل اسم الطبيب بالعربي:")
    return DOCTOR_AR

async def doctor_ar(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["doctor_ar"] = update.message.text
    await update.message.reply_text("👨‍⚕️ أدخل اسم الطبيب بالإنجليزي:")
    return DOCTOR_EN

async def doctor_en(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["doctor_en"] = update.message.text
    await update.message.reply_text("📅 أدخل التاريخ الميلادي (مثال: 2024-01-15):")
    return DATE_G

async def date_g(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["date_g"] = update.message.text
    await update.message.reply_text("📅 أدخل التاريخ الهجري (مثال: 1445-06-03):")
    return DATE_H

async def date_h(update: Update, context):
    uid = update.effective_user.id
    user_data[uid]["date_h"] = update.message.text
    await update.message.reply_text("⏳ جاري إنشاء الإجازة...")
    try:
        headers = {"Authorization": f"Bearer {API_SECRET_KEY}"}
        response = requests.post("https://medical-leave-bot.onrender.com/create-leave", json=user_data[uid], headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            await update.message.reply_text(f"✅ تم إنشاء الإجازة!\n📄 رقم الهوية: {result['national_id']}\n💰 النقاط المتبقية: {result['remaining_points']}")
        else:
            error = response.json().get('error', 'خطأ غير معروف')
            await update.message.reply_text(f"❌ فشل: {error}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("❌ تم الإلغاء")
    return ConversationHandler.END

# ==================== إعداد التطبيق ====================
def setup_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^new_leave$")],
        states={NAME_AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_ar)],
                NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_en)],
                NATIONAL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, national_id)],
                HOSPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, hospital)],
                DOCTOR_AR: [MessageHandler(filters.TEXT & ~filters.COMMAND, doctor_ar)],
                DOCTOR_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, doctor_en)],
                DATE_G: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_g)],
                DATE_H: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_h)]},
        fallbacks=[CommandHandler("cancel", cancel)])
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(points|help)$"))
    app.add_handler(conv_handler)
    return app

# ==================== Flask webhook endpoint ====================
@flask_app.route("/", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "Bot is running"})
    
    try:
        update = Update.de_json(request.get_json(force=True), setup_bot().bot)
        setup_bot().process_update(update)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@flask_app.route("/points/<int:telegram_id>")
def points(telegram_id):
    # TODO: Connect to database
    return jsonify({"telegram_id": telegram_id, "points": 5})

@flask_app.route("/create-leave", methods=["POST"])
def create_leave_endpoint():
    # TODO: Connect to database
    return jsonify({"success": True, "document_path": "", "remaining_points": 4, "national_id": "123"})

if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port=5000)