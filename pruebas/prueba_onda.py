import math
import random

hz = 100         # muestras por segundo 
frecuencia = 5   # Que tan rapido vibra
amplitud = 0.02   # Que tan alto vibra
ruido = 0.005      # Que tan ruidosa es la señal

random.seed(42) # Establezco la semilla para que la secuencia de números aleatorios sea siempre la misma, para poder reproducir los resultados

def generar_onda(hz, frecuencia, amplitud, ruido):
    muestras = []
    for i in range(hz):
        t = i / hz # Tiempo en segundos de la muestra actual

        # Altura de la onda en ese momento: siempre entre -amplitud y +amplitud mas un poco de ruido aleatorio
        valor = round((amplitud * math.sin(2 * math.pi * frecuencia * t)) + random.uniform(-ruido, ruido), 3) # Le agrego un poco de ruido aleatorio a la onda

        muestras.append(valor) # Guardo la muestra en la lista

    return muestras

muestras = generar_onda(hz, frecuencia, amplitud, ruido)

print(len(muestras), "muestras generadas")
print(max(muestras), "es el valor maximo de la onda")
print(min(muestras), "es el valor minimo de la onda")
print(muestras[:10], "son las primeras 10 muestras de la onda")