import paho.mqtt.client as mqtt
import json

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

cliente.connect("localhost", 1883, 60)

cliente.subscribe("prueba/mqtt", qos=0)

def on_message(client, userdata, message):
    mensaje = json.loads(message.payload.decode("utf-8"))
    print(f"Mensaje recibido: {mensaje['node_id']} - Temperatura: {mensaje['temperature_c']}")

cliente.on_message = on_message

cliente.loop_forever()
