import os
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

# Leo el token y mi chat del archivo .env, así no quedan escritos en el código
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_AUTORIZADO = int(os.getenv("TELEGRAM_CHAT_ID"))

TOPIC_AMBIENTE = "emergentes/microinvernadero/ambiente/sim_ambiente_01"  # El mismo topic de la EA1

# Aquí guardo la última lectura de cada fuente, cada una en su clave (None = todavía no llega nada)
lecturas = {
    "mqtt": None,
    "telegram": None
}


# ---------- Ruta 1: MQTT (automática) ----------

# Esta función se ejecuta sola cada vez que sim_ambiente_01 publica algo
def on_message(client, userdata, message):
    try:
        datos = json.loads(message.payload)  # Paso el texto JSON a diccionario
        lecturas["mqtt"] = {
            "temperatura": datos["temperature_c"],
            "humedad": datos["humidity_pct"]
        }
        print(f"[MQTT] {lecturas['mqtt']}")
    except (ValueError, KeyError):
        print("[MQTT] Me llegó un mensaje dañado o incompleto, lo ignoro")  # Así el programa no se cae


# ---------- Ruta 2: Telegram (manual) ----------

# Responde /ayuda con los comandos que tengo
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/medir <temperatura> <humedad>  Registra una lectura manual. Ej: /medir 24.5 68\n"
        "/estado  Muestra la última lectura de cada fuente\n"
        "/ayuda  Muestra este mensaje"
    )


# ---------- Arranque del programa ----------

# 1. Prendo MQTT primero y lo dejo trabajando por detrás
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_message = on_message
cliente.connect("localhost", 1883, 60)
cliente.subscribe(TOPIC_AMBIENTE)
cliente.loop_start()  # Con loop_start MQTT corre en segundo plano y el programa sigue a la siguiente línea

# 2. Armo el bot y le digo que solo me atienda a mí
app = ApplicationBuilder().token(TOKEN).build()
solo_yo = filters.Chat(chat_id=CHAT_AUTORIZADO)  # Si me escribe otra persona, la ignoro
app.add_handler(CommandHandler("ayuda", ayuda, filters=solo_yo))

print(f"Programa central escuchando MQTT en {TOPIC_AMBIENTE} y Telegram. Ctrl+C para salir.")

# 3. Prendo Telegram de último porque run_polling se queda aquí pegado hasta que presiono Ctrl+C
app.run_polling()

# Cuando presiono Ctrl+C, apago MQTT bien
cliente.loop_stop()
cliente.disconnect()
print("Programa central detenido.")
