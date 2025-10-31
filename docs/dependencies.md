# Dependencias del Pipeline

Este documento describe las **dependencias entre componentes** del pipeline de procesamiento de datos de ventas. Cada etapa tiene requisitos previos que deben cumplirse antes de su ejecución.

---

## Flujo

```
┌─────────────────────┐
│   DATOS DE ENTRADA  │
│ - sales_data.csv    │
│ - product_catalog.csv│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    1. VALIDACIÓN    │ ◄─── Requiere: Esquema versionado
│                     │      (sales_schema_v1.json)
└──────────┬──────────┘
           │
           │ Si falla → ❌ DETENER PIPELINE
           │
           ▼ Si éxito
┌─────────────────────┐
│  2. PROCESAMIENTO   │ ◄─── Depende de: Validación exitosa
│                     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. ENRIQUECIMIENTO │ ◄─── Requiere: Catálogo de productos
│                     │      Depende de: Procesamiento exitoso
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. VALIDACIÓN DE    │ ◄─── Depende de: Enriquecimiento exitoso
│    CALIDAD          │
└──────────┬──────────┘
           │
           │ Si falla calidad → ⚠️ ALERTAR pero CONTINUAR
           │
           ▼
┌─────────────────────┐
│   5. GENERACIÓN     │ ◄─── Depende de: Calidad aprobada
│   DE REPORTES       │
└─────────────────────┘
```

---

## 1. Validación de Datos

### **Requiere:**
-  Archivo de entrada: `data/raw/sales_data.csv`
- Esquema de validación versionado: `data/schemas/sales_schema_v1.json`
-  Catálogo de productos (para validación de negocio): `data/reference/product_catalog.csv`

### **Valida:**
- Presencia de todas las columnas requeridas
- Tipos de datos correctos (integer, float, string, date)
- Formatos válidos (fechas, IDs de productos)
- Reglas de negocio:
  - `venta_id` únicos
  - `producto_id` existen en catálogo
  - Fechas no futuras
  - Cantidades y precios positivos

### **Produce:**
- Reporte de validación: `{'success': True/False, 'errors': [...]}`
- Log de errores encontrados

### **Comportamiento en caso de fallo:**
- ❌ **DETIENE el pipeline completo**
- 🔴 Genera alerta crítica
- 📝 Registra errores en logs
- No continúa a procesamiento

### **Justificación:**
Si los datos de entrada no cumplen el esquema básico, no tiene sentido procesarlos. La validación temprana previene errores downstream y garantiza calidad desde el origen.

---

## 2. Procesamiento de Datos

### **Depende de:**
-  **Validación exitosa** (paso 1 completado con `success: True`)
-  Datos validados en memoria o archivo temporal

### **Requiere:**
- Configuración de procesamiento en `config/pipeline_config.yaml`:
  - Estrategia para duplicados
  - Manejo de valores nulos
  - Reglas de cálculo

### **Ejecuta:**
- **Limpieza de duplicados:** Elimina registros con `venta_id` duplicado
- **Manejo de valores nulos:** 
  - `cliente_id` NULL → Reemplazar con "N/A"
  - Otros campos requeridos NULL → Eliminar fila
- **Cálculos:**
  - `total_venta = cantidad × precio_unitario`
  - `porcentaje_descuento = ((precio_base - precio_unitario) / precio_base) × 100`

### **Produce:**
- DataFrame procesado con campos adicionales
- Reporte de procesamiento: `{'record_count': N, 'duplicates_removed': M}`

### **Comportamiento en caso de fallo:**
-  **DETIENE el pipeline**
- Registra el punto de fallo para debugging
- Permite reintentos manuales

### **Justificación:**
El procesamiento depende de datos válidos porque necesita estructuras de datos consistentes. Si la validación falla, el procesamiento operaría sobre datos corruptos.

---

## 3. Enriquecimiento de Datos

### **Depende de:**
-  **Procesamiento exitoso** (paso 2 completado)
-  DataFrame procesado disponible

### **Requiere:**
- Catálogo de productos actualizado: `data/reference/product_catalog.csv`
- Configuración de join en `config/pipeline_config.yaml`:
  - Columna clave: `producto_id`
  - Columnas a agregar: `nombre`, `categoria`, `marca`, `precio_base`, `stock`

