"""
Evaluation package para Phase 4
Módulos de evaluación agrícola
"""

from .metrics_agro import (
    AgriculturalMetrics,
    evaluate_batch as evaluate_agricultural_metrics,
)
from .crop_classifier import CropClassifier
from .area_estimator import AreaEstimator
from .temporal_analyzer import TemporalAnalyzer
from .economic_analyzer import EconomicAnalyzer
from .use_cases import (
    WaterStressDetector,
    CropHealthMonitor,
    YieldPredictionHelper,
    evaluate_use_cases,
)
from .report_generator import ReportGenerator

__all__ = [
    "AgriculturalMetrics",
    "CropClassifier",
    "AreaEstimator",
    "TemporalAnalyzer",
    "EconomicAnalyzer",
    "WaterStressDetector",
    "CropHealthMonitor",
    "YieldPredictionHelper",
    "ReportGenerator",
    "evaluate_agricultural_metrics",
    "evaluate_use_cases",
]

__version__ = "1.0.0"
