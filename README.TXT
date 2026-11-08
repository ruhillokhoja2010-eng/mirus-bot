MIRUS — ФИНАЛЬНЫЕ ФАЙЛЫ

1) САЙТ (репозиторий Mirus-app, Render Static Site)
   Загрузить все файлы из папки site/ в корень репозитория:
   index.html, sw.js, manifest.json, иконки *.png
   (заменить index.html и sw.js; остальные — если их ещё нет)

2) БОТ (репозиторий бота, Render Web Service)
   Загрузить все файлы из папки bot/ в корень репозитория:
   main.py (заменить старый), knowledge.py, calc.py
   Удалить файл bot_start_snippet.py, если он был загружен (он не нужен).
   В Render → Environment добавить:
     BOT_TOKEN   = 8644786361:AAEwDgQxc-DUJ5i2E2M-E6ChiocPHeT3pUi8 @BotFather
     ADMIN_ID    = 7306883771
     MINI_APP_URL = https://mirus-app.onrender.com (по желанию)

3) ПРОВЕРКА
   Сайт: открыть https://mirus-app.onrender.com
   Бот: /start, /lang, /calculator, /help, «Столица Таджикистана», «2+2*3»