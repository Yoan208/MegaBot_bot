import os
import telebot
from flask import Flask, request
from mega_local import Mega   # usamos la versión local corregida

# =========================
# CONFIGURACIÓN
# =========================

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("❌ No se encontró la variable de entorno TOKEN. Configúrala en Render.")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_TELEGRAM_FILE_SIZE = int(1.9 * 1024 * 1024 * 1024)  # ~1.9GB

# =========================
# FUNCIÓN DE DESCARGA MEGA
# =========================

def mega_download(url: str, output_dir: str) -> str:
    m = Mega()
    m.login()  # login anónimo
    try:
        file_path = m.download_url(url, output_dir)
    except Exception as e:
        raise ValueError(f"Error al procesar el enlace MEGA: {e}")
    if not file_path or not os.path.exists(file_path):
        raise ValueError("No se pudo descargar el archivo desde MEGA.")
    return file_path

# =========================
# HANDLERS DE TELEGRAM
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hola 👋, envíame un enlace de MEGA completo (incluyendo la parte después de #).")

@bot.message_handler(func=lambda m: "mega.nz" in m.text)
def handle_message(message):
    msg = bot.reply_to(message, "🔍 Procesando enlace...")
    file_path = None
    try:
        bot.edit_message_text("⬇️ Descargando archivo desde MEGA...", msg.chat.id, msg.message_id)
        file_path = mega_download(message.text.strip(), DOWNLOAD_DIR)
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_mb = round(file_size / (1024 * 1024), 2)

        if file_size > MAX_TELEGRAM_FILE_SIZE:
            bot.edit_message_text(
                f"⚠️ El archivo es demasiado grande para Telegram.\n{filename} — {size_mb} MB",
                msg.chat.id, msg.message_id
            )
            return

        bot.edit_message_text(f"📤 Enviando archivo ({size_mb} MB)...", msg.chat.id, msg.message_id)
        with open(file_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"Archivo: {filename}")
        bot.edit_message_text("✅ Archivo enviado correctamente.", msg.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", msg.chat.id, msg.message_id)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# =========================
# ENDPOINTS FLASK PARA WEBHOOKS
# =========================

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://TU-SERVICIO.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))






