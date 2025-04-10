from pylsl import StreamInlet, resolve_streams  # Librería para leer streams de LSL
import time
import pandas as pd

# Resolver todos los streams disponibles
print("Buscando todos los streams disponibles...")
all_streams = resolve_streams()

# Filtrar los streams de tipo 'P1' y 'P2'
stream_P1 = next((stream for stream in all_streams if stream.type() == 'P1'), None)
stream_P2 = next((stream for stream in all_streams if stream.type() == 'P2'), None)

# Verificar que ambos streams estén disponibles
if not stream_P1 or not stream_P2:
    raise RuntimeError("No se encontraron ambos streams de tipo 'P1' y 'P2'.")

# Crear inlets para leer datos de los streams
inlet_P1 = StreamInlet(stream_P1)
inlet_P2 = StreamInlet(stream_P2)

# Lista para almacenar los datos
data_list = []

print("Comenzando a guardar datos en 'datos_streams.xlsx'. Presiona Ctrl+C para detener.")

start_time = time.time()  # Tiempo inicial

try:
    while True:
        try:
            # Leer una muestra de cada stream
            sample_P1, _ = inlet_P1.pull_sample(timeout=0.5)
            sample_P2, _ = inlet_P2.pull_sample(timeout=0.5)

            # Verificar que ambas muestras sean válidas
            if sample_P1 and sample_P2:
                elapsed_time = time.time() - start_time  # Tiempo transcurrido en segundos
                # Agregar los datos a la lista
                data_list.append([elapsed_time, sample_P1[0], sample_P2[0]])
                #print(f"Guardado: Tiempo={elapsed_time:.3f}s, P1={sample_P1[0]}, P2={sample_P2[0]}")
                #Este print verifica los datos que se están guardando, pero puede ser comentado para evitar saturar la consola.

        except Exception as e:
            print(f"Error al leer los streams: {e}. Intentando reconectar...")
            # Intentar reconectar los streams
            try:
                stream_P1 = next((stream for stream in resolve_streams() if stream.type() == 'P1'), None)
                stream_P2 = next((stream for stream in resolve_streams() if stream.type() == 'P2'), None)
                if stream_P1 and stream_P2:
                    inlet_P1 = StreamInlet(stream_P1)
                    inlet_P2 = StreamInlet(stream_P2)
                    print("Reconexión exitosa.")
                else:
                    print("No se encontraron streams. Reintentando en 2 segundos...")
                    time.sleep(2)
            except Exception as reconnection_error:
                print(f"Error durante la reconexión: {reconnection_error}")
                time.sleep(2)

except KeyboardInterrupt:
    print("Detenido por el usuario. Guardando datos en 'datos_streams.xlsx'...")

# Crear un DataFrame con los datos
df = pd.DataFrame(data_list, columns=["Tiempo (s)", "P1", "P2"])

# Guardar en formato Excel, se reescriben los datos si el archivo ya existe
df.to_excel("datos_streams.xlsx", index=False)
print("Archivo 'datos_streams.xlsx' guardado correctamente.")