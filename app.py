import os
import sqlite3
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS interventi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        descrizione TEXT,
        stato TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ore (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intervento_id INTEGER,
        tecnico TEXT,
        ore REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS note (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intervento_id INTEGER,
        tecnico TEXT,
        testo TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS foto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intervento_id INTEGER,
        tecnico TEXT,
        file_id TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

init_db()

application = ApplicationBuilder().token(TOKEN).build()

keyboard = ReplyKeyboardMarkup(
    [["📋 Nuovo Intervento"],
     ["📂 Interventi"],
     ["🕒 Inserisci Ore"],
     ["📝 Nota"],
     ["📸 Foto"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Gestionale Lavori Attivo", reply_markup=keyboard)

async def nuovo_intervento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["step"] = "cliente"
    await update.message.reply_text("Nome cliente?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    step = context.user_data.get("step")

    if step == "cliente":
        context.user_data["cliente"] = update.message.text
        context.user_data["step"] = "descrizione"
        await update.message.reply_text("Descrizione lavoro?")
        return

    if step == "descrizione":
        cliente = context.user_data["cliente"]
        descrizione = update.message.text

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO interventi (cliente, descrizione, stato) VALUES (?, ?, ?)",
                  (cliente, descrizione, "Aperto"))
        conn.commit()
        conn.close()

        context.user_data.clear()
        await update.message.reply_text("Intervento creato.")
        return

    if update.message.text == "📋 Nuovo Intervento":
        await nuovo_intervento(update, context)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Bot attivo"

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=os.environ.get("RENDER_EXTERNAL_URL") + "/" + TOKEN
    )
