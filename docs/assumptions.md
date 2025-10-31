# Supuestos del Pipeline de Datos de Ventas

## Contexto de Negocio

Este pipeline procesa datos de ventas de , una tienda de electrónica. El sistema procesa las transacciones diarias para generar reportes consolidados y detectar anomalías.

---

## 1. Supuestos de Datos de Entrada

### 1.1 Archivo: `sales_data.csv`


**Estructura:**
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| venta_id | Integer | ID único de venta | 1001 |
| fecha | String (YYYY-MM-DD) | Fecha de la transacción | 2024-10-27 |
| producto_id | String | Código del producto | P001 |
| cantidad | Integer | Unidades vendidas | 2 |
| precio_unitario | Float | Precio unitario en COP | 1500000.00 |
| cliente_id | String | ID del cliente (opcional) | C001 o NULL |
| vendedor | String | Nombre del vendedor | Juan Pérez |

**Características:**
- **Volumen esperado:** 500-1500 registros/día
- **Formato:** CSV, UTF-8, separador: coma
- **Frecuencia:** Diario (batch nocturno)
- **Tamaño aproximado:** 50-150 KB por archivo

**Reglas de Negocio:**
- `venta_id` es único y autoincrementable
- `fecha` siempre corresponde al día de operación
- `cantidad` debe ser ≥ 1
- `precio_unitario` debe ser > 0
- `cliente_id` puede ser NULL (ventas sin registro)
- `vendedor` siempre debe estar presente

---

### 1.2 Archivo: 

**Fuente:** Sistema de inventario, actualizado manualmente cada lunes

**Estructura:**
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| producto_id | String | Código único del producto | P001 |
| nombre | String | Nombre del producto | Laptop Dell Inspiron 15 |
| categoria | String | Categoría del producto | Computadoras |
| marca | String | Marca del fabricante | Dell |
| precio_base | Float | Precio sugerido en COP | 1500000.00 |
| stock | Integer | Unidades disponibles | 50 |

**Características:**
- **Volumen:** ~100-200 productos activos
- **Actualización:** Semanal (cada lunes)
- **Categorías disponibles:** Computadoras, Accesorios, Pantallas, Audio, Gaming
