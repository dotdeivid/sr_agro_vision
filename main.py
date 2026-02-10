#!/usr/bin/env python3
"""
SR Agro Vision - Main Entry Point
Super-Resolución para Imágenes Satelitales en Agricultura de Precisión

Uso:
    python main.py                    # Menú interactivo
    python main.py download           # Descarga datos Sentinel-2
    python main.py train              # Entrenar modelo
    python main.py predict            # Aplicar SR a imagen
    python main.py evaluate           # Evaluación agrícola completa
"""

import argparse
import sys
from pathlib import Path

# Colores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NC = '\033[0m'  # Reset

def print_banner():
    """Imprime banner del proyecto"""
    banner = f"""
{Colors.CYAN}{'='*70}
{Colors.BOLD}    🌾 SR AGRO VISION{Colors.NC}
{Colors.CYAN}    Super-Resolución para Agricultura de Precisión
{'='*70}{Colors.NC}
"""
    print(banner)

def print_menu():
    """Imprime menú principal interactivo"""
    menu = f"""
{Colors.BOLD}{Colors.GREEN}OPCIONES DISPONIBLES:{Colors.NC}

{Colors.BOLD}📥 DATOS{Colors.NC}
  {Colors.CYAN}1.{Colors.NC} download    - Descargar imágenes Sentinel-2
  {Colors.CYAN}2.{Colors.NC} preprocess  - Preprocesar imágenes descargadas
  {Colors.CYAN}3.{Colors.NC} dataset     - Crear dataset de entrenamiento (pares LR-HR)
  {Colors.CYAN}4.{Colors.NC} pipeline    - Pipeline completo (download → preprocess → dataset)

{Colors.BOLD}🧠 ENTRENAMIENTO{Colors.NC}
  {Colors.CYAN}5.{Colors.NC} train       - Entrenar modelo (ESPCN, SwinIR, GAN)
  {Colors.CYAN}6.{Colors.NC} resume      - Reanudar entrenamiento desde checkpoint
  {Colors.CYAN}7.{Colors.NC} ablation    - Ablation study (comparar configuraciones)

{Colors.BOLD}🔮 INFERENCIA{Colors.NC}
  {Colors.CYAN}8.{Colors.NC} predict     - Aplicar SR a imagen individual
  {Colors.CYAN}9.{Colors.NC} batch       - Procesar múltiples imágenes (batch)
  {Colors.CYAN}10.{Colors.NC} ensemble    - Predicción con ensemble de modelos

{Colors.BOLD}📊 EVALUACIÓN{Colors.NC}
  {Colors.CYAN}11.{Colors.NC} evaluate    - Evaluación agrícola completa (métricas + reportes)
  {Colors.CYAN}12.{Colors.NC} metrics     - Solo métricas agrícolas (NDVI, EVI, SAVI)
  {Colors.CYAN}13.{Colors.NC} visualize   - Generar visualizaciones comparativas

{Colors.BOLD}🛠️ UTILIDADES{Colors.NC}
  {Colors.CYAN}14.{Colors.NC} info        - Información del proyecto y configuración
  {Colors.CYAN}15.{Colors.NC} clean       - Limpiar outputs antiguos
  {Colors.CYAN}16.{Colors.NC} test        - Ejecutar tests

{Colors.BOLD}❓ AYUDA{Colors.NC}
  {Colors.CYAN}17.{Colors.NC} help        - Ayuda detallada por comando
  {Colors.CYAN}0.{Colors.NC} exit        - Salir

{Colors.YELLOW}Ingrese el número de opción o comando:{Colors.NC} """
    
    return input(menu).strip()