### **Ejecuta:**
- **Join/Merge:** Combina datos de ventas con catálogo de productos
- **Validación de join:** Identifica productos sin match
- **Agregación de campos:** Añade información de producto a cada venta

### **Produce:**
- DataFrame enriquecido con todas las columnas combinadas
- Lista de `producto_id` no encontrados en catálogo (para alertas)

### **Comportamiento en caso de fallo:**
- Si **catálogo no existe:**  DETIENE el pipeline
- Si **algunos productos no se encuentran:**  ALERTA pero CONTINÚA
  - Solo si < 5% de productos no encontrados
  - Si ≥ 5%, detiene el pipeline

### **Justificación:**
El enriquecimiento depende de datos procesados y limpios porque necesita claves únicas (`producto_id`) sin duplicados para hacer el join correctamente. También requiere que el catálogo esté actualizado para proporcionar información precisa.

---

## 4. Validación de Calidad

### **Depende de:**
-  **Enriquecimiento exitoso** (paso 3 completado)
- DataFrame enriquecido disponible

### **Requiere:**
- Umbrales de calidad definidos en `config/pipeline_config.yaml`:
  - `completeness_threshold: 0.95` (95% de datos completos)
  - `freshness_max_hours: 36` (máximo 36 horas de antigüedad)
  - `row_count_variation: 0.30` (variación máxima del 30%)

### **Valida:**
- **Completitud:** % de campos no nulos ≥ 95%
- **Frescura:** Fecha de datos ≤ 36 horas
- **Consistencia de volumen:** Número de registros no varía >30% vs promedio últimos 7 días
- **Integridad referencial:** % de productos encontrados ≥ 95%

### **Produce:**
- Reporte de calidad: `{'passed': True/False, 'metrics': {...}, 'issues': [...]}`
- Score de calidad (0-100)

### **Comportamiento en caso de fallo:**
-  **ALERTA pero NO DETIENE** (por defecto)
- Genera reporte de calidad detallado
- Marca los datos como "calidad cuestionable"
- Permite que el pipeline continúe (configurable)

### **Justificación:**
La validación de calidad depende de datos enriquecidos porque necesita el dataset completo para calcular métricas como completitud y consistencia. Se ejecuta al final para no interrumpir el flujo principal, pero antes de generar reportes finales.

---

## 5. Generación de Reportes

### **Depende de:**
- **Validación de calidad completada** (paso 4)
-  Datos enriquecidos disponibles (incluso si calidad tiene warnings)

### **Requiere:**
- Datos finales procesados y enriquecidos
- Configuración de reportes en `config/pipeline_config.yaml`
- Plantilla de reporte (opcional)

### **Genera:**
1. **Archivo enriquecido:** `data/processed/sales_enriched_YYYYMMDD_HHMMSS.csv`
   - Todos los datos procesados y enriquecidos
   - Incluye campos calculados
   - Listo para análisis

2. **Reporte de ejecución:** `data/outputs/report_YYYYMMDD_HHMMSS.json`
   ```json
   {
     "execution_id": "20241030_220000",
     "timestamp": "2024-10-30T22:00:00",
     "records_processed": 103,
     "pipeline_version": "1.0",
     "quality_score": 98.5,
     "execution_time_seconds": 12.5,
     "status": "success"
   }
   ```

3. **Logs de ejecución:** `logs/pipeline_execution.log`
   - Log detallado de toda la ejecución
   - Warnings y errores

### **Comportamiento en caso de fallo:**
- Si falla generación de reportes: ⚠️ ALERTA
- Los datos procesados se mantienen en memoria
- Intenta reintento automático (1 vez)

### **Justificación:**
Los reportes son el producto final del pipeline y deben generarse solo después de que todos los pasos anteriores se completen. Dependen de la validación de calidad para incluir métricas de calidad en el reporte.

---

## Dependencias de Archivos de Configuración

### **Esquema de Validación** (`data/schemas/sales_schema_v1.json`)
- **Versionado:** Sí (v1.0)
- **Usado por:** Validación (paso 1)
- **Frecuencia de cambio:** Baja (solo si cambia estructura de datos)
- **Crítico:**  SÍ - Sin esto, la validación no puede ejecutarse

