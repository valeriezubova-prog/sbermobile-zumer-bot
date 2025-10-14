import os
import json
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret-path")
BASE_URL = os.getenv("BASE_URL")
FLOW_PATH = os.getenv("FLOW_PATH", "sbermobile_zumer_botflow.json")

with open(FLOW_PATH, "r", encoding="utf-8") as f:
    FLOW = json.load(f)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

app = FastAPI(title="SberMobile Zumer Bot")

user_scores = {}
user_step = {}

LABELS = FLOW["logic"]["labels"]
TIE = FLOW["logic"]["tie_breaker"]

def to_winner(scores: dict) -> str:
    best_val = max((scores.get(l, 0) for l in LABELS), default=0)
    top = [l for l in LABELS if scores.get(l, 0) == best_val]
    if len(top) == 1:
        return top[0]
    for t in TIE:
        if t in top:
            return t
    return top[0] if top else LABELS[0]

async def send_node(chat_id: int, node_id: str):
    node = FLOW["nodes"].get(node_id)
    if not node:
        await bot.send_message(chat_id, "Ой, я запутался. Начнём заново: /start")
        user_step[chat_id] = "q1"
        return
    user_step[chat_id] = node_id

    if node["type"] == "message":
        buttons = node.get("buttons") or []
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for b in buttons:
            kb.add(b)
        await bot.send_message(chat_id, node["text"], reply_markup=kb)
        return

    if node["type"] == "question":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for opt in node["options"]:
            kb.add(opt["text"])
        await bot.send_message(chat_id, node["question"], reply_markup=kb)
        return

    if node["type"] == "result":
        scores = user_scores.get(chat_id, {})
        winner = to_winner(scores)
        txt = node["result_text"].replace("{{winner}}", winner)
        buttons = node.get("buttons") or []
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for b in buttons:
            kb.add(b)
        await bot.send_message(chat_id, txt, reply_markup=kb)
        return

    if node["type"] == "switch_by_winner":
        scores = user_scores.get(chat_id, {})
        winner = to_winner(scores)
        text = node["cases"].get(winner, {}).get("text", f"Тебе подойдёт «{winner}»")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for b in node.get("buttons", []):
            kb.add(b)
        await bot.send_message(chat_id, text, reply_markup=kb)
        return

@dp.message_handler(commands=["start"])
async def cmd_start(msg: types.Message):
    chat_id = msg.chat.id
    user_scores[chat_id] = {}
    await bot.send_message(chat_id, FLOW["bot"]["greeting"])
    user_step[chat_id] = "q1"
    await send_node(chat_id, "q1")

@dp.message_handler(commands=["retry"])
async def cmd_retry(msg: types.Message):
    chat_id = msg.chat.id
    user_scores[chat_id] = {}
    user_step[chat_id] = "q1"
    await send_node(chat_id, "q1")

@dp.message_handler(commands=["help"])
async def cmd_help(msg: types.Message):
    await msg.answer("Я подбираю тариф СберМобайла. Жми /start и проходи короткий тест 💚")

@dp.message_handler()
async def on_text(msg: types.Message):
    chat_id = msg.chat.id
    node_id = user_step.get(chat_id, "q1")
    node = FLOW["nodes"].get(node_id)

    if node and node.get("type") == "message":
        nb = node.get("next_by_button", {})
        nxt = nb.get(msg.text)
        if nxt:
            await send_node(chat_id, nxt)
            return
        await msg.answer("Нажми кнопку ниже 👇")
        return

    if node and node.get("type") == "question":
        chosen = None
        for opt in node.get("options", []):
            if opt["text"] == msg.text:
                chosen = opt; break
        if not chosen:
            await msg.answer("Выбери вариант кнопкой 👇")
            return
        sc = user_scores.setdefault(chat_id, {})
        for k, v in chosen.get("scores", {}).items():
            sc[k] = sc.get(k, 0) + v
        await send_node(chat_id, node["next"])
        return

    if node and msg.text in (node.get("buttons") or []):
        nxt = node.get("next_by_button", {}).get(msg.text)
        if nxt:
            await send_node(chat_id, nxt)
            return

    await msg.answer("Жми на кнопки ниже, так быстрее 😉")

@app.on_event("startup")
async def on_startup():
    if BASE_URL and BOT_TOKEN and WEBHOOK_SECRET:
        await bot.set_webhook(f"{BASE_URL}/webhook/{WEBHOOK_SECRET}")
    else:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

@app.get("/")
async def root():
    return {"ok": True, "status": "running"}

@app.get("/set-webhook")
async def set_webhook(url: str = None):
    base = url or BASE_URL
    if not base:
        raise HTTPException(400, "Укажи ?url=https://<your-service>.onrender.com или установи BASE_URL")
    await bot.set_webhook(f"{base}/webhook/{WEBHOOK_SECRET}")
    return {"ok": True, "webhook": f"{base}/webhook/{WEBHOOK_SECRET}"}

@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        raise HTTPException(403, "forbidden")
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return {"ok": True}
