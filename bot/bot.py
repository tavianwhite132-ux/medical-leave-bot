import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

# قراءة الإعدادات من متغيرات البيئة (لـ Render) أو استخدام القيم الافتراضية (للتشغيل المحلي)
API_URL = os.environ.get("API_URL", "http://localhost:5000/create-leave")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "MySecretKey2024")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8810255564:AAGSe6JspZLPmN8dbLbDFlL1rzZhofrxEpM")

NAME_AR, NAME_EN, NATIONAL_ID, HOSPITAL, DOCTOR_AR, DOCTOR_EN, DATE_G, DATE_H = range(8)

user_data = {}

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
            response = requests.get(f"http://localhost:5000/points/{query.from_user.id}")
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
        response = requests.post(API_URL, json=user_data[uid], headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            pdf_path = result.get('document_path', '')
            
            # التحقق من وجود ملف PDF
            if pdf_path and os.path.exists(pdf_path) and pdf_path.endswith('.pdf'):
                with open(pdf_path, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"medical_leave_{result['national_id']}.pdf",
                        caption=f"✅ تم إنشاء الإجازة بنجاح!\n\n"
                                f"📄 رقم الهوية: {result['national_id']}\n"
                                f"💰 النقاط المتبقية: {result['remaining_points']}"
                    )
            else:
                # إذا لم يوجد ملف PDF، حاول البحث عن ملف Word
                word_path = pdf_path.replace('.pdf', '.docx') if pdf_path else None
                if word_path and os.path.exists(word_path):
                    with open(word_path, 'rb') as word_file:
                        await update.message.reply_document(
                            document=word_file,
                            filename=f"medical_leave_{result['national_id']}.docx",
                            caption=f"✅ تم إنشاء الإجازة بنجاح!\n\n"
                                    f"📄 رقم الهوية: {result['national_id']}\n"
                                    f"💰 النقاط المتبقية: {result['remaining_points']}\n\n"
                                    f"⚠️ تم إرسال الملف بصيغة Word (PDF غير متوفر)"
                        )
                else:
                    await update.message.reply_text(
                        f"✅ تم إنشاء الإجازة!\n\n"
                        f"📄 رقم الهوية: {result['national_id']}\n"
                        f"💰 النقاط المتبقية: {result['remaining_points']}\n\n"
                        f"📁 الملف موجود على الخادم: {pdf_path}"
                    )
        else:
            error = response.json().get('error', 'خطأ غير معروف')
            await update.message.reply_text(f"❌ فشل: {error}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("❌ تم الإلغاء")
    return ConversationHandler.END

def main():
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
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()