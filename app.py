import os
import sqlite3
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Initialize Flask app
app = Flask(__name__)

# SQLite database setup
conn = sqlite3.connect("notes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        user_id INTEGER,
        tag TEXT,
        content TEXT
    )
''')
conn.commit()

# Bot command: /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to *Memo_360Bot*!\n\n"
        "You can use the following commands:\n"
        "/save <tag> <note> - Save a note\n"
        "/view - View all saved notes\n"
        "/search <keyword> - Search through notes\n"
        "/recall - Recall quick saved notes",
        parse_mode="Markdown"
    )

# Bot command: /save <tag> <note>
def save(update: Update, context: CallbackContext):
    try:
        tag = context.args[0]
        content = ' '.join(context.args[1:])
        cursor.execute("INSERT INTO notes (user_id, tag, content) VALUES (?, ?, ?)",
                       (update.effective_user.id, tag, content))
        conn.commit()
        update.message.reply_text(f"✅ Note saved under tag: `{tag}`", parse_mode="Markdown")
    except IndexError:
        update.message.reply_text("❗Usage: /save <tag> <note>")

# Bot command: /view
def view(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, content FROM notes WHERE user_id=?", (user_id,))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("📭 No saved notes.")
    else:
        response = "\n".join([f"📌 *{tag}*: {content}" for tag, content in notes])
        update.message.reply_text(response, parse_mode="Markdown")

# Bot command: /search <keyword>
def search(update: Update, context: CallbackContext):
    keyword = ' '.join(context.args)
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, content FROM notes WHERE user_id=? AND content LIKE ?", 
                   (user_id, f"%{keyword}%"))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("🔍 No matching notes found.")
    else:
        response = "\n".join([f"🔖 *{tag}*: {content}" for tag, content in notes])
        update.message.reply_text(response, parse_mode="Markdown")

# Bot command: /recall (quick saved notes from file)
def recall_notes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        with open(f"notes_{user_id}.txt", "r") as f:
            notes = f.read()
        update.message.reply_text("📂 Your notes:\n" + notes)
    except FileNotFoundError:
        update.message.reply_text("📭 You don't have any quick-saved notes yet.")

# Flask route to handle Telegram webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Dispatcher and command registration
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("save", save))
dispatcher.add_handler(CommandHandler("view", view))
dispatcher.add_handler(CommandHandler("search", search))
dispatcher.add_handler(CommandHandler("recall", recall_notes))

if __name__ == "__main__":
    app.run(debug=True)