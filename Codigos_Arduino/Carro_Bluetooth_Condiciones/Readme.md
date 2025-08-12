# Sistema de Control de dos motores con TB6612FNG

Este proyecto implementa un sistema de control para un carro utilizando Arduino, el controlador de motores TB6612FNG y comunicación Bluetooth. El carro puede recibir comandos tanto por Bluetooth como por el monitor serial y ejecutar movimientos básicos de navegación.

## Características

- Control de carro mediante comandos de dirección (W, S, A, D)
- Comunicación dual: Bluetooth y monitor serial (Modulo HC-05)
- Control automático de tiempo de movimiento (330ms por comando)
- Parada automática de seguridad
- Compatible con controlador de motores TB6612FNG

## Componentes Requeridos

### Hardware
- Arduino Uno/Nano/compatible
- Controlador de motores TB6612FNG
- 2 motores DC
- Módulo Bluetooth (HC-05)
- Fuente de alimentación para motores
- Cables de conexión

### Software
- Arduino IDE
- Biblioteca SoftwareSerial (incluida en Arduino IDE)

## Conexiones

### TB6612FNG al Arduino
```
TB6612FNG    →    Arduino
PWM1         →    Pin 3
AIN2         →    Pin 4
AIN1         →    Pin 5
STBY         →    Pin 6
BIN1         →    Pin 7
BIN2         →    Pin 8
PWM2         →    Pin 9
```

### Módulo Bluetooth
```
Bluetooth    →    Arduino
TX           →    Pin 11
RX           →    Pin 10
VCC          →    5V
GND          →    GND
```

### Motores
- Motor A: Conectar a las salidas AO1 y AO2 del TB6612FNG
- Motor B: Conectar a las salidas BO1 y BO2 del TB6612FNG

## Comandos de Control

| Comando | Acción |
|---------|--------|
| `W` | Avanzar hacia adelante |
| `S` | Retroceder |
| `A` | Girar a la izquierda |
| `D` | Girar a la derecha |

## Configuración

### Velocidad de los Motores
```cpp
int Vel1 = 80;  // Velocidad motor A (0-255)
int Vel2 = 80;  // Velocidad motor B (0-255)
```

### Tiempo de Movimiento
```cpp
if (millis() - startTime >= 330) {  // 330ms por comando
```

### Comunicación Serial
```cpp
Serial.begin(9600);      // Monitor serial
BTSerial.begin(9600);    // Bluetooth
```

## Funcionamiento

1. **Inicialización**: El sistema configura los pines y activa el controlador de motores
2. **Recepción de Comandos**: Escucha comandos tanto del Bluetooth como del monitor serial
3. **Ejecución**: Al recibir un comando válido, activa los motores según la dirección especificada
4. **Temporización**: Cada movimiento dura exactamente 330ms
5. **Parada Automática**: Los motores se detienen automáticamente al finalizar el tiempo

## Características de Seguridad

- **Parada Automática**: Los motores se detienen si no hay comandos activos
- **Control de Tiempo**: Cada comando tiene una duración limitada para evitar movimientos excesivos
- **Estado de Reposo**: El sistema vuelve automáticamente al estado de reposo ('C')

## Modificaciones Posibles

### Cambiar Velocidad
Modifica las variables `Vel1` y `Vel2` para ajustar la velocidad de los motores (rango: 0-255).

### Cambiar Tiempo de Movimiento
Modifica el valor `330` en la condición del temporizador para cambiar la duración de cada movimiento.

### Agregar Nuevos Comandos
Añade nuevos casos en el switch para implementar movimientos adicionales:
```cpp
case 'X': // Nuevo comando
    // Lógica del nuevo movimiento
    break;
```

## Diagnóstico

### Monitor Serial
El código incluye mensajes de depuración que se pueden visualizar en el monitor serial:
- Estado de inicialización
- Comandos recibidos por Bluetooth
- Comandos recibidos por monitor serial

### Problemas Comunes
- **Motores no se mueven**: Verificar conexiones y alimentación del TB6612FNG
- **No recibe comandos Bluetooth**: Verificar pareamiento y conexiones del módulo
- **Movimiento errático**: Revisar conexiones de los motores y configuración de velocidad

## Autor

Código desarrollado para control control de dos motores con Arduino para implementarlo con técnicas EOG.

## Licencia

Este proyecto está disponible bajo licencia libre para uso educativo y de desarrollo.