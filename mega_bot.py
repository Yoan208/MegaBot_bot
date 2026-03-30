import os
import telebot
from mega import Mega

# =========================
# CONFIGURACIÓN
# =========================

TOKEN = os.getenv("TOKEN")  # Render guardará tu token como variable de entorno
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_TELEGRAM_FILE_SIZE = int(1.9 * 1024 * 1024 * 1024)  # ~1.9GB

# =========================
# FUNCIÓN DE DESCARGA MEGA
# =========================

def mega_download(url: str, output_dir: str) -> str:
    """
    Descarga un archivo desde MEGA usando mega.py
    y devuelve la ruta del archivo descargado.
    """
    m = Mega()
    try:
        file_path = m.download_url(url, output_dir)
        if not file_path or not os.path.exists(file_path):
            raise ValueError("No se pudo descargar el archivo desde MEGA.")
        return file_path
    except Exception as e:
        raise RuntimeError(f"Error al procesar el enlace MEGA: {e}")

# =========================
# HANDLERS
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Hola 👋\n\nEnvíame un enlace de MEGA (completo, con la clave después del #) y te enviaré el archivo."
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "Formato correcto de enlace: https://mega.nz/file/<ID>#<CLAVE>")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()

    if "mega.nz" not in text:
        return

    msg = bot.reply_to(message, "🔍 Procesando enlace...")

    file_path = None
    try:
        bot.edit_message_text("⬇️ Descargando archivo desde MEGA...", msg.chat.id, msg.message_id)

        file_path = mega_download(text, DOWNLOAD_DIR)
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_mb = round(file_size / (1024 * 1024), 2)

        if file_size > MAX_TELEGRAM_FILE_SIZE:
            bot.edit_message_text(
                f"⚠️ El archivo es demasiado grande para Telegram.\n"
                f"{filename} — {size_mb} MB",
                msg.chat.id,
                msg.message_id
            )
            return

        bot.edit_message_text(
            f"📤 Enviando archivo ({size_mb} MB)...",
            msg.chat.id,
            msg.message_id
        )

        with open(file_path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"Archivo: {filename}")

        bot.edit_message_text("✅ Archivo enviado correctamente.", msg.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", msg.chat.id, msg.message_id)

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

# =========================
# MAIN
# =========================

bot.infinity_polling()


