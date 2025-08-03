import os
import sqlite3
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)
conn = sqlite3.connect("notes.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS notes
                  (user_id INTEGER, tag TEXT, content TEXT)''')
conn.commit()

def start(update, context):
    update.message.reply_text("Welcome to Memo_360Bot! Use /save <tag> <note> to store your notes.")

def save(update, context):
    try:
        tag = context.args[0]
        content = ' '.join(context.args[1:])
        cursor.execute("INSERT INTO notes VALUES (?, ?, ?)", (update.effective_user.id, tag, content))
        conn.commit()
        update.message.reply_text("Note saved under tag: " + tag)
    except:
        update.message.reply_text("Usage: /save <tag> <note>")

def view(update, context):
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, content FROM notes WHERE user_id=?", (user_id,))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("No saved notes.")
    else:
        response = "\n".join([f"[{tag}] {content}" for tag, content in notes])
        update.message.reply_text(response)

def search(update, context):
    keyword = ' '.join(context.args)
    user_id = update.effective_user.id
    cursor.execute("SELECT tag, content FROM notes WHERE user_id=? AND content LIKE ?", (user_id, f"%{keyword}%"))
    notes = cursor.fetchall()
    if not notes:
        update.message.reply_text("No notes found.")
    else:
        response = "\n".join([f"[{tag}] {content}" for tag, content in notes])
        update.message.reply_text(response)

def save_note(update, context):
    if not context.args:
        update.message.reply_text("❗Usage: /save your message here")
        return
    note = ' '.join(context.args)
    user_id = update.effective_user.id

    # You can save this to a database later
    with open(f"notes_{user_id}.txt", "a") as f:
        f.write(note + "\n")

    update.message.reply_text("📝 Saved!")

def recall_notes(update, context):
    user_id = update.effective_user.id
    try:
        with open(f"notes_{user_id}.txt", "r") as f:
            notes = f.read()
        update.message.reply_text("🗃️ Your notes:\n" + notes)
    except FileNotFoundError:
        update.message.reply_text("📭 You don't have any saved notes yet.")


@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("save", save))
dispatcher.add_handler(CommandHandler("view", view))
dispatcher.add_handler(CommandHandler("search", search))
dispatcher.add_handler(CommandHandler("save", save_note))
dispatcher.add_handler(CommandHandler("recall", recall_notes))




if __name__ == "__main__":
    app.run(debug=True)