def interactive_menu():
    """Modo interactivo con menú"""
    print_banner()
    
    while True:
        choice = print_menu()
        
        # Mapeo de números a comandos
        command_map = {
            '1': 'download',
            '2': 'preprocess',
            '3': 'dataset',
            '4': 'pipeline',
            '5': 'train',
            '6': 'resume',
            '7': 'ablation',
            '8': 'predict',
            '9': 'batch',
            '10': 'ensemble',
            '11': 'evaluate',
            '12': 'metrics',
            '13': 'visualize',
            '14': 'info',
            '15': 'clean',
            '16': 'test',
            '17': 'help',
            '0': 'exit'
        }
        
        # Convertir número a comando
        command = command_map.get(choice, choice)
        
        if command == 'exit':
            print(f"\n{Colors.GREEN}¡Hasta luego! 👋{Colors.NC}\n")
            break
        elif command in command_map.values():
            execute_command(command)
        else:
            print(f"{Colors.RED}❌ Opción inválida. Intente nuevamente.{Colors.NC}")
        
        input(f"\n{Colors.YELLOW}Presione Enter para continuar...{Colors.NC}")
        print("\n" * 2)

def execute_command(command, args=None):
    """Ejecuta comando seleccionado"""
    
    # Importaciones dinámicas para evitar cargar todo al inicio
    if command == 'download':
        from scripts import download_sentinel
        download_sentinel.main(args)
    
    elif command == 'preprocess':
        from scripts import preprocess_sentinel
        preprocess_sentinel.main(args)
    
    elif command == 'dataset':
        from scripts import create_dataset
        create_dataset.main(args)
    
    elif command == 'pipeline':
        from scripts import pipeline
        pipeline.main(args)
    
    elif command == 'train':
        from src.training import trainer
        trainer.main(args)
    
    elif command == 'resume':
        from src.training import trainer
        if args:
            args.resume = True
        trainer.main(args)
    
    elif command == 'ablation':
        from src.experiments import ablation
        ablation.main(args)
    
    elif command == 'predict':
        from src.inference import predictor
        predictor.main(args)
    
    elif command == 'batch':
        from src.inference import predictor
        if args:
            args.batch = True
        predictor.main(args)
    
    elif command == 'ensemble':
        from src.inference import ensemble
        ensemble.main(args)
    
    elif command == 'evaluate':
        from src.evaluation import evaluator
        evaluator.main(args)
    
    elif command == 'metrics':
        from src.evaluation import metrics_agro
        metrics_agro.main(args)
    
    elif command == 'visualize':
        from src.evaluation import evaluator
        if args:
            args.visualize_only = True
        evaluator.main(args)
    
    elif command == 'info':
        show_info()
    
    elif command == 'clean':
        clean_outputs()
    
    elif command == 'test':
        run_tests()
    
    elif command == 'help':
        show_help(args)

