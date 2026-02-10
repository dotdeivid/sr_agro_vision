"""
Script de verificación para Phase 4
Valida que todos los módulos estén correctamente implementados
"""
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import traceback

def test_imports():
    """Verifica que todos los módulos se puedan importar"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE IMPORTS")
    print("="*60 + "\n")
    
    modules = [
        ("agricultural_metrics", "AgriculturalMetrics"),
        ("crop_classification", "CropClassifier"),
        ("area_estimation", "AreaEstimator"),
        ("temporal_analysis", "TemporalAnalyzer"),
        ("economic_analysis", "EconomicAnalyzer"),
        ("use_cases", "WaterStressDetector, CropHealthMonitor"),
        ("generate_report", "ReportGenerator"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, class_names in modules:
        try:
            exec(f"from src.evaluation.{module_name} import {class_names}")
            print(f"✓ {module_name}.py")
            passed += 1
        except Exception as e:
            print(f"✗ {module_name}.py - ERROR:")
            print(f"  {str(e)}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nResultado: {passed}/{len(modules)} módulos OK")
    return failed == 0


def test_basic_functionality():
    """Prueba funcionalidad básica de cada módulo"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE FUNCIONALIDAD BÁSICA")
    print("="*60 + "\n")
    
    import numpy as np
    
    # Crear imagen de prueba
    test_img = np.random.rand(4, 64, 64).astype(np.float32)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: AgriculturalMetrics
    tests_total += 1
    try:
        from src.evaluation.agricultural_metrics import AgriculturalMetrics
        metrics = AgriculturalMetrics(test_img, test_img)
        ndvi = metrics.calculate_ndvi(test_img[0], test_img[3])
        assert ndvi.shape == (64, 64), "NDVI shape incorrecta"
        print("✓ AgriculturalMetrics - NDVI calculation")
        tests_passed += 1
    except Exception as e:
        print(f"✗ AgriculturalMetrics - {str(e)}")
    
    # Test 2: AreaEstimator
    tests_total += 1
    try:
        from src.evaluation.area_estimation import AreaEstimator
        estimator = AreaEstimator(gsd_meters=10.0)
        mask = estimator.create_vegetation_mask(test_img, ndvi_threshold=0.3)
        assert mask.shape == (64, 64), "Mask shape incorrecta"
        area = estimator.calculate_area(mask)
        assert 'area_ha' in area, "area_ha no está en el resultado"
        print("✓ AreaEstimator - Vegetation mask & area calculation")
        tests_passed += 1
    except Exception as e:
        print(f"✗ AreaEstimator - {str(e)}")
    
    # Test 3: WaterStressDetector
    tests_total += 1
    try:
        from src.evaluation.use_cases import WaterStressDetector
        detector = WaterStressDetector()
        stress_map, stats = detector.detect_stress(test_img)
        assert stress_map.shape == (64, 64), "Stress map shape incorrecta"
        assert 'healthy_percent' in stats, "Stats incompletas"
        print("✓ WaterStressDetector - Stress detection")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WaterStressDetector - {str(e)}")
    
    # Test 4: EconomicAnalyzer
    tests_total += 1
    try:
        from src.evaluation.economic_analysis import EconomicAnalyzer
        analyzer = EconomicAnalyzer()
        comparison = analyzer.compare_alternatives(n_images=10, area_km2=100)
        assert 'sentinel2_sr' in comparison, "Comparison incompleta"
        assert 'savings_vs_planet' in comparison, "Savings no calculados"
        print("✓ EconomicAnalyzer - Cost comparison")
        tests_passed += 1
    except Exception as e:
        print(f"✗ EconomicAnalyzer - {str(e)}")
    
    # Test 5: TemporalAnalyzer
    tests_total += 1
    try:
        from src.evaluation.temporal_analysis import TemporalAnalyzer
        from datetime import datetime
        analyzer = TemporalAnalyzer()
        analyzer.add_observation(datetime.now(), test_img, test_img)
        df = analyzer.calculate_ndvi_timeseries()
        assert len(df) == 1, "DataFrame debería tener 1 observación"
        print("✓ TemporalAnalyzer - Time series")
        tests_passed += 1
    except Exception as e:
        print(f"✗ TemporalAnalyzer - {str(e)}")
    
    # Test 6: CropClassifier
    tests_total += 1
    try:
        from src.evaluation.crop_classification import CropClassifier
        classifier = CropClassifier()
        features = classifier.extract_features(test_img)
        assert features.shape[0] == 64*64, "Features shape incorrecta"
        assert features.shape[1] == 9, "Debería haber 9 features"
        print("✓ CropClassifier - Feature extraction")
        tests_passed += 1
    except Exception as e:
        print(f"✗ CropClassifier - {str(e)}")
    
    print(f"\nResultado: {tests_passed}/{tests_total} tests funcionales OK")
    return tests_passed == tests_total


def check_config():
    """Verifica que el archivo de configuración exista y sea válido"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE CONFIGURACIÓN")
    print("="*60 + "\n")
    
    import yaml
    from pathlib import Path
    
    config_file = Path("config/phase4/evaluation_config.yaml")
    
    if not config_file.exists():
        print(f"✗ Archivo de configuración no encontrado: {config_file}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verificar secciones requeridas
        required_sections = [
            'paths', 'agricultural_metrics', 'crop_classification',
            'area_estimation', 'temporal_analysis', 'economic_analysis',
            'use_cases', 'report', 'evaluation'
        ]
        
        for section in required_sections:
            if section not in config:
                print(f"✗ Sección faltante en config: {section}")
                return False
        
        print(f"✓ Archivo de configuración OK")
        print(f"  Secciones: {len(config)} / {len(required_sections)}")
        return True
        
    except Exception as e:
        print(f"✗ Error leyendo configuración: {str(e)}")
        return False


def main():
    """Ejecuta todas las verificaciones"""
    print("\n🔍 INICIANDO VERIFICACIÓN DE PHASE 4")
    print("="*60)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test functionality
    functionality_ok = test_basic_functionality()
    
    # Test config
    config_ok = check_config()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    print(f"Imports:        {'✓ OK' if imports_ok else '✗ FAILED'}")
    print(f"Functionality:  {'✓ OK' if functionality_ok else '✗ FAILED'}")
    print(f"Configuration:  {'✓ OK' if config_ok else '✗ FAILED'}")
    
    if imports_ok and functionality_ok and config_ok:
        print("\n🎉 VERIFICACIÓN COMPLETA - TODO CORRECTO!")
        return 0
    else:
        print("\n⚠️ VERIFICACIÓN FALLÓ - Revisar errores arriba")
        return 1


if __name__ == "__main__":
    sys.exit(main())
