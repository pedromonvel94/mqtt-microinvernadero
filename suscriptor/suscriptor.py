import paho.mqtt.client as mqtt
import json
import time
import statistics
import os
import sys
import psutil
from concurrent.futures import ProcessPoolExecutor
from analisis import analizar_ventana

# Modo: py suscriptor\suscriptor.py secuencial  o  py suscriptor\suscriptor.py paralelo
if len(sys.argv) > 1:
    MODO = sys.argv[1]
else:
    MODO = "secuencial"

if MODO == "paralelo":
    TRABAJADORES = 4
else:
    TRABAJADORES = 1

VENTANAS_POR_CORRIDA = 10
ARCHIVO_RESULTADOS = "resultados/resultados.csv"

# Topics permitidos, con su node_id y sus campos obligatorios
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

ultima_secuencia = {}   # Ultimo sequence de cada nodo
corridas_en_curso = {}  # Tiempos y anomalias de cada corrida


# Devuelve el mensaje como diccionario si esta bien, o None si esta malo
def validar_mensaje(topic, payload):
    # 1. ¿Topic conocido?
    if topic not in TEMAS_CONOCIDOS:
        print(f"[RECHAZADO] {topic} -> topic desconocido")
        return None

    # 2. ¿JSON valido?
    try:
        mensaje = json.loads(payload)
    except ValueError:
        print(f"[RECHAZADO] {topic} -> no es un JSON valido")
        return None

    # 2b. ¿Es un objeto {...}?
    if not isinstance(mensaje, dict):
        print(f"[RECHAZADO] {topic} -> el JSON no es un objeto {{...}}")
        return None

    esperado = TEMAS_CONOCIDOS[topic]

    # 3. ¿Estan todos los campos?
    faltan = [campo for campo in esperado["campos"] if campo not in mensaje]
    if faltan:
        print(f"[RECHAZADO] {topic} -> faltan campos: {faltan}")
        return None

    # 4. ¿El node_id corresponde al topic?
    if mensaje["node_id"] != esperado["node_id"]:
        print(f"[RECHAZADO] {topic} -> el node_id '{mensaje['node_id']}' no corresponde a este topic")
        return None

    # 5. ¿sequence es entero?
    if not isinstance(mensaje["sequence"], int):
        print(f"[RECHAZADO] {topic} -> sequence no es un numero entero")
        return None

    # 6. Vibracion: ¿samples_g trae 100 numeros?
    if "samples_g" in esperado["campos"]:
        muestras = mensaje["samples_g"]
        if not isinstance(muestras, list) or len(muestras) != mensaje["sample_rate_hz"]:
            print(f"[RECHAZADO] {topic} -> samples_g debe tener {mensaje['sample_rate_hz']} muestras")
            return None
        if not all(isinstance(valor, (int, float)) for valor in muestras):
            print(f"[RECHAZADO] {topic} -> samples_g tiene valores que no son numeros")
            return None

    return mensaje


# Devuelve True si el mensaje se usa, False si se descarta
def revisar_secuencia(mensaje):
    clave = (mensaje["node_id"], mensaje.get("run_id"))
    actual = mensaje["sequence"]
    anterior = ultima_secuencia.get(clave)

    # 0. Primer mensaje -> aceptar
    if anterior is None:
        pass
    # 1. Duplicado -> descartar
    elif actual == anterior:
        print(f"  [DUPLICADO] {clave[0]} sequence {actual} ya habia llegado -> descartado")
        return False
    # 2. Reinicio -> aceptar
    elif actual == 1:
        print(f"  [AVISO] {clave[0]} volvio a empezar en sequence 1 (el nodo se reinicio)")
    # 3. Fuera de orden -> descartar
    elif actual < anterior:
        print(f"  [FUERA DE ORDEN] {clave[0]} llego sequence {actual} despues de {anterior} -> descartado")
        return False
    # 4. Se perdieron mensajes -> avisar y aceptar
    elif actual > anterior + 1:
        print(f"  [SALTO] {clave[0]} paso de sequence {anterior} a {actual}: "
              f"se perdieron {actual - anterior - 1} mensajes")
    # 5. Llego el siguiente -> aceptar

    ultima_secuencia[clave] = actual
    return True


