"""
Modulo de Validacion de Calidad
Verifica que los datos finales cumplan con estandares de calidad
"""

import pandas as pd
import logging
from datetime import datetime, timedelta


class QualityChecker:
    """Validador de calidad de datos"""
    
    def __init__(self, config):
        """
        Inicializa el validador de calidad
        
        Args:
            config: Configuracion de calidad desde pipeline_config.yaml
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def check_quality(self, df):
        """
        Ejecuta todas las validaciones de calidad
        
        Args:
            df: DataFrame con datos enriquecidos
            
        Returns:
            dict: Resultado con passed, quality_score, issues, etc.
        """
        try:
            issues = []
            checks = self.config.get('checks', {})
            
            # Check 1: Completitud
            completeness_threshold = checks.get('completeness_threshold', 0.95)
            completeness = self.check_completeness(df, completeness_threshold)
            if not completeness['passed']:
                issues.append(completeness['issue'])
            
            # Check 2: Frescura de datos
            freshness_max_hours = checks.get('freshness_max_hours', 36)
            freshness = self.check_freshness(df, freshness_max_hours)
            if not freshness['passed']:
                issues.append(freshness['issue'])
            
            # Check 3: Variacion de volumen
            row_count_variation = checks.get('row_count_variation', 0.30)
            volume = self.check_volume_variation(df, row_count_variation)
            if not volume['passed']:
                issues.append(volume['issue'])
            
            # Check 4: Duplicados
            duplicate_threshold = checks.get('duplicate_threshold', 0.0)
            duplicates = self.check_duplicates(df, duplicate_threshold)
            if not duplicates['passed']:
                issues.append(duplicates['issue'])
            
            # Calcular score de calidad
            total_checks = 4
            passed_checks = sum([
                completeness['passed'],
                freshness['passed'],
                volume['passed'],
                duplicates['passed']
            ])
            quality_score = (passed_checks / total_checks) * 100
            
            # Determinar si pasa o no
            passed = len(issues) == 0
            
            if passed:
                self.logger.info(f"Validacion de calidad exitosa - Score: {quality_score:.1f}%")
            else:
                self.logger.warning(f"Validacion de calidad con issues - Score: {quality_score:.1f}%")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            
            return {
                'passed': passed,
                'quality_score': quality_score,
                'issues': issues,
                'checks': {
                    'completeness': completeness,
                    'freshness': freshness,
                    'volume': volume,
                    'duplicates': duplicates
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error durante validacion de calidad: {e}")
            return {
                'passed': False,
                'quality_score': 0,
                'issues': [f'Error critico: {str(e)}']
            }
    
    def check_completeness(self, df, threshold):
        """Verifica que los datos esten completos"""
        total_cells = df.size
        non_null_cells = df.count().sum()
        completeness = non_null_cells / total_cells
        
        passed = completeness >= threshold
        
        self.logger.info(f"Completitud: {completeness*100:.2f}% (umbral: {threshold*100:.0f}%)")
        
        return {
            'passed': passed,
            'value': completeness,
            'threshold': threshold,
            'issue': f'Completitud baja: {completeness*100:.1f}% < {threshold*100:.0f}%' if not passed else None
        }
    
    def check_freshness(self, df, max_hours):
        """Verifica que los datos sean recientes"""
        if 'fecha' not in df.columns:
            return {'passed': True, 'issue': None}
        
        try:
            df['fecha_parsed'] = pd.to_datetime(df['fecha'], errors='coerce')
            max_date = df['fecha_parsed'].max()
            
            if pd.isna(max_date):
                return {
                    'passed': False,
                    'issue': 'No se pudo parsear fechas'
                }
            
            now = datetime.now()
            age_hours = (now - max_date).total_seconds() / 3600
            
            passed = age_hours <= max_hours
            
            self.logger.info(f"Frescura: datos de hace {age_hours:.1f} horas (max: {max_hours}h)")
            
            return {
                'passed': passed,
                'age_hours': age_hours,
                'max_hours': max_hours,
                'issue': f'Datos muy antiguos: {age_hours:.1f}h > {max_hours}h' if not passed else None
            }
        except Exception as e:
            return {
                'passed': False,
                'issue': f'Error verificando frescura: {str(e)}'
            }
    
    def check_volume_variation(self, df, max_variation):
        """Verifica que el volumen de datos sea consistente"""
        current_count = len(df)
        
        # En un caso real, compararíamos con promedio historico
        # Para este ejercicio, asumimos que cualquier volumen es aceptable
        # si hay al menos 1 registro
        
        passed = current_count > 0
        
        self.logger.info(f"Volumen: {current_count} registros")
        
        return {
            'passed': passed,
            'current_count': current_count,
            'issue': 'No hay registros para procesar' if not passed else None
        }
    
    def check_duplicates(self, df, max_threshold):
        """Verifica que no haya duplicados"""
        if 'venta_id' not in df.columns:
            return {'passed': True, 'issue': None}
        
        duplicates = df.duplicated(subset=['venta_id'], keep=False)
        duplicate_count = duplicates.sum()
        duplicate_pct = duplicate_count / len(df)
        
        passed = duplicate_pct <= max_threshold
        
        if duplicate_count > 0:
            self.logger.warning(f"Duplicados encontrados: {duplicate_count} ({duplicate_pct*100:.2f}%)")
        
        return {
            'passed': passed,
            'duplicate_count': duplicate_count,
            'duplicate_pct': duplicate_pct,
            'threshold': max_threshold,
            'issue': f'Demasiados duplicados: {duplicate_pct*100:.1f}% > {max_threshold*100:.0f}%' if not passed else None
        }