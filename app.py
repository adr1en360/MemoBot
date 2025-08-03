import os
import sqlite3
from flask import Flask, request
from telegram import Bot, Update, InputFile
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

# Flask setup
app = Flask(__name__)

# SQLite setup
conn = sqlite3.connect("notes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        user_id INTEGER,
        tag TEXT,
        note TEXT
    )
''')
conn.commit()

# Commands
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to MemoBot!\n\n"
        "Use the following commands:\n"
        "/save <tag> <note>\n"
        "/view - View all notes\n"
        "/search <keyword>\n"
        "/delete <tag>\n"
        "/export - Export all notes"
    )

def save(update: Update, context: CallbackContext):
    try:
        tag = context.args[0]
        note = ' '.join(context.args[1:])
        cursor.execute("INSERT INTO notes (user_id, tag, note) VALUES (?, ?, ?)",
                       (update.effective_user.id, tag, note))
        conn.commit()
        update.message.reply_text(f"✅ Saved under `{tag}`", parse_mode='Markdown')
    except IndexError:
        update.message.reply_text("❗Usage: /save <tag> <note>")

def view(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, note FROM notes WHERE user_id=?", (user_id,))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("📭 No saved notes.")
    else:
        response = "\n".join([f"📌 {tag}: {note}" for tag, note in notes])
        update.message.reply_text(response)

def search(update: Update, context: CallbackContext):
    keyword = ' '.join(context.args)
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, note FROM notes WHERE user_id=? AND note LIKE ?", 
                   (user_id, f"%{keyword}%"))
    results = cursor.fetchall()
    if results:
        response = "\n".join([f"🔍 {tag}: {note}" for tag, note in results])
        update.message.reply_text(response)
    else:
        update.message.reply_text("🔍 No matching notes found.")

def delete(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not context.args:
        update.message.reply_text("❗Usage: /delete <tag>")
        return
    tag = context.args[0]
    cursor.execute("DELETE FROM notes WHERE user_id=? AND tag=?", (user_id, tag))
    deleted = cursor.rowcount
    conn.commit()
    if deleted:
        update.message.reply_text(f"🗑️ Deleted {deleted} note(s) under `{tag}`", parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ No notes found for that tag.")

def export_notes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, note FROM notes WHERE user_id=?", (user_id,))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("📭 No notes to export.")
        return

    content = ""
    for tag, note in notes:
        content += f"[{tag}] {note}\n"

    file = BytesIO()
    file.write(content.encode('utf-8'))
    file.seek(0)
    update.message.reply_document(InputFile(file, filename="your_notes.txt"))

# Webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Dispatcher
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("save", save))
dispatcher.add_handler(CommandHandler("view", view))
dispatcher.add_handler(CommandHandler("search", search))
dispatcher.add_handler(CommandHandler("delete", delete))
dispatcher.add_handler(CommandHandler("export", export_notes))

# Run server
if __name__ == "__main__":
    app.run(debug=True)