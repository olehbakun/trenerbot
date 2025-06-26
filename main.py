import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

(META, GENDER, AGE, WEIGHT, HEIGHT, LEVEL, MENU) = range(7)
user_data = {}

meta_keyboard = ReplyKeyboardMarkup([["💪 Набір маси", "⚖️ Схуднення", "🧩 Інше"]], resize_keyboard=True)
gender_keyboard = ReplyKeyboardMarkup([["👨 Чоловік", "👩 Жінка"]], resize_keyboard=True)
level_keyboard = ReplyKeyboardMarkup([["📗 Початковий", "📘 Середній", "📕 Просунутий"]], resize_keyboard=True)
menu_keyboard = ReplyKeyboardMarkup([["🧠 Інше питання"]], resize_keyboard=True)

logging.basicConfig(level=logging.INFO)

def save_user(uid, key, value):
    if uid not in user_data:
        user_data[uid] = {}
    user_data[uid][key] = value

def get_profile(uid):
    return user_data.get(uid, {})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я фітнес-бот. Обери мету:", reply_markup=meta_keyboard)
    return META

async def set_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "meta", update.message.text)
    await update.message.reply_text("Окей! Тепер обери стать:", reply_markup=gender_keyboard)
    return GENDER

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "gender", update.message.text)
    await update.message.reply_text("Скільки тобі років?")
    return AGE

async def set_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "age", update.message.text)
    await update.message.reply_text("Яка твоя вага в кг?")
    return WEIGHT

async def set_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "weight", update.message.text)
    await update.message.reply_text("Який у тебе зріст у см?")
    return HEIGHT

async def set_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "height", update.message.text)
    await update.message.reply_text("Оціни свій рівень підготовки:", reply_markup=level_keyboard)
    return LEVEL

async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id, "level", update.message.text)
    await update.message.reply_text("Готово! Тепер можеш задати будь-яке питання:", reply_markup=menu_keyboard)
    return MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = get_profile(update.effective_user.id)
    user_question = update.message.text
    prompt = (
        f"Ти — персональний фітнес-тренер. Відповідай українською. "
        f"Стать: {profile.get('gender')}, вік: {profile.get('age')}, "
        f"вага: {profile.get('weight')} кг, зріст: {profile.get('height')} см, "
        f"мета: {profile.get('meta')}, рівень: {profile.get('level')}. "
        f"Питання: {user_question}"
    )

    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        res = response.json()
        reply = res["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"⚠️ Помилка: {e}"

    await update.message.reply_text(reply)
    return MENU

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            META: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_meta)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_height)],
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_level)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
        },
        fallbacks=[]
    )
    app.add_handler(conv)
    print("Бот запущено")
    app.run_polling()
