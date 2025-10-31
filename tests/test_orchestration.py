import pytest
from unittest.mock import patch
from src.orchestrator import PipelineOrchestrator


class TestPipelineOrchestration:
    """Pruebas unitarias del orquestador de pipeline"""

    def test_pipeline_initialization(self):
        """Test que el orquestador se inicializa correctamente"""
        orchestrator = PipelineOrchestrator('config/pipeline_config.yaml')
        assert orchestrator.config is not None
        assert 'version' in orchestrator.config
        assert 'validation' in orchestrator.config

    def test_execution_flow_success(self):
        """Test flujo de ejecución exitoso"""
        with patch('src.data_validation.DataValidator') as mock_validator, \
             patch('src.data_processing.DataProcessor') as mock_processor, \
             patch('src.data_enrichment.DataEnricher') as mock_enricher, \
             patch('src.quality_checks.QualityChecker') as mock_quality:

            # Simular flujo correcto
            mock_validator.return_value.validate.return_value = {'success': True}
            mock_processor.return_value.process.return_value = {
                'success': True,
                'processed_data': [],
                'record_count': 100
            }
            mock_enricher.return_value.enrich.return_value = {
                'success': True,
                'enriched_data': [],
                'message': 'OK'
            }
            mock_quality.return_value.check_quality.return_value = {
                'passed': True,
                'quality_score': 95
            }

            orchestrator = PipelineOrchestrator('config/pipeline_config.yaml')
            result = orchestrator.execute_pipeline()

            assert result['success'] is True
            assert 'execution_id' in result
            assert result['records_processed']  > 0

    def test_execution_flow_failure(self):

        
        with  patch('src.data_validation.DataValidator', autospec=True) as mock_validator, \
              patch('src.data_processing.DataProcessor', autospec=True), \
              patch('src.data_enrichment.DataEnricher', autospec=True), \
              patch('src.quality_checks.QualityChecker', autospec=True):

        # Simular validación fallida
             mock_validator.return_value.validate.return_value = {
            'success': False,
            'errors': ['Schema validation failed']
        }

        orchestrator = PipelineOrchestrator('config/pipeline_config.yaml')
        result = orchestrator.execute_pipeline()

        assert result['success'] is False
        assert 'error' in result
