"""
Script para generar datos de prueba del pipeline
Genera: sales_data.csv y product_catalog.csv
"""

import pandas as pd
import random
import os
from datetime import datetime, timedelta

# Asegurar que las carpetas existen
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/reference', exist_ok=True)


def generate_product_catalog():
    """Genera el catálogo de productos"""
    
    productos = [
        # Computadoras
        {'producto_id': 'P001', 'nombre': 'Laptop Dell Inspiron 15', 'categoria': 'Computadoras', 'marca': 'Dell', 'precio_base': 1500000.00, 'stock': 50},
        {'producto_id': 'P002', 'nombre': 'Laptop HP Pavilion 14', 'categoria': 'Computadoras', 'marca': 'HP', 'precio_base': 1800000.00, 'stock': 35},
        {'producto_id': 'P003', 'nombre': 'MacBook Air M2', 'categoria': 'Computadoras', 'marca': 'Apple', 'precio_base': 4500000.00, 'stock': 20},
        {'producto_id': 'P004', 'nombre': 'PC Gamer Asus ROG', 'categoria': 'Computadoras', 'marca': 'Asus', 'precio_base': 6000000.00, 'stock': 15},
        
        # Accesorios
        {'producto_id': 'P005', 'nombre': 'Mouse Logitech MX Master 3', 'categoria': 'Accesorios', 'marca': 'Logitech', 'precio_base': 350000.00, 'stock': 200},
        {'producto_id': 'P006', 'nombre': 'Teclado Mecánico Corsair K95', 'categoria': 'Accesorios', 'marca': 'Corsair', 'precio_base': 650000.00, 'stock': 80},
        {'producto_id': 'P007', 'nombre': 'Webcam Logitech C920', 'categoria': 'Accesorios', 'marca': 'Logitech', 'precio_base': 280000.00, 'stock': 120},
        {'producto_id': 'P008', 'nombre': 'Hub USB-C Anker', 'categoria': 'Accesorios', 'marca': 'Anker', 'precio_base': 180000.00, 'stock': 150},
        
        # Pantallas
        {'producto_id': 'P009', 'nombre': 'Monitor LG 27" 4K', 'categoria': 'Pantallas', 'marca': 'LG', 'precio_base': 1200000.00, 'stock': 45},
        {'producto_id': 'P010', 'nombre': 'Monitor Samsung 24" Curvo', 'categoria': 'Pantallas', 'marca': 'Samsung', 'precio_base': 800000.00, 'stock': 60},
        {'producto_id': 'P011', 'nombre': 'Monitor Gaming Asus 144Hz', 'categoria': 'Pantallas', 'marca': 'Asus', 'precio_base': 1500000.00, 'stock': 30},
        
        # Audio
        {'producto_id': 'P012', 'nombre': 'Auriculares Sony WH-1000XM5', 'categoria': 'Audio', 'marca': 'Sony', 'precio_base': 1100000.00, 'stock': 70},
        {'producto_id': 'P013', 'nombre': 'Auriculares Gaming HyperX', 'categoria': 'Audio', 'marca': 'HyperX', 'precio_base': 450000.00, 'stock': 90},
        {'producto_id': 'P014', 'nombre': 'Bocinas Logitech Z623', 'categoria': 'Audio', 'marca': 'Logitech', 'precio_base': 550000.00, 'stock': 40},
        {'producto_id': 'P015', 'nombre': 'Micrófono Blue Yeti', 'categoria': 'Audio', 'marca': 'Blue', 'precio_base': 680000.00, 'stock': 35},
        
        # Gaming
        {'producto_id': 'P016', 'nombre': 'Consola PlayStation 5', 'categoria': 'Gaming', 'marca': 'Sony', 'precio_base': 2500000.00, 'stock': 25},
        {'producto_id': 'P017', 'nombre': 'Xbox Series X', 'categoria': 'Gaming', 'marca': 'Microsoft', 'precio_base': 2400000.00, 'stock': 30},
        {'producto_id': 'P018', 'nombre': 'Nintendo Switch OLED', 'categoria': 'Gaming', 'marca': 'Nintendo', 'precio_base': 1600000.00, 'stock': 50},
        {'producto_id': 'P019', 'nombre': 'Control Xbox Wireless', 'categoria': 'Gaming', 'marca': 'Microsoft', 'precio_base': 280000.00, 'stock': 100},
        {'producto_id': 'P020', 'nombre': 'Silla Gaming DXRacer', 'categoria': 'Gaming', 'marca': 'DXRacer', 'precio_base': 1300000.00, 'stock': 20},
    ]
    
    df = pd.DataFrame(productos)
    df.to_csv('data/reference/product_catalog.csv', index=False)
    print(f"Catálogo generado: {len(df)} productos")
    print(f"   Guardado en: data/reference/product_catalog.csv")
    return df


