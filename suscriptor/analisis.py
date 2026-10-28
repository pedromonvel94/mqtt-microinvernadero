import math
import statistics

# Una ventana normal tiene amplitud 0.02 g  -> RMS aprox 0.014
# Una ventana con anomalia tiene el doble   -> RMS aprox 0.028
# El umbral queda en medio de los dos valores
UMBRAL_RMS = 0.02

# Esta funcion es la MISMA para el modo secuencial y el modo paralelo.
# Va en un archivo aparte porque en Windows cada trabajador del ProcessPoolExecutor
# es un proceso nuevo que tiene que poder importarla.
def analizar_ventana(muestras):
    # RMS: raiz del promedio de los cuadrados. Mide la "energia" de la vibracion
    rms = math.sqrt(sum(valor ** 2 for valor in muestras) / len(muestras))

    # Pico: el valor mas lejano de 0, sin importar si es positivo o negativo
    pico = max(abs(valor) for valor in muestras)

    # Desviacion estandar: que tan dispersas estan las muestras alrededor de su promedio
    desviacion = statistics.pstdev(muestras)

    if rms > UMBRAL_RMS:
        etiqueta = "anomalia"
    else:
        etiqueta = "normal"

    return {
        "rms": round(rms, 5),
        "pico": round(pico, 5),
        "desviacion": round(desviacion, 5),
        "etiqueta": etiqueta
    }
