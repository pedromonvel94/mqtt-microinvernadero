import paho.mqtt.client as mqtt
import math
import json
import time
import random

'''
{
  "node_id": "sim_vib_01",
  "run_id": "secuencial_01",
  "sequence": 1,
  "uptime_ms": 0,
  "sample_rate_hz": 100,
  "samples_g": [0.02, -0.01, 0.03]
}
'''

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Me creo un cliente MQTT con la versión 2 de la API de callbacks
cliente.connect("localhost", 1883, 60) # Me conecto al broker MQTT en localhost, puerto 1883, con un keepalive de 60 segundos

topic = "emergentes/microinvernadero/vibracion/sim_vib_01" #"En el proyecto emergentes, del microinvernadero, datos de vibración, enviados por el nodo sim_vib_01"

payload = {
  "node_id": "sim_vib_01",
  "run_id": "secuencial_01",
  "sequence": 1,
  "uptime_ms": 0,
  "sample_rate_hz": 100,
  "samples_g": [0.02, -0.01, 0.03]
}

hz = 100         # muestras por segundo 
frecuencia = 5   # Que tan rapido vibra
amplitud = 0.02   # Que tan alto vibra
ruido = 0.005      # Que tan ruidosa es la señal
ventanas_por_corrida = 10  # Cuantas ventanas de datos voy a generar
factor_anomalia = 2

random.seed(42) # Establezco la semilla para que la secuencia de números aleatorios sea siempre la misma, para poder reproducir los resultados

def generar_onda(hz, frecuencia, amplitud, ruido):
  muestras = []
  for i in range(hz):
    t = i / hz # Tiempo en segundos de la muestra actual

    # Altura de la onda en ese momento: siempre entre -amplitud y +amplitud mas un poco de ruido aleatorio
    valor = round((amplitud * math.sin(2 * math.pi * frecuencia * t)) + random.uniform(-ruido, ruido), 3) # Le agrego un poco de ruido aleatorio a la onda

    muestras.append(valor) # Guardo la muestra en la lista

  return muestras

cliente.loop_start()

# time.time() devuelve la hora actual en SEGUNDOS (ej: 1792366085.31)
hora_inicio = time.time()

for numero_ventana in range(1, ventanas_por_corrida + 1): # Genero 10 ventanas de datos, numeradas del 1 al 10
  payload["sequence"] = numero_ventana    
  segundos_transcurridos = time.time() - hora_inicio
  payload["uptime_ms"] = int(segundos_transcurridos * 1000)
  
  if numero_ventana in [3, 7]: # Simulo que en la ventana 3 y 7 hay un evento de vibración más fuerte
    payload["samples_g"] = generar_onda(hz, frecuencia, amplitud * factor_anomalia, ruido) # Genero una onda con el doble de amplitud para simular un evento de vibración más fuerte
  else:
    payload["samples_g"] = generar_onda(hz, frecuencia, amplitud, ruido) # Genero una onda normal

  # Envío el payload por MQTT
  comprobante = cliente.publish(topic, json.dumps(payload))
  comprobante.wait_for_publish() # Espero a que se publique el mensaje antes de continuar

  # Muestro un resumen corto en la terminal (lo que se PUBLICA sigue llevando las 100 muestras completas)
  muestras = payload["samples_g"]
  print(f"Ventana {payload['sequence']:2} | uptime {payload['uptime_ms']:5} ms | "
        f"samples_g {muestras[:5]} ... ({len(muestras)} muestras) | "
        f"min {min(muestras):+.3f} | max {max(muestras):+.3f}")

  time.sleep(1)

print("Deteniendo cliente MQTT...")
cliente.disconnect()
cliente.loop_stop()
print("Programa finalizado.")