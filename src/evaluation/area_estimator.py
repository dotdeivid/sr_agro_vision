"""
Estimación de área cultivada
Compara precisión de SR vs HR en medición de áreas
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, Tuple


class AreaEstimator:
    """
    Estima área cultivada a partir de imágenes satelitales
    """

    def __init__(self, gsd_meters=10.0):
        """
        Args:
            gsd_meters: Ground Sample Distance en metros (10m para Sentinel-2)
        """
        self.gsd = gsd_meters
        self.pixel_area_m2 = gsd_meters**2
        self.pixel_area_ha = self.pixel_area_m2 / 10000  # Hectáreas

    def create_vegetation_mask(self, image, ndvi_threshold=0.3):
        """
        Crea máscara de vegetación usando NDVI

        Args:
            image: [C, H, W] con [R, G, B, NIR]
            ndvi_threshold: Umbral para considerar vegetación

        Returns:
            mask: [H, W] binary mask
        """
        red = image[0]
        nir = image[3]

        # Calcular NDVI
        denominator = nir + red
        denominator = np.where(denominator == 0, 1e-8, denominator)
        ndvi = (nir - red) / denominator

        # Crear máscara
        mask = (ndvi > ndvi_threshold).astype(np.uint8)

        return mask

    def calculate_area(self, mask):
        """
        Calcula área en píxeles, m² y hectáreas

        Args:
            mask: [H, W] binary mask

        Returns:
            Dict con áreas en diferentes unidades
        """
        pixel_count = np.sum(mask)
        area_m2 = pixel_count * self.pixel_area_m2
        area_ha = pixel_count * self.pixel_area_ha

        return {
            "pixels": int(pixel_count),
            "area_m2": float(area_m2),
            "area_ha": float(area_ha),
        }

    def compare_areas(self, sr_img, hr_img, ndvi_threshold=0.3):
        """
        Compara estimación de área entre SR y HR

        Args:
            sr_img: Imagen SR [C, H, W]
            hr_img: Imagen HR ground truth [C, H, W]
            ndvi_threshold: Umbral NDVI

        Returns:
            Dict con métricas de comparación
        """
        # Crear máscaras
        mask_sr = self.create_vegetation_mask(sr_img, ndvi_threshold)
        mask_hr = self.create_vegetation_mask(hr_img, ndvi_threshold)

        # Calcular áreas
        area_sr = self.calculate_area(mask_sr)
        area_hr = self.calculate_area(mask_hr)

        # Errores
        error_pixels = int(area_sr["pixels"] - area_hr["pixels"])
        error_ha = float(area_sr["area_ha"] - area_hr["area_ha"])
        error_percent = (
            (error_ha / area_hr["area_ha"] * 100) if area_hr["area_ha"] > 0 else 0
        )

        # Métricas de overlap
        intersection = np.sum(mask_sr & mask_hr)
        union = np.sum(mask_sr | mask_hr)
        iou = intersection / union if union > 0 else 0

        dice = (
            2 * intersection / (np.sum(mask_sr) + np.sum(mask_hr))
            if (np.sum(mask_sr) + np.sum(mask_hr)) > 0
            else 0
        )

        return {
            "sr_area_ha": area_sr["area_ha"],
            "hr_area_ha": area_hr["area_ha"],
            "error_ha": error_ha,
            "error_percent": error_percent,
            "iou": iou,
            "dice": dice,
            "mask_sr": mask_sr,
            "mask_hr": mask_hr,
        }

    def evaluate_batch(self, sr_dir, hr_dir, output_dir, ndvi_threshold=0.3):
        """
        Evalúa batch de imágenes

        Args:
            sr_dir: Directorio con imágenes SR (.npy)
            hr_dir: Directorio con imágenes HR (.npy)
            output_dir: Directorio para resultados
            ndvi_threshold: Umbral NDVI
        """
        sr_dir = Path(sr_dir)
        hr_dir = Path(hr_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Buscar imágenes
        sr_files = sorted(list(sr_dir.glob("*.npy")))

        all_results = []

        print(f"\n📏 Evaluando áreas en {len(sr_files)} imágenes...")

        for sr_file in sr_files:
            hr_file = hr_dir / sr_file.name

            if not hr_file.exists():
                continue

            # Cargar
            sr_img = np.load(sr_file)
            hr_img = np.load(hr_file)

            # Comparar
            result = self.compare_areas(sr_img, hr_img, ndvi_threshold)
            result["filename"] = sr_file.name

            all_results.append(result)

            # Visualizar
            self._visualize_masks(
                result["mask_sr"],
                result["mask_hr"],
                output_dir / f"masks_{sr_file.stem}.png",
            )

        # Resumen
        self._print_summary(all_results)

        # Guardar
        self._save_results(all_results, output_dir)

        return all_results

    def _visualize_masks(self, mask_sr, mask_hr, output_path):
        """Visualiza máscaras SR vs HR"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # SR mask
        axes[0].imshow(mask_sr, cmap="Greens")
        axes[0].set_title("SR Vegetation Mask")
        axes[0].axis("off")

        # HR mask
        axes[1].imshow(mask_hr, cmap="Greens")
        axes[1].set_title("HR Vegetation Mask (GT)")
        axes[1].axis("off")

        # Diferencia
        diff = np.abs(mask_sr.astype(float) - mask_hr.astype(float))
        axes[2].imshow(diff, cmap="hot")
        axes[2].set_title("Difference")
        axes[2].axis("off")

        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        plt.close()

    def _print_summary(self, results):
        """Imprime resumen de resultados"""
        print(f"\n{'='*60}")
        print("📊 RESULTADOS ESTIMACIÓN DE ÁREA")
        print(f"{'='*60}\n")

        # Verificar si hay resultados
        if not results:
            print("⚠️  No hay datos para evaluar")
            print("   Estimación de área requiere:")
            print("   - Imágenes multiespectrales con banda NIR")
            print("   - O dataset específico con máscaras de vegetación\n")
            return

        errors_ha = [r["error_ha"] for r in results]
        errors_percent = [abs(r["error_percent"]) for r in results]
        ious = [r["iou"] for r in results]
        dices = [r["dice"] for r in results]

        print(f"Error Absoluto (ha):")
        print(f"   Mean: {np.mean(np.abs(errors_ha)):.2f} ha")
        print(f"   Std:  {np.std(errors_ha):.2f} ha")

        print(f"\nError Relativo (%):")
        print(f"   Mean: {np.mean(errors_percent):.2f}%")
        print(f"   Std:  {np.std(errors_percent):.2f}%")

        print(f"\nIoU (Overlap):")
        print(f"   Mean: {np.mean(ious):.4f}")

        print(f"\nDice Coefficient:")
        print(f"   Mean: {np.mean(dices):.4f}")

    def _save_results(self, results, output_dir):
        """Guarda resultados en JSON"""
        import json

        # Verificar si hay resultados
        if not results:
            # Crear archivo vacío indicando que no hay datos
            summary = {
                "note": "No data available for RGB datasets",
                "mean_error_ha": 0,
                "mean_error_percent": 0,
                "mean_iou": 0,
                "mean_dice": 0,
            }

            with open(output_dir / "area_estimation_summary.json", "w") as f:
                json.dump(summary, f, indent=2)

            print(f"\n✅ Resultados guardados en: {output_dir}")
            return

        # Remover máscaras para JSON
        results_json = []
        for r in results:
            r_copy = r.copy()
            r_copy.pop("mask_sr", None)
            r_copy.pop("mask_hr", None)
            results_json.append(r_copy)

        with open(output_dir / "area_estimation_results.json", "w") as f:
            json.dump(results_json, f, indent=2)

        # Resumen
        summary = {
            "mean_error_ha": float(np.mean([abs(r["error_ha"]) for r in results])),
            "mean_error_percent": float(
                np.mean([abs(r["error_percent"]) for r in results])
            ),
            "mean_iou": float(np.mean([r["iou"] for r in results])),
            "mean_dice": float(np.mean([r["dice"] for r in results])),
        }

        with open(output_dir / "area_estimation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Resultados guardados en: {output_dir}")


# Test
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Area Estimation")
    parser.add_argument("--sr-dir", type=str, required=True)
    parser.add_argument("--hr-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="outputs/reports/area")
    parser.add_argument(
        "--gsd", type=float, default=10.0, help="Ground sample distance (meters)"
    )
    parser.add_argument("--ndvi-threshold", type=float, default=0.3)

    args = parser.parse_args()

    estimator = AreaEstimator(gsd_meters=args.gsd)
    results = estimator.evaluate_batch(
        args.sr_dir, args.hr_dir, args.output_dir, args.ndvi_threshold
    )
