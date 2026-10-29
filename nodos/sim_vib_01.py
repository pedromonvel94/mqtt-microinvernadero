import paho.mqtt.client as mqtt
import math
import json
import time
import random
import sys

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
factor_anomalia = 2

# Datos que se pasan al ejecutar. Ejemplo: py nodos\sim_vib_01.py secuencial 5 10
# Python guarda esas palabras en la lista sys.argv:
#   sys.argv[0] -> el nombre del archivo
#   sys.argv[1] -> modo (secuencial o paralelo), se usa para armar el run_id
#   sys.argv[2] -> cuantas corridas enviar seguidas
#   sys.argv[3] -> cuantos lotes tiene cada corrida
# Si no se pasa nada: 1 corrida de 10 lotes con run_id "prueba_01"
if len(sys.argv) > 1:     # ¿Escribiste algo despues del nombre del archivo?
  modo = sys.argv[1]      # Si -> modo = "secuencial" (o "paralelo")
else:
  modo = "prueba"         # No -> usa "prueba"

if len(sys.argv) > 2:          # ¿Escribiste un segundo dato?
  corridas = int(sys.argv[2])  # Si -> corridas = 5 (int convierte el texto "5" en el numero 5)
else:
  corridas = 1                 # No -> manda 1 sola corrida

if len(sys.argv) > 3:                      # ¿Escribiste un tercer dato?
  lotes_por_corrida = int(sys.argv[3])  # Si -> usa ese numero de lotes
else:
  lotes_por_corrida = 10                # No -> 10 lotes por corrida, como pide el enunciado

pausa_entre_corridas = 3  # Segundos de espera entre una corrida y la siguiente

print(f"Modo: {modo} | Corridas: {corridas} | Lotes por corrida: {lotes_por_corrida}")

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

for numero_corrida in range(1, corridas + 1):
  payload["run_id"] = f"{modo}_{numero_corrida:02}" # Ejemplo: secuencial_01, secuencial_02 ... paralelo_05

  # Reinicio la semilla en cada corrida: TODAS las corridas envian exactamente los mismos lotes,
  # asi los dos modos analizan los mismos datos y se pueden comparar
  random.seed(42)

  print(f"--- Corrida {payload['run_id']}: {lotes_por_corrida} lotes ---")

  for numero_lote in range(1, lotes_por_corrida + 1): # Genero los lotes de la corrida, numerados desde 1
    payload["sequence"] = numero_lote
    segundos_transcurridos = time.time() - hora_inicio
    payload["uptime_ms"] = int(segundos_transcurridos * 1000)

    if numero_lote in [3, 7]: # Simulo que en el lote 3 y 7 hay un evento de vibración más fuerte
      payload["samples_g"] = generar_onda(hz, frecuencia, amplitud * factor_anomalia, ruido) # Genero una onda con el doble de amplitud para simular un evento de vibración más fuerte
    else:
      payload["samples_g"] = generar_onda(hz, frecuencia, amplitud, ruido) # Genero una onda normal

    # Envío el payload por MQTT
    comprobante = cliente.publish(topic, json.dumps(payload))
    comprobante.wait_for_publish() # Espero a que se publique el mensaje antes de continuar

    # Muestro un resumen corto en la terminal (lo que se PUBLICA sigue llevando las 100 muestras completas)
    muestras = payload["samples_g"]
    print(f"Lote {payload['sequence']:2} | uptime {payload['uptime_ms']:6} ms | "
          f"samples_g {muestras[:5]} ... ({len(muestras)} muestras) | "
          f"min {min(muestras):+.3f} | max {max(muestras):+.3f}")

    time.sleep(1)

  if numero_corrida < corridas:
    time.sleep(pausa_entre_corridas) # Pequeña pausa para separar una corrida de la siguiente

print("Deteniendo cliente MQTT...")
cliente.disconnect()
cliente.loop_stop()
print("Programa finalizado.")