def show_info():
    """Muestra información del proyecto"""
    from src.utils import device
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}ℹ️  INFORMACIÓN DEL PROYECTO{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
    
    # Versión
    print(f"{Colors.BOLD}Versión:{Colors.NC} 2.0")
    print(f"{Colors.BOLD}Proyecto:{Colors.NC} SR Agro Vision")
    print(f"{Colors.BOLD}Descripción:{Colors.NC} Super-Resolución Satelital para Agricultura\n")
    
    # Hardware
    hw_device = device.get_device()
    print(f"{Colors.BOLD}Hardware Detectado:{Colors.NC}")
    print(f"  • Dispositivo: {hw_device}")
    
    if hw_device.type == 'cuda':
        import torch
        print(f"  • GPU: {torch.cuda.get_device_name(0)}")
        print(f"  • VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Rutas
    print(f"\n{Colors.BOLD}Rutas del Proyecto:{Colors.NC}")
    print(f"  • Datos: data/")
    print(f"  • Configs: configs/")
    print(f"  • Outputs: outputs/")
    print(f"  • Modelos: outputs/weights/")
    print(f"  • Logs: outputs/logs/")
    
    # Modelos disponibles
    weights_dir = Path("outputs/weights")
    if weights_dir.exists():
        models = list(weights_dir.glob("*.pth"))
        print(f"\n{Colors.BOLD}Modelos Entrenados ({len(models)}):{Colors.NC}")
        for model in models[:5]:  # Mostrar primeros 5
            size_mb = model.stat().st_size / 1024**2
            print(f"  • {model.name} ({size_mb:.1f} MB)")
        if len(models) > 5:
            print(f"  • ... y {len(models) - 5} más")
    else:
        print(f"\n{Colors.YELLOW}⚠️  No hay modelos entrenados aún{Colors.NC}")
    
    print()

def clean_outputs():
    """Limpia outputs antiguos (weights, logs, results)"""
    import shutil
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}🧹 LIMPIAR OUTPUTS{Colors.NC}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.NC}\n")
    
    print(f"{Colors.RED}ADVERTENCIA:{Colors.NC} Esto eliminará:")
    print(f"  • outputs/weights/ (modelos entrenados)")
    print(f"  • outputs/logs/ (logs TensorBoard)")
    print(f"  • outputs/results/ (resultados evaluación)")
    print(f"  • outputs/reports/ (reportes generados)\n")
    
    confirm = input(f"{Colors.YELLOW}¿Está seguro? (yes/no): {Colors.NC}")
    
    if confirm.lower() != 'yes':
        print(f"{Colors.GREEN}✅ Operación cancelada{Colors.NC}")
        return
    
    dirs_to_clean = [
        'outputs/weights',
        'outputs/logs',
        'outputs/results',
        'outputs/reports'
    ]
    
    for dir_path in dirs_to_clean:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            print(f"{Colors.GREEN}✓{Colors.NC} Eliminado: {dir_path}")
        else:
            print(f"{Colors.YELLOW}⊘{Colors.NC} No existe: {dir_path}")
    
    print(f"\n{Colors.GREEN}✅ Limpieza completada{Colors.NC}")

