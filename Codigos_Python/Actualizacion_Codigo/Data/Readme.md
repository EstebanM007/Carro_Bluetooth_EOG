
# 📊 Detección de movimientos oculares en señal EOG

Este código en Python carga datos de una señal EOG (electrooculografía) horizontal desde un archivo CSV, calcula **umbrales** estadísticos y detecta eventos significativos (picos positivos y negativos). Luego grafica la señal con los umbrales y marca las activaciones detectadas. A continuación se explica cada parte del código y su aplicación práctica en un entorno de análisis de datos.
## 📥 Carga de datos

* **Librerías:** Se importan `pandas` para manejo de datos, `matplotlib.pyplot` para graficar y `os` para gestionar rutas de archivos.
* **Ruta del archivo:** Se obtiene la ruta del script actual con `os.path.dirname(os.path.abspath(__file__))` para asegurar que el archivo CSV esté en la misma carpeta.
* **Lectura del CSV:** El código lee el archivo `datos_streams.csv` usando `pd.read_csv(csv_path, sep=';')`, ya que los datos están separados por punto y coma.
* **Extracción de columnas:** Del DataFrame `df` resultante se extraen dos columnas:

  * `time = df['Tiempo (s)']` → tiempo en segundos.
  * `signal = df['Data2']` → señal EOG horizontal (se asume que la columna de interés es “Data2”).

Estos pasos cargan la señal y el vector de tiempo correspondientes para su análisis posterior.

## 🎚️ Cálculo de umbrales

* **Parámetro de umbral `k`:** Se define `k = 3` (puede ajustarse a 1.5, 2, 2.5, etc.) para determinar cuántas desviaciones estándar lejos de la media se consideran un evento significativo.
* **Media y desviación estándar:** Se calcula la media (`mu = signal.mean()`) y la desviación estándar (`sigma = signal.std()`) de la señal completa.
* **Umbrales alto y bajo:** Con `mu` y `sigma` se establecen:

  * **Umbral alto:** `threshold_high = mu + k * sigma`
  * **Umbral bajo:** `threshold_low  = mu - k * sigma`
    Estos umbrales representan límites estadísticos: cualquier valor de señal por encima del umbral alto o por debajo del umbral bajo se considerará una activación relevante. Al incrementar `k`, los umbrales se alejan de la media (se vuelve más difícil superar el umbral), y viceversa.

## 🎯 Detección de activaciones

* **Máscaras booleanas:** Se crean dos máscaras lógicas sobre la señal para detectar picos:

  ```python
  activation_pos = signal > threshold_high   # Señal superior al umbral alto
  activation_neg = signal < threshold_low    # Señal inferior al umbral bajo
  ```

  Cada una es una serie de valores `True`/`False` indicando los instantes donde la señal supera los límites.
* **Interpretación en EOG:** En este contexto de EOG horizontal, los valores por encima del umbral alto se etiquetan como **"Activación Derecha"** (movimiento ocular hacia la derecha) y los por debajo del umbral bajo como **"Activación Izquierda"** (movimiento hacia la izquierda). Esto se refleja más adelante en la gráfica con puntos de colores diferentes.
* **Flexibilidad:** Ajustando `k` puedes controlar la sensibilidad del detector: un `k` menor detectará más activaciones (incluso pequeñas), mientras un `k` mayor solo marcará picos pronunciados.

## 📊 Visualización de resultados

* **Figura y señal:** Se crea una figura con `plt.figure(figsize=(10, 4))` y se grafica la señal con `plt.plot(time, signal, label='Señal EOG')`. Esto muestra la amplitud de la señal EOG a lo largo del tiempo.
* **Líneas de umbral:** Las dos líneas horizontales punteadas se dibujan con `plt.axhline`:

  ```python
  plt.axhline(threshold_high, color='C1', linestyle='--', label=f'Umbral alto = μ + {k}·σ')
  plt.axhline(threshold_low,  color='C1', linestyle='--', label=f'Umbral bajo = μ - {k}·σ')
  ```

  Estas líneas (`umbral alto` y `umbral bajo`) muestran los límites estadísticos calculados. Se les añade etiqueta y color distintivo. Además, se anotan sus valores numéricos junto a las líneas usando `plt.text`, para mayor claridad.
* **Puntos de activación:** Se usan gráficos de dispersión (`plt.scatter`) para marcar los instantes de activación:

  ```python
  plt.scatter(time[activation_pos], signal[activation_pos], color='C2', marker='.', label='Activación Derecha')
  plt.scatter(time[activation_neg], signal[activation_neg], color='C3', marker='.', label='Activación Izquierda')
  ```

  Aquí se plotean solo los puntos de `time` y `signal` donde las máscaras son `True`. Se usan colores diferentes (por ejemplo, `C2` para activaciones positivas, `C3` para negativas) para diferenciarlos visualmente.
* **Etiquetas y leyenda:** Finalmente, se etiquetan los ejes (`plt.xlabel('Tiempo (s)')`, `plt.ylabel('Amplitud EOG')`), se pone un título (`plt.title('EOG Horizontal con Umbrales y Detecciones')`), se añade la leyenda (`plt.legend(loc='upper left')`), y se ajusta el layout (`plt.tight_layout()`). El `plt.show()` despliega la gráfica completa. El resultado es un gráfico claro que muestra la señal EOG, los límites de umbral y los momentos en que la señal excedió esos límites.

## ⚙️ Uso y personalización

* **Requisitos:** Este script requiere tener `pandas` y `matplotlib` instalados. Puedes instalarlos con `pip install pandas matplotlib`.
* **Preparar los datos:** Asegúrate de que el archivo `datos_streams.csv` exista y contenga las columnas `'Tiempo (s)'` (tiempo en segundos) y la columna de señal (aquí llamada `'Data2'`). Si tu archivo tiene nombres distintos, ajusta `df['Tiempo (s)']` y `df['Data2']` por el nombre correcto.
* **Ajuste de umbral:** Modifica la variable `k` al comienzo del código para cambiar la sensibilidad. Por ejemplo, `k=2` detectará activaciones más suaves, mientras que `k=4` sólo detectará picos muy grandes.
* **Ejecución:** Coloca el script en la misma carpeta del CSV (o ajusta la ruta), y ejecútalo en un entorno Python. El código mostrará una gráfica interactiva con la señal EOG y las activaciones detectadas.
* **Aplicaciones:** Este método es útil en análisis de señales biomédicas, especialmente para detectar sutiles movimientos oculares horizontales en experimentos de EOG o interfaces cerebro-computadora. También puedes adaptar la idea a otras señales donde interese detectar picos estadísticos (por ejemplo, en ECG, EEG, etc.).

## 🔑 Resumen

* El código **lee una señal EOG** horizontal desde un CSV y extrae tiempo y amplitud.
* Calcula **umbrales estadísticos** (media ± k·desviación estándar) para definir límites de activación.
* Crea máscaras booleanas para identificar **eventos significativos** (picos arriba/abajo de los umbrales).
* Grafica la señal completa, dibuja líneas de umbral y **marca las activaciones** con colores diferenciados.
* Es fácil de ajustar cambiando `k`, y sirve para detectar movimientos oculares fuertes hacia la **derecha** o **izquierda** en la señal EOG.
