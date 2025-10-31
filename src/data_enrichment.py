"""
Modulo de Enriquecimiento de Datos
Combina datos de ventas con catalogo de productos
"""

import pandas as pd
import logging


class DataEnricher:
    """Enriquecedor de datos"""
    
    def __init__(self, config):
        """
        Inicializa el enriquecedor
        
        Args:
            config: Configuracion de enriquecimiento desde pipeline_config.yaml
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def enrich(self, sales_df):
        """
        Enriquece datos de ventas con informacion del catalogo
        
        Args:
            sales_df: DataFrame con datos de ventas procesados
            
        Returns:
            dict: Resultado con enriched_data, success, etc.
        """
        try:
            # Leer catalogo
            catalog_path = self.config['catalog_path']
            self.logger.info(f"Cargando catalogo desde: {catalog_path}")
            catalog_df = pd.read_csv(catalog_path)
            
            # Obtener configuracion de join
            join_key = self.config.get('join_key', 'producto_id')
            columns_to_add = self.config.get('columns_to_add', [])
            
            # Hacer merge
            self.logger.info(f"Haciendo merge por: {join_key}")
            
            # Antes del merge, guardar productos originales
            original_products = set(sales_df[join_key].unique())
            
            # Hacer left join para mantener todas las ventas
            enriched_df = sales_df.merge(
                catalog_df[columns_to_add + [join_key]],
                on=join_key,
                how='left'
            )
            
            # Identificar productos no encontrados
            missing_mask = enriched_df[columns_to_add[0]].isna()
            missing_products = enriched_df[missing_mask][join_key].unique()
            
            if len(missing_products) > 0:
                missing_pct = (len(missing_products) / len(original_products)) * 100
                self.logger.warning(
                    f"Productos no encontrados en catalogo: {missing_products.tolist()} "
                    f"({missing_pct:.1f}% del total)"
                )
                
                # Decidir si continuar o fallar
                handle_missing = self.config.get('handle_missing_products', 'warn')
                threshold = self.config.get('missing_products_threshold', 0.05)
                
                if handle_missing == 'error' or missing_pct/100 > threshold:
                    return {
                        'success': False,
                        'error': f'Demasiados productos no encontrados: {missing_pct:.1f}%',
                        'missing_products': missing_products.tolist()
                    }
            
            # Calcular porcentaje de descuento ahora que tenemos precio_base
            if 'precio_base' in enriched_df.columns and 'precio_unitario' in enriched_df.columns:
                enriched_df['porcentaje_descuento'] = (
                    (enriched_df['precio_base'] - enriched_df['precio_unitario']) / 
                    enriched_df['precio_base'] * 100
                )
                enriched_df['porcentaje_descuento'] = enriched_df['porcentaje_descuento'].fillna(0)
                enriched_df['tiene_descuento'] = enriched_df['porcentaje_descuento'] > 0
                
                self.logger.info("Calculado porcentaje de descuento")
            
            self.logger.info(f"Enriquecimiento completado: {len(enriched_df)} registros")
            self.logger.info(f"Columnas agregadas: {columns_to_add}")
            
            return {
                'success': True,
                'enriched_data': enriched_df,
                'message': f'Enriquecidos {len(enriched_df)} registros',
                'missing_products': missing_products.tolist() if len(missing_products) > 0 else []
            }
            
        except Exception as e:
            self.logger.error(f"Error durante enriquecimiento: {e}")
            return {
                'success': False,
                'error': str(e)
            }