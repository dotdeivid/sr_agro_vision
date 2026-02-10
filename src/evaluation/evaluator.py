"""
Script principal para ejecutar evaluación completa Fase 4
Orquesta todos los módulos en secuencia
"""
import argparse
import yaml
from pathlib import Path
import numpy as np
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation.agricultural_metrics import evaluate_batch as eval_agri
from src.evaluation.area_estimation import AreaEstimator
from src.evaluation.temporal_analysis import TemporalAnalyzer
from src.evaluation.economic_analysis import EconomicAnalyzer
from src.evaluation.use_cases import evaluate_use_cases
from src.evaluation.generate_report import ReportGenerator


def load_config(config_path):
    """Load evaluation config"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_phase4_evaluation(config_path):
    """
    Execute complete Phase 4 evaluation
    """
    print("\n" + "="*70)
    print("🌾 FASE 4: EVALUACIÓN DOMINIO AGRÍCOLA".center(70))
    print("="*70 + "\n")
    
    # Load config
    config = load_config(config_path)
    paths = config['paths']
    output_dir = Path(paths['output'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Agricultural Metrics
    print("\n📊 PASO 1: MÉTRICAS AGRÍCOLAS")
    print("-" * 70)
    metrics_dir = output_dir / config['agricultural_metrics']['output_subdir']
    eval_agri(
        sr_dir=paths['sr_results'],
        hr_dir=paths['hr_ground_truth'],
        output_dir=metrics_dir
    )
    
    # 2. Area Estimation
    print("\n📏 PASO 2: ESTIMACIÓN DE ÁREA")
    print("-" * 70)
    area_dir = output_dir / config['area_estimation']['output_subdir']
    estimator = AreaEstimator(gsd_meters=config['area_estimation']['gsd_meters'])
    estimator.evaluate_batch(
        sr_dir=paths['sr_results'],
        hr_dir=paths['hr_ground_truth'],
        output_dir=area_dir,
        ndvi_threshold=config['area_estimation']['ndvi_vegetation_threshold']
    )
    
    # 3. Economic Analysis
    print("\n💰 PASO 3: ANÁLISIS ECONÓMICO")
    print("-" * 70)
    econ_dir = output_dir / config['economic_analysis']['output_subdir']
    analyzer = EconomicAnalyzer()
    analyzer.generate_report(
        n_images=12,
        area_km2=config['economic_analysis']['roi']['area_km2'],
        output_dir=econ_dir
    )
    
    # 4. Use Cases
    print("\n🎯 PASO 4: CASOS DE USO")
    print("-" * 70)
    usecase_dir = output_dir / config['use_cases']['output_subdir']
    evaluate_use_cases(
        sr_dir=paths['sr_results'],
        hr_dir=paths['hr_ground_truth'],
        output_dir=usecase_dir
    )
    
    # 5. Generate Final Report
    print("\n📄 PASO 5: GENERAR INFORME FINAL")
    print("-" * 70)
    report_dir = output_dir / config['report']['output_subdir']
    generator = ReportGenerator(output_dir)
    generator.generate_full_report(report_dir)
    
    print("\n" + "="*70)
    print("✅ EVALUACIÓN FASE 4 COMPLETADA")
    print("="*70)
    print(f"📁 Resultados: {output_dir}")
    print(f"📄 Informe: {report_dir}/PHASE4_FINAL_REPORT.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Phase 4 Evaluation')
    parser.add_argument('--config', type=str,
                       default='config/phase4/evaluation_config.yaml',
                       help='Path to evaluation config')
    
    args = parser.parse_args()
    
    try:
        run_phase4_evaluation(args.config)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
