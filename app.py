import os
import sqlite3
import telebot

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS interventi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            descrizione TEXT,
            stato TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "Gestionale Lavori Attivo\n\nScrivi:\nnuovo")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.lower()

    if text == "nuovo":
        user_states[message.chat.id] = "cliente"
        bot.send_message(message.chat.id, "Nome cliente?")
        return

    state = user_states.get(message.chat.id)

    if state == "cliente":
        user_states[message.chat.id] = {"cliente": message.text}
        bot.send_message(message.chat.id, "Descrizione lavoro?")
        return

    if isinstance(state, dict):
        cliente = state["cliente"]
        descrizione = message.text

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO interventi (cliente, descrizione, stato) VALUES (?, ?, ?)",
                  (cliente, descrizione, "Aperto"))
        conn.commit()
        conn.close()

        user_states.pop(message.chat.id)
        bot.send_message(message.chat.id, "Intervento creato.")

print("Bot avviato...")
bot.infinity_polling()