# Anota el tiempo de una ventana y cierra la corrida al llegar a 10
def registrar_ventana(run_id, sequence, resultado, tiempo_ms):
    # Primera ventana de la corrida
    if run_id not in corridas_en_curso:
        corridas_en_curso[run_id] = {"tiempos_ms": [], "anomalias": []}
        psutil.cpu_percent()  # Empieza a medir CPU

    corrida = corridas_en_curso[run_id]
    corrida["tiempos_ms"].append(tiempo_ms)
    if resultado["etiqueta"] == "anomalia":
        corrida["anomalias"].append(str(sequence))

    print(f"[VENTANA] {run_id} | sequence {sequence:2} | RMS {resultado['rms']:.5f} | "
          f"pico {resultado['pico']:.5f} | desviacion {resultado['desviacion']:.5f} | "
          f"{resultado['etiqueta']:8} | {tiempo_ms:.3f} ms")

    if len(corrida["tiempos_ms"]) == VENTANAS_POR_CORRIDA:
        cerrar_corrida(run_id)


# Saca el resumen, lo guarda en el CSV y borra la corrida
def cerrar_corrida(run_id):
    corrida = corridas_en_curso[run_id]

    mediana_ms = round(statistics.median(corrida["tiempos_ms"]), 4)
    cpu = psutil.cpu_percent()  # CPU promedio durante la corrida
    anomalias = " ".join(corrida["anomalias"])  # ["3", "7"] -> "3 7"

    print(f"\n===== RESUMEN {run_id} =====")
    print(f"  Mediana: {mediana_ms} ms/ventana | CPU promedio: {cpu} % | Ventanas con anomalia: {anomalias}\n")

    with open(ARCHIVO_RESULTADOS, "a") as archivo:  # "a" = agregar al final
        archivo.write(f"{MODO},{TRABAJADORES},{run_id},{mediana_ms},{cpu},{anomalias}\n")

    del corridas_en_curso[run_id]


def on_message(client, userdata, message):
    inicio = time.perf_counter()  # Cronometro: llega el mensaje

    mensaje = validar_mensaje(message.topic, message.payload)
    if mensaje is None:
        return

    if not revisar_secuencia(mensaje):
        return

    if "samples_g" in mensaje:
        if MODO == "paralelo":
            tarea = pool.submit(analizar_ventana, mensaje["samples_g"])  # Se la manda a un trabajador
            resultado = tarea.result()  # Espera el resultado del trabajador
        else:
            resultado = analizar_ventana(mensaje["samples_g"])  # Se analiza aqui mismo
        fin = time.perf_counter()  # Cronometro: termina el analisis

        tiempo_ms = (fin - inicio) * 1000
        registrar_ventana(mensaje["run_id"], mensaje["sequence"], resultado, tiempo_ms)
    else:
        print(f"[AMBIENTE]  {mensaje['node_id']} | sequence {mensaje['sequence']:2} | "
              f"temperatura {mensaje['temperature_c']} °C | humedad {mensaje['humidity_pct']} % | "
              f"luz {mensaje['light_pct']} %")


if __name__ == "__main__":
    if MODO == "paralelo":
        pool = ProcessPoolExecutor(max_workers=TRABAJADORES)  # Crea los 4 trabajadores
        pool.submit(analizar_ventana, [0.0]).result()  # Los arranca antes de que lleguen mensajes

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_message = on_message
    cliente.connect("localhost", 1883, 60)
    cliente.subscribe("emergentes/microinvernadero/#", qos=0)

    # Crea el CSV con los nombres de las columnas
    if not os.path.exists(ARCHIVO_RESULTADOS):
        os.makedirs("resultados", exist_ok=True)
        with open(ARCHIVO_RESULTADOS, "w") as archivo:
            archivo.write("modo,trabajadores,run_id,mediana_ms,cpu_pct,ventanas_anomalas\n")

    print(f"Suscriptor en modo {MODO} | {TRABAJADORES} trabajadores | {VENTANAS_POR_CORRIDA} ventanas por corrida")
    print("Escuchando emergentes/microinvernadero/# ... (Ctrl+C para salir)")
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("Suscriptor detenido.")
        cliente.disconnect()
        if MODO == "paralelo":
            pool.shutdown()  # Apaga los trabajadores
