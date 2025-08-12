# 📡 Interfaz LSL-Serial Mejorada v2.0

Una aplicación profesional para conectar streams LSL (Lab Streaming Layer) con puertos seriales para comunicación con microcontroladores.

![Interfaz Principal](Interfaz%20de%20Configuracion%20LSL%20y%20COM.png)

## 🎯 Descripción General

Esta aplicación realiza un puente inteligente entre streams de datos LSL y comunicación serial, permitiendo:

- **Escaneo automático** de puertos COM disponibles
- **Detección de streams LSL** activos en la red
- **Configuración de umbrales** personalizables por stream
- **Envío de comandos** al microcontrolador basado en condiciones
- **Reconexión automática** en caso de desconexiones

## ✨ Funcionalidades Principales

### 🔍 Detección y Configuración
- ✅ Escaneo automático de puertos seriales COM
- ✅ Detección de streams LSL disponibles
- ✅ Configuración de baudios personalizable (1200-115200)
- ✅ Soporte para streams manuales por nombre específico
- ✅ Múltiples condiciones por stream (positivas y negativas)

### 🔧 Control Avanzado
- ✅ **Reconexión automática** de streams desconectados
- ✅ **Modo simulación** para pruebas sin hardware
- ✅ **Consola serial** integrada para monitoreo
- ✅ **Estadísticas en tiempo real** de streams
- ✅ **Guardar/Cargar configuraciones** en formato JSON

### 🖥️ Interfaz de Usuario
- ✅ Interfaz gráfica intuitiva con Tkinter
- ✅ Visualización de logs por stream en modo simulación
- ✅ Control de conexión/desconexión en tiempo real
- ✅ Menú de herramientas con funciones auxiliares

## 🚀 Instalación y Uso

### 📋 Requisitos Previos

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
.\venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 📦 Instalación de Dependencias

```bash
# Actualizar pip
python.exe -m pip install --upgrade pip
```

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

**Dependencias principales:**
- `tkinter` - Interfaz gráfica (incluido en Python)
- `pyserial` - Comunicación serial
- `pylsl` - Lab Streaming Layer

### ▶️ Ejecución

```bash
python Interfaz.py
```

## 🎛️ Configuración de Streams

### Configuración Básica por Stream:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Stream** | Stream LSL o "Stream Manual" | `EEG (EEG)` |
| **Nombre** | Nombre específico (solo manual) | `MyEEGStream` |
| **Lim Sup (+)** | Límite inferior positivo | `1.0` |
| **Lim Inf (+)** | Límite superior positivo | `0.5` |
| **Letra (+)** | Carácter a enviar | `W` |
| **Lim Sup (-)** | Límite inferior negativo | `-0.5` |
| **Lim Inf (-)** | Límite superior negativo | `-1.0` |
| **Letra (-)** | Carácter a enviar | `S` |

### 🔄 Lógica de Funcionamiento

```
Si valor_stream está en [Lim_Inf_+, Lim_Sup_+] → Enviar Letra_+
Si valor_stream está en [Lim_Inf_-, Lim_Sup_-] → Enviar Letra_-
```

## 📊 Funciones Avanzadas

### 📈 Estadísticas de Streams
- Accede a **Herramientas → Estadísticas de Streams**
- Visualiza mín, máx, promedio y sugerencias de umbrales
- Ayuda a configurar rangos óptimos

### 💾 Gestión de Configuraciones
- **Guardar configuración**: Exporta a JSON para reutilizar
- **Cargar configuración**: Importa configuraciones previas
- Incluye configuraciones de puerto serial y streams

### 🔧 Modo Simulación
- Habilita **"Simular COM"** para pruebas
- Visualiza logs detallados por stream
- Perfecto para desarrollo sin hardware

## 🛠️ Generación de Ejecutable

### Opción 1: PyInstaller (Recomendado)

