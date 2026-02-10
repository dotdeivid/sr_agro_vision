"""
Evaluation package para Phase 4
Módulos de evaluación agrícola
"""

from .agricultural_metrics import AgriculturalMetrics, evaluate_batch as evaluate_agricultural_metrics
from .crop_classification import CropClassifier
from .area_estimation import AreaEstimator
from .temporal_analysis import TemporalAnalyzer
from .economic_analysis import EconomicAnalyzer
from .use_cases import WaterStressDetector, CropHealthMonitor, YieldPredictionHelper, evaluate_use_cases
from .generate_report import ReportGenerator

__all__ = [
    'AgriculturalMetrics',
    'CropClassifier',
    'AreaEstimator',
    'TemporalAnalyzer',
    'EconomicAnalyzer',
    'WaterStressDetector',
    'CropHealthMonitor',
    'YieldPredictionHelper',
    'ReportGenerator',
    'evaluate_agricultural_metrics',
    'evaluate_use_cases',
]

__version__ = '1.0.0'
