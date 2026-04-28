import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
import maigret
from maigret import maigret as maigret_search

TOKEN = "8458962370:AAH5ZYsP86JxGbhMf0t72u-86c7t8thsuzs"
ADMIN_ID = 5777388644

CHANNEL = "https://t.me/+HphbJWHr-Ag2MTFi"
CHANNEL_ID = -1003922720896  # ⚠️ позже лучше вставить реальный ID канала

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ---
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    return cursor.execute("SELECT id FROM users").fetchall()

# --- КНОПКИ ---
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Username поиск")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Рассылка")]
    ],
    resize_keyboard=True
)

# --- ПРОВЕРКА ПОДПИСКИ ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False

# --- START ---
@dp.message(Command("start"))
async def start(message: Message):
    add_user(message.from_user.id)

    if not await check_sub(message.from_user.id):
        await message.answer(
            f"❗ Для использования подпишись:\n{CHANNEL}\n\nПосле подписки напиши /start"
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("Админ панель", reply_markup=admin_menu)
    else:
        await message.answer("OSINT бот готов", reply_markup=menu)

# --- РАССЫЛКА ---
@dp.message(lambda msg: msg.text == "📢 Рассылка")
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Отправь текст:")

    @dp.message()
    async def send_all(msg: Message):
        users = get_users()
        for user in users:
            try:
                await bot.send_message(user[0], msg.text)
            except:
                pass
        await msg.answer("Готово")

# --- MAIGRET ---
async def search_username(username):
    try:
        result = await asyncio.to_thread(maigret_search, username)

        found = []
        not_found = []

        for site, data in result.items():
            if data.get("status") == "Claimed":
                found.append(site)
            else:
                not_found.append(site)

        return found[:5], not_found[:3]

    except Exception as e:
        print(e)
        return [], []

# --- REPORT ---
def generate_report(username, found, not_found):
    report = f"🔎 OSINT REPORT\n\n"
    report += f"👤 Username: {username}\n"
    report += f"🌐 Найдено: {len(found)} сайтов\n\n"

    for site in found:
        report += f"📍 {site} — найден\n"

    for site in not_found:
        report += f"📍 {site} — нет\n"

    return report

# --- ПОИСК ---
@dp.message(lambda msg: msg.text == "🔎 Username поиск")
async def username_start(message: Message):
    if not await check_sub(message.from_user.id):
        await message.answer(f"❗ Подпишись:\n{CHANNEL}")
        return

    await message.answer("Введи username:")

    @dp.message()
    async def process(msg: Message):
        wait = await msg.answer("⏳ Поиск...")

        found, not_found = await search_username(msg.text)
        report = generate_report(msg.text, found, not_found)

        await wait.edit_text(report)

# --- RUN ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())