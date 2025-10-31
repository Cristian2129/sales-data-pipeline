# Estrategias de Escalabilidad

Este documento describe las estrategias de escalabilidad para el pipeline de datos de ventas de la tienda de electrónica. El sistema procesa transacciones diarias para generar reportes consolidados y detectar anomalías.

## Contexto del Proyecto

El pipeline procesa dos fuentes principales de datos. El archivo sales_data.csv contiene entre 500 y 1500 registros diarios con información de transacciones. El archivo products.csv mantiene un catálogo de 100 a 200 productos activos, actualizado semanalmente.

El volumen diario estimado es de 50 a 150 KB para ventas, con procesamiento en batch nocturno. Los productos se actualizan cada lunes desde el sistema de inventario.

## Nivel 1: Procesamiento Local

### Características

Volumen: Menos de 1GB
Herramientas: Pandas, Python puro
Ejecución: GitHub Actions estándar
Recursos: 2-4 CPU cores, 7GB RAM

### Aplicación al Pipeline de Ventas

El procesamiento local es ideal para el volumen actual del negocio. Los archivos diarios de ventas (50-150 KB) y el catálogo de productos se procesan eficientemente con Pandas.

GitHub Actions ejecuta el pipeline nocturno automáticamente. Lee los archivos CSV, aplica las reglas de negocio, cruza información de ventas con productos y genera reportes consolidados.

### Ventajas para el Negocio

Sin costos de infraestructura adicional. Configuración simple que el equipo puede mantener fácilmente. Integración directa con el repositorio del código. Suficiente para procesar el volumen actual de transacciones.

### Limitaciones

El tiempo máximo de ejecución es de 6 horas por job. Los recursos están limitados a lo que ofrece GitHub Actions. No es viable si el volumen de ventas crece significativamente.

### Casos de Uso Actuales

Validación diaria de datos de ventas. Cruce con catálogo de productos. Detección de anomalías básicas. Generación de reportes de ventas por vendedor, categoría y fecha. Cálculo de métricas de negocio.

## Nivel 2: Procesamiento en la Nube (Azure)

### Características

Volumen: 1GB - 10GB
Herramientas: Azure Functions, Azure Batch
Recursos: Escalado automático
Costo: Aproximadamente $0.20 por GB procesado

### Cuándo Migrar a este Nivel

Cuando el negocio crezca y se procesen más de 5000 transacciones diarias. Si se agregan múltiples sucursales que reportan ventas. Cuando se requiera procesamiento en tiempo real. Si se necesitan integraciones con otros sistemas empresariales.

### Implementación para el Pipeline

Azure Functions puede procesar archivos de ventas cuando se suben a Blob Storage. Cada tienda o sucursal sube su archivo independiente. El sistema escala automáticamente según la cantidad de archivos recibidos.

Azure Batch permite procesar múltiples archivos en paralelo. Útil para reprocesar datos históricos o generar reportes de periodos extensos.

### Ventajas

Escalado automático según demanda del negocio. Pago solo por el tiempo de procesamiento usado. Mayor capacidad para manejar picos de ventas. Integración con otros servicios de Azure como bases de datos y almacenamiento.

### Componentes Principales

Azure Functions maneja triggers automáticos cuando llegan nuevos archivos. Azure Batch procesa múltiples archivos simultáneamente. Azure Blob Storage almacena archivos de entrada y resultados. Azure SQL Database guarda datos procesados para consultas rápidas.

## Nivel 3: Procesamiento Distribuido

### Características

Volumen: Mayor a 10GB
Herramientas: Azure Databricks, Azure Synapse Analytics
Recursos: Cluster distribuido
Costo: Variable según configuración

### Cuándo Considerar este Nivel

Cuando el negocio escale a nivel nacional con decenas de tiendas. Si se procesan millones de transacciones mensuales. Cuando se requiere análisis predictivo con Machine Learning. Para análisis en tiempo real de tendencias de ventas.

### Aplicación Empresarial

Azure Databricks permite analizar patrones de ventas históricos a gran escala. Identificar tendencias estacionales y comportamiento de clientes. Entrenar modelos de Machine Learning para predicción de demanda.

Azure Synapse Analytics consolida datos de múltiples fuentes. Integra información de ventas, inventario, logística y finanzas. Genera reportes ejecutivos con Power BI.

### Arquitectura Propuesta

Los datos de ventas de múltiples sucursales fluyen hacia Azure Data Lake. Azure Data Factory orquesta la ingesta y movimiento de datos. Databricks procesa y transforma los datos en paralelo. Los resultados se almacenan en Delta Lake para análisis histórico. Power BI consulta directamente para dashboards ejecutivos.

### Ventajas Empresariales

Procesamiento de grandes volúmenes sin degradación de rendimiento. Análisis predictivo para toma de decisiones estratégicas. Consolidación de información de toda la organización. Capacidad para análisis en tiempo real de ventas.


