import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from flask import Flask
import threading
import os

# 🔑 Твой токен
TOKEN = "8470491330:AAFKxv4plcjXZ-0JO_BLPZbYiSxZ24Vekjw"

# 🔧 Инициализация бота и планировщика
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# 🌐 Flask для Render (держит порт открытым)
app = Flask(__name__)

@app.route('/')
def home():
    return "Kompas Zhizni Bot is running 🧭"

# 🧭 Кнопки и категории
def get_rating_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"rate_{i}")
    builder.adjust(5)
    return builder.as_markup()

def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Начнём 🚀", callback_data="start_rating")
    return builder.as_markup()

categories = [
    ("💼🔥", "Бизнес"),
    ("👨‍👩‍👧‍👦❤️", "Семья"),
    ("🧘‍♂️🌿", "Здоровье"),
    ("🧠✨", "Я")
]

user_data = {}

# 📲 Обработка начала
@dp.message(F.text)
async def start(message: Message):
    await message.answer(
        "Ассаламу алейкум, Биржан! 🌙\n"
        "Готов сделать небольшую самооценку по важным сферам жизни?",
        reply_markup=get_start_keyboard()
    )

@dp.callback_query(F.data == "start_rating")
async def start_rating(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data[user_id] = {"step": 0, "answers": {}, "month": datetime.now().month}
    icon, name = categories[0]
    await callback.message.edit_text(
        f"Оцени свой {icon} <b>{name}</b> от 1 до 10 👇",
        reply_markup=get_rating_keyboard()
    )

@dp.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        return await callback.answer("Начни заново 🙏", show_alert=True)

    step = user_data[user_id]["step"]
    rating = int(callback.data.split("_")[1])
    icon, category = categories[step]
    user_data[user_id]["answers"][category] = rating
    user_data[user_id]["step"] += 1

    if user_data[user_id]["step"] < len(categories):
        icon, next_category = categories[user_data[user_id]["step"]]
        await callback.message.edit_text(
            f"Теперь оцени свой {icon} <b>{next_category}</b> от 1 до 10 👇",
            reply_markup=get_rating_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Отлично, Биржан 🙌\n"
            "Твои оценки сохранены. В конце месяца я покажу тебе общий итог 📊"
        )

# 🗓 Напоминание каждую пятницу
async def send_weekly_reminder():
    for user_id in user_data.keys():
        await bot.send_message(
            user_id,
            "🌙 Пятница — время подвести итоги недели!\n"
            "Готов пройти самооценку? ✨",
            reply_markup=get_start_keyboard()
        )

# 🗓 Отчёт 1 числа каждого месяца
async def send_monthly_report():
    for user_id, data in user_data.items():
        answers = data.get("answers", {})
        if not answers:
            continue

        report = "📊 <b>Твой отчёт за месяц:</b>\n\n"
        for cat, score in answers.items():
            report += f"{cat}: {score}/10\n"

        avg = sum(answers.values()) / len(answers)
        report += f"\nСредняя оценка месяца: <b>{avg:.1f}/10</b>\n\n"
        report += "💡 Продолжай осознанно расти, Биржан!"

        await bot.send_message(user_id, report)

# 🔁 Настройка расписания
def setup_scheduler():
    scheduler.add_job(send_weekly_reminder, CronTrigger(day_of_week="fri", hour=19, minute=0))
    scheduler.add_job(send_monthly_report, CronTrigger(day=1, hour=10, minute=0))
    scheduler.start()

# 🚀 Запуск бота
async def run_bot():
    print("✅ Kompas Zhizni Bot запущен и слушает события...")
    setup_scheduler()
    await dp.start_polling(bot)

# 🌐 Запуск Flask + Бота
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(run_bot())