def generate_sales_data(num_records=100, days_back=30):
    """Genera datos de ventas sintéticos"""
    
    # Leer el catálogo para obtener productos válidos
    catalog = pd.read_csv('data/reference/product_catalog.csv')
    product_ids = catalog['producto_id'].tolist()
    
    # Configuración
    vendedores = ['Juan Pérez', 'María López', 'Pedro Gómez', 'Ana Rodríguez', 'Luis Martínez']
    
    # Generar datos
    ventas = []
    base_date = datetime.now()
    
    for i in range(num_records):
        # Fecha aleatoria en los últimos N días
        random_days = random.randint(0, days_back)
        fecha = (base_date - timedelta(days=random_days)).strftime('%Y-%m-%d')
        
        # Seleccionar producto aleatorio
        producto_id = random.choice(product_ids)
        producto_info = catalog[catalog['producto_id'] == producto_id].iloc[0]
        precio_base = producto_info['precio_base']
        
        # Cantidad (más probable vender 1-2 unidades)
        cantidad = random.choices([1, 2, 3, 4, 5], weights=[50, 30, 10, 5, 5])[0]
        
        # Precio unitario (80% sin descuento, 20% con descuento)
        if random.random() < 0.8:
            # Sin descuento (puede variar ±5%)
            precio_unitario = precio_base * random.uniform(0.95, 1.05)
        else:
            # Con descuento (10-30% off)
            descuento = random.uniform(0.10, 0.30)
            precio_unitario = precio_base * (1 - descuento)
        
        # Cliente (70% con ID, 30% sin ID)
        if random.random() < 0.7:
            cliente_id = f"C{random.randint(1, 500):03d}"
        else:
            cliente_id = None
        
        venta = {
            'venta_id': 1000 + i,
            'fecha': fecha,
            'producto_id': producto_id,
            'cantidad': cantidad,
            'precio_unitario': round(precio_unitario, 2),
            'cliente_id': cliente_id,
            'vendedor': random.choice(vendedores)
        }
        ventas.append(venta)
    
    # Agregar algunos registros con problemas para testing
    # 1. Producto que no existe en catálogo
    ventas.append({
        'venta_id': 2000,
        'fecha': base_date.strftime('%Y-%m-%d'),
        'producto_id': 'P999',
        'cantidad': 1,
        'precio_unitario': 100000.00,
        'cliente_id': 'C001',
        'vendedor': 'Juan Pérez'
    })
    
    # 2. Precio con descuento mayor al 30%
    ventas.append({
        'venta_id': 2001,
        'fecha': base_date.strftime('%Y-%m-%d'),
        'producto_id': 'P001',
        'cantidad': 1,
        'precio_unitario': 900000.00,
        'cliente_id': 'C002',
        'vendedor': 'María López'
    })
    
    # 3. Duplicado
    ventas.append({
        'venta_id': 1050,
        'fecha': base_date.strftime('%Y-%m-%d'),
        'producto_id': 'P005',
        'cantidad': 2,
        'precio_unitario': 350000.00,
        'cliente_id': 'C003',
        'vendedor': 'Pedro Gómez'
    })
    
    df = pd.DataFrame(ventas)
    df.to_csv('data/raw/sales_data.csv', index=False)
    print(f" Datos de ventas generados: {len(df)} registros")
    print(f"   Guardado en: data/raw/sales_data.csv")
    print(f"   Período: últimos {days_back} días")
    print(f"   Incluye: 1 producto inexistente, 1 descuento >30%, 1 duplicado")
    return df

def main():
    """Función principal"""
    print("\nGenerando datos de prueba para el pipeline...\n")
    
    generate_product_catalog()
    print()
    
    generate_sales_data(num_records=100, days_back=30)
    print()

if __name__ == "__main__":
    main()