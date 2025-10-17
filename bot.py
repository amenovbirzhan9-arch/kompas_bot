import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from collections import defaultdict

# 🔹 ВСТАВЬ СЮДА СВОЙ ТОКЕН
TOKEN = "8470491330:AAFKxv4plcjXZ-0JO_BLPZbYiSxZ24Vekjw"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранение данных пользователей
user_data = defaultdict(lambda: {"business": [], "family": [], "health": []})

# Клавиатура для выбора категории
categories_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💼 Бизнес")],
        [KeyboardButton(text="🏡 Семья")],
        [KeyboardButton(text="💪 Здоровье")]
    ],
    resize_keyboard=True
)

# Клавиатура для оценки по 10-бальной шкале
def rating_kb(category):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 11)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=f"Выбери оценку для {category}"
    )

# /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Ассаламу алейкум, {user_name}! 🌙\n"
        f"Каждую пятницу я буду спрашивать тебя, как ты оцениваешь свои состояния по 10-бальной шкале:\n"
        f"💼 Бизнес\n🏡 Семья\n💪 Здоровье\n\n"
        f"Начнём прямо сейчас?",
        reply_markup=categories_kb
    )

# Выбор категории
@dp.message(lambda message: message.text in ["💼 Бизнес", "🏡 Семья", "💪 Здоровье"])
async def choose_category(message: Message):
    category_map = {
        "💼 Бизнес": "business",
        "🏡 Семья": "family",
        "💪 Здоровье": "health"
    }
    category = category_map[message.text]
    await message.answer(f"Оцени {message.text} по 10-бальной шкале 👇", reply_markup=rating_kb(message.text))
    dp["category"] = category

# Оценка по шкале
@dp.message(lambda message: message.text.isdigit() and 1 <= int(message.text) <= 10)
async def rating_handler(message: Message):
    user_id = message.from_user.id
    category = dp.get("category", None)

    if not category:
        await message.answer("Сначала выбери категорию 💼/🏡/💪", reply_markup=categories_kb)
        return

    rating = int(message.text)
    user_data[user_id][category].append(rating)

    await message.answer(f"✅ Записано! Твоя оценка: {rating} за {category}.", reply_markup=categories_kb)

# Автоматическое сообщение каждую пятницу
async def weekly_check():
    while True:
        now = datetime.now()
        if now.weekday() == 4 and now.hour == 10:  # Пятница 10:00
            for user_id in user_data.keys():
                await bot.send_message(
                    user_id,
                    "Пятница! Время оценить свою неделю 🌞\nВыбери категорию:",
                    reply_markup=categories_kb
                )
            await asyncio.sleep(86400)  # ждать сутки
        await asyncio.sleep(3600)  # проверять раз в час

# Отчёт 1 числа месяца
async def monthly_report():
    while True:
        now = datetime.now()
        if now.day == 1 and now.hour == 9:
            for user_id, data in user_data.items():
                report = []
                for k, v in data.items():
                    if v:
                        avg = sum(v) / len(v)
                        name = "Бизнес" if k == "business" else "Семья" if k == "family" else "Здоровье"
                        report.append(f"{name}: {avg:.1f} баллов")
                        user_data[user_id][k] = []  # очищаем оценки
                if report:
                    text = "📊 <b>Отчёт за месяц:</b>\n" + "\n".join(report)
                    await bot.send_message(user_id, text)
            await asyncio.sleep(86400)
        await asyncio.sleep(3600)

# Основная функция
async def main():
    print("✅ Бот запущен и работает...")
    asyncio.create_task(weekly_check())
    asyncio.create_task(monthly_report())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
