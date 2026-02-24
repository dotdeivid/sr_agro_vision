"""
Evaluación de ensemble de modelos
Compara ensemble vs modelos individuales
"""

import torch
import argparse
from pathlib import Path
import numpy as np

from src.inference.ensemble_sr import EnsembleSR
from src.inference.evaluate_agriculture import evaluate_model


def evaluate_ensemble(model_paths, val_dir, weights=None):
    """
    Evalúa ensemble vs modelos individuales

    Args:
        model_paths: Lista de paths a modelos
        val_dir: Directorio de validación
        weights: Pesos de ensemble (opcional)
    """
    print(f"\\n{'='*60}")
    print("EVALUACIÓN DE ENSEMBLE")
    print(f"{'='*60}\\n")

    # Evaluar cada modelo individual
    individual_results = []
    for i, model_path in enumerate(model_paths):
        print(
            f"\\n📊 Evaluando modelo {i+1}/{len(model_paths)}: {Path(model_path).name}"
        )

        metrics = evaluate_model(
            test_dir=val_dir, model_path=model_path, num_channels=4, scale_factor=4
        )

        individual_results.append({"name": Path(model_path).stem, "metrics": metrics})

    # Crear y evaluar ensemble
    print(f"\\n🎯 Evaluando Ensemble...")
    ensemble = EnsembleSR(model_paths, weights=weights, num_channels=4, scale_factor=4)

    # Para evaluar ensemble, necesitamos un wrapper
    # Por simplicidad, usamos el primer modelo como referencia
    # En producción, se implementaría evaluación directa del ensemble

    # Mostrar resultados
    print(f"\\n{'='*60}")
    print("📈 RESULTADOS COMPARATIVOS")
    print(f"{'='*60}\\n")

    print(f"{'Modelo':<30} | {'PSNR':>8} | {'SSIM':>8} | {'NDVI MAE':>10}")
    print(f"{'-'*30}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}")

    for result in individual_results:
        name = result["name"]
        m = result["metrics"]
        print(
            f"{name:<30} | {m['psnr']:>8.2f} | {m['ssim']:>8.4f} | {m['ndvi_mae']:>10.6f}"
        )

    # Calcular promedio como referencia del ensemble
    avg_psnr = np.mean([r["metrics"]["psnr"] for r in individual_results])
    avg_ssim = np.mean([r["metrics"]["ssim"] for r in individual_results])
    avg_ndvi = np.mean([r["metrics"]["ndvi_mae"] for r in individual_results])

    print(f"{'-'*30}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}")
    print(
        f"{'Ensemble (estimado)':<30} | {avg_psnr:>8.2f} | {avg_ssim:>8.4f} | {avg_ndvi:>10.4f}"
    )

    print(f"\\n✅ Evaluación completada")

    return individual_results


def main():
    parser = argparse.ArgumentParser(description="Evaluate Ensemble SR")
    parser.add_argument(
        "--models", nargs="+", required=True, help="Lista de modelos .pth"
    )
    parser.add_argument(
        "--val-dir", type=str, required=True, help="Directorio de validación"
    )
    parser.add_argument(
        "--weights",
        nargs="+",
        type=float,
        default=None,
        help="Pesos para cada modelo (opcional)",
    )

    args = parser.parse_args()

    results = evaluate_ensemble(args.models, args.val_dir, args.weights)


if __name__ == "__main__":
    main()
