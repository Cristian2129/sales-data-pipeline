"""
Modulo de Procesamiento de Datos
Limpia, transforma y calcula campos adicionales
"""

import pandas as pd
import logging


class DataProcessor:
    """Procesador de datos"""
    
    def __init__(self, config):
        """
        Inicializa el procesador
        
        Args:
            config: Configuracion de procesamiento desde pipeline_config.yaml
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def process(self):
        """
        Ejecuta el procesamiento completo de datos
        
        Returns:
            dict: Resultado con processed_data, record_count, etc.
        """
        try:
            # Leer datos
            self.logger.info("Cargando datos de ventas...")
            df = pd.read_csv('data/raw/sales_data.csv')
            initial_count = len(df)
            self.logger.info(f"Registros iniciales: {initial_count}")
            
            # Ejecutar pasos de procesamiento
            steps = self.config.get('steps', [])
            
            for step in steps:
                if step == 'remove_duplicates':
                    df = self.remove_duplicates(df)
                elif step == 'handle_missing_values':
                    df = self.handle_missing_values(df)
                elif step == 'calculate_totals':
                    df = self.calculate_totals(df)
                elif step == 'identify_discounts':
                    # Este paso necesita el catalogo, se hara en enriquecimiento
                    pass
                else:
                    self.logger.warning(f"Paso desconocido: {step}")
            
            final_count = len(df)
            removed = initial_count - final_count
            
            self.logger.info(f"Registros finales: {final_count}")
            if removed > 0:
                self.logger.info(f"Registros eliminados: {removed}")
            
            return {
                'success': True,
                'processed_data': df,
                'record_count': final_count,
                'records_removed': removed
            }
            
        except Exception as e:
            self.logger.error(f"Error durante procesamiento: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_duplicates(self, df):
        """Elimina registros duplicados"""
        duplicate_cols = self.config.get('duplicate_columns', ['venta_id'])
        
        initial_count = len(df)
        df_clean = df.drop_duplicates(subset=duplicate_cols, keep='first')
        removed = initial_count - len(df_clean)
        
        if removed > 0:
            self.logger.info(f"Eliminados {removed} duplicados basados en: {duplicate_cols}")
        
        return df_clean
    
    def handle_missing_values(self, df):
        """Maneja valores nulos segun estrategia configurada"""
        strategy = self.config.get('missing_value_strategy', {})
        
        for column, action in strategy.items():
            if column in df.columns:
                null_count = df[column].isna().sum()
                
                if null_count > 0:
                    if action == 'drop_row':
                        initial_count = len(df)
                        df = df.dropna(subset=[column])
                        removed = initial_count - len(df)
                        self.logger.info(f"Eliminadas {removed} filas por {column} nulo")
                    
                    elif action == 'N/A' or isinstance(action, str):
                        df[column] = df[column].fillna(action)
                        self.logger.info(f"Completados {null_count} valores nulos en {column} con '{action}'")
                    
                    elif isinstance(action, (int, float)):
                        df[column] = df[column].fillna(action)
                        self.logger.info(f"Completados {null_count} valores nulos en {column} con {action}")
        
        return df
    
    def calculate_totals(self, df):
        """Calcula campos totales"""
        calculations = self.config.get('calculations', {})
        
        # Calcular total_venta
        if 'total_venta' in calculations:
            if 'cantidad' in df.columns and 'precio_unitario' in df.columns:
                df['total_venta'] = df['cantidad'] * df['precio_unitario']
                self.logger.info("Campo 'total_venta' calculado")
        
        return df