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
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    NC = "\033[0m"  # Reset


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
  {Colors.CYAN}1.{Colors.NC} download     - Descargar imágenes Sentinel-2
  {Colors.CYAN}2.{Colors.NC} preprocess   - Preprocesar imágenes descargadas
  {Colors.CYAN}3.{Colors.NC} dataset      - Crear dataset de entrenamiento (pares LR-HR)
  {Colors.CYAN}4.{Colors.NC} pipeline     - Pipeline completo (download → preprocess → dataset)

{Colors.BOLD}🧠 ENTRENAMIENTO{Colors.NC}
  {Colors.CYAN}5.{Colors.NC} train        - Entrenar modelo (ESPCN, SwinIR, GAN)
  {Colors.CYAN}6.{Colors.NC} resume       - Reanudar entrenamiento desde checkpoint
  {Colors.CYAN}7.{Colors.NC} ablation     - Ablation study (comparar configuraciones)

{Colors.BOLD}🔮 INFERENCIA{Colors.NC}
  {Colors.CYAN}8.{Colors.NC} predict      - Aplicar SR a imagen individual
  {Colors.CYAN}9.{Colors.NC} batch        - Procesar múltiples imágenes (batch)
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
  {Colors.CYAN}0.{Colors.NC} exit         - Salir

