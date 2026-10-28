import paho.mqtt.client as mqtt
import json

# Por cada topic conocido: que node_id debe traer y que campos son obligatorios
TEMAS_CONOCIDOS = {
    "emergentes/microinvernadero/ambiente/sim_ambiente_01": {
        "node_id": "sim_ambiente_01",
        "campos": ["node_id", "sequence", "uptime_ms", "temperature_c", "humidity_pct", "light_pct"]
    },
    "emergentes/microinvernadero/vibracion/sim_vib_01": {
        "node_id": "sim_vib_01",
        "campos": ["node_id", "run_id", "sequence", "uptime_ms", "sample_rate_hz", "samples_g"]
    }
}

# Ultimo sequence recibido de cada nodo (y de cada corrida, en el caso de vibracion)
# Ejemplo: {("sim_vib_01", "secuencial_01"): 4, ("sim_ambiente_01", None): 12}
ultima_secuencia = {}


# Revisa que el mensaje sea correcto. Devuelve (mensaje, None) si esta bien,
# o (None, motivo) si hay que descartarlo
def validar_mensaje(topic, payload):
    # 1. ¿El topic esta en la lista de TEMAS_CONOCIDOS?
    if topic not in TEMAS_CONOCIDOS:
        return None, "topic desconocido"

    # 2. ¿Es un JSON valido? (try/except para que un mensaje roto no tumbe el programa)
    try:
        mensaje = json.loads(payload)  # Si el texto no es JSON valido, json.loads lanza un error
    except ValueError:
        return None, "no es un JSON valido"

    # 2b. ¿El JSON es un objeto {...}? (un JSON tambien puede ser solo un numero o una lista)
    if not isinstance(mensaje, dict):
        return None, "el JSON no es un objeto {...}"

    esperado = TEMAS_CONOCIDOS[topic]

    # 3. ¿Estan todos los campos obligatorios de este topic?
    faltan = [campo for campo in esperado["campos"] if campo not in mensaje]
    if faltan:
        return None, f"faltan campos: {faltan}"

    # 4. ¿El node_id corresponde al topic por el que llego?
    if mensaje["node_id"] != esperado["node_id"]:
        return None, f"el node_id '{mensaje['node_id']}' no corresponde a este topic"

    # 5. ¿sequence es un numero entero?
    if not isinstance(mensaje["sequence"], int):
        return None, "sequence no es un numero entero"

    # 6. Solo vibracion: ¿samples_g trae exactamente sample_rate_hz (100) numeros?
    if "samples_g" in esperado["campos"]:
        muestras = mensaje["samples_g"]
        if not isinstance(muestras, list) or len(muestras) != mensaje["sample_rate_hz"]:
            return None, f"samples_g debe ser una lista de {mensaje['sample_rate_hz']} muestras"
        if not all(isinstance(valor, (int, float)) for valor in muestras):
            return None, "samples_g tiene valores que no son numeros"

    return mensaje, None


# Compara el sequence que llego con el anterior del mismo nodo.
# Devuelve True si el mensaje se puede usar, False si hay que descartarlo
def revisar_secuencia(mensaje):
    clave = (mensaje["node_id"], mensaje.get("run_id"))  # El nodo ambiental no tiene run_id -> None
    actual = mensaje["sequence"]
    anterior = ultima_secuencia.get(clave)

    # 0. Primer mensaje de este nodo/corrida: no hay con que comparar -> aceptar
    if anterior is None:
        pass
    # 1. Igual al anterior: es un DUPLICADO -> descartar
    elif actual == anterior:
        print(f"  [DUPLICADO] {clave[0]} sequence {actual} ya habia llegado -> descartado")
        return False
    # 2. Es 1: el nodo se REINICIO -> aceptar y empezar a contar de nuevo
    elif actual == 1:
        print(f"  [AVISO] {clave[0]} volvio a empezar en sequence 1 (el nodo se reinicio)")
    # 3. Menor que el anterior: llego TARDE (fuera de orden) -> descartar
    elif actual < anterior:
        print(f"  [FUERA DE ORDEN] {clave[0]} llego sequence {actual} despues de {anterior} -> descartado")
        return False
    # 4. Mayor que anterior + 1: se PERDIERON mensajes en el camino -> avisar y aceptar
    elif actual > anterior + 1:
        print(f"  [SALTO] {clave[0]} paso de sequence {anterior} a {actual}: "
              f"se perdieron {actual - anterior - 1} mensajes")

    # 5. Si no cayo en ningun caso es porque llego el siguiente esperado (anterior + 1) -> aceptar

    ultima_secuencia[clave] = actual  # Guardo este sequence para compararlo con el proximo
    return True


def on_message(client, userdata, message):
    mensaje, motivo = validar_mensaje(message.topic, message.payload)
    if mensaje is None:
        print(f"[RECHAZADO] {message.topic} -> {motivo}")
        return

    if not revisar_secuencia(mensaje):
        return

    if "samples_g" in mensaje:
        muestras = mensaje["samples_g"]
        print(f"[VIBRACION] {mensaje['node_id']} | run {mensaje['run_id']} | "
              f"sequence {mensaje['sequence']:2} | {len(muestras)} muestras | "
              f"min {min(muestras):+.3f} | max {max(muestras):+.3f}")
    else:
        print(f"[AMBIENTE]  {mensaje['node_id']} | sequence {mensaje['sequence']:2} | "
              f"temperatura {mensaje['temperature_c']} °C | humedad {mensaje['humidity_pct']} % | "
              f"luz {mensaje['light_pct']} %")


# Todo lo que arranca el programa va dentro de este if.
# En la Fase 5 es obligatorio: en Windows los procesos del ProcessPoolExecutor
# vuelven a leer este archivo y no deben conectarse otra vez a MQTT
if __name__ == "__main__":
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_message = on_message
    cliente.connect("localhost", 1883, 60)
    cliente.subscribe("emergentes/microinvernadero/#", qos=0)

    print("Suscriptor escuchando emergentes/microinvernadero/# ... (Ctrl+C para salir)")
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("Suscriptor detenido.")
        cliente.disconnect()
