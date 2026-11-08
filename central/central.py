import os
import json
import math
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


# Ruta 1: MQTT (automática)

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


# Ruta 2: Telegram (manual)

# Responde /ayuda con los comandos que tengo
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/medir <temperatura> <humedad>  Registra una lectura manual. Ej: /medir 24.5 68\n"
        "/estado  Muestra la última lectura de cada fuente\n"
        "/ayuda  Muestra este mensaje"
    )


# Convierte el texto a número; si no se puede, devuelve None
def convertir_numero(texto):
    try:
        return float(texto)
    except ValueError:
        return None


# Responde /medir: valida la temperatura y la humedad y, si todo está bien, las guarda en la cajita de Telegram
async def medir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partes = context.args  # Las palabras que escribí después de /medir. Ej: ["24.5", "68"]

    # 1. ¿Escribí exactamente dos valores?
    if len(partes) != 2:
        await update.message.reply_text("Error: debes enviar dos valores. Uso: /medir <temperatura> <humedad>. Ej: /medir 24.5 68")
        return

    temperatura = convertir_numero(partes[0])
    humedad = convertir_numero(partes[1])

    # 2. ¿La temperatura es un número?
    if temperatura is None:
        await update.message.reply_text(f"Error: la temperatura '{partes[0]}' no es un número. Usa punto para los decimales. Ej: 24.5")
        return

    # 3. ¿La humedad es un número?
    if humedad is None:
        await update.message.reply_text(f"Error: la humedad '{partes[1]}' no es un número. Usa punto para los decimales. Ej: 68")
        return

    # 4. ¿Son finitos? float() acepta "nan" e "inf", por eso lo reviso aparte
    if not math.isfinite(temperatura):
        await update.message.reply_text("Error: la temperatura debe ser un número finito (no se acepta nan ni inf).")
        return
    if not math.isfinite(humedad):
        await update.message.reply_text("Error: la humedad debe ser un número finito (no se acepta nan ni inf).")
        return

    # 5. ¿La humedad está entre 0 y 100?
    if humedad < 0 or humedad > 100:
        await update.message.reply_text(f"Error: la humedad debe estar entre 0 y 100. Enviaste {humedad:g}.")
        return

    # Si llegué hasta aquí todo está bien: guardo la lectura (solo en la cajita de Telegram)
    lecturas["telegram"] = {
        "temperatura": temperatura,
        "humedad": humedad
    }
    print(f"[TELEGRAM] {lecturas['telegram']}")
    await update.message.reply_text(f"Lectura manual registrada: {temperatura:g} °C, {humedad:g} % HR.")  # :g quita el .0 sobrante


# Convierte una lectura en texto; si la cajita está vacía, simplemente digo que no hay datos
def describir(lectura):
    if lectura is None:
        return "sin datos todavía"
    else:
        return f"{lectura['temperatura']:g} °C, {lectura['humedad']:g} % HR"


# Responde /estado: muestra cada fuente por separado, sin mezclarlas
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Última lectura MQTT: {describir(lecturas['mqtt'])}\n"
        f"Última lectura Telegram: {describir(lecturas['telegram'])}"
    )


# Arranque del programa

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
app.add_handler(CommandHandler("medir", medir, filters=solo_yo))
app.add_handler(CommandHandler("estado", estado, filters=solo_yo))

print(f"Programa central escuchando MQTT en {TOPIC_AMBIENTE} y Telegram. Ctrl+C para salir.")

# 3. Prendo Telegram de último porque run_polling se queda aquí pegado hasta que presiono Ctrl+C
app.run_polling()

# Cuando presiono Ctrl+C, apago MQTT bien
cliente.loop_stop()
cliente.disconnect()
print("Programa central detenido.")
