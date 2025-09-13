# Файл: Aube1g.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import secrets, string, sqlite3, re
from datetime import datetime, timedelta

BOT_TOKEN = "8236417916:AAH7RKGsM-c5xHMtWiXlAmWnQPz44CqRChw"
ADMIN_USERNAME = "Aubeig"
ADMIN_ID = 7467472235

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def init_db():
    conn = sqlite3.connect('anon_bot.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS links (link_id TEXT PRIMARY KEY, user_id INTEGER, title TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (user_id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS messages (message_id INTEGER PRIMARY KEY AUTOINCREMENT, link_id TEXT, from_user_id INTEGER, to_user_id INTEGER, message_text TEXT, message_type TEXT DEFAULT \'text\', file_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (link_id) REFERENCES links (link_id))')
    conn.commit(); conn.close()

def save_user(uid, uname, fname):
    conn = sqlite3.connect('anon_bot.db'); cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (uid, uname, fname))
    conn.commit(); conn.close()

def create_anon_link(uid, title, desc):
    link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    conn = sqlite3.connect('anon_bot.db'); cursor = conn.cursor()
    cursor.execute('INSERT INTO links (link_id, user_id, title, description, expires_at) VALUES (?, ?, ?, ?, ?)', (link_id, uid, title, desc, datetime.now() + timedelta(days=30)))
    conn.commit(); conn.close()
    return link_id

def get_link_info(link_id):
    conn = sqlite3.connect('anon_bot.db'); cursor = conn.cursor()
    cursor.execute('SELECT l.user_id, l.title, l.description, u.username FROM links l JOIN users u ON l.user_id = u.user_id WHERE l.link_id = ?', (link_id,))
    info = cursor.fetchone(); conn.close()
    return info

def save_message(link_id, from_uid, to_uid, text, mtype='text', fid=None):
    conn = sqlite3.connect('anon_bot.db'); cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (link_id, from_user_id, to_user_id, message_text, message_type, file_id) VALUES (?, ?, ?, ?, ?, ?)', (link_id, from_uid, to_uid, text, mtype, fid))
    mid = cursor.lastrowid
    conn.commit(); conn.close()
    return mid

def escape_markdown(text):
    if not text: return ""
    return re.sub(f'([{re.escape(r"_*[]()~`>#+-=|{}.!")}])', r'\\\1', str(text))

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Мои ссылки", callback_data="my_links"), InlineKeyboardButton("➕ Создать ссылку", callback_data="create_link")]
    ])

def admin_keyboard():
    WEB_APP_URL = "https://aube1g-admin-panel.onrender.com" # <-- ЗАМЕНИМ ПОЗЖЕ
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👁️ Открыть веб-панель", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("📢 Оповещение", callback_data="admin_broadcast")]
    ])
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    if context.args:
        link_id = context.args[0]
        link_info = get_link_info(link_id)
        if link_info:
            context.user_data['current_link'] = link_id
            await update.message.reply_text(f"🔗 *Анонимная ссылка*\n\n✍️ Напишите ваше сообщение или отправьте медиа\\.", parse_mode='MarkdownV2')
            return
    await update.message.reply_text("👋 *Добро пожаловать в Анонимный Бот\\!*\n\nИспользуйте кнопки для создания ссылок и получения анонимных сообщений.", reply_markup=main_keyboard(), parse_mode='MarkdownV2')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data == "create_link":
        context.user_data['creating_link'] = 'title'
        await query.edit_message_text("📝 Введите название для вашей ссылки:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; text = update.message.text
    save_user(user.id, user.username, user.first_name)
    if context.user_data.get('creating_link') == 'title':
        context.user_data['link_title'] = text
        context.user_data['creating_link'] = 'description'
        await update.message.reply_text("📋 Теперь введите описание:")
        return
    if context.user_data.get('creating_link') == 'description':
        link_id = create_anon_link(user.id, context.user_data['link_title'], text)
        link_url = f"https://t.me/{context.bot.username}?start={link_id}"
        await update.message.reply_text(f"✅ *Ссылка создана\\!*\n\n`{link_url}`", parse_mode='MarkdownV2', reply_markup=main_keyboard())
        context.user_data.clear()
        return
    if context.user_data.get('current_link'):
        link_id = context.user_data['current_link']
        link_info = get_link_info(link_id)
        if link_info:
            to_user_id = link_info[0]
            save_message(link_id, user.id, to_user_id, text)
            try:
                await context.bot.send_message(chat_id=to_user_id, text=f"📨 *Новое анонимное сообщение*\n\n{escape_markdown(text)}", parse_mode='MarkdownV2')
            except Exception as e: logging.error(f"Notify failed for {to_user_id}: {e}")
            await update.message.reply_text("✅ Отправлено анонимно!", reply_markup=main_keyboard())
            context.user_data.pop('current_link', None)
        return
    await update.message.reply_text("Используйте кнопки.", reply_markup=main_keyboard())

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.user_data.get('current_link'): return
    link_id = context.user_data['current_link']
    link_info = get_link_info(link_id)
    if not link_info: return
    to_user_id, caption = link_info[0], update.message.caption or ""
    fid, mtype = (update.message.photo[-1].file_id, 'photo') if update.message.photo else (update.message.video.file_id, 'video') if update.message.video else (update.message.voice.file_id, 'voice')
    if fid:
        save_message(link_id, user.id, to_user_id, caption, mtype, fid)
        try:
            await context.bot.send_message(chat_id=to_user_id, text=f"📨 *Новое медиа-сообщение ({mtype})*", parse_mode='MarkdownV2')
        except Exception as e: logging.error(f"Notify media failed for {to_user_id}: {e}")
        await update.message.reply_text("✅ Медиа отправлено анонимно!", reply_markup=main_keyboard())
        context.user_data.pop('current_link', None)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username == ADMIN_USERNAME:
        await update.message.reply_text("🛠️ *Панель администратора*", reply_markup=admin_keyboard(), parse_mode='MarkdownV2')

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, handle_media))
    app.run_polling()
    
if __name__ == "__main__": main()
