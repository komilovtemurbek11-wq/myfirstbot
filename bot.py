# -*- coding: utf-8 -*-
# Nitro Movies Bot — Temur uchun sozlangan
# Funksiyalar:
# - /start -> foydalanuvchi uchun menyu (Kinolar / Seriallar / Multfilmlar / Xizmatlar / Admin bilan bog'lanish)
# - Admin uchun /start -> qo'shimcha "🛠 Admin panel" tugmasi ko'rinadi (boshqalarga ko'rinmaydi)
# - Reply qilib: "add <kategoriya> <kod>" (kategoriya: kino | serial | multfilm) [faqat admin]
# - Reply qilib: "del <kod>"  [faqat admin]
# - Kod yozilsa -> saqlangan media yuboriladi
# - /id -> user ID (admin ro'yxatini to'ldirish uchun)
#
# Saqlash: SQLite (code, category, file_id, media_type)
# Qo'llab-quvvatlanadigan media: video, document, animation (gif), sticker
# Katta fayllar: Telegram file_id orqali yuboriladi (2GB/4GB gacha)

import os
import sqlite3
import telebot
from telebot import types

# ===================== MUHIM SOZLAMALAR =====================
TOKEN = os.getenv("BOT_TOKEN", "8374881360:AAG4awRqTVHRJCptoLY1ItLss6r6oLl0DRE")

# Faqat adminlar (faqat shu ID'lar add/del va admin panelni ko'radi)
ADMIN_IDS = {5051898362}

# Admin username
ADMIN_USERNAME = "temur_2080"  # @temur_2080

DB_PATH = "media.db"
# ============================================================

bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True)

# ====== SQLite ======
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

db_init()

# ====== Kategoriya normalize ======
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

# ====== Menyular ======
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

# ====== /start ======
@bot.message_handler(commands=['start'])
def cmd_start(message: telebot.types.Message):
    is_admin = message.from_user.id in ADMIN_IDS
    text_user = (
        "🎬 <b>Nitro Movies</b> botiga xush kelibsiz!\n\n"
        "Kod yuboring va to‘liq kino/serial/multfilmlarni oling.\n"
        "Masalan: <code>7</code>\n"
    )
    if is_admin:
        text_user += "\n" + admin_help_text()
    bot.send_message(message.chat.id, text_user, reply_markup=main_menu(is_admin), disable_web_page_preview=True)

# ====== /id ======
@bot.message_handler(commands=['id'])
def cmd_id(message: telebot.types.Message):
    bot.reply_to(message, f"Sizning ID: <code>{message.from_user.id}</code>")

# ====== Menyu tugmalari ======
@bot.message_handler(func=lambda m: m.text in ["🎥 Kinolar", "📺 Seriallar", "🎞 Multfilmlar"])
def menu_categories(message: telebot.types.Message):
    mapping = {
        "🎥 Kinolar": "kino",
        "📺 Seriallar": "serial",
        "🎞 Multfilmlar": "multfilm",
    }
    cat = mapping[message.text]
    is_admin = message.from_user.id in ADMIN_IDS
    bot.reply_to(
        message,
        f"Tanlandi: <b>{message.text}</b>\n\n"
        "Kod yuboring (masalan <code>7</code>) — bot mos faylni yuboradi."
        + ("\n\n" + "Admin: media xabariga reply qilib <code>add "+cat+" &lt;kod&gt;</code>" if is_admin else ""),
        reply_markup=main_menu(is_admin)
    )

@bot.message_handler(func=lambda m: m.text == "⭐ Xizmatlar")
def menu_services(message: telebot.types.Message):
    bot.send_message(
        message.chat.id,
        "⭐ <b>Xizmatlar</b>\n\n"
        "Telegram Premium / Telegram Stars / Admin bilan bog‘lanish:",
        reply_markup=services_keyboard(),
        disable_web_page_preview=True
    )

@bot.message_handler(func=lambda m: m.text == "📩 Admin bilan bog‘lanish")
def menu_admin_contact(message: telebot.types.Message):
    bot.send_message(
        message.chat.id,
        f"👉 <b>Admin:</b> @{ADMIN_USERNAME}",
        reply_markup=main_menu(message.from_user.id in ADMIN_IDS),
        disable_web_page_preview=True
    )

@bot.message_handler(func=lambda m: m.text == "🛠 Admin panel")
def menu_admin_panel(message: telebot.types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return  # yashirin
    bot.reply_to(message, admin_help_text(), reply_markup=main_menu(True))

# ====== ADD / DEL (faqat adminlar) ======
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("add"))
def handle_add(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        # foydalanuvchiga soddaroq javob, admin detallarini bermaymiz
        return bot.reply_to(message, "⛔ Ruxsat yo‘q.")
    parts = message.text.split()
    if len(parts) < 3:
        return bot.reply_to(message, "❗ Format: <code>add &lt;kategoriya&gt; &lt;kod&gt;</code>\nMasalan: <code>add kino fastx10</code>")
    raw_cat = parts[1]
    code = " ".join(parts[2:]).strip()
    category = normalize_category(raw_cat)
    if not category:
        return bot.reply_to(message, "❗ Kategoriya: <code>kino</code> | <code>serial</code> | <code>multfilm</code>")

    if not message.reply_to_message:
        return bot.reply_to(message, "❗ <b>Media xabariga reply</b> qilib yuboring (video/document/animation/sticker), keyin <code>add ...</code> yozing.")

    r = message.reply_to_message
    file_id = None
    media_type = None

    if r.video:
        file_id = r.video.file_id
        media_type = "video"
    elif r.document:
        file_id = r.document.file_id
        media_type = "document"
    elif r.animation:
        file_id = r.animation.file_id
        media_type = "animation"
    elif r.sticker:
        file_id = r.sticker.file_id
        media_type = "sticker"
    else:
        return bot.reply_to(message, "❗ Faqat video/document/animation/sticker yuboring va shunga reply qiling.")

    try:
        db_add(code, category, file_id, media_type)
        bot.reply_to(message, f"✅ Qo‘shildi:\n• Kategoriya: <b>{category}</b>\n• Kod: <code>{code}</code>\n• Media: <i>{media_type}</i>")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Saqlashda xato: {e}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("del"))
def handle_del(message: telebot.types.Message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ Ruxsat yo‘q.")
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "❗ Format: <code>del &lt;kod&gt;</code>")
    code = " ".join(parts[1:]).strip()
    deleted = db_delete(code)
    if deleted:
        bot.reply_to(message, f"🗑 O‘chirildi: <code>{code}</code>")
    else:
        bot.reply_to(message, f"❌ Topilmadi: <code>{code}</code>")

# ====== Kod bilan olish ======
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def by_code(message: telebot.types.Message):
    code = message.text.strip()
    row = db_get(code)
    if not row:
        return  # jim turamiz yoki: bot.reply_to(message, "❌ Bunday kod topilmadi.")
    _, category, file_id, media_type = row

    try:
        caption = f"📦 Kod: <code>{code}</code>\n📂 Kategoriya: <b>{category}</b>"
        if media_type == "video":
            bot.send_video(message.chat.id, file_id, caption=caption)
        elif media_type == "document":
            bot.send_document(message.chat.id, file_id, caption=caption)
        elif media_type == "animation":
            bot.send_animation(message.chat.id, file_id, caption=caption)
        elif media_type == "sticker":
            bot.send_sticker(message.chat.id, file_id)
            bot.send_message(message.chat.id, caption)
        else:
            bot.send_document(message.chat.id, file_id, caption=caption)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Yuborishda xato: {e}")

# ====== Run ======
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.skip_pending = True
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
