import asyncio
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
import g4f

BOT_TOKEN = "8644786361:AAEwDgQxcDUJ5i2E2M-E6ChiocPHeT3pUi8"

# Канал проекта
MY_CHANNEL = "mirusmedia_ru"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================================================================
# 📚 БАЗА ЗНАНИЙ
# =====================================================================
KNOWLEDGE_BASE = {
    "версия": "🚀 Текущая версия Mirus — 3.5!",
    "автор": "👨‍💻 Создатель и разработчик этого бота — Ruhillokhoja.",
    "канал": f"📢 Наш официальный канал: @{MY_CHANNEL}. Подписывайся! 🔥",
    "python": "🐍 Python — мощный и простой в изучении язык программирования, на котором написан этот бот.",
    "github": "💻 GitHub — платформа для хостинга IT-проектов и совместной разработки кода.",
    "render": "☁️ Render — облачный хостинг, на котором круглосуточно работает этот бот.",
    "aiogram": "🤖 Aiogram — асинхронный фреймворк для создания Telegram-ботов на Python.",
    "html": "🌐 HTML — язык разметки для создания веб-страниц.",
    "css": "🎨 CSS — язык стилей для оформления веб-страниц.",
    "javascript": "⚡ JavaScript — язык программирования, который делает веб-страницы интерактивными.",
    "bmw": "🏎️ BMW — легендарный немецкий автопроизводитель, известный спортивными моделями (например, M5 F90).",
    "porsche": "🏁 Porsche — культовый немецкий производитель спорткаров (например, 911 GT3 RS).",
    "автомобиль": "🚗 Автомобиль — техническое средство передвижения из тысяч деталей и электроники.",
    "аккумулятор": "🔋 Аккумулятор (АКБ) — источник тока, питающий стартер и бортовую сеть автомобиля.",
    "физика": "⚡ Физика — наука о природе, изучающая материю, энергию, пространство и время.",
    "математика": "📐 Математика — царица наук, изучающая величины и пространственные отношения.",
    "химия": "🧪 Химия — наука о веществах, их составе и свойствах.",
}

# Коллекция интересных фактов
RANDOM_FACTS = [
    "💡 Знаешь ли ты? Первый в истории программист — это женщина, Ада Лавлейс (в XIX веке).",
    "💡 Знаешь ли ты? Язык программирования Python назван в честь британского комедийного шоу «Летающий цирк Монти Пайтона», а не в честь змеи! 🐍",
    "💡 Знаешь ли ты? Большинство современных автомобилей содержат больше строк кода программного обеспечения, чем ранние космические корабли NASA! 🚗💻",
    "💡 Знаешь ли ты? Свет от Солнца доходит до Земли примерно за 8 минут и 20 секунд. ☀️",
]

def check_custom_knowledge(user_text: str) -> str | None:
    msg = user_text.strip().lower()
    for word, answer in KNOWLEDGE_BASE.items():
        if word in msg:
            return answer
    return None