### **Configuración del Pipeline** (`config/pipeline_config.yaml`)
- **Versionado:** Sí (incluye campo `version`)
- **Usado por:** Todos los componentes
- **Frecuencia de cambio:** Media (ajustes de umbrales, rutas)
- **Crítico:**  SÍ - Todos los componentes lo leen

### **Catálogo de Productos** (`data/reference/product_catalog.csv`)
- **Versionado:** No (se sobrescribe)
- **Usado por:** Validación (paso 1), Enriquecimiento (paso 3)
- **Frecuencia de actualización:** Semanal (cada lunes)
- **Crítico:**  SÍ - Sin esto, el enriquecimiento no puede ejecutarse

---

## Criterios de Decisión para Dependencias

### **¿Por qué estas dependencias?**

1. **Validación antes de Procesamiento:**
   - Evita procesar datos corruptos
   - Fail-fast: detectar errores temprano
   - Ahorra recursos computacionales

2. **Procesamiento antes de Enriquecimiento:**
   - El enriquecimiento necesita claves únicas (sin duplicados)
   - Los cálculos deben hacerse antes de agregar más columnas
   - Optimización: procesar menos datos es más rápido

3. **Enriquecimiento antes de Calidad:**
   - La validación de calidad necesita el dataset completo
   - Algunas métricas (completitud) requieren todas las columnas
   - Validar calidad al final evita reprocesar

4. **Calidad antes de Reportes:**
   - Los reportes deben incluir métricas de calidad
   - Permite marcar datos como "calidad cuestionable"
   - El usuario final debe saber la calidad de los datos

---

## Flujo de Excepciones

```
Validación FALLA
    ↓
 DETENER TODO
    ↓
Registrar error
    ↓
Enviar alerta
    ↓
No continuar
    ↓
Requiere intervención manual
```

```
Procesamiento FALLA
    ↓
 DETENER TODO
    ↓
Los datos están en estado inconsistente
    ↓
Registrar punto de fallo
    ↓
Permitir reintento manual
```

```
Enriquecimiento: Productos no encontrados
    ↓
¿Porcentaje < 5%?
    ├─ SÍ → ⚠️ ADVERTENCIA + CONTINUAR
    └─ NO → ❌ DETENER + ALERTA
```

```
Calidad FALLA
    ↓
⚠️ ADVERTENCIA (no detiene)
    ↓
Marcar datos como "calidad baja"
    ↓
Generar reporte de calidad detallado
    ↓
CONTINUAR con reportes
```

---

## Estrategias de Manejo de Fallos

### **Nivel 1: Fallos Críticos (Detienen Pipeline)**
- Validación de esquema falla
- Archivo de entrada no existe
- Catálogo de productos no existe
- Error de sintaxis en configuración

**Acción:**
- Detener inmediatamente
- No procesar datos parcialmente
- Enviar alerta crítica
- Registrar en logs con nivel ERROR

### **Nivel 2: Fallos de Advertencia (No Detienen)**
- Algunos productos no encontrados (<5%)
- Calidad por debajo del umbral
- Variación de volumen inusual

**Acción:**
- Continuar pipeline
- Marcar datos con advertencia
- Incluir en reporte de calidad
- Registrar con nivel WARNING

### **Nivel 3: Fallos Informativos (Solo Log)**
- Valores nulos esperados (cliente_id)
- Duplicados encontrados y eliminados
- Descuentos mayores al esperado

**Acción:**
- Continuar sin interrupción
- Registrar con nivel INFO
- Incluir en resumen de ejecución

---

## Versiones y Compatibilidad

### **Esquema de Validación:**
- **Versión actual:** 1.0
- **Cambios incompatibles:** Requieren nueva versión (1.0 → 2.0)
- **Cambios compatibles:** Mantienen versión, actualizan fecha

### **Catálogo de Productos:**
- **Sin versionado explícito**
- **Actualización:** Sobrescribe archivo existente
- **Compatibilidad:** Siempre debe tener las columnas mínimas requeridas

---
