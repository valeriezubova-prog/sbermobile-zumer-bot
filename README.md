# SberMobile Zumer Bot (Render, FastAPI + aiogram)

Бот с вебхуком для Telegram. Готов к деплою на Render (бесплатный план).

## Что внутри
- `main.py` — код бота (FastAPI + aiogram).
- `sbermobile_zumer_botflow.json` — сценарий с вопросами/баллами.
- `requirements.txt` — зависимости.
- `render.yaml` — конфиг Render.
- `README.md` — эти инструкции.

## Быстрый старт (Render)
1. Создай бота у @BotFather → получи **BOT_TOKEN**.
2. Создай репозиторий на GitHub и добавь эти файлы (или распакуй ZIP и залей как репо).
3. На https://render.com нажми **New+ → Blueprint** → подключи репозиторий.
4. Выбери **Free plan**.
5. В переменных окружения Render укажи:
   - `BOT_TOKEN` — токен из BotFather.
   - `WEBHOOK_SECRET` — любой сложный набор символов (например, `zumer_12345_xx`).
   - `BASE_URL` — появится после первого деплоя (формат `https://<service>.onrender.com`). Можно добавить позже.
6. Дождись деплоя → затем зайди во вкладку **Environment** и допиши `BASE_URL`.
7. Открой в браузере: `https://<service>.onrender.com/set-webhook` — вебхук установится.
8. В Telegram у своего бота нажми **/start**.

> Если `BASE_URL` задан до старта, вебхук поставится автоматически.
