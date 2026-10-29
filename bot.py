import os
import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from thefuzz import process
from aiohttp import web

# ==========================================
# НАСТРОЙКИ
# ==========================================
TOKEN = "8644786361:AAEwDgQxcDUJ5i2E2M-E6ChiocPHeT3pUi8"  
ADMIN_ID = 7306883771        

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

class UserState(StatesGroup):
    active_chat = State()

# ==========================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            question_key TEXT,
            answer TEXT,
            lang TEXT
        )
    """)
    
    # Таблица для личных заметок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note_text TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM knowledge")
    if cursor.fetchone()[0] == 0:
        initial_data = [
            # Приветствия и роль личного помощника
            ("приветствие", "привет", "👋 Привет! Я Mirus AI— твой личный помощник . Я готов помочь с учебой, распланировать задачи или просто выслушать, если ты устал.", "ru"),
            ("приветствие", "здравствуйте", "Здравствуйте! Рад нашему общению. Чем могу помочь вам сегодня в качестве личного помощника?", "ru"),
            ("помощник", "что ты умеешь", "🤖 Я твой Mirus AI — личный помощник. Я умею:\n• Отвечать на учебные вопросы (физика, алгебра, история);\n• Работать как личный психолог и поддерживать беседу;\n• Вести твои личные заметки (`/note`);\n• Считать (`/calc`), проводить викторины (`/quiz`) и многое другое!", "ru"),
            
            # Психологическая поддержка и эмпатия
            ("психология", "я устал", "😔 Понимаю тебя. Учёба и постоянные дела отнимают много сил. Попробуй сделать небольшую паузу, выпить воды, подышать свежим воздухом или просто отвлечься на 15 минут. Ты отлично справляешься!", "ru"),
            ("психология", "мне грустно", "🫂 Мне жаль, что тебе грустно. Помни, что трудные периоды — это временное явление. Если хочешь выговориться или разобрать какую-то задачу вместе, я всегда здесь.", "ru"),
            ("психология", "стресс перед экзаменом", "🧠 Волнение перед важными событиями — это абсолютно нормально. Главное — дыши глубоко и верь в свои силы. Давай повторим нужную тему через поиск или мини-викторину (`/quiz`), чтобы обрести уверенность!", "ru"),
            ("психология", "как мотивировать себя", "🔥 Мотивация приходит во время действия! Начни с малого: поставь одну простую задачу, разбей её на шаги и сделай первый. У тебя всё получится, я в тебя верю!", "ru"),

            # Базовые учебные темы
            ("история", "история таджикистана", "🏛 **История Таджикистана:**\n• Государства Бактрия, Согд, Кушанидов и Саманидов (IX-X вв.).\n• Образование Таджикской ССР (1924).\n• Независимость: 9 сентября 1991 года.", "ru"),
            ("география", "география таджикистана", "🌍 **География:** Столица — Душанбе. 93% территории занимают горы (Памир, Тянь-Шань). Высочайшая точка — пик Исмоили Сомони (7495 м).", "ru"),
            ("физика", "второй закон ньютона", "⚡ **Второй закон Ньютона:** $F = m \\cdot a$ (Сила равна произведению массы на ускорение).", "ru"),
            ("алгебра", "дискриминант", "📐 **Дискриминант:** Для квадратного уравнения $ax^2 + bx + c = 0$ формула: $D = b^2 - 4ac$.", "ru"),
        ]
        cursor.executemany(
            "INSERT INTO knowledge (category, question_key, answer, lang) VALUES (?, ?, ?, ?)",
            initial_data
        )
        conn.commit()
    conn.close()

init_db()

# ==========================================
# ОБРАБОТЧИКИ КОМАНД
# ==========================================

@dp.message(Command("start"))
@dp.message(Command("help"))
async def cmd_start_help(message: types.Message, state: FSMContext):
    await state.set_state(UserState.active_chat)
    help_text = (
        "🤖 **Привет! Я Mirus AI** — твой умный личный помощник и друг.\n\n"
        "💬 *Ты можешь просто написать мне о своих делах, спросить совет, поделиться усталостью или задать учебный вопрос.*\n\n"
        "📖 **Основные команды:**\n"
        "• `/list` — Все темы в базе\n"
        "• `/search <слово>` — Точный поиск\n"
        "• `/random` — Случайный факт\n"
        "• `/quiz` — Викторина\n"
        "• `/calc <пример>` — Калькулятор\n"
        "• `/note <текст>` — Сохранить личную заметку\n"
        "• `/mynotes` — Мои заметки\n"
        "• `/suggest <текст>` — Предложить тему админу\n"
        "• `/stats` — Статистика базы"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("list"))
async def cmd_list_knowledge(message: types.Message):
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, question_key FROM knowledge ORDER BY category ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📂 База знаний пуста.")
        return

    categories = {}
    for category, question_key in rows:
        cat_title = category.capitalize()
        if cat_title not in categories:
            categories[cat_title] = []
        categories[cat_title].append(question_key)

    response_text = "📚 **Список тем и категорий Mirus AI:**\n\n"
    for cat, keys in categories.items():
        response_text += f"📂 **{cat}:**\n"
        for key in keys:
            response_text += f"  • `{key}`\n"
        response_text += "\n"
    await message.answer(response_text, parse_mode="Markdown")

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    query = message.text.replace("/search", "", 1).strip().lower()
    if not query:
        await message.answer("⚠️ Укажи слово: `/search устал` или `/search ньютона`", parse_mode="Markdown")
        return

    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question_key, answer FROM knowledge WHERE question_key LIKE ? OR answer LIKE ?", (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    conn.close()

    if not results:
        await message.answer(f"❌ Ничего не найдено по запросу `'{query}'`.", parse_mode="Markdown")
        return

    response_text = f"🔍 **Результаты поиска:** `'{query}'`\n\n"
    for key, answer in results:
        response_text += f"🔑 **Ключ:** `{key}`\n{answer}\n\n"
    await message.answer(response_text, parse_mode="Markdown")

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question_key, answer, category FROM knowledge")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📂 База пуста.")
        return

    key, answer, category = random.choice(rows)
    await message.answer(f"🎲 **Тема:** `{key.capitalize()}` (*{category.capitalize()}*)\n\n{answer}", parse_mode="Markdown")

@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    expr = message.text.replace("/calc", "", 1).strip()
    if not expr:
        await message.answer("⚠️ Пример: `/calc 50 * 2 + 15`", parse_mode="Markdown")
        return
    try:
        if not all(c in "0123456789+-*/(). " for c in expr):
            await message.answer("❌ Только цифры и базовые знаки мат. операторов.")
            return
        res = eval(expr)
        await message.answer(f"🧮 `{expr} = {res}`", parse_mode="Markdown")
    except:
        await message.answer("❌ Ошибка вычисления.")

@dp.message(Command("note"))
async def cmd_note(message: types.Message):
    text = message.text.replace("/note", "", 1).strip()
    if not text:
        await message.answer("⚠️ Напиши текст заметки: `/note Купить тетрадь`", parse_mode="Markdown")
        return
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (user_id, note_text) VALUES (?, ?)", (message.from_user.id, text))
    conn.commit()
    conn.close()
    await message.answer("📝 Заметка успешно сохранена в твой блокнот!")

@dp.message(Command("mynotes"))
async def cmd_mynotes(message: types.Message):
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT note_text FROM notes WHERE user_id = ?", (message.from_user.id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📂 У тебя нет сохраненных заметок. Используй `/note`.")
        return

    text = "📋 **Твои заметки:**\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. {r[0]}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM knowledge")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM notes")
    notes_total = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 **Статистика Mirus AI:**\n• Записей в базе: `{total}`\n• Заметок пользователей: `{notes_total}`", parse_mode="Markdown")

# Админ-команды
@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет прав.")
        return
    parts = message.text.replace("/add", "", 1).split("|")
    if len(parts) < 3:
        await message.answer("⚠️ Формат: `/add категория | ключ | ответ`", parse_mode="Markdown")
        return
    cat, key, ans = parts[0].strip().lower(), parts[1].strip().lower(), parts[2].strip()
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO knowledge (category, question_key, answer, lang) VALUES (?, ?, ?, ?)", (cat, key, ans, "ru"))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Добавлено: `{key}` в категорию `{cat}`", parse_mode="Markdown")

@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет прав.")
        return
    key = message.text.replace("/delete", "", 1).strip().lower()
    if not key:
        await message.answer("⚠️ Укажи ключ: `/delete привет`")
        return
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge WHERE question_key = ?", (key,))
    conn.commit()
    conn.close()
    await message.answer(f"🗑 Удалено: `{key}`", parse_mode="Markdown")

# ==========================================
# ИНТЕЛЛЕКТУАЛЬНЫЙ ПОИСК И ПСИХОЛОГ-РЕЖИМ
# ==========================================
@dp.message(UserState.active_chat)
async def smart_search(message: types.Message):
    query = message.text.lower().strip()
    conn = sqlite3.connect("mirus_knowledge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question_key, answer FROM knowledge")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("⚠️ База пуста.")
        return

    keys = [r[0] for r in rows]
    answers = {r[0]: r[1] for r in rows}
    match, score = process.extractOne(query, keys)

    # Если бот уверен в совпадении (>55%), выдает ответ из базы (учёба, приветствие или психология)
    if score >= 55:
        await message.answer(answers[match], parse_mode="Markdown")
    else:
        # Мягкий ответ психолога/помощника, если фраза незнакома
        await message.answer(
            "💭 Я внимательно тебя слушаю, но пока не до конца понял этот запрос.\n"
            "Ты можешь написать `/help` для списка команд или добавить эту мысль/тему в базу через администратора!",
            parse_mode="Markdown"
        )

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER (24/7)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Mirus AI is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    print("Mirus AI (Личный помощник и психолог) успешно запущен...")
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