{Colors.YELLOW}Ingrese el número de opción o comando:{Colors.NC} """

    return input(menu).strip()


def interactive_menu():
    """Modo interactivo con menú"""
    print_banner()

    while True:
        choice = print_menu()

        # Mapeo de números a comandos
        command_map = {
            "1": "download",
            "2": "preprocess",
            "3": "dataset",
            "4": "pipeline",
            "5": "train",
            "6": "resume",
            "7": "ablation",
            "8": "predict",
            "9": "batch",
            "10": "ensemble",
            "11": "evaluate",
            "12": "metrics",
            "13": "visualize",
            "14": "info",
            "15": "clean",
            "16": "test",
            "17": "help",
            "0": "exit",
        }

        # Convertir número a comando
        command = command_map.get(choice, choice)

        if command == "exit":
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
    if command == "download":
        from scripts import download_sentinel

        download_sentinel.main(args)

    elif command == "preprocess":
        from scripts import preprocess_sentinel

        preprocess_sentinel.main(args)

    elif command == "dataset":
        from scripts import create_dataset

        create_dataset.main(args)

    elif command == "pipeline":
        from scripts import pipeline

        pipeline.main(args)

    elif command == "train":
        from src.training import trainer

        trainer.main(args)

    elif command == "resume":
        from src.training import trainer
        import yaml, copy

        if args and hasattr(args, "checkpoint") and args.checkpoint:
            # Inyectar resume_checkpoint en el config en memoria
            with open(args.config) as f:
                config = yaml.safe_load(f)
            config["training"]["resume_checkpoint"] = args.checkpoint
            import tempfile, os as _os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as tmp:
                yaml.dump(config, tmp)
                tmp_path = tmp.name
            args_copy = copy.copy(args)
            args_copy.config = tmp_path
            try:
                trainer.main(args_copy)
            finally:
                _os.unlink(tmp_path)
        else:
            # Sin checkpoint específico → auto-detect (ya funciona en trainer)
            trainer.main(args)

    elif command == "ablation":
        from src.experiments import ablation

        ablation.main(args)

    elif command == "predict":
        from src.inference import predictor

        predictor.main(args)

    elif command == "batch":
        from src.inference import predictor

        if args:
            args.batch = True
        predictor.main(args)

    elif command == "ensemble":
        from src.inference import ensemble

        ensemble.main(args)

    elif command == "evaluate":
        from src.evaluation import evaluator

        evaluator.main(args)

    elif command == "metrics":
        from src.evaluation import metrics_agro

        metrics_agro.main(args)

    elif command == "visualize":
        from src.evaluation import evaluator
        import copy

        viz_args = copy.copy(args) if args else None
        if viz_args is not None:
            viz_args.visualize_only = True
        evaluator.main(viz_args)

    elif command == "info":
        show_info()

    elif command == "clean":
        clean_outputs()

    elif command == "test":
        run_tests()

    elif command == "help":
        show_help(args)


def show_info():
    """Muestra información del proyecto"""
    from src.utils import device

    print(f"\n{Colors.BOLD}{Colors.CYAN}ℹ️  INFORMACIÓN DEL PROYECTO{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}\n")

    # Versión
    print(f"{Colors.BOLD}Versión:{Colors.NC} 2.0")
    print(f"{Colors.BOLD}Proyecto:{Colors.NC} SR Agro Vision")
    print(
        f"{Colors.BOLD}Descripción:{Colors.NC} Super-Resolución Satelital para Agricultura\n"
    )

    # Hardware
    hw_device = device.get_device()
    print(f"{Colors.BOLD}Hardware Detectado:{Colors.NC}")
    print(f"  • Dispositivo: {hw_device}")

    if hw_device.type == "cuda":
        import torch

        print(f"  • GPU: {torch.cuda.get_device_name(0)}")
        print(
            f"  • VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
        )

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

    if confirm.lower() != "yes":
        print(f"{Colors.GREEN}✅ Operación cancelada{Colors.NC}")
        return

    dirs_to_clean = [
        "outputs/weights",
        "outputs/logs",
        "outputs/results",
        "outputs/reports",
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

    result = subprocess.run(["python", "-m", "pytest", "tests/", "-v"])

    if result.returncode == 0:
        print(f"\n{Colors.GREEN}✅ Todos los tests pasaron{Colors.NC}")
    else:
        print(f"\n{Colors.RED}❌ Algunos tests fallaron{Colors.NC}")


def show_help(args=None):
    """Muestra ayuda general o detallada por comando"""

    C = Colors  # alias corto

    # Mapa de ayuda detallada por comando
    command_help = {
        "download": f"""
{C.BOLD}{C.CYAN}📥 COMANDO: download{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Descarga imágenes Sentinel-2 desde Copernicus Data Space.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py download --region REGION [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --region      Región a descargar (requerido)
                Ejemplos: corrientes_argentina, valencia_spain
  --output      Directorio de salida  (default: data/raw)
  --start-date  Fecha inicio YYYY-MM-DD (default: 2023-09-01)
  --end-date    Fecha fin   YYYY-MM-DD  (default: 2024-03-01)
  --max-images  Máximo de imágenes     (default: 10)
  --cloud-max   Nubosidad máxima en %  (default: 20)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py download --region corrientes_argentina{C.NC}
  {C.GREEN}python main.py download --region valencia_spain --max-images 5 --cloud-max 10{C.NC}

{C.BOLD}REQUISITOS:{C.NC}
  .env con COPERNICUS_USER y COPERNICUS_PASS
""",
        "preprocess": f"""
{C.BOLD}{C.CYAN}🔧 COMANDO: preprocess{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Preprocesa imágenes .SAFE descargadas: extrae bandas RGB+NIR,
normaliza a reflectancia [0,1] y filtra por nubosidad.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py preprocess [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --input           Directorio con .SAFE  (default: data/raw)
  --output          Directorio de salida  (default: data/preprocessed)
  --cloud-threshold Umbral nubosidad 0-1  (default: 0.2)
  --no-filter-clouds No filtrar por nubes

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py preprocess{C.NC}
  {C.GREEN}python main.py preprocess --cloud-threshold 0.3 --no-filter-clouds{C.NC}

{C.BOLD}SALIDA:{C.NC}
  GeoTIFF de 4 canales [R, G, B, NIR] en data/preprocessed/
""",
        "dataset": f"""
{C.BOLD}{C.CYAN}📦 COMANDO: dataset{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Genera pares LR-HR de patches .npy para entrenamiento.
Divide automáticamente en train/val.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py dataset [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --input       GeoTIFFs de entrada (default: data/preprocessed)
  --output      Directorio salida   (default: data/datasets)
  --scale       Factor de escalado: 2, 4, 8 (default: 4)
  --patch-size  Tamaño patch HR en px (default: 256)
  --stride      Stride entre patches  (default: 128)
  --train-split Proporción train      (default: 0.8)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py dataset --scale 4 --patch-size 256{C.NC}
  {C.GREEN}python main.py dataset --scale 2 --stride 64 --train-split 0.9{C.NC}

{C.BOLD}SALIDA:{C.NC}
  data/datasets/train/{{LR,HR}}/*.npy
  data/datasets/val/{{LR,HR}}/*.npy
""",
        "pipeline": f"""
{C.BOLD}{C.CYAN}🚀 COMANDO: pipeline{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Pipeline completo automático: download → preprocess → dataset → train.
Ejecuta todos los pasos en secuencia.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py pipeline --region REGION [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --region          Región a descargar (requerido)
  --scale           Factor escalado 2/4/8 (default: 4)
  --start-date      Fecha inicio YYYY-MM-DD
  --end-date        Fecha fin   YYYY-MM-DD
  --skip-download   Saltar descarga  (usar data/raw existente)
  --skip-preprocess Saltar preprocesamiento
  --skip-dataset    Saltar creación de dataset
  --skip-training   Saltar entrenamiento
  --cloud-threshold Umbral nubosidad (default: 0.2)
  --patch-size      Tamaño de patches (default: 256)
  --train-split     Proporción train  (default: 0.8)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py pipeline --region corrientes_argentina{C.NC}
  {C.GREEN}python main.py pipeline --region valencia_spain --skip-download --scale 4{C.NC}
""",
        "train": f"""
{C.BOLD}{C.CYAN}🧠 COMANDO: train{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Entrena un modelo de super-resolución (ESPCN, SwinIR o GAN).
Si existen checkpoints previos en checkpoint_dir, reanuda automáticamente.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py train --config CONFIG [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --config      Archivo YAML de configuración (requerido)
  --resume      Reanudar desde el último checkpoint
  --checkpoint  Ruta a checkpoint específico .pth

{C.BOLD}CONFIGS DISPONIBLES:{C.NC}
  configs/training/sentinel_espcn_x2.yaml   ESPCN x2 (rápido)
  configs/training/sentinel_espcn_x4.yaml   ESPCN x4 (recomendado)
  configs/training/sentinel_swinir_x4.yaml  SwinIR x4 (mejor calidad)
  configs/training/sentinel_gan_x4.yaml     GAN x4 (fotorrealismo)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py train --config configs/training/sentinel_espcn_x4.yaml{C.NC}
  {C.GREEN}python main.py train --config configs/training/sentinel_swinir_x4.yaml --checkpoint outputs/weights/sentinel_espcn_x4/checkpoint_epoch_50.pth{C.NC}

{C.BOLD}MONITOREO:{C.NC}
  {C.GREEN}tensorboard --logdir outputs/logs/{C.NC}
""",
        "resume": f"""
{C.BOLD}{C.CYAN}🔄 COMANDO: resume{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Reanuda el entrenamiento desde el último checkpoint guardado.
Equivalente a 'train' pero con detección automática de checkpoint.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py resume --config CONFIG [--checkpoint RUTA]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --config      Archivo YAML de configuración (requerido)
  --checkpoint  Ruta a checkpoint específico (opcional)
                Sin este flag, se usa el último checkpoint_epoch_N.pth
                encontrado en checkpoint_dir del config

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py resume --config configs/training/sentinel_espcn_x4.yaml{C.NC}
  {C.GREEN}python main.py resume --config configs/training/sentinel_espcn_x4.yaml --checkpoint outputs/weights/sentinel_espcn_x4/checkpoint_epoch_50.pth{C.NC}
""",
        "ablation": f"""
{C.BOLD}{C.CYAN}🧪 COMANDO: ablation{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Ejecuta ablation study: compara múltiples variantes de modelos
y genera tabla comparativa de PSNR, SSIM, NDVI MAE, SAM.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py ablation --base-config CONFIG --val-dir DIR [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --base-config  Config base YAML (requerido)
  --val-dir      Directorio validación con subdirectorios SR/ y HR/ (requerido)
  --output-dir   Directorio de resultados (default: outputs/results/ablation)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py ablation --base-config configs/training/sentinel_espcn_x4.yaml --val-dir data/datasets/val{C.NC}
""",
        "predict": f"""
{C.BOLD}{C.CYAN}🔮 COMANDO: predict{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Aplica super-resolución a una imagen .npy o archivo GeoTIFF.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py predict --input IMAGEN --model MODELO --output SALIDA [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --input    Imagen .npy de entrada (requerido)
  --model    Ruta al modelo .pth    (requerido)
  --output   Imagen de salida .npy  (requerido)
  --scale    Factor de escalado 2/4/8 (default: 4)
  --channels Número de canales: 3=RGB, 4=RGB+NIR (default: 3)
  --batch    Procesar directorio completo

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py predict --input data/datasets/val/LR/img.npy --model outputs/weights/sentinel_espcn_x4/best_psnr_x4.pth --output outputs/results/img_sr.npy{C.NC}
""",
        "batch": f"""
{C.BOLD}{C.CYAN}🗂️  COMANDO: batch{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Procesa un directorio completo de imágenes con super-resolución.
Equivalente a 'predict --batch'.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py batch --input DIR_LR --model MODELO --output DIR_SR [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --input    Directorio con imágenes LR .npy (requerido)
  --model    Ruta al modelo .pth             (requerido)
  --output   Directorio de salida            (requerido)
  --scale    Factor de escalado (default: 4)
  --channels Canales: 3=RGB, 4=RGB+NIR (default: 3)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py batch --input data/datasets/val/LR --model outputs/weights/sentinel_espcn_x4/best_psnr_x4.pth --output outputs/results/sr{C.NC}
""",
        "ensemble": f"""
{C.BOLD}{C.CYAN}🎭 COMANDO: ensemble{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Predicción usando ensemble de múltiples modelos combinados por promedio ponderado.
Mejora calidad respecto a un solo modelo.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py ensemble --models M1 M2 ... --input INPUT --output OUTPUT [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --models   Lista de modelos .pth (requerido, mínimo 2)
  --input    Imagen o directorio .npy de entrada (requerido)
  --output   Imagen o directorio de salida       (requerido)
  --weights  Pesos para cada modelo (opcional, default: promedio simple)
  --channels Número de canales (default: 4)
  --scale    Factor de escalado (default: 4)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py ensemble --models outputs/weights/best_psnr_x4.pth outputs/weights/best_ndvi_x4.pth --input data/datasets/val/LR --output outputs/results/ensemble --weights 0.6 0.4{C.NC}
""",
        "evaluate": f"""
{C.BOLD}{C.CYAN}📊 COMANDO: evaluate{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Evaluación agrícola completa: métricas (NDVI/EVI/SAVI), estimación de área,
análisis económico, casos de uso y reporte final.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py evaluate --sr-dir DIR --hr-dir DIR [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --sr-dir      Directorio con imágenes SR (requerido)
  --hr-dir      Directorio con ground truth HR (requerido)
  --output-dir  Directorio de salida (default: outputs/reports)
  --config      Config YAML alternativo (default: configs/evaluation/evaluation.yaml)
  --visualize   Generar visualizaciones comparativas

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py evaluate --sr-dir outputs/results/sr --hr-dir data/datasets/val/HR{C.NC}
  {C.GREEN}python main.py evaluate --sr-dir outputs/results/sr --hr-dir data/datasets/val/HR --output-dir outputs/reports/v2 --visualize{C.NC}
""",
        "metrics": f"""
{C.BOLD}{C.CYAN}🌱 COMANDO: metrics{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Calcula solo métricas agrícolas (NDVI, EVI, SAVI) con estadísticas
detalladas (MAE, RMSE, R², Pearson). Versión liviana de 'evaluate'.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py metrics --sr-dir DIR --hr-dir DIR [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --sr-dir     Directorio con imágenes SR .npy (requerido)
  --hr-dir     Directorio con ground truth .npy (requerido)
  --output-dir Directorio de salida (default: outputs/results/metrics)

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py metrics --sr-dir outputs/results/sr --hr-dir data/datasets/val/HR{C.NC}
""",
        "visualize": f"""
{C.BOLD}{C.CYAN}🖼️  COMANDO: visualize{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Genera visualizaciones comparativas LR vs SR vs HR con mapas de NDVI
y error absoluto. No genera reportes completos.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py visualize --sr-dir DIR --hr-dir DIR [opciones]{C.NC}

{C.BOLD}OPCIONES:{C.NC}
  --sr-dir     Directorio con imágenes SR (requerido)
  --hr-dir     Directorio con ground truth HR (requerido)
  --output-dir Directorio de salida (default: outputs/reports)
  --config     Config YAML alternativo

{C.BOLD}EJEMPLOS:{C.NC}
  {C.GREEN}python main.py visualize --sr-dir outputs/results/sr --hr-dir data/datasets/val/HR{C.NC}
""",
        "info": f"""
{C.BOLD}{C.CYAN}ℹ️  COMANDO: info{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Muestra información del proyecto: hardware detectado (CPU/GPU/MPS),
rutas del proyecto y modelos entrenados disponibles.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py info{C.NC}
""",
        "clean": f"""
{C.BOLD}{C.CYAN}🧹 COMANDO: clean{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Elimina outputs generados: weights, logs, results y reports.
Pide confirmación antes de eliminar.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py clean{C.NC}

{C.BOLD}ADVTERTENCIA:{C.NC}
  {C.YELLOW}Esto elimina modelos entrenados. Hacer backup antes si es necesario.{C.NC}
""",
        "test": f"""
{C.BOLD}{C.CYAN}🧪 COMANDO: test{C.NC}
{C.CYAN}{'─'*60}{C.NC}
Ejecuta la suite de tests unitarios con pytest.

{C.BOLD}USO:{C.NC}
  {C.GREEN}python main.py test{C.NC}

{C.BOLD}TESTS INCLUIDOS:{C.NC}
  tests/test_models.py     Arquitecturas ESPCN, SwinIR, GAN
  tests/test_training.py   Loss, métricas, checkpoints
  tests/test_inference.py  Predictor, ensemble
  tests/test_evaluation.py Métricas agrícolas, reportes
""",
    }

    subcommand = None
    if args and hasattr(args, "subcommand"):
        subcommand = args.subcommand

    if subcommand and subcommand in command_help:
        print(command_help[subcommand])
    elif subcommand:
        print(
            f"\n{C.YELLOW}⚠️  No hay ayuda específica para '{subcommand}'. Mostrando ayuda general.{C.NC}"
        )
        show_help()
    else:
        # Ayuda general
        print(
            f"""
{C.BOLD}{C.CYAN}📖 AYUDA - SR AGRO VISION{C.NC}
{C.CYAN}{'='*70}{C.NC}

{C.BOLD}USO BÁSICO:{C.NC}

  Modo Interactivo (Recomendado):
    {C.GREEN}python main.py{C.NC}

  Modo Directo:
    {C.GREEN}python main.py <comando> [opciones]{C.NC}

{C.BOLD}DATOS:{C.NC}
  {C.CYAN}download{C.NC}     Descargar imágenes Sentinel-2
  {C.CYAN}preprocess{C.NC}   Preprocesar imágenes descargadas
  {C.CYAN}dataset{C.NC}      Crear dataset de entrenamiento (pares LR-HR)
  {C.CYAN}pipeline{C.NC}     Pipeline completo automático

{C.BOLD}ENTRENAMIENTO:{C.NC}
  {C.CYAN}train{C.NC}        Entrenar modelo (ESPCN, SwinIR, GAN)
  {C.CYAN}resume{C.NC}       Reanudar entrenamiento desde checkpoint
  {C.CYAN}ablation{C.NC}     Ablation study (comparar configuraciones)

{C.BOLD}INFERENCIA:{C.NC}
  {C.CYAN}predict{C.NC}      Aplicar SR a imagen individual
  {C.CYAN}batch{C.NC}        Procesar directorio completo
  {C.CYAN}ensemble{C.NC}     Predicción con ensemble de modelos

{C.BOLD}EVALUACIÓN:{C.NC}
  {C.CYAN}evaluate{C.NC}     Evaluación agrícola completa
  {C.CYAN}metrics{C.NC}      Solo métricas agrícolas (NDVI, EVI, SAVI)
  {C.CYAN}visualize{C.NC}    Generar visualizaciones comparativas

{C.BOLD}UTILIDADES:{C.NC}
  {C.CYAN}info{C.NC}  {C.CYAN}clean{C.NC}  {C.CYAN}test{C.NC}

{C.BOLD}AYUDA POR COMANDO:{C.NC}
  {C.GREEN}python main.py help <comando>{C.NC}
  Ejemplo: {C.GREEN}python main.py help train{C.NC}

{C.BOLD}EJEMPLOS RÁPIDOS:{C.NC}
  {C.GREEN}python main.py pipeline --region corrientes_argentina{C.NC}
  {C.GREEN}python main.py train --config configs/training/sentinel_espcn_x4.yaml{C.NC}
  {C.GREEN}python main.py predict --input img.npy --model outputs/weights/best_psnr_x4.pth --output sr.npy{C.NC}
  {C.GREEN}python main.py evaluate --sr-dir outputs/results/sr --hr-dir data/datasets/val/HR{C.NC}
"""
        )


def create_parser():
    """Crea parser de argumentos CLI"""
    parser = argparse.ArgumentParser(
        description="SR Agro Vision - Super-Resolución para Agricultura de Precisión",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                              # Menú interactivo
  python main.py download --region corrientes # Descargar datos
  python main.py train --config espcn_x4.yaml # Entrenar modelo
  python main.py predict --input img.tif      # Aplicar SR
        """,
    )

    # Subparsers para cada comando
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # ========== DOWNLOAD ==========
    download_parser = subparsers.add_parser(
        "download", help="Descargar imágenes Sentinel-2"
    )
    download_parser.add_argument(
        "--region",
        type=str,
        required=True,
        help="Región a descargar (corrientes_argentina, etc.)",
    )
    download_parser.add_argument(
        "--output", type=str, default="data/raw", help="Directorio de salida"
    )
    download_parser.add_argument(
        "--start-date", type=str, default="2023-09-01", help="Fecha inicio (YYYY-MM-DD)"
    )
    download_parser.add_argument(
        "--end-date", type=str, default="2024-03-01", help="Fecha fin (YYYY-MM-DD)"
    )
    download_parser.add_argument(
        "--max-images", type=int, default=10, help="Máximo de imágenes"
    )
    download_parser.add_argument(
        "--cloud-max", type=int, default=20, help="Nubosidad máxima permitida (%)"
    )

    # ========== PREPROCESS ==========
    preprocess_parser = subparsers.add_parser("preprocess", help="Preprocesar imágenes")
    preprocess_parser.add_argument(
        "--input", type=str, default="data/raw", help="Directorio con .SAFE"
    )
    preprocess_parser.add_argument(
        "--output", type=str, default="data/preprocessed", help="Directorio de salida"
    )
    preprocess_parser.add_argument(
        "--cloud-threshold", type=float, default=0.2, help="Umbral de nubosidad (0-1)"
    )
    preprocess_parser.add_argument(
        "--no-filter-clouds", action="store_true", help="No filtrar por nubes"
    )

    # ========== DATASET ==========
    dataset_parser = subparsers.add_parser(
        "dataset", help="Crear dataset de entrenamiento"
    )
    dataset_parser.add_argument(
        "--input", type=str, default="data/preprocessed", help="Directorio con GeoTIFFs"
    )
    dataset_parser.add_argument(
        "--output", type=str, default="data/datasets", help="Directorio de salida"
    )
    dataset_parser.add_argument(
        "--scale", type=int, default=4, choices=[2, 4, 8], help="Factor de escalado"
    )
    dataset_parser.add_argument(
        "--patch-size", type=int, default=256, help="Tamaño de patches HR"
    )
    dataset_parser.add_argument(
        "--stride", type=int, default=128, help="Stride entre patches"
    )
    dataset_parser.add_argument(
        "--train-split", type=float, default=0.8, help="Proporción train/val"
    )

    # ========== PIPELINE ==========
    pipeline_parser = subparsers.add_parser(
        "pipeline", help="Pipeline completo automático"
    )
    pipeline_parser.add_argument("--region", type=str, required=True)
    pipeline_parser.add_argument("--scale", type=int, default=4, choices=[2, 4, 8])
    pipeline_parser.add_argument("--skip-download", action="store_true")
    pipeline_parser.add_argument("--skip-preprocess", action="store_true")
    pipeline_parser.add_argument("--skip-dataset", action="store_true")
    pipeline_parser.add_argument("--skip-training", action="store_true")

    # ========== TRAIN ==========
    train_parser = subparsers.add_parser("train", help="Entrenar modelo")
    train_parser.add_argument(
        "--config", type=str, required=True, help="Archivo de configuración YAML"
    )
    train_parser.add_argument(
        "--resume", action="store_true", help="Reanudar desde checkpoint"
    )
    train_parser.add_argument(
        "--checkpoint", type=str, help="Ruta a checkpoint específico"
    )

    # ========== PREDICT ==========
    predict_parser = subparsers.add_parser("predict", help="Aplicar SR a imagen")
    predict_parser.add_argument(
        "--input", type=str, required=True, help="Imagen o directorio de entrada"
    )
    predict_parser.add_argument(
        "--model", type=str, required=True, help="Ruta al modelo .pth"
    )
    predict_parser.add_argument(
        "--output", type=str, required=True, help="Imagen o directorio de salida"
    )
    predict_parser.add_argument(
        "--batch", action="store_true", help="Procesar directorio completo"
    )
    predict_parser.add_argument(
        "--scale", type=int, default=4, help="Factor de escalado"
    )
    predict_parser.add_argument(
        "--channels", type=int, default=3, help="Número de canales (3=RGB, 4=RGBNIR)"
    )

    # ========== BATCH (alias de predict --batch) ==========
    batch_parser = subparsers.add_parser(
        "batch", help="Aplicar SR a directorio completo"
    )
    batch_parser.add_argument(
        "--input", type=str, required=True, help="Directorio LR de entrada"
    )
    batch_parser.add_argument(
        "--model", type=str, required=True, help="Ruta al modelo .pth"
    )
    batch_parser.add_argument(
        "--output", type=str, required=True, help="Directorio de salida SR"
    )
    batch_parser.add_argument("--scale", type=int, default=4, help="Factor de escalado")
    batch_parser.add_argument(
        "--channels", type=int, default=4, help="Canales (3=RGB, 4=RGBNIR)"
    )

    # ========== VISUALIZE ==========
    visualize_parser = subparsers.add_parser(
        "visualize", help="Generar visualizaciones comparativas"
    )
    visualize_parser.add_argument(
        "--sr-dir", type=str, required=True, help="Directorio con imágenes SR"
    )
    visualize_parser.add_argument(
        "--hr-dir", type=str, required=True, help="Directorio con ground truth HR"
    )
    visualize_parser.add_argument(
        "--output-dir", type=str, default="outputs/reports", help="Directorio de salida"
    )
    visualize_parser.add_argument(
        "--config", type=str, default="configs/evaluation/evaluation.yaml"
    )

    ensemble_parser = subparsers.add_parser("ensemble", help="Predicción con ensemble")
    ensemble_parser.add_argument("--input", type=str, required=True)
    ensemble_parser.add_argument(
        "--models", type=str, nargs="+", required=True, help="Lista de modelos .pth"
    )
    ensemble_parser.add_argument("--output", type=str, required=True)
    ensemble_parser.add_argument(
        "--weights", type=float, nargs="+", help="Pesos para cada modelo"
    )

    # ========== EVALUATE ==========
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Evaluación agrícola completa"
    )
    evaluate_parser.add_argument(
        "--config",
        type=str,
        default="configs/evaluation/evaluation.yaml",
        help="Archivo de configuración",
    )
    evaluate_parser.add_argument(
        "--sr-dir",
        type=str,
        default=None,
        help="Directorio con imágenes SR (opcional si se usa --model + --lr-dir)",
    )
    evaluate_parser.add_argument(
        "--hr-dir", type=str, required=True, help="Directorio con ground truth HR"
    )
    evaluate_parser.add_argument(
        "--lr-dir",
        type=str,
        default=None,
        help="Directorio con patches LR (para generar SR on-the-fly con --model)",
    )
    evaluate_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Modelo .pth para generar SR desde LR automáticamente",
    )
    evaluate_parser.add_argument(
        "--scale",
        type=int,
        default=4,
        help="Factor de escalado del modelo (default: 4)",
    )
    evaluate_parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/reports",
        help="Directorio para reportes",
    )
    evaluate_parser.add_argument(
        "--visualize", action="store_true", help="Generar visualizaciones"
    )

    # ========== METRICS ==========
    metrics_parser = subparsers.add_parser("metrics", help="Solo métricas agrícolas")
    metrics_parser.add_argument("--sr-dir", type=str, required=True)
    metrics_parser.add_argument("--hr-dir", type=str, required=True)
    metrics_parser.add_argument(
        "--output-dir", type=str, default="outputs/results/metrics"
    )

    # ========== ABLATION ==========
    ablation_parser = subparsers.add_parser("ablation", help="Ablation study")
    ablation_parser.add_argument("--base-config", type=str, required=True)
    ablation_parser.add_argument("--val-dir", type=str, required=True)
    ablation_parser.add_argument(
        "--output-dir", type=str, default="outputs/results/ablation"
    )

    # ========== INFO ==========
    subparsers.add_parser("info", help="Información del proyecto")

    # ========== CLEAN ==========
    subparsers.add_parser("clean", help="Limpiar outputs antiguos")

    # ========== TEST ==========
    subparsers.add_parser("test", help="Ejecutar tests")

    # ========== HELP ==========
    help_parser = subparsers.add_parser("help", help="Ayuda detallada")
    help_parser.add_argument("subcommand", nargs="?", help="Comando específico")

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