```bash
# Instalación
pip install pyinstaller

# Generación básica
pyinstaller --onefile Interfaz.py

# Con interfaz gráfica (sin consola)
pyinstaller --onefile --windowed Interfaz.py

# Versión completa con dependencias
pyinstaller --onefile --windowed --add-binary ".\.venv\Lib\site-packages\pylsl\lib\lsl.dll;pylsl/lib" Interfaz.py
```

### Opción 2: Auto-Py-To-Exe

```bash
# Instalación
pip install auto-py-to-exe

# Ejecutar interfaz gráfica
auto-py-to-exe
```

![Auto Py to Exe](auto-py-to-exe.png)

## 📁 Estructura del Proyecto

```
proyecto/
├── Interfaz.py              # Script principal
├── requirements.txt         # Dependencias
├── README.md               # Esta documentación
├── config_ejemplo.json     # Configuración de ejemplo
└── assets/
    ├── Interfaz de Configuracion LSL y COM.png
    └── auto-py-to-exe.png
```

## 🔧 Configuración Serial

### Puertos Soportados
- **Windows**: COM1, COM2, COM3, etc.
- **Linux**: /dev/ttyUSB0, /dev/ttyACM0, etc.
- **macOS**: /dev/cu.usbserial-*, /dev/tty.*

### Baudios Disponibles
```
1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
```

## 🐛 Solución de Problemas

### Stream no se conecta
1. ✅ Verificar que el stream LSL esté activo
2. ✅ Usar **"Actualizar"** para refrescar streams
3. ✅ Probar con **Stream Manual** usando nombre exacto
4. ✅ Habilitar **reconexión automática**

### Puerto serial no disponible
1. ✅ Verificar conexiones físicas
2. ✅ Comprobar que no esté en uso por otra aplicación
3. ✅ Usar **modo simulación** para pruebas

### Error en ejecutable
1. ✅ Incluir todas las DLLs necesarias con `--add-binary`
2. ✅ Probar en máquina limpia sin Python
3. ✅ Verificar permisos de ejecución

## 📝 Ejemplo de Configuración JSON

```json
{
  "serial_settings": {
    "port": "COM3",
    "baudrate": "9600",
    "simulate": false,
    "show_console": true,
    "auto_reconnect": true
  },
  "stream_conditions": [
    {
      "stream": "EEG (EEG)",
      "stream_type": "auto",
      "manual_name": "",
      "pos_lower": 0.5,
      "pos_upper": 1.0,
      "pos_letter": "A",
      "neg_lower": -1.0,
      "neg_upper": -0.5,
      "neg_letter": "B"
    }
  ]
}
```

## 💡 Consejos y Mejores Prácticas

### ⚡ Rendimiento
- Usa **reconexión automática** para mayor estabilidad
- Limita el historial de logs para evitar uso excesivo de memoria
- Configura umbrales realistas basados en estadísticas

### 🔒 Estabilidad
- Siempre prueba en **modo simulación** primero
- Guarda configuraciones funcionales como respaldo
- Usa timeout apropiados para streams lentos

### 🎯 Configuración Óptima
- Analiza las **estadísticas de streams** antes de configurar umbrales
- Usa rangos no solapados para evitar envíos múltiples
- Asigna letras distintas para cada condición

## 📞 Soporte

Para reportar bugs o solicitar funcionalidades:
1. Verifica la consola de errores integrada
2. Revisa los logs de streams en modo simulación
3. Documenta la configuración que causa problemas

## 🆕 Novedades v1.0

- ✨ **Configuración de baudios** personalizable
- ✨ **Streams manuales** por nombre específico
- ✨ **Reconexión automática** mejorada
- ✨ **Estadísticas en tiempo real**
- ✨ **Mejor manejo de errores** y logging
- ✨ **Interfaz mejorada** con scroll y menús
- ✨ **Consola serial** integrada opcional

---

🚀 **¡Desarrollado para facilitar la integración entre análisis de datos LSL y control de hardware!**