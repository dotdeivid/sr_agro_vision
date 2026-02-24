"""
Script principal para ejecutar evaluación completa
Orquesta todos los módulos en secuencia
"""

import argparse
import yaml
from pathlib import Path
import numpy as np
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation.metrics_agro import evaluate_batch as eval_agri
from src.evaluation.area_estimator import AreaEstimator
from src.evaluation.temporal_analyzer import TemporalAnalyzer
from src.evaluation.economic_analyzer import EconomicAnalyzer
from src.evaluation.use_cases import evaluate_use_cases
from src.evaluation.report_generator import ReportGenerator


def generate_sr_from_model(lr_dir, model_path, sr_dir, scale=4, num_channels=4):
    """
    Genera imágenes SR aplicando el modelo sobre los patches LR.
    Guarda los resultados como .npy en sr_dir.

    Args:
        lr_dir:       Directorio con patches LR .npy
        model_path:   Ruta al modelo .pth entrenado
        sr_dir:       Directorio de salida para patches SR .npy
        scale:        Factor de escalado del modelo
        num_channels: Número de canales (4 para RGB+NIR)
    """
    import torch
    from tqdm import tqdm
    from src.models.espcn import ESPCNMultispectral
    from src.utils.device import get_device

    lr_dir = Path(lr_dir)
    sr_dir = Path(sr_dir)
    sr_dir.mkdir(parents=True, exist_ok=True)

    lr_files = sorted(lr_dir.glob("*.npy"))
    if len(lr_files) == 0:
        raise ValueError(f"No se encontraron patches LR en {lr_dir}")

    print(f"\n🔮 Generando SR con modelo: {model_path}")
    print(f"   LR patches: {len(lr_files)} → SR en {sr_dir}")

    device = get_device()
    model = ESPCNMultispectral(
        scale_factor=scale, num_channels=num_channels, num_features=64
    )
    model.load_state_dict(
        torch.load(model_path, map_location=device, weights_only=True)
    )
    model.to(device)
    model.eval()

    with torch.no_grad():
        for lr_path in tqdm(lr_files, desc="Generando SR"):
            lr = np.load(lr_path)  # [C, H, W]

            # Filtrar patches con canales incorrectos silenciosamente
            if lr.shape[0] != num_channels:
                continue

            tensor = (
                torch.from_numpy(lr).unsqueeze(0).float().to(device)
            )  # [1, C, H, W]
            sr_tensor = model(tensor)  # [1, C, H*s, W*s]
            sr = sr_tensor.squeeze(0).cpu().numpy()  # [C, H*s, W*s]

            np.save(sr_dir / lr_path.name, sr)

    n_sr = len(list(sr_dir.glob("*.npy")))
    print(f"   ✅ {n_sr} patches SR generados")


