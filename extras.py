# extras.py
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

MENU = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📖 Что я знаю", callback_data="menu:list")],
    [InlineKeyboardButton(text="🎲 Случайная тема", callback_data="menu:random")],
    [InlineKeyboardButton(text="🧠 Викторина", callback_data="menu:quiz")],
    [InlineKeyboardButton(text="📝 Мои заметки", callback_data="menu:notes")],
])

HELLO = (
    "👋 Привет. Я Mirus - помогу с учёбой и просто выслушаю.\n\n"
    "Попробуй написать так:\n"
    "• «объясни второй закон Ньютона»\n"
    "• «я устал, не могу заставить себя сесть за уроки»\n"
    "• «напомни в 18:00 повторить алгебру»\n\n"
    "Или нажми кнопку ниже 👇"
)

@router.message(Command("start2"))
async def hello_new(message: types.Message):
    await message.answer(HELLO, reply_markup=MENU, parse_mode="HTML")
