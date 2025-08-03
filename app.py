import os
import sqlite3
from flask import Flask, request, send_file
from telegram import (
    Bot, Update, InlineKeyboardButton,
    InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Dispatcher, CommandHandler, MessageHandler,
    Filters, CallbackContext, CallbackQueryHandler
)
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Set up dispatcher
dispatcher = Dispatcher(bot, None, use_context=True)

# Ensure the database exists
def init_db():
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tag TEXT,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Command Handlers ---

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📝 *Welcome to MemoBot!*\n\n"
        "You can save, view, search, and export notes right from Telegram.\n\n"
        "Available commands:\n"
        "`/save <tag> <note>` - Save a note\n"
        "`/view <tag>` - View notes\n"
        "`/search <keyword>` - Search your notes\n"
        "`/delete <tag>` - Delete a note\n"
        "`/export` - Export all notes\n",
        parse_mode='Markdown'
    )

def save(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args

    if len(args) < 2:
        update.message.reply_text("❌ Use format: `/save tag note`", parse_mode='Markdown')
        return

    tag = args[0]
    note = ' '.join(args[1:])

    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, tag, note) VALUES (?, ?, ?)", (user_id, tag, note))
    conn.commit()
    conn.close()

    update.message.reply_text("✅ Note saved under *{}*.".format(tag), parse_mode='Markdown')

def view(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args

    if len(args) != 1:
        update.message.reply_text("❌ Use format: `/view tag`", parse_mode='Markdown')
        return

    tag = args[0]

    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("SELECT note FROM notes WHERE user_id = ? AND tag = ?", (user_id, tag))
    results = c.fetchall()
    conn.close()

    if results:
        text = f"📒 *Notes under `{tag}`:*\n\n"
        for i, (note,) in enumerate(results, 1):
            text += f"{i}. {note}\n"
        update.message.reply_text(text, parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ No notes found under this tag.")

def search(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args

    if len(args) < 1:
        update.message.reply_text("❌ Use format: `/search keyword`", parse_mode='Markdown')
        return

    keyword = ' '.join(args)

    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("SELECT tag, note FROM notes WHERE user_id = ? AND note LIKE ?", (user_id, f"%{keyword}%"))
    results = c.fetchall()
    conn.close()

    if results:
        text = f"🔍 *Search results for `{keyword}`:*\n\n"
        for tag, note in results:
            text += f"- ({tag}) {note}\n"
        update.message.reply_text(text, parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ No matches found.")

def delete(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args

    if len(args) != 1:
        update.message.reply_text("❌ Use format: `/delete tag`", parse_mode='Markdown')
        return

    tag = args[0]

    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE user_id = ? AND tag = ?", (user_id, tag))
    deleted = c.rowcount
    conn.commit()
    conn.close()

    if deleted:
        update.message.reply_text(f"🗑️ Deleted {deleted} note(s) under `{tag}`.", parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ No notes found to delete.")

def export_notes(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("SELECT tag, note FROM notes WHERE user_id = ?", (user_id,))
    notes = c.fetchall()
    conn.close()

    if not notes:
        update.message.reply_text("⚠️ You have no saved notes.")
        return

    output = ""
    tags = {}
    for tag, note in notes:
        tags.setdefault(tag, []).append(note)

    for tag, entries in tags.items():
        output += f"Tag: {tag}\n"
        for note in entries:
            output += f"- {note}\n"
        output += "\n"

    file = BytesIO()
    file.write(output.encode("utf-8"))
    file.seek(0)
    update.message.reply_document(InputFile(file, filename="your_notes.txt"))

def inline_buttons(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💾 Save", switch_inline_query_current_chat="/save ")],
        [InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat="/search ")],
        [InlineKeyboardButton("📂 View", switch_inline_query_current_chat="/view ")],
        [InlineKeyboardButton("🗑 Delete", switch_inline_query_current_chat="/delete ")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Use buttons to send commands:", reply_markup=reply_markup)

# --- Dispatcher Setup ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("save", save))
dispatcher.add_handler(CommandHandler("view", view))
dispatcher.add_handler(CommandHandler("search", search))
dispatcher.add_handler(CommandHandler("delete", delete))
dispatcher.add_handler(CommandHandler("export", export_notes))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^\s*/?$'), inline_buttons))

# --- Webhook Route ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "MemoBot is running!"

# --- Start Flask App ---
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
