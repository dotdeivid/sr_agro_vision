"""
Análisis económico: Comparación de costos HR vs SR
Evalúa viabilidad económica de SR
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict
import json


class EconomicAnalyzer:
    """
    Analiza viabilidad económica de SR vs imágenes HR
    """

    def __init__(self):
        # Costos aproximados (USD per km²)
        self.costs = {
            "sentinel2": 0,  # Gratis
            "planet_3m": 5.0,  # Planet 3m resolution
            "worldview_50cm": 30.0,  # WorldView alta resolución
            "sr_processing": {
                "gpu_hour": 0.50,  # GPU cloud cost
                "storage_per_gb": 0.03,  # Storage mensual
                "processing_time_per_image": 0.1,  # horas
            },
        }

    def calculate_sr_cost(self, n_images, area_km2=100):
        """
        Calcula costo de procesamiento SR

        Args:
            n_images: Número de imágenes a procesar
            area_km2: Área cubierta en km²

        Returns:
            Dict con desglose de costos
        """
        processing_time = (
            n_images * self.costs["sr_processing"]["processing_time_per_image"]
        )
        gpu_cost = processing_time * self.costs["sr_processing"]["gpu_hour"]

        # Storage (asumiendo 100MB por imagen SR)
        storage_gb = n_images * 0.1
        storage_cost_monthly = (
            storage_gb * self.costs["sr_processing"]["storage_per_gb"]
        )

        total = gpu_cost + storage_cost_monthly

        return {
            "gpu_cost": gpu_cost,
            "storage_cost_monthly": storage_cost_monthly,
            "total": total,
            "cost_per_image": total / n_images if n_images > 0 else 0,
            "cost_per_km2": total / area_km2 if area_km2 > 0 else 0,
        }

    def calculate_hr_satellite_cost(
        self, n_images, area_km2=100, resolution_type="planet_3m"
    ):
        """
        Calcula costo de imágenes HR satelitales

        Args:
            n_images: Número de imágenes
            area_km2: Área
            resolution_type: 'planet_3m' o 'worldview_50cm'

        Returns:
            Dict con costos
        """
        cost_per_km2 = self.costs.get(resolution_type, self.costs["planet_3m"])

        total = n_images * area_km2 * cost_per_km2

        return {
            "resolution_type": resolution_type,
            "cost_per_km2": cost_per_km2,
            "total": total,
            "cost_per_image": total / n_images if n_images > 0 else 0,
        }

    def compare_alternatives(self, n_images, area_km2=100):
        """
        Compara costos de diferentes alternativas

        Returns:
            Dict con comparación
        """
        # SR (Sentinel-2 gratis + processing)
        sr_cost = self.calculate_sr_cost(n_images, area_km2)

        # Planet 3m
        planet_cost = self.calculate_hr_satellite_cost(n_images, area_km2, "planet_3m")

        # WorldView 50cm
        worldview_cost = self.calculate_hr_satellite_cost(
            n_images, area_km2, "worldview_50cm"
        )

        comparison = {
            "sentinel2_free": {
                "total": 0,
                "description": "Sentinel-2 10m (gratis, sin SR)",
            },
            "sentinel2_sr": {
                "total": sr_cost["total"],
                "breakdown": sr_cost,
                "description": "Sentinel-2 + SR processing",
            },
            "planet_3m": {
                "total": planet_cost["total"],
                "breakdown": planet_cost,
                "description": "Planet 3m resolution",
            },
            "worldview_50cm": {
                "total": worldview_cost["total"],
                "breakdown": worldview_cost,
                "description": "WorldView 50cm resolution",
            },
        }

        # Savings
        comparison["savings_vs_planet"] = planet_cost["total"] - sr_cost["total"]
        comparison["savings_vs_worldview"] = worldview_cost["total"] - sr_cost["total"]
        comparison["savings_percent_planet"] = (
            (comparison["savings_vs_planet"] / planet_cost["total"] * 100)
            if planet_cost["total"] > 0
            else 0
        )
        comparison["savings_percent_worldview"] = (
            (comparison["savings_vs_worldview"] / worldview_cost["total"] * 100)
            if worldview_cost["total"] > 0
            else 0
        )

        return comparison

    def calculate_roi(self, n_images, area_km2, yield_improvement_percent=5):
        """
        Calcula ROI considerando mejora en rendimiento de cultivos

        Args:
            n_images: Número de imágenes/monitoreos
            area_km2: Área cultivada
            yield_improvement_percent: Mejora en rendimiento por mejor monitoreo

        Returns:
            Dict con ROI
        """
        # Supuestos económicos (ajustar según cultivo)
        yield_value_per_ha = 1000  # USD/ha (ejemplo: soja)
        area_ha = area_km2 * 100

        # Valor total de producción
        total_production_value = area_ha * yield_value_per_ha

        # Mejora por mejor monitoreo
        value_improvement = total_production_value * (yield_improvement_percent / 100)

        # Costo SR
        sr_cost = self.calculate_sr_cost(n_images, area_km2)["total"]

        # ROI
        roi = ((value_improvement - sr_cost) / sr_cost * 100) if sr_cost > 0 else 0
        payback_months = (
            (sr_cost / value_improvement * 12) if value_improvement > 0 else 999
        )

        return {
            "production_value": total_production_value,
            "value_improvement": value_improvement,
            "sr_cost": sr_cost,
            "net_benefit": value_improvement - sr_cost,
            "roi_percent": roi,
            "payback_months": payback_months,
        }

    def visualize_cost_comparison(self, n_images, area_km2, output_path):
        """
        Visualiza comparación de costos
        """
        comparison = self.compare_alternatives(n_images, area_km2)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Plot 1: Comparación de costos
        alternatives = [
            "Sentinel-2\n(Free)",
            f"Sentinel-2\n+ SR",
            "Planet\n3m",
            "WorldView\n50cm",
        ]
        costs = [
            comparison["sentinel2_free"]["total"],
            comparison["sentinel2_sr"]["total"],
            comparison["planet_3m"]["total"],
            comparison["worldview_50cm"]["total"],
        ]
        colors = ["green", "orange", "blue", "red"]

        axes[0].bar(alternatives, costs, color=colors, alpha=0.7)
        axes[0].set_ylabel("Cost (USD)")
        axes[0].set_title(f"Cost Comparison\n{n_images} images, {area_km2} km²")
        axes[0].grid(True, axis="y", alpha=0.3)

        # Añadir valores
        for i, cost in enumerate(costs):
            axes[0].text(i, cost, f"${cost:.2f}", ha="center", va="bottom")

        # Plot 2: Savings
        savings_labels = ["vs Planet", "vs WorldView"]
        savings_values = [
            comparison["savings_percent_planet"],
            comparison["savings_percent_worldview"],
        ]

        axes[1].barh(savings_labels, savings_values, color=["blue", "red"], alpha=0.7)
        axes[1].set_xlabel("Savings (%)")
        axes[1].set_title("SR Cost Savings")
        axes[1].grid(True, axis="x", alpha=0.3)

        # Añadir valores
        for i, saving in enumerate(savings_values):
            axes[1].text(
                saving, i, f"{saving:.1f}%", ha="left", va="center", fontsize=12
            )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"✅ Visualización guardada: {output_path}")

    def generate_report(self, n_images, area_km2, output_dir):
        """
        Genera reporte económico completo
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Comparación
        comparison = self.compare_alternatives(n_images, area_km2)

        # ROI
        roi = self.calculate_roi(n_images, area_km2)

        # Visualización
        self.visualize_cost_comparison(
            n_images, area_km2, output_dir / "cost_comparison.png"
        )

        # Guardar JSON
        report = {
            "params": {"n_images": n_images, "area_km2": area_km2},
            "cost_comparison": comparison,
            "roi_analysis": roi,
        }

        with open(output_dir / "economic_analysis.json", "w") as f:
            json.dump(report, f, indent=2)

        # Imprimir resumen
        print(f"\n{'='*60}")
        print("💰 ANÁLISIS ECONÓMICO")
        print(f"{'='*60}\n")
        print(f"Parámetros:")
        print(f"   Imágenes: {n_images}")
        print(f"   Área: {area_km2} km²")
        print(f"\nCostos:")
        print(f"   Sentinel-2 (gratis): $0")
        print(f"   Sentinel-2 + SR: ${comparison['sentinel2_sr']['total']:.2f}")
        print(f"   Planet 3m: ${comparison['planet_3m']['total']:.2f}")
        print(f"   WorldView 50cm: ${comparison['worldview_50cm']['total']:.2f}")
        print(f"\nAhorro con SR:")
        print(
            f"   vs Planet: ${comparison['savings_vs_planet']:.2f} ({comparison['savings_percent_planet']:.1f}%)"
        )
        print(
            f"   vs WorldView: ${comparison['savings_vs_worldview']:.2f} ({comparison['savings_percent_worldview']:.1f}%)"
        )
        print(f"\nROI:")
        print(f"   ROI: {roi['roi_percent']:.1f}%")
        print(f"   Payback: {roi['payback_months']:.1f} meses")

        print(f"\n✅ Reporte guardado en: {output_dir}")

        return report


# Test
if __name__ == "__main__":
    analyzer = EconomicAnalyzer()
    report = analyzer.generate_report(
        n_images=12, area_km2=100, output_dir="outputs/reports/economic"
    )
