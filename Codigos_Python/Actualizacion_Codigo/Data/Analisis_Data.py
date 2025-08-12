import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Carga de datos
ruta_actual = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(ruta_actual, 'datos.csv')
df = pd.read_csv(csv_path, sep=';')
time = df['Time (s)']
signal = df['EOG1']  # Asumiendo que la columna de interez se llama 'name'

# 2. Parámetros de umbral
k = 2.2  # <-- aquí ajustas tu umbral (por ejemplo 1.5, 2, 2.5...)
mu = signal.mean()
sigma = signal.std()
threshold_high = mu + k * sigma
threshold_low  = mu - k * sigma

# 3. Detección de activaciones
activation_pos = signal > threshold_high
activation_neg = signal < threshold_low

# 4. Plot con etiquetas de umbral
plt.figure(figsize=(10, 4))
plt.plot(time, signal, label='Señal EOG')

# Líneas punteadas
plt.axhline(threshold_high, color='C1', linestyle='--', label=f'Umbral alto = μ + {k}·σ')
plt.axhline(threshold_low,  color='C1', linestyle='--', label=f'Umbral bajo = μ − {k}·σ')

# Anotaciones numéricas junto a las líneas
x_loc = time.iloc[-1] + (time.iloc[-1] - time.iloc[0]) * 0.01  # un pelín a la derecha
plt.text(x_loc, threshold_high, f'{threshold_high:.1f}', va='center')
plt.text(x_loc, threshold_low,  f'{threshold_low:.1f}',  va='center')

# Puntos de activación
plt.scatter(time[activation_pos], signal[activation_pos],
            color='C2', marker='.', label='Activación Derecha')
plt.scatter(time[activation_neg], signal[activation_neg],
            color='C3', marker='.', label='Activación Izquierda')

# Etiquetas y leyenda
plt.xlabel('Tiempo (s)')
plt.ylabel('Amplitud EOG')
plt.title('EOG Horizontal con Umbrales y Detecciones')
plt.legend(loc='upper left')
plt.tight_layout()
plt.show()
