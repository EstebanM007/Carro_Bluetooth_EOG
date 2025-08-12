from pylsl import StreamInlet, resolve_streams  # Librería para leer streams de LSL
import serial
import time
# Este programa lee 1 stream de tipo 'EOG' (Electrooculografía) a través de LSL (Lab Streaming Layer)
# Configuración del puerto serial
serialPort = serial.Serial('COM4', 9600, timeout=1)
print("Puerto serial configurado correctamente.")

# Función para buscar streams de manera continua
def buscar_stream(tipo_stream):
    while True:
        print(f"Buscando stream de tipo '{tipo_stream}'...")
        streams = [stream for stream in resolve_streams() if stream.type() == tipo_stream]
        if streams:
            print(f"Stream de tipo '{tipo_stream}' encontrado.")
            return streams[0]
        print(f"No se encontró stream de tipo '{tipo_stream}'. Reintentando en 2 segundos...")
        time.sleep(2)

# Función para crear un inlet y manejar reconexión
def crear_inlet(tipo_stream):
    while True:
        try:
            stream = buscar_stream(tipo_stream)
            inlet = StreamInlet(stream)
            print(f"Inlet creado para el stream de tipo '{tipo_stream}'.")
            return inlet
        except Exception as e:
            print(f"Error al crear el inlet: {e}. Reintentando en 2 segundos...")
            time.sleep(2)

# Crear un inlet para el stream de tipo 'EOG'
inlet_EOG = crear_inlet('EOG')

# Bucle principal para procesar los datos del stream
while True:
    try:
        # Leer una muestra del stream con un tiempo de espera de 0.5 segundos
        sample, _ = inlet_EOG.pull_sample(timeout=0.5)
        if sample:
            # Aplicar condiciones a la señal EOG
            if 472.1 <= sample[0] <= 490:  # Usar directamente sample[0] para las condiciones
                serialPort.write(b'D')  # Enviar comando 'D' por el puerto serial
                print("D enviado")
            elif -490 <= sample[0] <= -481.1:  # Usar directamente sample[0] para las condiciones
                serialPort.write(b'W')  # Enviar comando 'W' por el puerto serial
                print("W enviado")
        else:
            print("Sin muestra")

    except Exception as e:
        print(f"Error al procesar los datos: {e}. Intentando reconectar el stream...")
        inlet_EOG = crear_inlet('EOG')  # Volver a buscar y crear el inlet
