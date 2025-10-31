"""
Modulo de Validacion de Datos
Valida que los datos cumplan con el esquema y reglas de negocio
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta


class DataValidator:
    """Validador de datos de entrada"""
    
    def __init__(self, config):
        """
        Inicializa el validador
        
        Args:
            config: Configuracion de validacion desde pipeline_config.yaml
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.schema = self.load_schema()
        
    def load_schema(self):
        """Carga el esquema de validacion desde JSON"""
        try:
            schema_path = self.config['schema_path']  # ← Cambio aquí (sin ["paths"])
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error cargando esquema: {e}")
            raise
    
    def validate(self):
        """
        Ejecuta todas las validaciones
        
        Returns:
            dict: Resultado de la validacion con success, errors, etc.
        """
        errors = []
        
        try:
            # Validar que existan los archivos requeridos
            self.logger.info("Validando existencia de archivos...")
            for filename in self.config['required_files']:
                filepath = f"data/raw/{filename}"
                try:
                    with open(filepath, 'r') as f:
                        pass
                except FileNotFoundError:
                    errors.append(f"Archivo no encontrado: {filepath}")
            
            if errors:
                return {'success': False, 'errors': errors}
            
            # Leer datos de ventas
            sales_data = pd.read_csv('data/raw/sales_data.csv')
            catalog_data = pd.read_csv('data/reference/product_catalog.csv')
            
            # Validar columnas requeridas
            self.logger.info("Validando columnas requeridas...")
            missing_cols = self.validate_required_columns(sales_data)
            if missing_cols:
                errors.extend(missing_cols)
            
            # Validar tipos de datos
            if self.config.get('validate_data_types', True):
                self.logger.info("Validando tipos de datos...")
                type_errors = self.validate_data_types(sales_data)
                if type_errors:
                    errors.extend(type_errors)
            
            # Validar reglas de negocio
            if self.config.get('validate_business_rules', True):
                self.logger.info("Validando reglas de negocio...")
                business_errors = self.validate_business_rules(sales_data, catalog_data)
                if business_errors:
                    errors.extend(business_errors)
            
            if errors:
                return {
                    'success': False,
                    'errors': errors,
                    'total_errors': len(errors)
                }
            
            return {
                'success': True,
                'message': f'Validacion exitosa: {len(sales_data)} registros validados',
                'record_count': len(sales_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error durante validacion: {e}")
            return {
                'success': False,
                'errors': [f"Error critico: {str(e)}"]
            }
    
    def validate_required_columns(self, df):
        """Valida que existan todas las columnas requeridas"""
        errors = []
        required_cols = self.schema['required_columns']
        
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
        
        return errors
    
    def validate_data_types(self, df):
        """Valida que los tipos de datos sean correctos"""
        errors = []
        
        # Validar venta_id es numerico
        if 'venta_id' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['venta_id']):
                errors.append("venta_id debe ser numerico")
        
        # Validar cantidad es numerico
        if 'cantidad' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['cantidad']):
                errors.append("cantidad debe ser numerico")
        
        # Validar precio_unitario es numerico
        if 'precio_unitario' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['precio_unitario']):
                errors.append("precio_unitario debe ser numerico")
        
        # Validar formato de fecha
        if 'fecha' in df.columns:
            try:
                pd.to_datetime(df['fecha'], format='%Y-%m-%d', errors='coerce')
            except:
                errors.append("fecha debe tener formato YYYY-MM-DD")
        
        return errors
    
    def validate_business_rules(self, sales_df, catalog_df):
        """Valida reglas de negocio"""
        errors = []
        warnings = []
        
        # Validar que productos existan en catalogo
        if 'producto_id' in sales_df.columns:
            catalog_ids = set(catalog_df['producto_id'])
            sales_ids = set(sales_df['producto_id'])
            missing_products = sales_ids - catalog_ids
            
            if missing_products:
                warnings.append(f"Productos no encontrados en catalogo: {missing_products}")
                self.logger.warning(f"Productos no encontrados: {missing_products}")
        
        # Validar que cantidad sea positiva
        if 'cantidad' in sales_df.columns:
            negative_qty = sales_df[sales_df['cantidad'] <= 0]
            if len(negative_qty) > 0:
                errors.append(f"Encontradas {len(negative_qty)} ventas con cantidad <= 0")
        
        # Validar que precio sea positivo
        if 'precio_unitario' in sales_df.columns:
            negative_price = sales_df[sales_df['precio_unitario'] <= 0]
            if len(negative_price) > 0:
                errors.append(f"Encontrados {len(negative_price)} registros con precio <= 0")
        
        # Validar fechas no futuras
        if 'fecha' in sales_df.columns:
            today = datetime.now().date()
            sales_df['fecha_parsed'] = pd.to_datetime(sales_df['fecha'], errors='coerce').dt.date
            future_dates = sales_df[sales_df['fecha_parsed'] > today]
            if len(future_dates) > 0:
                errors.append(f"Encontradas {len(future_dates)} ventas con fechas futuras")
        
        # Validar IDs unicos
        if 'venta_id' in sales_df.columns:
            duplicates = sales_df[sales_df.duplicated(subset=['venta_id'], keep=False)]
            if len(duplicates) > 0:
                warnings.append(f"Encontrados {len(duplicates)} IDs duplicados (seran eliminados en procesamiento)")
                self.logger.warning(f"IDs duplicados: {duplicates['venta_id'].tolist()}")
        
        # Los warnings no detienen el pipeline
        for warning in warnings:
            self.logger.warning(warning)
        
        return errors