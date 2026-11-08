# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import sqlite3
import random
import html
import ast
import operator

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, CallbackQuery)
from aiohttp import web

from knowledge import ENTRIES, LANGS, DEFAULT_LANG, TEXTS, t, find_answer, entry_answer
import calc as calculator

# ==========================================
# НАСТРОЙКИ (берутся из Environment на Render)
# ==========================================
TOKEN = os.environ["8644786361:AAEwDgQxc-DUJ5i2E2M-E6ChiocPHeT3pUi8"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7306883771"))
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://mirus-app.onrender.com")
DB = "mirus_knowledge.db"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==========================================
# БАЗА ДАННЫХ
# ==========================================
def db():
    return sqlite3.connect(DB)

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, question_key TEXT, answer TEXT, lang TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, note_text TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, lang TEXT)""")
    conn.commit()
    conn.close()

init_db()

def get_lang(user_id, tg_code=None):
    conn = db(); c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] in LANGS:
        return row[0]
    if tg_code:
        code = tg_code.split("-")[0].lower()
        if code in LANGS:
            return code
    return DEFAULT_LANG

def set_lang(user_id, lang):
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO users (user_id, lang) VALUES (?, ?) "
              "ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang", (user_id, lang))
    conn.commit(); conn.close()

def extra_entries():
    """Записи, добавленные админом через /add (хранятся в базе)."""
    conn = db(); c = conn.cursor()
    c.execute("SELECT category, question_key, answer, lang FROM knowledge")
    rows = c.fetchall()
    conn.close()
    out = []
    for cat, key, ans, lg in rows:
        lg = lg if lg in LANGS else DEFAULT_LANG
        out.append({"cat": cat, "keys": {lg: [key]}, "ans": {lg: ans}})
    return out

def count(sql, params=()):
    conn = db(); c = conn.cursor()
    c.execute(sql, params)
    n = c.fetchone()[0]
    conn.close()
    return n

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ
# ==========================================
def lang_keyboard(prefix="setlang"):
    rows = [[InlineKeyboardButton(text=name, callback_data=f"{prefix}:{code}")]
            for code, name in LANGS.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def main_keyboard(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("open_app", lang), web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="🌐 " + LANGS[lang].split(" ", 1)[1], callback_data="lang_menu"),
         InlineKeyboardButton(text="❓ /help", callback_data="help")],
    ])

def arg_of(message: types.Message, cmd: str) -> str:
    return (message.text or "").replace(cmd, "", 1).strip()

CALC_STATE = {}   # user_id -> текущее выражение кнопочного калькулятора

def keypad_markup(expr: str):
    rows = []
    for row in calculator.keypad_labels():
        rows.append([InlineKeyboardButton(text=b, callback_data=f"calc:{b}") for b in row])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def keypad_text(expr: str, error: bool = False) -> str:
    shown = html.escape(calculator.display(expr))
    prev = calculator.preview(expr)
    lines = [f"🧮 <b>Калькулятор</b>", "", f"<code>{shown}</code>"]
    if error:
        lines.append("❌ Неверное выражение")
    elif prev is not None and expr and prev != calculator.display(expr):
        lines.append(f"= <b>{html.escape(prev)}</b>")
    return "\n".join(lines)

# ==========================================
# КОМАНДЫ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    set_lang(message.from_user.id, lang)
    name = html.escape(message.from_user.first_name or "друг")
    await message.answer(t("welcome", lang, name=name), reply_markup=main_keyboard(lang))

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    await message.answer(t("help", lang), parse_mode="HTML")

@dp.message(Command("lang"))
async def cmd_lang(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    await message.answer(t("lang_choose", lang), reply_markup=lang_keyboard())

@dp.callback_query(F.data == "lang_menu")
async def cb_lang_menu(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id, callback.from_user.language_code)
    await callback.message.answer(t("lang_choose", lang), reply_markup=lang_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id, callback.from_user.language_code)
    await callback.message.answer(t("help", lang), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    if code not in LANGS:
        await callback.answer()
        return
    set_lang(callback.from_user.id, code)
    await callback.message.answer(t("lang_set", code, lang=LANGS[code]), reply_markup=main_keyboard(code))
    await callback.answer()

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    cats = {}
    for e in list(ENTRIES) + extra_entries():
        title = e["cat"].capitalize()
        keys = e["keys"].get(lang) or e["keys"].get(DEFAULT_LANG) or next(iter(e["keys"].values()))
        cats.setdefault(title, []).append(keys[0])
    lines = []
    for cat, keys in cats.items():
        lines.append(f"<b>📂 {html.escape(cat)}</b>")
        lines += [f"  • {html.escape(k)}" for k in keys[:12]]
        lines.append("")
    await message.answer("\n".join(lines) or t("not_found", lang), parse_mode="HTML")

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    q = arg_of(message, "/search").lower()
    if not q:
        await message.answer(t("search_usage", lang))
        return
    ans, score = find_answer(q, lang, extra_entries())
    if ans:
        await message.answer(ans)
    else:
        await message.answer(t("search_none", lang, q=html.escape(q)), parse_mode="HTML")

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    pool = list(ENTRIES) + extra_entries()
    e = random.choice(pool)
    key = (e["keys"].get(lang) or e["keys"].get(DEFAULT_LANG) or next(iter(e["keys"].values())))[0]
    await message.answer(f"{t('random_title', lang)}: <b>{html.escape(key.capitalize())}</b>\n\n"
                         f"{html.escape(entry_answer(e, lang))}", parse_mode="HTML")

@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    expr = arg_of(message, "/calc")
    if not expr:
        await message.answer(t("calc_usage", lang))
        return
    try:
        res = calculator.fmt(calculator.evaluate(expr))
        await message.answer(f"🧮 {html.escape(calculator.pretty(calculator.normalize(expr)))} = <b>{html.escape(res)}</b>", parse_mode="HTML")
    except ValueError:
        await message.answer(t("calc_error", lang))

@dp.message(Command("calculator"))
async def cmd_calculator(message: types.Message):
    CALC_STATE[message.from_user.id] = ""
    await message.answer(keypad_text(""), reply_markup=keypad_markup(""), parse_mode="HTML")

@dp.callback_query(F.data.startswith("calc:"))
async def cb_calc(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    uid = callback.from_user.id
    expr = CALC_STATE.get(uid, "")
    expr, error = calculator.press(expr, key)
    CALC_STATE[uid] = expr
    try:
        await callback.message.edit_text(keypad_text(expr, error), reply_markup=keypad_markup(expr), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@dp.message(Command("note"))
async def cmd_note(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    text = arg_of(message, "/note")
    if not text:
        await message.answer(t("note_usage", lang))
        return
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, note_text) VALUES (?, ?)", (message.from_user.id, text))
    conn.commit(); conn.close()
    await message.answer(t("note_saved", lang))

@dp.message(Command("mynotes"))
async def cmd_mynotes(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    conn = db(); c = conn.cursor()
    c.execute("SELECT note_text FROM notes WHERE user_id = ? ORDER BY id", (message.from_user.id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await message.answer(t("mynotes_empty", lang))
        return
    body = "\n".join(f"{i}. {html.escape(r[0])}" for i, r in enumerate(rows, 1))
    await message.answer(f"<b>{t('mynotes_title', lang)}</b>\n\n{body}", parse_mode="HTML")

@dp.message(Command("suggest"))
async def cmd_suggest(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    text = arg_of(message, "/suggest")
    if not text:
        await message.answer(t("suggest_usage", lang))
        return
    who = message.from_user.username or str(message.from_user.id)
    await bot.send_message(ADMIN_ID, f"💡 Предложение от @{who}:\n{text}")
    await message.answer(t("suggest_sent", lang))

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    total = count("SELECT COUNT(*) FROM knowledge") + len(ENTRIES)
    notes = count("SELECT COUNT(*) FROM notes")
    users = count("SELECT COUNT(*) FROM users")
    await message.answer(t("stats", lang, total=total, notes=notes, users=users))

# ---------- админ ----------
@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("admin_only", lang))
        return
    parts = arg_of(message, "/add").split("|")
    if len(parts) < 3:
        await message.answer("Формат: /add категория | ключ | ответ")
        return
    cat, key, ans = parts[0].strip().lower(), parts[1].strip().lower(), parts[2].strip()
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO knowledge (category, question_key, answer, lang) VALUES (?, ?, ?, ?)",
              (cat, key, ans, DEFAULT_LANG))
    conn.commit(); conn.close()
    await message.answer(f"✅ Добавлено: {key} ({cat})")

@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("admin_only", lang))
        return
    key = arg_of(message, "/delete").lower()
    if not key:
        await message.answer("Укажите ключ: /delete ключ")
        return
    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM knowledge WHERE question_key = ?", (key,))
    conn.commit(); conn.close()
    await message.answer(f"🗑 Удалено: {key}")

# ---------- обычные сообщения ----------
@dp.message(F.text & ~F.text.startswith("/"))
async def chat(message: types.Message):
    lang = get_lang(message.from_user.id, message.from_user.language_code)
    if calculator.is_arithmetic(message.text):
        try:
            res = calculator.fmt(calculator.evaluate(message.text))
            await message.answer(f"🧮 {html.escape(calculator.pretty(calculator.normalize(message.text)))} = <b>{html.escape(res)}</b>", parse_mode="HTML")
            return
        except ValueError:
            pass
    ans, score = find_answer(message.text, lang, extra_entries())
    if ans:
        await message.answer(ans)
    else:
        await message.answer(t("not_found", lang))

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER
# ==========================================
async def handle_ping(request):
    return web.Response(text="Mirus AI is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()

async def main():
    logging.info("Mirus AI запущен")
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