def get_local_response(text: str) -> str | None:
    msg = text.strip().lower()

    custom_ans = check_custom_knowledge(text)
    if custom_ans:
        return custom_ans

    if any(q in msg for q in ["факты", "факт", "расскажи факт", "интересный факт"]):
        return f"🧠 {random.choice(RANDOM_FACTS)}"

    if any(phrase in msg for phrase in ["как дела", "как ты", "как жизнь", "чихели", "как делишки", "как оно"]):
        return "У меня всё отлично, спасибо! 🚀 Работаю на максимум, готов решать задачи и отвечать на вопросы! А у тебя как? 😊"

    if any(q in msg for q in ["что ты умеешь", "что умеешь", "что ты умееш", "что умееш", "твои функции", "возможности"]):
        return (
            "🤖 **Возможности Mirus:**\n\n"
            "1. 🔢 **Математика:** Быстро считаю примеры любой сложности (например: `250 * 4` или `(100+50)/3`).\n"
            "2. 💬 **Общение и юмор:** Поддерживаю живой диалог, отвечаю на приветствия и рассказываю интересные факты.\n"
            "3. 🧠 **База знаний:** Мгновенно отвечаю на вопросы про IT, программирование, автомобили и науку.\n"
            "4. 🌐 **Умный ИИ-поиск:** Если тема сложная, подключаю внешние нейросети и нахожу ответ на любой вопрос!\n"
            "5. 📝 **Отзывы:** Принимаю ваши предложения и пожелания через команду `/feedback`.\n\n"
            "💡 *Просто напиши мне любой вопрос или математический пример!*"
        )

    if any(word in msg for word in ["привет", "салом", "hello", "hi", "здравствуй", "добрый день", "добрый вечер", "доброе утро", "салом алейкум"]):
        return "Привет! 👋 Я Mirus. Очень рад тебя видеть! Чем могу помочь сегодня? 😊"

    if any(word in msg for word in ["спасибо", "рахмат", "благодарю", "thanks", "thx"]):
        return "Всегда пожалуйста! 😉 Рад был помочь! Если будут ещё вопросы — обращайся! ✨"

    if any(word in msg for word in ["пока", "до свидания", "бай", "goodbye", "до встречи"]):
        return "До свидания! 👋 Хорошего дня и отличного настроения! ✨"

    if any(q in msg for q in ["кто ты", "кто такой"]):
        return "Я Mirus — твой умный виртуальный помощник! 🤖"

    clean_math = re.sub(r'[^0-9\+\-\*\/\(\)\.\,\s]', '', msg).strip()
    if clean_math and re.search(r'\d', clean_math) and re.search(r'[\+\-\*\/]', clean_math):
        if re.match(r'^[0-9\+\-\*\/\(\)\.\,\s]+$', msg):
            try:
                expr = clean_math.replace(',', '.')
                result = eval(expr, {"__builtins__": None}, {})
                return f"🔢 Результат: {result} ✅"
            except Exception:
                pass

    return None

# =====================================================================
# 💌 СООБЩЕНИЕ ДЛЯ ОТЗЫВОВ И СВЯЗИ
# =====================================================================
@dp.message(Command("feedback"))
async def feedback_cmd(message: types.Message):
    text = (
        "✨ **Оставить отзыв или предложение** ✨\n\n"
        "Огромное спасибо за ваш отзыв! 🙏\n"
        "Мы очень ценим ваше мнение и постоянно совершенствуем бота. 🚀\n\n"
        "📬 **Наш официальный Telegram-канал:**\n"
        f"• @{MY_CHANNEL}\n\n"
        "Пишите свои идеи, предложения и отзывы в комментариях канала! 💙"
    )
    await message.answer(text, parse_mode="Markdown")

async def get_ai_response(user_message: str) -> str:
    local_ans = get_local_response(user_message)
    if local_ans:
        return local_ans

    providers = [g4f.Provider.DDG, g4f.Provider.Blackbox]
    
    for provider in providers:
        try:
            response = await asyncio.wait_for(
                g4f.ChatCompletion.create_async(
                    model=g4f.models.gpt_35_turbo,
                    messages=[{"role": "user", "content": user_message}],
                    provider=provider
                ),
                timeout=8.0
            )
            if response and len(str(response).strip()) > 0:
                return f"🤖 {str(response)}"
        except Exception:
            continue

    return (
        "💡 Я пока не знаю ответа на этот вопрос.\n\n"
        f"Спасибо за ваш вопрос! Вы можете написать свой отзыв или замечание в наш канал (@{MY_CHANNEL}) — мы обязательно научим бота новому! 🙏✨"
    )

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Привет! 👋 Я Mirus. Задай мне сложный вопрос, напиши математический пример или отправь /feedback! 😊✨")

@dp.message()
async def handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_text = await get_ai_response(message.text)
    
    try:
        await message.answer(ai_text, parse_mode="Markdown")
    except Exception:
        await message.answer(ai_text)

async def main():
    print("Бот Mirus успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
