# Microinvernadero didáctico con MQTT

Proyecto de la asignatura Tecnologías Emergentes (IU Digital de Antioquia). Cada actividad evaluada amplía el mismo sistema:

| Actividad | Qué agrega | Carpetas |
|---|---|---|
| EA1 | Dos nodos Python simulados que publican por MQTT y un suscriptor que valida y analiza los datos (secuencial vs paralelo) | `nodos/`, `suscriptor/`, `resultados/` |
| EA2 | Programa central que recibe la telemetría MQTT de `sim_ambiente_01` y acepta mediciones manuales por Telegram | `central/` |

Cada entrega queda marcada con una etiqueta de git (`entrega-ea1`, `entrega-ea2`, ...).

## Requisitos

- Python 3.12
- Broker Mosquitto en el mismo computador (`localhost:1883`)
- Para la EA2: una cuenta de Telegram y un bot creado con @BotFather

## Instalación

Desde la carpeta del proyecto, en PowerShell:

```
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Verificar que Mosquitto esté corriendo:

```
Get-Service mosquitto
```

## EA1: nodos simulados y suscriptor

Cada comando en su propia terminal, con el venv activado:

```
python suscriptor/suscriptor.py secuencial      (o paralelo)
python nodos/sim_ambiente_01.py
python nodos/sim_vib_01.py secuencial 5         (o paralelo 5)
```

- `sim_ambiente_01` publica temperatura, humedad y luz cada 10 s en `emergentes/microinvernadero/ambiente/sim_ambiente_01`.
- `sim_vib_01` publica lotes de 100 muestras de vibración por segundo en `emergentes/microinvernadero/vibracion/sim_vib_01`.
- El suscriptor valida cada mensaje, detecta duplicados y saltos de `sequence`, analiza cada lote (RMS, pico y desviación estándar) y guarda el resumen de cada corrida en `resultados/resultados.csv`.

## EA2: mediciones automáticas y manuales con Telegram

### Configuración

1. Copiar `.env.example` con el nombre `.env`.
2. Llenar `TELEGRAM_TOKEN` con el token de @BotFather y `TELEGRAM_CHAT_ID` con el número del chat privado autorizado.

El archivo `.env` está en el `.gitignore`: el token nunca queda en el código ni en el repositorio.

### Ejecución

En dos terminales, con el venv activado:

```
python central/central.py
python nodos/sim_ambiente_01.py
```

El nodo `sim_ambiente_01` de la EA1 se usa sin modificarlo: el programa central solo se suscribe a su topic.

### Comandos del bot

| Comando | Qué hace |
|---|---|
| `/medir <temperatura> <humedad>` | Registra una lectura manual. Ejemplo: `/medir 24.5 68` |
| `/estado` | Muestra la última lectura de MQTT y la de Telegram por separado (o "sin datos todavía") |
| `/ayuda` | Muestra los comandos disponibles |

### Cómo funciona

- MQTT corre en segundo plano (`loop_start`) y Telegram en primer plano (`run_polling`, long polling sin webhook), así los dos canales funcionan al mismo tiempo.
- La última lectura de cada fuente se guarda en memoria por separado; ninguna fuente sobrescribe a la otra.
- `/medir` valida que los dos valores sean números finitos (`math.isfinite`, para rechazar `nan` e `inf`) y que la humedad esté entre 0 y 100. Si la entrada es inválida, responde el motivo y la última lectura no cambia.
- El bot solo atiende el chat autorizado; los mensajes de otras personas se ignoran.
- Solo puede haber un programa usando el bot a la vez; si aparece el error `Conflict`, hay otra instancia abierta.
