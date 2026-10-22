import paho.mqtt.client as mqtt
import json
import time
import random

'''
{
  "node_id": "sim_ambiente_01",
  "sequence": 1,
  "uptime_ms": 10000,
  "temperature_c": 24.5,
  "humidity_pct": 58.0,
  "light_pct": 63
}
'''

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Me creo un cliente MQTT con la versión 2 de la API de callbacks
cliente.connect("localhost", 1883, 60) # Me conecto al broker MQTT en localhost, puerto 1883, con un keepalive de 60 segundos

topic = "emergentes/microinvernadero/ambiente/sim_ambiente_01" #"En el proyecto emergentes, del microinvernadero, datos de ambiente, enviados por el nodo sim_ambiente_01"

payload = {
  "node_id": "sim_ambiente_01",
  "sequence": 1,
  "uptime_ms": 0,
  "temperature_c": 24.5,
  "humidity_pct": 58.0,
  "light_pct": 63
}

# Variables para simular los datos de temperatura, humedad y luz
min_temperatura = 18
max_temperatura = 27
min_humedad = 55
max_humedad = 80
min_luz = 0
max_luz = 100

# Función para simular una caminata aleatoria dentro de un rango
def caminata_aleatoria(valor_actual, min_valor, max_valor, paso_maximo, decimales):
    paso = random.uniform(-paso_maximo, paso_maximo)
    nuevo_valor = valor_actual + paso
    limitado = max(min(nuevo_valor, max_valor), min_valor)
    return round(limitado, decimales)

cliente.loop_start()

# time.time() devuelve la hora actual en SEGUNDOS (ej: 1792366085.31)
hora_inicio = time.time()

while True:
    try:
        ahora = time.time()
        
        segundos_transcurridos = ahora - hora_inicio
        
        # Construyo el payload con los datos simulados
        payload["uptime_ms"] = int(segundos_transcurridos * 1000) #lo paso a milisegundos y le quito los decimales
        
        payload["temperature_c"] = caminata_aleatoria(payload["temperature_c"], min_temperatura, max_temperatura, 0.5, 2) # Simula cambios pequeños en la temperatura
        payload["humidity_pct"] = caminata_aleatoria(payload["humidity_pct"], min_humedad, max_humedad, 0.5, 2) 
        payload["light_pct"] = caminata_aleatoria(payload["light_pct"], min_luz, max_luz, 1.0, 1)
        
        datos = json.dumps(payload) # Convierte el diccionario payload a una cadena JSON para enviarlo por MQTT
        
        print(f"Enviando datos: {datos}")
        
        comprobante = cliente.publish(topic, datos)
        comprobante.wait_for_publish()
        
        payload["sequence"] += 1
        
        time.sleep(10)
    except KeyboardInterrupt:
        print("Interrupción del programa. Saliendo...")
        break 

print("Deteniendo cliente MQTT...")
cliente.disconnect()
cliente.loop_stop()
print("Programa finalizado.")
