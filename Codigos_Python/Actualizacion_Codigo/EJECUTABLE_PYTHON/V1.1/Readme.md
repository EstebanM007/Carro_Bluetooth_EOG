# 🧠 **Interfaz de Configuración LSL y COM v1.1**

## 🎯 **Descripción del Proyecto**

Aplicación avanzada en Python para integrar **Lab Streaming Layer (LSL)** con comunicación serie. Permite monitorear streams de datos en tiempo real, aplicar condiciones personalizadas y enviar comandos automáticos a microcontroladores a través de puertos COM.

![Interfaz Principal](Interfaz%20de%20Configuracion%20LSL%20y%20COM.png)

### ✨ **Nuevas Características v1.1**

- 🚀 **Selección de velocidad de baudios** configurable (300 - 256000)
- 🎨 **Interfaz modernizada** con colores e iconos
- 📊 **Estadísticas en tiempo real** (tiempo activo, muestras procesadas, comandos enviados)
- 🔧 **Validación mejorada** de configuraciones con mensajes de error claros
- 📱 **Interfaz responsive** con scroll para múltiples streams
- 💾 **Sistema de configuración** mejorado (guardar/cargar con más parámetros)
- 🖥️ **Consola serial mejorada** con timestamps y límite de líneas
- ⚡ **Mayor estabilidad** en el manejo de conexiones y errores

---

## 🔧 **Funcionalidades Principales**

### 1. 🌐 **Gestión de Streams LSL**
- Detección automática de streams disponibles
- Configuración de múltiples condiciones por stream
- Monitoreo en tiempo real de valores

### 2. 📡 **Comunicación Serial**
- **Velocidades soportadas**: 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200, 128000, 256000 baudios
- Modo simulación para pruebas sin hardware
- Consola serial con timestamps
- Detección automática de puertos disponibles

### 3. ⚙️ **Sistema de Condiciones**
- **Condiciones positivas y negativas** por stream
- Rangos configurables (mín/máx)
- Caracteres personalizados por condición
- Validación en tiempo real

### 4. 📊 **Monitoreo y Estadísticas**
- Tiempo de conexión activa
- Contador de muestras procesadas
- Contador de comandos enviados
- Logs por stream en modo simulación

---

## 📦 **Instalación y Dependencias**

### 🔧 **Requisitos del Sistema**
- Python 3.7 o superior
- Windows, macOS o Linux

### 📥 **Instalación de Dependencias**

1. Clona o descarga el proyecto
2. Navega al directorio del proyecto
3. Instala las dependencias:

```bash
python.exe -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

### 📄 **Archivo requirements.txt**
```
tkinter
pyserial>=3.5
pylsl>=1.16.0
```

---

## 🚀 **Uso de la Aplicación**

### 1. **Configuración Inicial**

1. **Ejecuta la aplicación:**
   ```bash
   python Interfaz.py
   ```

2. **Configurar Puerto Serial:**
   - Selecciona el puerto COM disponible
   - Elige la velocidad de baudios apropiada (por defecto 9600)
   - Activa "Modo simulación" para pruebas sin hardware

3. **Actualizar Streams:**
   - Haz clic en "🔄 Actualizar" para detectar streams LSL

### 2. **Configuración de Condiciones**

1. **Agregar Stream:**
   - Clic en "➕ Agregar Stream"
   - Selecciona el stream LSL de la lista

2. **Configurar Condiciones:**
   - **Condición Positiva (+):** Define rango y carácter para valores "buenos"
   - **Condición Negativa (-):** Define rango y carácter para valores "malos"
   - Ejemplo: Si valor está entre 0.5-1.0 → enviar 'A', si está entre -1.0--0.5 → enviar 'B'

3. **Validaciones Automáticas:**
   - Rangos válidos (mín < máx)
   - Al menos una condición por stream
   - Caracteres únicos de un solo dígito

### 3. **Operación**

1. **Conectar:**
   - Clic en "🟢 Conectar"
   - Verifica estado en la interfaz
   - Monitorea estadísticas en tiempo real

2. **Monitoreo:**
   - **Consola Serial:** Muestra comandos enviados con timestamps
   - **Logs de Simulación:** Detalles de procesamiento por stream
   - **Estadísticas:** Tiempo activo, muestras y comandos

3. **Desconectar:**
   - Clic en "🔴 Desconectar" para terminar la sesión

---

## 💾 **Gestión de Configuraciones**

### **Guardar Configuración**
- Clic en "💾 Guardar Config"
- Guarda: puertos, baudios, condiciones y configuraciones

### **Cargar Configuración**
- Clic en "📂 Cargar Config"
- Restaura configuración completa desde archivo JSON

### **Ejemplo de Archivo de Configuración:**
```json
{
  "serial_port": "COM3 - Arduino Uno",
  "baud_rate": "115200",
  "simulate_serial": false,
  "conditions": [
    {
      "stream": "EEG (EEG) - 8ch",
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

---

## 🛠️ **Conversión a Ejecutable (.EXE)**

### **Opción 1: PyInstaller (Recomendado)**

1. **Instalar PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Instalar dependencias en el entorno:**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

4. **Generar ejecutable:**
   ```bash
   pyinstaller --onefile --windowed --name "InterfazLSL-COM" Interfaz.py
   ```

5. **Para incluir DLL de pylsl:**
   ```bash
   pyinstaller --onefile --windowed --add-binary ".\.venv\Lib\site-packages\pylsl\lib\lsl.dll;pylsl/lib" --name "InterfazLSL-COM" Interfaz.py
   ```

### **Opción 2: Auto-Py-To-Exe (Interfaz Gráfica)**

1. **Instalar herramienta:**
   ```bash
   pip install auto-py-to-exe
   ```

2. **Ejecutar interfaz:**
   ```bash
   auto-py-to-exe
   ```

3. **Configuraciones recomendadas:**
   - ✅ **Un archivo** (onefile)
   - ✅ **Basado en ventana** (windowed)
   - ✅ **Agregar archivos adicionales** si es necesario
   - ✅ **Ícono personalizado** (.ico)

---

## ⚠️ **Consideraciones Importantes**

### **Para Uso en Producción:**
- Verifica que todos los streams LSL estén activos antes de conectar
- Usa velocidades de baudios apropiadas para tu microcontrolador
- Prueba la configuración en modo simulación primero

### **Solución de Problemas:**
- **Error de conexión serial:** Verifica que el puerto no esté en uso
- **Streams no detectados:** Asegúrate de que las aplicaciones LSL estén ejecutándose
- **Comandos no enviados:** Revisa las condiciones y rangos configurados

### **Limitaciones del .EXE:**
- No se pueden instalar paquetes dinámicamente
- Las dependencias deben estar incluidas en tiempo de compilación
- Usa detección de entorno congelado si necesitas comportamiento diferente:

```python
import sys
if getattr(sys, 'frozen', False):
    # Ejecutándose como .exe
    pass
else:
    # Ejecutándose como script Python
    pass
```

---

## 📊 **Especificaciones Técnicas**

- **Lenguaje:** Python 3.7+
- **GUI:** Tkinter nativo
- **Comunicación:** PySerial
- **Streaming:** PyLSL (Lab Streaming Layer)
- **Formatos:** JSON para configuraciones
- **Arquitectura:** Multi-threading para procesamiento en tiempo real

---

## 🎨 **Capturas de Pantalla**

La interfaz actualizada incluye:
- 🎨 Colores y iconos modernos
- 📊 Panel de estadísticas en tiempo real
- 🖥️ Consola serial mejorada
- 📱 Diseño responsive con scroll

---

## 🔄 **Historial de Versiones**

### **v1.1* (Actual)
- ✨ Selección de velocidad de baudios
- 🎨 Interfaz modernizada con iconos
- 📊 Estadísticas en tiempo real
- 🔧 Validación mejorada
- 💾 Sistema de configuración expandido

### **v1.0** (Anterior)
- 🌐 Gestión básica de streams LSL
- 📡 Comunicación serial básica
- ⚙️ Sistema de condiciones simple

---

## 📞 **Soporte y Contacto**

Para reportar errores, solicitar características o obtener soporte técnico, utiliza los canales apropiados del proyecto.

**¡Disfruta del poder de LSL-COM v1.1!** 🚀