def load_config(config_path):
    """Load evaluation config"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_evaluation(config_path):
    """
    Execute complete agricultural evaluation
    """
    print("\n" + "=" * 70)
    print("🌾 EVALUACIÓN AGRÍCOLA COMPLETA".center(70))
    print("=" * 70 + "\n")

    # Load config
    config = load_config(config_path)
    paths = config["paths"]
    output_dir = Path(paths["output"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Agricultural Metrics
    print("\n📊 PASO 1: MÉTRICAS AGRÍCOLAS")
    print("-" * 70)

    # Detectar tipo de dataset
    dataset_type = config.get("evaluation", {}).get("dataset_type", "multiespectral")
    print(f"   Dataset type: {dataset_type}")

    metrics_dir = output_dir / config["agricultural_metrics"]["output_subdir"]
    eval_agri(
        sr_dir=paths["sr_results"],
        hr_dir=paths["hr_ground_truth"],
        output_dir=metrics_dir,
        dataset_type=dataset_type,
    )

    # 2. Area Estimation
    print("\n📏 PASO 2: ESTIMACIÓN DE ÁREA")
    print("-" * 70)
    area_dir = output_dir / config["area_estimation"]["output_subdir"]
    estimator = AreaEstimator(gsd_meters=config["area_estimation"]["gsd_meters"])
    estimator.evaluate_batch(
        sr_dir=paths["sr_results"],
        hr_dir=paths["hr_ground_truth"],
        output_dir=area_dir,
        ndvi_threshold=config["area_estimation"]["ndvi_vegetation_threshold"],
    )

    # 3. Economic Analysis
    print("\n💰 PASO 3: ANÁLISIS ECONÓMICO")
    print("-" * 70)
    econ_dir = output_dir / config["economic_analysis"]["output_subdir"]
    analyzer = EconomicAnalyzer()
    analyzer.generate_report(
        n_images=12,
        area_km2=config["economic_analysis"]["roi"]["area_km2"],
        output_dir=econ_dir,
    )

    # 4. Use Cases
    print("\n🎯 PASO 4: CASOS DE USO")
    print("-" * 70)
    usecase_dir = output_dir / config["use_cases"]["output_subdir"]
    evaluate_use_cases(
        sr_dir=paths["sr_results"],
        hr_dir=paths["hr_ground_truth"],
        output_dir=usecase_dir,
    )

    # 5. Generate Final Report
    print("\n📄 PASO 5: GENERAR INFORME FINAL")
    print("-" * 70)
    report_dir = output_dir / config["report"]["output_subdir"]
    generator = ReportGenerator(output_dir)
    generator.generate_full_report(report_dir)

    print("\n" + "=" * 70)
    print("✅ EVALUACIÓN COMPLETADA")
    print("=" * 70)
    print(f"📁 Resultados: {output_dir}")
    print(f"📄 Informe: {report_dir}/evaluation_report.md")
    print("=" * 70 + "\n")


def main(args=None):
    """
    Función main para ser llamada desde main.py o directamente

    Args:
        args: Argumentos parseados (opcional, si None se parsean desde consola)
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Run Agricultural Evaluation")
        parser.add_argument(
            "--config",
            type=str,
            default="configs/evaluation/evaluation.yaml",
            help="Path to evaluation config",
        )
        parser.add_argument("--sr-dir", type=str, help="Directorio con imágenes SR")
        parser.add_argument("--hr-dir", type=str, help="Directorio con ground truth HR")
        parser.add_argument(
            "--lr-dir",
            type=str,
            help="Directorio con patches LR (para generar SR on-the-fly)",
        )
        parser.add_argument(
            "--model", type=str, help="Modelo .pth para generar SR desde LR"
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="outputs/reports",
            help="Directorio de salida",
        )
        parser.add_argument(
            "--visualize", action="store_true", help="Generar visualizaciones"
        )
        args = parser.parse_args()

    # Si vienen sr_dir y hr_dir directos, actualizar el config YAML en memoria
    config_path = getattr(args, "config", "configs/evaluation/evaluation.yaml")

    # Si el usuario pasa --model y --lr-dir, generar SR on-the-fly primero
    lr_dir = getattr(args, "lr_dir", None)
    model = getattr(args, "model", None)
    sr_dir = getattr(args, "sr_dir", None)
    hr_dir = getattr(args, "hr_dir", None)
    out_dir = getattr(args, "output_dir", "outputs/reports")

    if model and lr_dir:
        # Generar SR y usar esa carpeta como sr_dir
        auto_sr_dir = Path(out_dir) / "sr_generated"
        generate_sr_from_model(
            lr_dir=lr_dir,
            model_path=model,
            sr_dir=auto_sr_dir,
        )
        # Sobrescribir sr_dir con el generado
        args.sr_dir = str(auto_sr_dir)
        sr_dir = args.sr_dir

    try:
        # Si el usuario pasa --visualize-only (set por main.py en comando 'visualize')
        if getattr(args, "visualize_only", False):
            print("\n🖼️  MODO SOLO VISUALIZACIONES")
            config = load_config(config_path)
            paths = config["paths"]
            # Usar sr_dir/hr_dir si vienen como args, si no del config
            sr_dir = getattr(args, "sr_dir", None) or paths["sr_results"]
            hr_dir = getattr(args, "hr_dir", None) or paths["hr_ground_truth"]
            output_dir = getattr(args, "output_dir", None) or paths["output"]

            from src.evaluation.metrics_agro import AgriculturalMetrics, evaluate_batch

            summary = evaluate_batch(
                sr_dir=sr_dir,
                hr_dir=hr_dir,
                output_dir=output_dir,
            )
            print(f"\n✅ Visualizaciones generadas en: {output_dir}")
            return

        # Si vienen sr_dir/hr_dir como args CLI, sobrescribir paths del config
        if getattr(args, "sr_dir", None) and getattr(args, "hr_dir", None):
            # Parchear config con paths desde CLI
            import yaml, copy

            config = load_config(config_path)
            config = copy.deepcopy(config)
            config["paths"]["sr_results"] = args.sr_dir
            config["paths"]["hr_ground_truth"] = args.hr_dir
            if getattr(args, "output_dir", None):
                config["paths"]["output"] = args.output_dir

            # Escribir config temporal y usar
            import tempfile, os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as tmp:
                yaml.dump(config, tmp)
                tmp_path = tmp.name
            try:
                run_evaluation(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            run_evaluation(config_path)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
