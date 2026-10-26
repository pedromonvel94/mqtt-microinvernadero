import math
import random

hz = 100         # muestras por segundo 
frecuencia = 5   # Que tan rapido vibra
amplitud = 0.02   # Que tan alto vibra
ruido = 0.005      # Que tan ruidosa es la señal
ventanas_por_corrida = 10  # Cuantas ventanas de datos voy a generar
factor_anomalia = 2

random.seed(42) # Establezco la semilla para que la secuencia de números aleatorios sea siempre la misma, para poder reproducir los resultados

def generar_onda(hz, frecuencia, amplitud, ruido):
    muestras = []
    for i in range(hz):
        t = i / hz # Tiempo en segundos de la muestra actual

        # Altura de la onda en ese momento: siempre entre -amplitud y +amplitud mas un poco de ruido aleatorio
        valor = round((amplitud * math.sin(2 * math.pi * frecuencia * t)) + random.uniform(-ruido, ruido), 3) # Le agrego un poco de ruido aleatorio a la onda

        muestras.append(valor) # Guardo la muestra en la lista

    return muestras

for numero_ventana in range(1, ventanas_por_corrida + 1): # Genero 10 ventanas de datos, numeradas del 1 al 10
    if numero_ventana in [3, 7]: # Simulo que en la ventana 3 y 7 hay un evento de vibración más fuerte
        ventana = generar_onda(hz, frecuencia, amplitud * factor_anomalia, ruido) # Genero una onda con el doble de amplitud para simular un evento de vibración más fuerte
    else:
        ventana = generar_onda(hz, frecuencia, amplitud, ruido)
        
    print(f"Ventana {numero_ventana}: {ventana[:10]} ... -> max {max(ventana)} min {min(ventana)}")