def run_tests():
    """Ejecuta suite de tests"""
    import subprocess
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}🧪 EJECUTANDO TESTS{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")
    
    result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'])
    
    if result.returncode == 0:
        print(f"\n{Colors.GREEN}✅ Todos los tests pasaron{Colors.NC}")
    else:
        print(f"\n{Colors.RED}❌ Algunos tests fallaron{Colors.NC}")

def show_help(args=None):
    """Muestra ayuda detallada"""
    
    if args and hasattr(args, 'subcommand') and args.subcommand:
        # Ayuda específica de comando
        help_text = get_command_help(args.subcommand)
    else:
        # Ayuda general
        help_text = f"""
{Colors.BOLD}{Colors.CYAN}📖 AYUDA - SR AGRO VISION{Colors.NC}
{Colors.CYAN}{'='*70}{Colors.NC}

{Colors.BOLD}USO BÁSICO:{Colors.NC}

  Modo Interactivo (Recomendado):
    {Colors.GREEN}python main.py{Colors.NC}
    
  Modo Directo:
    {Colors.GREEN}python main.py <comando> [opciones]{Colors.NC}

{Colors.BOLD}COMANDOS PRINCIPALES:{Colors.NC}

  {Colors.CYAN}download{Colors.NC}     Descarga imágenes Sentinel-2 desde Copernicus
  {Colors.CYAN}preprocess{Colors.NC}   Preprocesa imágenes (RGB+NIR, filtro nubes)
  {Colors.CYAN}dataset{Colors.NC}      Crea pares LR-HR para entrenamiento
  {Colors.CYAN}train{Colors.NC}        Entrena modelo de SR
  {Colors.CYAN}predict{Colors.NC}      Aplica SR a imagen
  {Colors.CYAN}evaluate{Colors.NC}     Evaluación agrícola completa

{Colors.BOLD}EJEMPLOS RÁPIDOS:{Colors.NC}

  # Pipeline completo automático
  {Colors.GREEN}python main.py pipeline --region corrientes_argentina{Colors.NC}
  
  # Entrenar modelo x4
  {Colors.GREEN}python main.py train --config configs/training/espcn_x4.yaml{Colors.NC}
  
  # Aplicar SR a imagen
  {Colors.GREEN}python main.py predict --input imagen.tif --model outputs/weights/best.pth{Colors.NC}
  
  # Evaluación completa
  {Colors.GREEN}python main.py evaluate --sr-dir outputs/results --hr-dir data/datasets/val/HR{Colors.NC}

{Colors.BOLD}AYUDA POR COMANDO:{Colors.NC}

  {Colors.GREEN}python main.py <comando> --help{Colors.NC}
  
  Ejemplo:
  {Colors.GREEN}python main.py train --help{Colors.NC}

{Colors.BOLD}MÁS INFORMACIÓN:{Colors.NC}
  
  Documentación: docs/
  README: README.md
  GitHub: [URL del proyecto]
"""
    
    print(help_text)

def get_command_help(command):
    """Retorna ayuda específica de un comando"""
    # Aquí podrías agregar ayuda detallada por comando
    return f"Ayuda para comando: {command}"

def create_parser():
    """Crea parser de argumentos CLI"""
    parser = argparse.ArgumentParser(
        description='SR Agro Vision - Super-Resolución para Agricultura de Precisión',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                              # Menú interactivo
  python main.py download --region corrientes # Descargar datos
  python main.py train --config espcn_x4.yaml # Entrenar modelo
  python main.py predict --input img.tif      # Aplicar SR
        """
    )
    
    # Subparsers para cada comando
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # ========== DOWNLOAD ==========
    download_parser = subparsers.add_parser('download', help='Descargar imágenes Sentinel-2')
    download_parser.add_argument('--region', type=str, required=True,
                                 help='Región a descargar (corrientes_argentina, etc.)')
    download_parser.add_argument('--output', type=str, default='data/raw',
                                 help='Directorio de salida')
    download_parser.add_argument('--start-date', type=str, default='20230901',
                                 help='Fecha inicio (YYYYMMDD)')
    download_parser.add_argument('--end-date', type=str, default='20240301',
                                 help='Fecha fin (YYYYMMDD)')
    download_parser.add_argument('--max-images', type=int, default=10,
                                 help='Máximo de imágenes')
    
    # ========== PREPROCESS ==========
    preprocess_parser = subparsers.add_parser('preprocess', help='Preprocesar imágenes')
    preprocess_parser.add_argument('--input', type=str, default='data/raw',
                                   help='Directorio con .SAFE')
    preprocess_parser.add_argument('--output', type=str, default='data/preprocessed',
                                   help='Directorio de salida')
    preprocess_parser.add_argument('--cloud-threshold', type=float, default=0.2,
                                   help='Umbral de nubosidad (0-1)')
    
    # ========== DATASET ==========
    dataset_parser = subparsers.add_parser('dataset', help='Crear dataset de entrenamiento')
    dataset_parser.add_argument('--input', type=str, default='data/preprocessed',
                                help='Directorio con GeoTIFFs')
    dataset_parser.add_argument('--output', type=str, default='data/datasets',
                                help='Directorio de salida')
    dataset_parser.add_argument('--scale', type=int, default=4, choices=[2, 4, 8],
                                help='Factor de escalado')
    dataset_parser.add_argument('--patch-size', type=int, default=256,
                                help='Tamaño de patches HR')
    dataset_parser.add_argument('--stride', type=int, default=128,
                                help='Stride entre patches')
    dataset_parser.add_argument('--train-split', type=float, default=0.8,
                                help='Proporción train/val')
    
    # ========== PIPELINE ==========
    pipeline_parser = subparsers.add_parser('pipeline', help='Pipeline completo automático')
    pipeline_parser.add_argument('--region', type=str, required=True)
    pipeline_parser.add_argument('--scale', type=int, default=4, choices=[2, 4, 8])
    pipeline_parser.add_argument('--skip-download', action='store_true')
    pipeline_parser.add_argument('--skip-preprocess', action='store_true')
    pipeline_parser.add_argument('--skip-dataset', action='store_true')
    pipeline_parser.add_argument('--skip-training', action='store_true')
    
    # ========== TRAIN ==========
    train_parser = subparsers.add_parser('train', help='Entrenar modelo')
    train_parser.add_argument('--config', type=str, required=True,
                              help='Archivo de configuración YAML')
    train_parser.add_argument('--resume', action='store_true',
                              help='Reanudar desde checkpoint')
    train_parser.add_argument('--checkpoint', type=str,
                              help='Ruta a checkpoint específico')
    
    # ========== PREDICT ==========
    predict_parser = subparsers.add_parser('predict', help='Aplicar SR a imagen')
    predict_parser.add_argument('--input', type=str, required=True,
                                help='Imagen o directorio de entrada')
    predict_parser.add_argument('--model', type=str, required=True,
                                help='Ruta al modelo .pth')
    predict_parser.add_argument('--output', type=str, required=True,
                                help='Imagen o directorio de salida')
    predict_parser.add_argument('--batch', action='store_true',
                                help='Procesar directorio completo')
    predict_parser.add_argument('--scale', type=int, default=4,
                                help='Factor de escalado')
    
    # ========== ENSEMBLE ==========
    ensemble_parser = subparsers.add_parser('ensemble', help='Predicción con ensemble')
    ensemble_parser.add_argument('--input', type=str, required=True)
    ensemble_parser.add_argument('--models', type=str, nargs='+', required=True,
                                 help='Lista de modelos .pth')
    ensemble_parser.add_argument('--output', type=str, required=True)
    ensemble_parser.add_argument('--weights', type=float, nargs='+',
                                 help='Pesos para cada modelo')
    
    # ========== EVALUATE ==========
    evaluate_parser = subparsers.add_parser('evaluate', help='Evaluación agrícola completa')
    evaluate_parser.add_argument('--config', type=str, 
                                 default='configs/evaluation/evaluation.yaml',
                                 help='Archivo de configuración')
    evaluate_parser.add_argument('--sr-dir', type=str, required=True,
                                 help='Directorio con imágenes SR')
    evaluate_parser.add_argument('--hr-dir', type=str, required=True,
                                 help='Directorio con ground truth HR')
    evaluate_parser.add_argument('--output-dir', type=str, default='outputs/reports',
                                 help='Directorio para reportes')
    evaluate_parser.add_argument('--visualize', action='store_true',
                                 help='Generar visualizaciones')
    
    # ========== METRICS ==========
    metrics_parser = subparsers.add_parser('metrics', help='Solo métricas agrícolas')
    metrics_parser.add_argument('--sr-dir', type=str, required=True)
    metrics_parser.add_argument('--hr-dir', type=str, required=True)
    metrics_parser.add_argument('--output-dir', type=str, default='outputs/results/metrics')
    
    # ========== ABLATION ==========
    ablation_parser = subparsers.add_parser('ablation', help='Ablation study')
    ablation_parser.add_argument('--base-config', type=str, required=True)
    ablation_parser.add_argument('--val-dir', type=str, required=True)
    ablation_parser.add_argument('--output-dir', type=str, default='outputs/results/ablation')
    
    # ========== INFO ==========
    subparsers.add_parser('info', help='Información del proyecto')
    
    # ========== CLEAN ==========
    subparsers.add_parser('clean', help='Limpiar outputs antiguos')
    
    # ========== TEST ==========
    subparsers.add_parser('test', help='Ejecutar tests')
    
    # ========== HELP ==========
    help_parser = subparsers.add_parser('help', help='Ayuda detallada')
    help_parser.add_argument('subcommand', nargs='?', help='Comando específico')
    
    return parser

def main():
    """Función principal"""
    parser = create_parser()
    
    # Si no hay argumentos, mostrar menú interactivo
    if len(sys.argv) == 1:
        interactive_menu()
        return
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Ejecutar comando
    if args.command:
        print_banner()
        execute_command(args.command, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
