import paho.mqtt.client as mqtt
import json

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.connect("localhost", 1883, 60)

cliente.loop_start()

diccionario = {
  "node_id": "sim_ambiente_01",
  "sequence": 1,
  "temperature_c": 24.5
}

datos = json.dumps(diccionario)

comprobante = cliente.publish("prueba/mqtt", datos)
comprobante.wait_for_publish()
cliente.disconnect()

cliente.loop_stop()