
#!/usr/bin/env python3
"""
Pipeline automatizado Fase 2: Desde descarga hasta evaluación
Super Resolución Satelital - Imágenes Multiespectrales
"""
import subprocess
import sys
from pathlib import Path
import argparse

# Colores para terminal
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_header(text):
    """Imprime header con formato"""
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}{Colors.NC}\n")

def print_step(step, total, text):
    """Imprime paso del pipeline"""
    print(f"\n{Colors.YELLOW}[{step}/{total}] {text}...{Colors.NC}")

def print_success(text):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def run_command(cmd, description, ignore_errors=False):
    """
    Ejecuta comando y maneja errores
    
    Args:
        cmd: Lista con comando y argumentos
        description: Descripción del paso
        ignore_errors: Si True, continúa aunque falle
    
    Returns:
        bool: True si exitoso, False si falló
    """
    print(f"\n{Colors.BLUE}▶️  {description}{Colors.NC}")
    print(f"Comando: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        if ignore_errors:
            print(f"{Colors.YELLOW}⚠️  Advertencia en: {description} (continuando...){Colors.NC}")
            return False
        else:
            print_error(f"Error en: {description}")
            print(f"\n{Colors.RED}Pipeline detenido. Revisa el error arriba.{Colors.NC}\n")
            sys.exit(1)
    
    print_success(f"Completado: {description}")
    return True

def check_credentials():
    """Verifica que existan credenciales de Copernicus"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    user = os.getenv('COPERNICUS_USER')
    pwd = os.getenv('COPERNICUS_PASS')
    
    if not user or not pwd:
        print_error("Credenciales de Copernicus no encontradas")
        print(f"\n{Colors.YELLOW}Solución:{Colors.NC}")
        print("1. Crea archivo .env en la raíz del proyecto:")
        print("   COPERNICUS_USER=tu_usuario")
        print("   COPERNICUS_PASS=tu_contraseña")
        print("\n2. Regístrate gratis en:")
        print("   https://scihub.copernicus.eu/dhus/#/self-registration\n")
        sys.exit(1)
    
    print_success(f"Credenciales encontradas: {user}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Pipeline Fase 2: Super Resolución Satelital',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Pipeline completo (todo automático)
  python scripts/run_phase2_pipeline.py --region corrientes_argentina --scale 4

  # Saltar descarga (usar datos existentes)
  python scripts/run_phase2_pipeline.py --skip-download --scale 4

  # Solo procesamiento (sin entrenamiento)
  python scripts/run_phase2_pipeline.py --skip-download --skip-training --scale 4

Regiones disponibles:
  - corrientes_argentina
  - rio_grande_do_sul
  - valencia_spain
        """
    )
    
    parser.add_argument('--region', type=str, default='corrientes_argentina',
                       help='Región a descargar (default: corrientes_argentina)')
    parser.add_argument('--max-images', type=int, default=10,
                       help='Máximo de imágenes a descargar (default: 10)')
    parser.add_argument('--scale', type=int, default=4, choices=[2, 4, 8],
                       help='Factor de escalado (default: 4)')
    parser.add_argument('--start-date', type=str, default='20230901',
                       help='Fecha inicio descarga YYYYMMDD (default: 20230901)')
    parser.add_argument('--end-date', type=str, default='20240301',
                       help='Fecha fin descarga YYYYMMDD (default: 20240301)')
    
    # Opciones de skip
    parser.add_argument('--skip-download', action='store_true',
                       help='Saltar descarga (usar datos existentes)')
    parser.add_argument('--skip-preprocess', action='store_true',
                       help='Saltar preprocesamiento')
    parser.add_argument('--skip-create-pairs', action='store_true',
                       help='Saltar creación de pares LR-HR')
    parser.add_argument('--skip-training', action='store_true',
                       help='Saltar entrenamiento')
    parser.add_argument('--skip-evaluation', action='store_true',
                       help='Saltar evaluación final')
    
    # Opciones avanzadas
    parser.add_argument('--cloud-threshold', type=float, default=0.2,
                       help='Umbral de nubosidad (0-1, default: 0.2)')
    parser.add_argument('--patch-size', type=int, default=256,
                       help='Tamaño de patches HR (default: 256)')
    parser.add_argument('--stride', type=int, default=128,
                       help='Stride entre patches (default: 128)')
    parser.add_argument('--train-split', type=float, default=0.8,
                       help='Proporción train/val (default: 0.8)')
    
    args = parser.parse_args()
    
    # Header
    print_header("🛰️  PIPELINE FASE 2: SUPER RESOLUCIÓN SATELITAL")
    print(f"Región: {args.region}")
    print(f"Factor de escalado: x{args.scale}")
    print(f"Imágenes máximas: {args.max_images}")
    print(f"Rango fechas: {args.start_date} - {args.end_date}\n")
    
    # Directorios
    PROJECT_ROOT = Path(__file__).parent.parent
    raw_dir = PROJECT_ROOT / "data/satellite/raw"
    preprocessed_dir = PROJECT_ROOT / "data/satellite/preprocessed"
    dataset_dir = PROJECT_ROOT / "data/satellite/dataset"
    weights_dir = PROJECT_ROOT / "weights/satellite"
    results_dir = PROJECT_ROOT / "results"
    
    # Cambiar al directorio del proyecto
    import os
    os.chdir(PROJECT_ROOT)
    
    total_steps = 6
    current_step = 0
    
    # =================================================================
    # PASO 0: Verificar credenciales (si se va a descargar)
    # =================================================================
    if not args.skip_download:
        current_step += 1
        print_step(current_step, total_steps, "Verificando credenciales de Copernicus")
        check_credentials()
    
    # =================================================================
    # PASO 1: Descargar imágenes Sentinel-2
    # =================================================================
    if not args.skip_download:
        current_step += 1
        print_step(current_step, total_steps, "Descarga de imágenes Sentinel-2")
        
        run_command([
            sys.executable,
            "data/satellite/download_sentinel.py",
            "--region", args.region,
            "--output", str(raw_dir),
            "--start-date", args.start_date,
            "--end-date", args.end_date,
            "--max-images", str(args.max_images)
        ], f"Descargando imágenes de {args.region}")
        
        # Verificar que se descargaron imágenes
        if not raw_dir.exists() or len(list(raw_dir.glob("*.SAFE"))) == 0:
            print_error("No se descargaron imágenes")
            print(f"\n{Colors.YELLOW}Posibles causas:{Colors.NC}")
            print("  - No hay imágenes en el rango de fechas especificado")
            print("  - Todas las imágenes tienen mucha nubosidad")
            print("  - Problemas de conexión\n")
            print(f"{Colors.YELLOW}Soluciones:{Colors.NC}")
            print("  - Ampliar rango de fechas: --start-date 20230101 --end-date 20241231")
            print("  - Probar otra región: --region rio_grande_do_sul\n")
            sys.exit(1)
    else:
        print_success("Descarga omitida (--skip-download)")
    
    # =================================================================
    # PASO 2: Preprocesar imágenes
    # =================================================================
    if not args.skip_preprocess:
        current_step += 1
        print_step(current_step, total_steps, "Preprocesamiento de imágenes")
        
        run_command([
            sys.executable,
            "data/satellite/preprocess_sentinel.py",
            "--input", str(raw_dir),
            "--output", str(preprocessed_dir),
            "--cloud-threshold", str(args.cloud_threshold)
        ], "Preprocesando imágenes (RGB+NIR, filtrado nubes)")
    else:
        print_success("Preprocesamiento omitido (--skip-preprocess)")
    
    # =================================================================
    # PASO 3: Crear pares LR-HR
    # =================================================================
    if not args.skip_create_pairs:
        current_step += 1
        print_step(current_step, total_steps, "Creación de dataset (pares LR-HR)")
        
        run_command([
            sys.executable,
            "data/satellite/create_satellite_pairs.py",
            "--input", str(preprocessed_dir),
            "--output", str(dataset_dir),
            "--scale", str(args.scale),
            "--patch-size", str(args.patch_size),
            "--stride", str(args.stride),
            "--train-split", str(args.train_split)
        ], f"Generando patches (scale x{args.scale}, size {args.patch_size})")
    else:
        print_success("Creación de pares omitida (--skip-create-pairs)")
    
    # =================================================================
    # PASO 4: Entrenar modelo
    # =================================================================
    if not args.skip_training:
        current_step += 1
        print_step(current_step, total_steps, f"Entrenamiento del modelo x{args.scale}")
        
        config_file = f"config/satellite_x{args.scale}.yaml"
        
        if not Path(config_file).exists():
            print_error(f"Archivo de configuración no encontrado: {config_file}")
            sys.exit(1)
        
        print(f"\n{Colors.YELLOW}Esto puede tomar varias horas...{Colors.NC}")
        print(f"{Colors.YELLOW}Monitorea el progreso en otra terminal con:{Colors.NC}")
        print(f"  tensorboard --logdir runs/satellite/\n")
        
        run_command([
            sys.executable,
            "training/train_satellite.py",
            "--config", config_file
        ], f"Entrenando modelo satelital x{args.scale}")
    else:
        print_success("Entrenamiento omitido (--skip-training)")
    
    # =================================================================
    # PASO 5: Evaluar modelo
    # =================================================================
    if not args.skip_evaluation:
        current_step += 1
        print_step(current_step, total_steps, "Evaluación y visualización de resultados")
        
        model_path = weights_dir / f"best_psnr_x{args.scale}.pth"
        
        if not model_path.exists():
            print(f"{Colors.YELLOW}⚠️  Modelo no encontrado: {model_path}{Colors.NC}")
            print(f"{Colors.YELLOW}Saltando evaluación...{Colors.NC}")
        else:
            run_command([
                sys.executable,
                "inference/evaluate_agriculture.py",
                "--test-dir", str(dataset_dir),
                "--model", str(model_path),
                "--scale", str(args.scale),
                "--channels", "4",
                "--visualize",
                "--output-dir", str(results_dir / "visualizations")
            ], "Evaluando modelo con métricas agrícolas", ignore_errors=True)
    else:
        print_success("Evaluación omitida (--skip-evaluation)")
    
    # =================================================================
    # RESUMEN FINAL
    # =================================================================
    print_header("✅ PIPELINE COMPLETADO")
    
    print(f"{Colors.GREEN}Archivos generados:{Colors.NC}\n")
    
    if not args.skip_download and raw_dir.exists():
        num_safe = len(list(raw_dir.glob("*.SAFE")))
        print(f"📥 Imágenes descargadas: {num_safe}")
        print(f"   Ubicación: {raw_dir}\n")
    
    if not args.skip_preprocess and preprocessed_dir.exists():
        num_preprocessed = len(list(preprocessed_dir.glob("*.tif")))
        print(f"🔧 Imágenes preprocesadas: {num_preprocessed}")
        print(f"   Ubicación: {preprocessed_dir}\n")
    
    if not args.skip_create_pairs and dataset_dir.exists():
        train_lr = dataset_dir / "train/LR"
        if train_lr.exists():
            num_train = len(list(train_lr.glob("*.npy")))
            print(f"📦 Dataset creado: {num_train} patches de entrenamiento")
            print(f"   Train: {dataset_dir / 'train'}")
            print(f"   Val: {dataset_dir / 'val'}\n")
    
    if not args.skip_training and weights_dir.exists():
        model_files = list(weights_dir.glob(f"*x{args.scale}.pth"))
        if model_files:
            print(f"🧠 Modelos entrenados:")
            for model_file in model_files:
                print(f"   {model_file}")
            print()
    
    if not args.skip_evaluation and (results_dir / "visualizations").exists():
        num_viz = len(list((results_dir / "visualizations").glob("*.png")))
        print(f"📊 Visualizaciones: {num_viz} imágenes")
        print(f"   Ubicación: {results_dir / 'visualizations'}\n")
    
    print(f"{Colors.YELLOW}Próximos pasos:{Colors.NC}\n")
    print("1. Ver resultados:")
    print(f"   open {results_dir / 'visualizations'}")
    print("\n2. Aplicar modelo a nuevas imágenes:")
    print(f"   python inference/upscale_satellite.py --input imagen.tif --model weights/satellite/best_psnr_x{args.scale}.pth --output resultado.tif")
    print("\n3. Ver logs de entrenamiento:")
    print("   tensorboard --logdir runs/satellite/")
    print()
    
    print_header("🌾 ¡Listo para tu tesis!")

if __name__ == "__main__":
    main()