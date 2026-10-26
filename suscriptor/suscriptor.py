import paho.mqtt.client as mqtt
import json

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

cliente.connect("localhost", 1883, 60)

cliente.subscribe("emergentes/microinvernadero/#", qos=0)

def on_message(client, userdata, message):
    mensaje = json.loads(message.payload.decode("utf-8"))
    print(f"""
        Topic:{message.topic} 
        ID: {mensaje['node_id']}
        Numero de Secuencia: {mensaje['sequence']}""")
    if "samples_g" in mensaje:
        muestras = mensaje["samples_g"]
        print(f"""
            # de Muestras: {len(muestras)}
            Muestra min: {min(muestras)}
            Muestra max: {max(muestras)}""")
    else:
        print(f"""
            Temperatura: {mensaje['temperature_c']} °C
            Humedad: {mensaje['humidity_pct']} %
            Luz: {mensaje['light_pct']} %""")

cliente.on_message = on_message

cliente.loop_forever()