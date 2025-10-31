## Diagrama Principal del Pipeline
```
┌─────────────────────────────────────────────────────────────────────┐
│                         INICIO DEL PIPELINE                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FUENTES DE DATOS                                │
├─────────────────────────────────────────────────────────────────────┤
│  data/raw/sales_data.csv                                         │
│     ├─ venta_id, fecha, producto_id                                 │
│     ├─ cantidad, precio_unitario                                     │
│     └─ cliente_id, vendedor                                          │
│                                                                       │
│  data/reference/product_catalog.csv                              │
│     ├─ producto_id, nombre, categoria                               │
│     └─ marca, precio_base, stock                                     │
│                                                                       │
│   data/schemas/sales_schema_v1.json                               │
│     └─ Esquema de validación versionado                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  PASO 1: VALIDACIÓN DE DATOS                         │
│                  [src/data_validation.py]                            │
├─────────────────────────────────────────────────────────────────────┤
│  Validaciones:                                                       │
│  Existencia de archivos requeridos                                │
│  Columnas requeridas presentes                                    │
│  Tipos de datos correctos                                         │
│  Formatos válidos (fechas, IDs)                                   │
│  Reglas de negocio:                                               │
│    • producto_id existe en catálogo                                  │
│    • Cantidades y precios positivos                                  │
│    • Fechas no futuras                                               │
│    • IDs únicos                                                      │
│                                                                       │
│  Salida: {'success': True/False, 'errors': [...]}                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │  Si success = True
                                 │  Si success = False → DETENER
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│               PASO 2: PROCESAMIENTO DE DATOS                         │
│               [src/data_processing.py]                               │
├─────────────────────────────────────────────────────────────────────┤
│  Operaciones:                                                        │
│  Eliminar duplicados (por venta_id)                              │
│     Antes: 103 registros → Después: 102 registros                   │
│                                                                       │
│   Manejar valores nulos                                           │
│     • cliente_id NULL → Reemplazar con "N/A"                        │
│     • vendedor NULL → Eliminar fila                                  │
│                                                                       │
│   Calcular campos derivados                                       │
│     • total_venta = cantidad × precio_unitario                       │
│                                                                       │
│  Salida: DataFrame procesado con 102 registros                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│             PASO 3: ENRIQUECIMIENTO DE DATOS                         │
│             [src/data_enrichment.py]                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Operaciones:                                                        │
│   Merge con catálogo (LEFT JOIN por producto_id)                  │
│     Ventas + Catálogo → Datos Enriquecidos                          │
│                                                                       │
│  Agregar columnas del catálogo:                                  │
│     • nombre (nombre del producto)                                   │
│     • categoria (Computadoras, Audio, Gaming, etc.)                 │
│     • marca (Dell, Sony, Microsoft, etc.)                           │
│     • precio_base (precio sugerido)                                  │
│     • stock (unidades disponibles)                                   │
│                                                                       │
│   Calcular campos adicionales:                                    │
│     • porcentaje_descuento = ((precio_base - precio_unitario)       │
│                                / precio_base) × 100                  │
│     • tiene_descuento = (porcentaje_descuento > 0)                  │
│                                                                       │
│   Productos no encontrados:                                        │
│     Si < 5% → ADVERTENCIA (continuar)                               │
│     Si ≥ 5% → ERROR (detener)                                       │
│                                                                       │
│  Salida: DataFrame enriquecido con todas las columnas               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│            PASO 4: VALIDACIÓN DE CALIDAD                             │
│            [src/quality_checks.py]                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Métricas evaluadas:                                                 │
│                                                                       │
│  Completitud:                                                     │
│     Umbral: ≥ 95% de campos no nulos                                │
│                                                                       │
│                                                                       │
│   Frescura:                                                        │
│     Umbral: ≤ 36 horas de antigüedad                                │
│                                                 │
│                                                                       │
│   Volumen:                                                         │
│     Umbral: Variación ≤ 30% vs promedio                             │
│                                                       │
│                                                                       │
│  Duplicados:                                                      │
│     Umbral: 0% duplicados                                            │
│     Actual: 0%                                                        │
│                                                                       │
│  Quality Score: 100%                                                 │
│                                                                       │
│   Si calidad < umbral:                                            │
│     - Generar advertencia (NO detiene por defecto)                   │
│     - Marcar datos como "calidad cuestionable"                       │
│     - Continuar con generación de reportes                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PASO 5: GENERACIÓN DE REPORTES                          │
│              [src/orchestrator.py - generate_reports()]              │
├─────────────────────────────────────────────────────────────────────┤
│  Salidas generadas:                                                  │
│                                                                       │
│  data/processed/sales_enriched_YYYYMMDD_HHMMSS.csv               │
│     └─ Datos finales procesados y enriquecidos                      │
│        (Listo para análisis y BI)                                    │
│                                                                       │
│   data/outputs/report_YYYYMMDD_HHMMSS.json                        │
│     └─ Reporte de ejecución:                                         │
│        • execution_id                                                │
│        • timestamp                                                   │
│        • records_processed                                           │
│        • pipeline_version                                            │
│        • quality_score                                               │
│        • status (success/failed)                                     │
│                                                                       │
│   logs/pipeline_execution.log                                      │
│     └─ Log detallado de toda la ejecución                           │
│        (INFO, WARNING, ERROR)                                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FIN DEL PIPELINE ✅                             │
│                                                                       │
│  Resultado exitoso:                                                  │
│  • 102 registros procesados                                          │
│  • Tiempo de ejecución: ~12 segundos                                │
│  • Quality Score: 100%                                               │
└─────────────────────────────────────────────────────────────────────┘