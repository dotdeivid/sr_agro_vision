"""
Ablation Study: Analiza contribución de cada componente
Compara diferentes configuraciones de forma sistemática
"""

import torch
import yaml
import argparse
from pathlib import Path
import pandas as pd
from typing import List, Dict
import subprocess
import json

from src.evaluation.metrics_agro import evaluate_batch as evaluate_model


class AblationStudy:
    """
    Ejecuta ablation study sistemático
    Compara diferentes configuraciones
    """

    def __init__(self, base_config_path, val_dir, output_dir):
        """
        Args:
            base_config_path: Config base
            val_dir: Directorio de validación
            output_dir: Directorio para resultados
        """
        self.base_config = yaml.safe_load(open(base_config_path))
        self.val_dir = Path(val_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = []

    def create_variant_config(self, variant_name, modifications):
        """
        Crea variant de configuración

        Args:
            variant_name: Nombre del variant
            modifications: Dict con modificaciones

        Returns:
            Path al config creado
        """
        config = self.base_config.copy()

        # Aplicar modificaciones
        for key, value in modifications.items():
            keys = key.split(".")
            current = config
            for k in keys[:-1]:
                current = current[k]
            current[keys[-1]] = value

        # Guardar
        config_path = self.output_dir / f"config_{variant_name}.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path

    def run_experiment(self, variant_name, model_path, config_path):
        """
        Ejecuta experimento y evalúa

        Returns:
            Dict con métricas
        """
        print(f"\n{'='*60}")
        print(f"🧪 Experimento: {variant_name}")
        print(f"{'='*60}")

        # Evaluar modelo con métricas agrícolas
        metrics = evaluate_model(
            sr_dir=str(self.val_dir / "SR"),
            hr_dir=str(self.val_dir / "HR"),
            output_dir=str(self.output_dir / variant_name),
        )

        if metrics is None:
            metrics = {}

        metrics["variant"] = variant_name
        metrics["config"] = str(config_path)
        metrics["model"] = str(model_path)

        self.results.append(metrics)

        return metrics

    def save_results(self):
        """Guarda resultados como CSV y JSON"""
        # DataFrame
        df = pd.DataFrame(self.results)

        # Ordenar por PSNR
        df = df.sort_values("psnr", ascending=False)

        # Guardar CSV
        csv_path = self.output_dir / "ablation_results.csv"
        df.to_csv(csv_path, index=False)
        print(f"\\n💾 Resultados guardados: {csv_path}")

        # Guardar JSON
        json_path = self.output_dir / "ablation_results.json"
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)

        return df

    def print_summary(self):
        """Imprime resumen de resultados"""
        df = pd.DataFrame(self.results)

        print(f"\\n{'='*80}")
        print("📊 RESUMEN ABLATION STUDY")
        print(f"{'='*80}\\n")

        # Tabla principal
        print(df[["variant", "psnr", "ssim", "ndvi_mae", "sam"]].to_string(index=False))

        # Baseline
        baseline = (
            df[df["variant"] == "baseline"].iloc[0]
            if "baseline" in df["variant"].values
            else None
        )

        if baseline is not None:
            print(f"\\n{'='*80}")
            print("📈 MEJORAS vs BASELINE")
            print(f"{'='*80}\\n")

            for _, row in df.iterrows():
                if row["variant"] != "baseline":
                    psnr_gain = row["psnr"] - baseline["psnr"]
                    ssim_gain = row["ssim"] - baseline["ssim"]
                    print(
                        f"{row['variant']:30s} | PSNR: +{psnr_gain:+.2f} dB | SSIM: +{ssim_gain:+.4f}"
                    )


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description="Run Ablation Study")
        parser.add_argument(
            "--base-config",
            type=str,
            default="configs/training/sentinel_espcn_x4.yaml",
            help="Base configuration",
        )
        parser.add_argument(
            "--val-dir",
            type=str,
            default="data/datasets/val",
            help="Validation directory (debe contener subdirectorios SR/ y HR/)",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="outputs/results/ablation",
            help="Output directory",
        )
        args = parser.parse_args()

    # Crear ablation study
    study = AblationStudy(args.base_config, args.val_dir, args.output_dir)

    # Definir experiments
    experiments = [
        {
            "name": "baseline",
            "model": "weights/satellite/best_psnr_x4.pth",
            "description": "L1 Loss + Basic Augmentation",
        },
        {
            "name": "perceptual",
            "model": "weights/satellite_perceptual/best_psnr_x4.pth",
            "description": "L1 + Perceptual Loss",
        },
        {
            "name": "gan",
            "model": "weights/satellite_gan/best_psnr_x4.pth",
            "description": "GAN Training",
        },
        # Añadir más según modelos entrenados
    ]

    # Ejecutar experiments
    for exp in experiments:
        model_path = Path(exp["model"])

        if not model_path.exists():
            print(f"⚠️ Modelo no encontrado: {model_path}")
            print(f"   Skipping {exp['name']}...")
            continue

        config_path = study.create_variant_config(exp["name"], {})
        study.run_experiment(exp["name"], model_path, config_path)

    # Guardar y mostrar resultados
    df = study.save_results()
    study.print_summary()

    print(f"\\n✅ Ablation Study completado!")
    print(f"   Resultados en: {args.output_dir}")


if __name__ == "__main__":
    main()
