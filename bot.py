# -*- coding: utf-8 -*-
# Nitro Movies Bot — Temur uchun sozlangan
# Webhook style (Render-da barqaror ishlashi uchun)

import os
import sqlite3
import telebot
from telebot import types
from flask import Flask, request

# ===================== MUHIM SOZLAMALAR =====================
TOKEN = os.getenv("BOT_TOKEN", "8374881360:AAG4awRqTVHRJCptoLY1ItLss6r6oLl0DRE")
ADMIN_IDS = {5051898362}
ADMIN_USERNAME = "temur_2080"
DB_PATH = "media.db"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True)
app = Flask(__name__)

# ===================== DATABASE =====================
def db_init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS media (
        code TEXT PRIMARY KEY,
        category TEXT,
        file_id TEXT,
        media_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
db_init()

def db_add(code, category, file_id, media_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO media (code, category, file_id, media_type) VALUES (?, ?, ?, ?)",
              (code, category, file_id, media_type))
    conn.commit()
    conn.close()

def db_get(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT code, category, file_id, media_type FROM media WHERE code = ?", (code,))
    row = c.fetchone()
    conn.close()
    return row

def db_delete(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM media WHERE code = ?", (code,))
    cnt = c.rowcount
    conn.commit()
    conn.close()
    return cnt

# ===================== UTILITY =====================
def normalize_category(cat_raw: str):
    if not cat_raw:
        return None
    cat = cat_raw.strip().lower()
    aliases = {
        "kino": "kino", "kinolar": "kino", "film": "kino", "filmlar": "kino",
        "serial": "serial", "seriallar": "serial",
        "mult": "multfilm", "multfilm": "multfilm", "multfilmlar": "multfilm",
        "cartoon": "multfilm", "animation": "multfilm", "anime": "multfilm",
    }
    return aliases.get(cat)

def main_menu(is_admin: bool = False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎥 Kinolar", "📺 Seriallar")
    kb.row("🎞 Multfilmlar")
    kb.row("⭐ Xizmatlar", "📩 Admin bilan bog‘lanish")
    if is_admin:
        kb.row("🛠 Admin panel")
    return kb

def services_keyboard():
    ikb = types.InlineKeyboardMarkup()
    ikb.add(
        types.InlineKeyboardButton("Telegram Premium", url=f"https://t.me/{ADMIN_USERNAME}"),
        types.InlineKeyboardButton("Telegram Stars", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    ikb.add(types.InlineKeyboardButton("Admin bilan bog‘lanish", url=f"https://t.me/{ADMIN_USERNAME}"))
    return ikb

def admin_help_text():
    return (
        "🛠 <b>Admin panel</b>\n"
        "➕ Qo‘shish: media xabariga <b>reply</b> qilib\n"
        "<code>add &lt;kategoriya&gt; &lt;kod&gt;</code>\n"
        "masalan: <code>add kino 7</code>\n\n"
        "🗑 O‘chirish:\n"
        "<code>del &lt;kod&gt;</code>\n\n"
        "📂 Kategoriyalar: <code>kino</code> | <code>serial</code> | <code>multfilm</code>\n"
        "📎 Media turlari: video, document, animation (gif), sticker\n"
    )

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ===================== BOT HANDLERS =====================
@bot.message_handler(commands=['start'])
def cmd_start(message: telebot.types.Message):
    is_admin_user = message.from_user.id in ADMIN_IDS
    text_user = "🎬 <b>Nitro Movies</b> botiga xush kelibsiz!\n\nKod yuboring va to‘liq kino/serial/multfilmlarni oling.\nMasalan: <code>7</code>"
    if is_admin_user:
        text_user += "\n\n" + admin_help_text()
    bot.send_message(message.chat.id, text_user, reply_markup=main_menu(is_admin_user), disable_web_page_preview=True)

@bot.message_handler(commands=['id'])
def cmd_id(message: telebot.types.Message):
    bot.reply_to(message, f"Sizning ID: <code>{message.from_user.id}</code>")

# Menyu tugmalari va add/del handlers shu yerga joylashadi
# (Hozircha polling handlersni webhook style uchun Flask orqali ishlatamiz)

# ===================== WEBHOOK ROUTES =====================
WEBHOOK_URL_BASE = f"https://myfirstbot-3.onrender.com"
WEBHOOK_URL_PATH = f"/{TOKEN}/"

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/set_webhook", methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    return "Webhook set!", 200

@app.route("/")
def index():
    return "Bot ishlayapti!", 200

# ===================== RUN SERVER =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
