import os
import sqlite3
from flask import Flask, request
import telegram
from telegram.ext import CommandHandler, Dispatcher, MessageHandler, Filters

TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

# === SQLite setup ===
conn = sqlite3.connect("notes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tag TEXT,
        note TEXT
    )
''')
conn.commit()

# === Command handlers ===

def start(update, context):
    update.message.reply_text("👋 Welcome to Memo_360Bot!\nUse /help to see what I can do.")

def help_command(update, context):
    help_text = (
        "📌 *Memo_360Bot Commands:*\n"
        "/save <tag> <note> – Save a note under a tag\n"
        "/view – View all your notes\n"
        "/search <keyword> – Search notes\n"
        "/delete <tag> – Delete all notes with a specific tag\n"
        "/clear – Delete all your notes\n"
        "/help – Show this help message"
    )
    update.message.reply_text(help_text, parse_mode=telegram.ParseMode.MARKDOWN)

def save(update, context):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 2:
        update.message.reply_text("❗ Format: /save <tag> <note>")
        return
    tag = args[0]
    note = " ".join(args[1:])
    cursor.execute("INSERT INTO notes (user_id, tag, note) VALUES (?, ?, ?)", (user_id, tag, note))
    conn.commit()
    update.message.reply_text(f"✅ Saved under *{tag}*", parse_mode=telegram.ParseMode.MARKDOWN)

def view(update, context):
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, note FROM notes WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        update.message.reply_text("📭 You have no saved notes.")
        return
    message = "🗂 *Your Notes:*\n"
    for tag, note in rows:
        message += f"🔖 *{tag}*: {note}\n"
    update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN)

def search(update, context):
    user_id = update.effective_user.id
    keyword = " ".join(context.args)
    if not keyword:
        update.message.reply_text("❗ Usage: /search <keyword>")
        return
    cursor.execute("SELECT tag, note FROM notes WHERE user_id=? AND note LIKE ?", (user_id, f"%{keyword}%"))
    results = cursor.fetchall()
    if not results:
        update.message.reply_text("🔍 No matching notes found.")
        return
    message = "🔎 *Search Results:*\n"
    for tag, note in results:
        message += f"🔖 *{tag}*: {note}\n"
    update.message.reply_text(message, parse_mode=telegram.ParseMode.MARKDOWN)

def delete(update, context):
    user_id = update.effective_user.id
    if not context.args:
        update.message.reply_text("❗ Usage: /delete <tag>")
        return
    tag = context.args[0]
    cursor.execute("DELETE FROM notes WHERE user_id=? AND tag=?", (user_id, tag))
    conn.commit()
    update.message.reply_text(f"🗑 Deleted all notes under *{tag}*", parse_mode=telegram.ParseMode.MARKDOWN)

def clear(update, context):
    user_id = update.effective_user.id
    cursor.execute("DELETE FROM notes WHERE user_id=?", (user_id,))
    conn.commit()
    update.message.reply_text("🧹 All your notes have been deleted.")

def unknown(update, context):
    update.message.reply_text("❓ I didn't recognize that command. Use /help to see available commands.")

# === Flask Webhook route ===

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Memo_360Bot is running!"

# === Dispatcher setup ===

dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("save", save))
dispatcher.add_handler(CommandHandler("view", view))
dispatcher.add_handler(CommandHandler("search", search))
dispatcher.add_handler(CommandHandler("delete", delete))
dispatcher.add_handler(CommandHandler("clear", clear))
dispatcher.add_handler(MessageHandler(Filters.command, unknown))  # catch unknown commands

