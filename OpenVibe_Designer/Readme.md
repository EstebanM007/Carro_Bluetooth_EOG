# Escenarios OpenViBE para Sistema EOG Horizontal

## Descripción General

Este repositorio contiene tres escenarios de OpenViBE diseñados para el desarrollo y testing de un sistema de Electrooculografía (EOG). Cada escenario implementa diferentes pipelines de procesamiento de señales para distintas etapas del desarrollo del sistema.

## Escenarios Implementados

### 1. EOG.xml
**Escenario de Adquisición en Tiempo Real**

Pipeline de procesamiento para conexión directa con tarjeta bioamplificadora:

```
Acquisition Client → Channel Selector → Temporal Filter → Signal Display
                         ↓                    ↓
                 Generic Stream Writer   LSL Export
                         ↓
                    CSV File Writer
```

**Componentes del Escenario**:
- **Acquisition Client**: Adquisición directa desde hardware bioamplificador
- **Channel Selector (Channel 1)**: Selección del canal EOG horizontal
- **Temporal Filter**: Filtro Butterworth 0.5Hz-30Hz para eliminación de deriva y ruido
- **Signal Display**: Visualización de señal filtrada y cruda
- **Generic Stream Writer**: Grabación de datos en formato .ov
- **LSL Export (Gipsa)**: Streaming en tiempo real vía Lab Streaming Layer
- **CSV File Writer**: Exportación de datos procesados

### 2. EOG_GenericStream.xml
**Escenario de Reproducción Offline**

Pipeline para análisis de señales previamente grabadas:

```
Generic Stream Reader → Channel Selector → Temporal Filter → Signal Display
                            ↓                    ↓
                       LSL Export         CSV File Writer
                            ↓
                      LSL Export (segundo)
```

**Componentes del Escenario**:
- **Generic Stream Reader**: Carga archivos .ov con datos EOG grabados
- **Channel Selector (EOG1)**: Extracción del canal de interés
- **Temporal Filter**: Mismo filtro Butterworth del escenario en vivo
- **Signal Display (doble)**: Visualización comparativa filtrada/sin filtrar
- **LSL Export (doble)**: Dos streams LSL para diferentes propósitos
- **CSV File Writer (Deprecado)**: Exportación de resultados del análisis

### 3. Prueba_2Streams.xml
**Escenario de Testing Multi-Stream**

Pipeline simplificado para validación de múltiples streams:

```
Sinus Oscillator → Signal Display → LSL Export
        ↓
Sinus Oscillator → Signal Display → LSL Export
```

**Componentes del Escenario**:
- **Sinus Oscillator (x2)**: Generadores de señales sintéticas para testing
- **Signal Display (x2)**: Visualización independiente de cada stream
- **LSL Export (x2)**: Exportación simultánea de múltiples streams
- **CSV File Writer (Deprecado)**: Logging de datos de prueba

## Arquitectura de Procesamiento

### Pipeline de Filtrado
Todos los escenarios implementan el mismo esquema de filtrado:
- **Filtro Butterworth**: Paso banda 0.5Hz a 30Hz
- **Propósito**: Eliminación de deriva DC y ruido de alta frecuencia
- **Preservación**: Componentes de señal EOG (0.1Hz-10Hz típicamente)

### Sistema de Streams
- **LSL (Lab Streaming Layer)**: Protocolo principal para transmisión de datos
- **Configuración Gipsa**: Adaptación específica para el laboratorio
- **Multi-streaming**: Capacidad de múltiples streams simultáneos

### Grabación y Reproducción
- **Formato .ov**: Formato nativo OpenViBE para datos temporales
- **CSV Export**: Formato estándar para análisis posterior
- **Compatibilidad**: Ciclo completo grabación → reproducción → análisis

## Configuración de Escenarios

### Parámetros de Filtrado
```xml
Temporal Filter:
  - Tipo: Butterworth
  - Frecuencia inferior: 0.5Hz
  - Frecuencia superior: 30Hz
  - Orden: [Configurado en cada escenario]
```

### Selección de Canales
- **EOG.xml**: Channel 1 (adquisición directa)
- **EOG_GenericStream.xml**: EOG1 (canal nombrado)
- **Prueba_2Streams.xml**: No aplicable (señales sintéticas)

### Configuraciones LSL
- **Identificador**: OpenViBE Stream
- **Tipo de datos**: Señal continua
- **Frecuencia de muestreo**: Heredada del escenario

## Casos de Uso

### Desarrollo (EOG.xml)
- Adquisición de datos EOG reales
- Calibración de parámetros de filtrado
- Validación en tiempo real del pipeline

### Testing/Debugging (EOG_GenericStream.xml)
- Análisis offline de datos grabados
- Desarrollo de algoritmos sin hardware
- Reproducibilidad de experimentos

### Validación de Sistema (Prueba_2Streams.xml)
- Testing de capacidad multi-stream
- Verificación de rendimiento del sistema
- Validación de protocolos de comunicación

## Flujo de Datos

### EOG Completo
1. **Adquisición** → Hardware bioamplificador
2. **Preprocesamiento** → Selección canal + filtrado
3. **Distribución** → LSL streams + grabación local
4. **Visualización** → Monitoreo en tiempo real

### Análisis Offline
1. **Carga** → Archivo .ov previamente grabado
2. **Procesamiento** → Mismo pipeline que tiempo real
3. **Análisis** → Múltiples streams LSL para diferentes análisis
4. **Exportación** → Resultados en CSV

### Testing Sintético
1. **Generación** → Señales sinusoidales controladas
2. **Streaming** → Múltiples streams LSL simultáneos
3. **Validación** → Verificación de integridad de datos

## Notas Técnicas

### Compatibilidad
- **OpenViBE**: Versión compatible con v3.6.0
- **LSL**: Protocolo estándar para streaming de datos
- **Hardware**: Tarjetas bioamplificadoras estándar

### Rendimiento
- **Latencia**: Minimizada para aplicaciones en tiempo real
- **Throughput**: Optimizado para múltiples streams simultáneos
- **Estabilidad**: Testing extensivo con señales sintéticas

### Escalabilidad
- **Modular**: Cada escenario es independiente y modificable
- **Extensible**: Fácil adición de nuevos componentes de procesamiento
- **Reutilizable**: Componentes compartidos entre escenarios

---

**Archivos del Proyecto**:
- `EOG.xml` - Escenario adquisición tiempo real
- `EOG_GenericStream.xml` - Escenario reproducción offline  
- `Prueba_2Streams.xml` - Escenario testing multi-stream