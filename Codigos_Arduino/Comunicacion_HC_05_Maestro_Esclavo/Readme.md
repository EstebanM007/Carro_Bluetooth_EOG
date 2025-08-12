# Sistema de Comunicación Bluetooth Bidireccional HC-05

Este proyecto implementa un sistema de comunicación bidireccional entre dos Arduino utilizando módulos Bluetooth HC-05. El sistema permite el intercambio automático de datos entre un dispositivo maestro y un dispositivo esclavo sin intervención manual.

## Características del Sistema

- **Comunicación Bidireccional**: Envío y recepción de datos entre dispositivos
- **Conexión Automática**: Los módulos se conectan automáticamente al encenderse
- **Interfaz Serial**: Control y monitoreo a través del monitor serial
- **Configuración Maestro-Esclavo**: Un HC-05 como maestro, otro como esclavo
- **Transmisión de Strings**: Soporte para mensajes de texto completos

## Componentes Requeridos

### Hardware (Para cada dispositivo)
- Arduino Uno/Nano/compatible
- Módulo Bluetooth HC-05
- Cables de conexión
- Fuente de alimentación

### Software
- Arduino IDE
- Biblioteca SoftwareSerial (incluida en Arduino IDE)
- Terminal serial para configuración AT

## Conexiones del HC-05

```
HC-05        →    Arduino
VCC          →    5V (o 3.3V)
GND          →    GND
TXD          →    Pin 11 (RX del SoftwareSerial)
RXD          →    Pin 10 (TX del SoftwareSerial)
EN/KEY       →    Pin 2 (solo para configuración AT)
```

**Nota**: Para configuración AT, conectar EN/KEY a un pin digital antes de encender el módulo.

## Configuración de los Módulos HC-05

### Paso 1: Configuración del Módulo Maestro

1. **Entrar en Modo AT**:
   - Mantener presionado el botón del HC-05 mientras se enciende
   - O conectar el pin EN/KEY a HIGH antes del encendido
   - El LED parpadeará lentamente (cada 2 segundos)

2. **Comandos AT para el Maestro**:
```
AT                          // Verificar comunicación
AT+ROLE=1                   // Configurar como maestro
AT+CMODE=0                  // Modo de conexión específica
AT+PSWD=1234               // Establecer password (opcional)
AT+UART=9600,0,0           // Configurar velocidad 9600 bps
AT+NAME=MAESTRO            // Nombre del dispositivo
```

3. **Configurar Dirección del Esclavo**:
```
AT+BIND=xxxx,xx,xxxxxx     // Vincular con dirección MAC del esclavo
```

### Paso 2: Configuración del Módulo Esclavo

1. **Entrar en Modo AT** (mismo proceso que el maestro)

2. **Comandos AT para el Esclavo**:
```
AT                          // Verificar comunicación
AT+ROLE=0                   // Configurar como esclavo
AT+CMODE=1                  // Modo de conexión cualquier dispositivo
AT+PSWD=1234               // Mismo password que el maestro
AT+UART=9600,0,0           // Configurar velocidad 9600 bps
AT+NAME=ESCLAVO            // Nombre del dispositivo
```

### Paso 3: Obtener Direcciones MAC

**Para obtener la dirección del esclavo**:
```
AT+ADDR?                   // Devuelve algo como: +ADDR:2018:06:123456
```

**Formato para BIND**:
- Si la dirección es: `2018:06:123456`
- El comando BIND será: `AT+BIND=2018,06,123456`

### Paso 4: Verificación de la Configuración

**Comandos útiles para verificar**:
```
AT+ROLE?                   // Verificar rol (0=esclavo, 1=maestro)
AT+ADDR?                   // Ver dirección MAC
AT+NAME?                   // Ver nombre del dispositivo
AT+PSWD?                   // Ver password
AT+BIND?                   // Ver dispositivo vinculado (solo maestro)
```

## Código para el Arduino Maestro

El código proporcionado corresponde al Arduino maestro:

```cpp
#include <SoftwareSerial.h>

SoftwareSerial bluetooth(10, 11); // TX,RX

void setup() {
  Serial.begin(9600);
  bluetooth.begin(9600);
  Serial.println("Arduino Maestro iniciado. Escribe tus datos para enviar:");
}

void loop() {
  // Enviar datos desde monitor serial a Bluetooth
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    Serial.print("Enviando por Bluetooth: ");
    Serial.println(data);
    bluetooth.println(data);
  }

  // Recibir datos de Bluetooth y mostrar en monitor serial
  if (bluetooth.available()) {
    String receivedData = bluetooth.readStringUntil('\n');
    Serial.print("Recibido por Bluetooth: ");
    Serial.println(receivedData);
  }

  delay(500);
}
```

## Código para el Arduino Esclavo

```cpp
#include <SoftwareSerial.h>

SoftwareSerial bluetooth(10, 11); // TX,RX

void setup() {
  Serial.begin(9600);
  bluetooth.begin(9600);
  Serial.println("Arduino Esclavo iniciado. Esperando conexión...");
}

void loop() {
  // Enviar datos desde monitor serial a Bluetooth
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    Serial.print("Enviando por Bluetooth: ");
    Serial.println(data);
    bluetooth.println(data);
  }

  // Recibir datos de Bluetooth y mostrar en monitor serial
  if (bluetooth.available()) {
    String receivedData = bluetooth.readStringUntil('\n');
    Serial.print("Recibido por Bluetooth: ");
    Serial.println(receivedData);
  }

  delay(500);
}
```

## Funcionamiento del Sistema

### Proceso de Conexión
1. **Encendido**: Al energizar ambos dispositivos, el HC-05 maestro busca automáticamente al esclavo
2. **Vinculación**: Se conectan usando la dirección MAC configurada y el password
3. **Comunicación**: Una vez conectados, pueden intercambiar datos bidireccionalmente

### Estados de los LEDs
- **Parpadeo rápido (varias veces por segundo)**: Buscando conexión
- **Parpadeo lento (cada 2 segundos)**: Conectado y funcionando
- **Encendido continuo**: Modo AT activo

## Solución de Problemas

### Problema: Los módulos no se conectan
**Soluciones**:
1. Verificar que las direcciones MAC sean correctas
2. Confirmar que ambos tengan el mismo password
3. Revisar que uno sea maestro (ROLE=1) y otro esclavo (ROLE=0)
4. Verificar la configuración UART (misma velocidad)

### Problema: No responde a comandos AT
**Soluciones**:
1. Verificar conexión del pin EN/KEY
2. Mantener presionado el botón al encender
3. Usar velocidad 38400 para comandos AT (algunos módulos)
4. Verificar conexiones TX/RX

### Problema: Datos corruptos o perdidos
**Soluciones**:
1. Verificar configuración UART
2. Ajustar el delay en el código
3. Revisar conexiones físicas
4. Verificar alimentación estable

## Comandos AT Adicionales

### Restaurar Configuración
```
AT+ORGL                    // Restaurar configuración original
AT+RESET                   // Reiniciar módulo
```

### Configuración Avanzada
```
AT+IPSCAN=1024,1,1024,1   // Parámetros de escaneo
AT+SNIFF=7,500,1,8        // Parámetros de sniff
AT+SENM=3,0               // Modo de notificación
```

## Aplicaciones del Sistema

- **Robótica**: Control remoto de robots
- **IoT**: Intercambio de datos entre sensores
- **Domótica**: Comunicación entre dispositivos del hogar
- **Telemetría**: Monitoreo remoto de sistemas
- **Educativo**: Aprendizaje de comunicaciones inalámbricas

## Consideraciones Importantes

1. **Alcance**: Aproximadamente 10 metros en espacio abierto
2. **Velocidad**: 9600 bps es estándar, puede configurarse hasta 115200 bps
3. **Consumo**: Considerar uso de baterías para aplicaciones portátiles
4. **Interferencias**: Evitar interferencias con otros dispositivos 2.4GHz
5. **Seguridad**: Cambiar passwords por defecto para mayor seguridad

## Autor

Sistema de comunicación Bluetooth bidireccional implementado para Arduino con módulos HC-05.

## Licencia

Este proyecto está disponible bajo licencia libre para uso educativo y de desarrollo.