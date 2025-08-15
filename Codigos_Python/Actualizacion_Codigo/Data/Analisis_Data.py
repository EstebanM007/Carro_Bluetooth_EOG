import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# ============================================================================
# 1. CARGA DE DATOS
# ============================================================================
# Obtiene la ruta del directorio donde se encuentra el script actual
ruta_actual = os.path.dirname(os.path.abspath(__file__))
# Construye la ruta completa al archivo CSV
csv_path = os.path.join(ruta_actual, 'datos.csv')
# Lee el archivo CSV usando punto y coma como separador
df = pd.read_csv(csv_path, sep=';')
# Extrae las columnas de tiempo y señal EOG
time = df['Time (s)']
signal = df['EOG1']  # Columna de la señal electrooculográfica

# ============================================================================
# 2. CÁLCULO DE PARÁMETROS ESTADÍSTICOS
# ============================================================================
# Factor multiplicador para definir los umbrales (ajustable según necesidad)
k = 2.2  # Valor típico entre 1.5 y 3.0
# Calcula la media (valor central) de la señal
mu = signal.mean()
# Calcula la desviación estándar (dispersión) de la señal
sigma = signal.std()

# ============================================================================
# 3. CÁLCULO DE UMBRALES (LÍMITES MÍNIMOS)
# ============================================================================
# Umbral superior: media + k veces la desviación estándar
threshold_high = mu + k * sigma
# Umbral inferior: media - k veces la desviación estándar
threshold_low = mu - k * sigma

# ============================================================================
# 4. CÁLCULO DE LÍMITES MÁXIMOS
# ============================================================================
# Factor adicional para los límites máximos (más estricto que los mínimos)
k_max = k + 0.8  # Incrementa el factor para límites más amplios
# Límite máximo superior: aún más alejado de la media
max_limit_high = mu + k_max * sigma
# Límite máximo inferior: aún más alejado de la media hacia abajo
max_limit_low = mu - k_max * sigma

# ============================================================================
# 5. DETECCIÓN DE ACTIVACIONES
# ============================================================================
# Detecta puntos donde la señal supera el umbral superior (movimiento derecha)
activation_pos = signal > threshold_high
# Detecta puntos donde la señal está por debajo del umbral inferior (movimiento izquierda)
activation_neg = signal < threshold_low

# ============================================================================
# 6. CREACIÓN DEL GRÁFICO
# ============================================================================
plt.figure(figsize=(12, 6))  # Aumentamos el tamaño para mejor visualización

# Graficamos la señal principal
plt.plot(time, signal, label='Señal EOG', linewidth=1.5, color='blue')

# ============================================================================
# 7. LÍNEAS DE UMBRALES MÍNIMOS (EXISTENTES)
# ============================================================================
# Umbrales mínimos con líneas punteadas naranjas
plt.axhline(threshold_high, color='orange', linestyle='--', linewidth=2, 
           label=f'Umbral mínimo alto = μ + {k}·σ')
plt.axhline(threshold_low, color='orange', linestyle='--', linewidth=2, 
           label=f'Umbral mínimo bajo = μ − {k}·σ')

# ============================================================================
# 8. LÍNEAS DE LÍMITES MÁXIMOS (NUEVAS)
# ============================================================================
# Límites máximos con líneas punteadas verdes
plt.axhline(max_limit_high, color='green', linestyle=':', linewidth=2, 
           label=f'Límite máximo alto = μ + {k_max}·σ')
plt.axhline(max_limit_low, color='green', linestyle=':', linewidth=2, 
           label=f'Límite máximo bajo = μ − {k_max}·σ')

# ============================================================================
# 9. ANOTACIONES NUMÉRICAS
# ============================================================================
# Calcula posición para las etiquetas (un poco a la derecha del gráfico)
x_loc = time.iloc[-1] + (time.iloc[-1] - time.iloc[0]) * 0.01

# Offset vertical para separar las etiquetas de las líneas (en unidades de la señal)
offset_vertical = (signal.max() - signal.min()) * 0.02  # 2% del rango total de la señal

# Etiquetas para umbrales mínimos (naranjas, posicionadas arriba de las líneas)
plt.text(x_loc, threshold_high + offset_vertical, f'{threshold_high:.1f}', 
         va='bottom', ha='left', color='orange', fontweight='bold', 
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
plt.text(x_loc, threshold_low + offset_vertical, f'{threshold_low:.1f}', 
         va='bottom', ha='left', color='orange', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# Etiquetas para límites máximos (verdes, posicionadas arriba de las líneas)
plt.text(x_loc, max_limit_high + offset_vertical, f'{max_limit_high:.1f}', 
         va='bottom', ha='left', color='green', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
plt.text(x_loc, max_limit_low + offset_vertical, f'{max_limit_low:.1f}', 
         va='bottom', ha='left', color='green', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# ============================================================================
# 10. PUNTOS DE ACTIVACIÓN
# ============================================================================
# Marca los puntos donde se detectaron movimientos oculares
plt.scatter(time[activation_pos], signal[activation_pos],
            color='red', marker='o', s=30, alpha=0.7, label='Activación Derecha')
plt.scatter(time[activation_neg], signal[activation_neg],
            color='purple', marker='o', s=30, alpha=0.7, label='Activación Izquierda')

# ============================================================================
# 11. CONFIGURACIÓN FINAL DEL GRÁFICO
# ============================================================================
plt.xlabel('Tiempo (s)', fontsize=12)
plt.ylabel('Amplitud EOG (μV)', fontsize=12)
plt.title('Análisis EOG: Umbrales Mínimos y Límites Máximos', fontsize=14, fontweight='bold')
plt.legend(loc='upper left', fontsize=10)
plt.grid(True, alpha=0.3)  # Añade una rejilla sutil
plt.tight_layout()

# ============================================================================
# 12. INFORMACIÓN ESTADÍSTICA EN CONSOLA
# ============================================================================
print("="*60)
print("ANÁLISIS ESTADÍSTICO DE LA SEÑAL EOG")
print("="*60)
print(f"Media (μ): {mu:.2f} mV")
print(f"Desviación estándar (σ): {sigma:.2f} mV")
print(f"Factor k (umbrales): {k}")
print(f"Factor k_max (límites): {k_max}")
print("-"*60)
print("UMBRALES MÍNIMOS:")
print(f"  Alto: {threshold_high:.2f} mV")
print(f"  Bajo: {threshold_low:.2f} mV")
print("-"*60)
print("LÍMITES MÁXIMOS:")
print(f"  Alto: {max_limit_high:.2f} mV")
print(f"  Bajo: {max_limit_low:.2f} mV")
print("-"*60)
print(f"Activaciones detectadas (derecha): {activation_pos.sum()}")
print(f"Activaciones detectadas (izquierda): {activation_neg.sum()}")
print("="*60)

plt.show()