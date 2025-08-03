# Memo_360Bot

Memo_360Bot is a simple Telegram bot for saving, viewing, and searching personal notes. Notes are stored in a local SQLite database. The bot is built with Python, Flask, and python-telegram-bot.

## Features

- **/start**: Get instructions and available commands.
- **/save `<tag>` `<note>`**: Save a note with a tag.
- **/view**: View all your saved notes.
- **/search `<keyword>`**: Search your notes by keyword.
- **/recall**: Recall quick-saved notes from a text file.

## Requirements

- Python 3.7+
- Telegram Bot Token
- [python-telegram-bot](https://python-telegram-bot.org/)
- Flask
- python-dotenv

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/MemoBot.git
   cd MemoBot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Create a `.env` file in the project root:
     ```
     BOT_TOKEN=your_telegram_bot_token
     ```

## Usage

1. **Run the bot server:**
   ```bash
   python app.py
   ```

2. **Set your Telegram bot webhook to:**
   ```
   https://your-server-address/webhook
   ```

3. **Interact with your bot on Telegram using the supported commands.**

## File Structure

- `app.py`: Main application file containing bot logic and Flask server.
- `notes.db`: SQLite database storing notes.
- `notes_<user_id>.txt`: Quick-saved notes per user.

## License

MIT License

## Author

[Your