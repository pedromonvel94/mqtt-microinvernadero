import paho.mqtt.client as mqtt
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

topic = "emergentes/microinvernadero/ambiente/sim_ambiente_01" #"En el proyecto emergentes, del microinvernadero, datos de ambiente, enviados por el nodo sim_ambiente_01"

payload = {
  "node_id": "sim_vib_01",
  "run_id": "secuencial_01",
  "sequence": 1,
  "uptime_ms": 0,
  "sample_rate_hz": 100,
  "samples_g": [0.02, -0.01, 0.03]
}