import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Database
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

application = ApplicationBuilder().token(TOKEN).build()

keyboard = ReplyKeyboardMarkup(
    [["📋 Nuovo Intervento"],
     ["📂 Interventi"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Gestionale Lavori Attivo", reply_markup=keyboard)

async def nuovo_intervento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = "cliente"
    await update.message.reply_text("Nome cliente?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.text == "📋 Nuovo Intervento":
        await nuovo_intervento(update, context)
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

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    application.run_polling()
