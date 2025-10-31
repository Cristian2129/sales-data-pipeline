"""
Orquestador Principal del Pipeline de Datos
Coordina la ejecución de todos los componentes del pipeline
"""

import yaml
import logging
import json
import os
from datetime import datetime

from src.data_validation import DataValidator
from src.data_processing import DataProcessor
from src.data_enrichment import DataEnricher
from src.quality_checks import QualityChecker


class PipelineOrchestrator:
    """Orquestador principal del pipeline de procesamiento de datos"""
    
    def __init__(self, config_path='config/pipeline_config.yaml'):
        """
        Inicializa el orquestador
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config = self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path):
        """Carga la configuración desde archivo YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            raise
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Asegurar que la carpeta de logs existe
        os.makedirs('logs', exist_ok=True)
        
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('log_file', 'logs/pipeline_execution.log')
        log_format = log_config.get('log_format', '%(asctime)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def execute_pipeline(self):
        """
        Ejecuta el pipeline completo con manejo de dependencias
        
        Returns:
            dict: Resultado de la ejecución con success, execution_id, etc.
        """
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"="*60)
        self.logger.info(f"Iniciando ejecucion del pipeline: {execution_id}")
        self.logger.info(f"Version del pipeline: {self.config.get('version', '1.0')}")
        self.logger.info(f"="*60)
        
        start_time = datetime.now()
        
        try:
            # PASO 1: Validacion de datos
            self.logger.info("\n[PASO 1/5] Ejecutando validacion de datos...")
            validator = DataValidator(self.config['validation'])
            validation_result = validator.validate()
            
            if not validation_result['success']:
                raise Exception(f"Validacion fallida: {validation_result.get('errors', 'Error desconocido')}")
            
            self.logger.info(f"Validacion exitosa: {validation_result.get('message', 'OK')}")
            
            # PASO 2: Procesamiento de datos
            self.logger.info("\n[PASO 2/5] Ejecutando procesamiento de datos...")
            processor = DataProcessor(self.config['processing'])
            processing_result = processor.process()
            
            if not processing_result['success']:
                raise Exception(f"Procesamiento fallido: {processing_result.get('error', 'Error desconocido')}")
            
            self.logger.info(f"Procesamiento exitoso: {processing_result['record_count']} registros procesados")
            
            # PASO 3: Enriquecimiento de datos
            self.logger.info("\n[PASO 3/5] Ejecutando enriquecimiento de datos...")
            enricher = DataEnricher(self.config['enrichment'])
            enrichment_result = enricher.enrich(processing_result['processed_data'])
            
            if not enrichment_result['success']:
                raise Exception(f"Enriquecimiento fallido: {enrichment_result.get('error', 'Error desconocido')}")
            
            self.logger.info(f"Enriquecimiento exitoso: {enrichment_result.get('message', 'OK')}")
            
            # PASO 4: Validacion de calidad
            self.logger.info("\n[PASO 4/5] Ejecutando validacion de calidad...")
            quality_checker = QualityChecker(self.config['quality'])
            quality_result = quality_checker.check_quality(enrichment_result['enriched_data'])
            
            if not quality_result['passed']:
                warning_msg = f"Validacion de calidad con advertencias: {quality_result.get('issues', [])}"
                self.logger.warning(warning_msg)
                
                # Decidir si detener o continuar basado en configuracion
                if self.config['quality'].get('stop_on_quality_failure', False):
                    raise Exception(f"Validacion de calidad fallida: {quality_result['issues']}")
            else:
                self.logger.info(f"Validacion de calidad exitosa - Score: {quality_result.get('quality_score', 'N/A')}")
            
            # PASO 5: Generacion de reportes
            self.logger.info("\n[PASO 5/5] Generando reportes...")
            self.generate_reports(
                enrichment_result['enriched_data'],
                execution_id,
                quality_result
            )
            
            # Calcular tiempo de ejecucion
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Pipeline completado exitosamente: {execution_id}")
            self.logger.info(f"Tiempo de ejecucion: {execution_time:.2f} segundos")
            self.logger.info(f"Registros procesados: {processing_result['record_count']}")
            self.logger.info(f"{'='*60}\n")
            
            return {
                'success': True,
                'execution_id': execution_id,
                'records_processed': processing_result['record_count'],
                'execution_time_seconds': execution_time,
                'quality_score': quality_result.get('quality_score', None)
            }
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            self.logger.error(f"\n{'='*60}")
            self.logger.error(f"ERROR en el pipeline: {str(e)}")
            self.logger.error(f"Tiempo antes del fallo: {execution_time:.2f} segundos")
            self.logger.error(f"{'='*60}\n")
            
            self.send_alert(f"Pipeline fallo: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_id': execution_id,
                'execution_time_seconds': execution_time
            }
    
    def generate_reports(self, data, execution_id, quality_result):
        """
        Genera reportes de ejecucion
        
        Args:
            data: DataFrame con datos procesados
            execution_id: ID de la ejecucion
            quality_result: Resultado de validacion de calidad
        """
        try:
            # Asegurar que la carpeta de outputs existe
            os.makedirs('data/outputs', exist_ok=True)
            
            # Guardar datos procesados
            output_file = f'data/processed/sales_enriched_{execution_id}.csv'
            os.makedirs('data/processed', exist_ok=True)
            data.to_csv(output_file, index=False)
            self.logger.info(f"Datos enriquecidos guardados en: {output_file}")
            
            # Generar reporte de ejecucion
            report = {
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'records_processed': len(data),
                'pipeline_version': self.config.get('version', '1.0'),
                'pipeline_name': self.config['pipeline']['name'],
                'quality_score': quality_result.get('quality_score', None),
                'quality_passed': quality_result.get('passed', False),
                'quality_issues': quality_result.get('issues', []),
                'output_file': output_file,
                'status': 'success'
            }
            
            # Guardar reporte JSON
            report_file = f'data/outputs/report_{execution_id}.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Reporte de ejecucion guardado en: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error generando reportes: {str(e)}")
            raise
    
    def send_alert(self, message):
        """
        Envia alertas (simulado para el ejercicio)
        
        Args:
            message: Mensaje de alerta
        """
        self.logger.warning(f"ALERTA: {message}")
        
        # En un escenario real, aqui se integraria con:
        # - Email (SMTP)
        # - Slack (webhook)
        # - Microsoft Teams
        # - PagerDuty
        # etc.


def main():
    """Funcion principal para ejecutar el pipeline"""
    try:
        orchestrator = PipelineOrchestrator('config/pipeline_config.yaml')
        result = orchestrator.execute_pipeline()
        
        if result['success']:
            print("\n[SUCCESS] Pipeline ejecutado exitosamente")
            print(f"Execution ID: {result['execution_id']}")
            print(f"Registros procesados: {result['records_processed']}")
            print(f"Tiempo: {result['execution_time_seconds']:.2f} segundos")
        else:
            print("\n[ERROR] Pipeline fallo")
            print(f"Error: {result['error']}")
            exit(1)
            
    except Exception as e:
        print(f"\n[FATAL ERROR] No se pudo inicializar el pipeline: {e}")
        exit(1)


if __name__ == "__main__":
    main()