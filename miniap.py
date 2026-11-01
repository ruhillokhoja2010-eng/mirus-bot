# miniapp.py
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

router = Router()
APP_URL = "https://ТВОЙ_ЛОГИН.github.io/mirus-app/"

@router.message(Command("app"))
async def cmd_app(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть Mirus", web_app=WebAppInfo(url=APP_URL))
    ]])
    await message.answer("Мини-приложение:", reply_markup=kb)

@router.message(F.web_app_data)
async def on_webapp(message: types.Message):
    await message.answer(f"Пришло из приложения: {message.web_app_data.data}")
