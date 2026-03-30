import os
import telebot
from flask import Flask, request
from mega_local import Mega   # tu copia local del fork corregido

# =========================
# CONFIGURACIÓN
# =========================

TOKEN = os.getenv("TOKEN")
MEGA_USER = os.getenv("MEGA_USER")
MEGA_PASS = os.getenv("MEGA_PASS")

if not TOKEN or not MEGA_USER or not MEGA_PASS:
    raise RuntimeError("❌ Faltan variables de entorno: TOKEN, MEGA_USER, MEGA_PASS")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_TELEGRAM_FILE_SIZE = int(1.9 * 1024 * 1024 * 1024)  # ~1.9GB

# =========================
# LOGIN A MEGA
# =========================

def mega_login():
    m = Mega()
    return m.login(MEGA_USER, MEGA_PASS)

# =========================
# HANDLERS DE TELEGRAM
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hola 👋, usa /listar para ver tus archivos en MEGA o /descargar <nombre> para bajar uno.")

@bot.message_handler(commands=['listar'])
def listar(message):
    m = mega_login()
    files = m.get_files()
    nombres = [finfo['a']['n'] for fid, finfo in files.items() if 'a' in finfo and 'n' in finfo['a']]
    if not nombres:
        bot.reply_to(message, "📂 Tu nube está vacía.")
    else:
        respuesta = "📂 Archivos en tu nube:\n" + "\n".join(nombres)
        bot.reply_to(message, respuesta)

@bot.message_handler(commands=['descargar'])
def descargar(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Debes indicar el nombre del archivo. Ejemplo: /descargar archivo.zip")
        return
    nombre = args[1]
    m = mega_login()
    files = m.get_files()
    for fid, finfo in files.items():
        if 'a' in finfo and finfo['a'].get('n') == nombre:
            path = m.download(fid, output_dir=DOWNLOAD_DIR)
            file_size = os.path.getsize(path)
            if file_size > MAX_TELEGRAM_FILE_SIZE:
                bot.reply_to(message, f"⚠️ El archivo {nombre} es demasiado grande para Telegram ({round(file_size/1024/1024,2)} MB).")
                os.remove(path)
                return
            with open(path, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"Archivo: {nombre}")
            os.remove(path)
            return
    bot.reply_to(message, f"❌ No encontré el archivo {nombre} en tu nube.")

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









