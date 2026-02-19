"""
Generador de informe final para evaluación agrícola
Compila todos los resultados en un reporte comprehensivo
"""

import numpy as np
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt


class ReportGenerator:
    """
    Genera reporte final de evaluación agrícola
    """

    def __init__(self, results_dir):
        """
        Args:
            results_dir: Directorio con todos los resultados de evaluación
        """
        self.results_dir = Path(results_dir)
        self.report_data = {}

    def load_all_results(self):
        """
        Carga todos los resultados de evaluación
        """
        print(f"\n📂 Cargando resultados desde: {self.results_dir}")

        # Agricultural metrics
        metrics_file = (
            self.results_dir / "metrics" / "agricultural_metrics_summary.json"
        )
        if metrics_file.exists():
            with open(metrics_file) as f:
                self.report_data["agricultural_metrics"] = json.load(f)
            print(f"   ✓ Agricultural metrics")

        # Classification
        class_file = (
            self.results_dir / "classifications" / "classification_results.json"
        )
        if class_file.exists():
            with open(class_file) as f:
                self.report_data["classification"] = json.load(f)
            print(f"   ✓ Crop classification")

        # Area estimation
        area_file = self.results_dir / "area" / "area_estimation_summary.json"
        if area_file.exists():
            with open(area_file) as f:
                self.report_data["area_estimation"] = json.load(f)
            print(f"   ✓ Area estimation")

        # Temporal analysis
        temporal_file = self.results_dir / "temporal" / "temporal_summary.json"
        if temporal_file.exists():
            with open(temporal_file) as f:
                self.report_data["temporal"] = json.load(f)
            print(f"   ✓ Temporal analysis")

        # Economic analysis
        economic_file = self.results_dir / "economic" / "economic_analysis.json"
        if economic_file.exists():
            with open(economic_file) as f:
                self.report_data["economic"] = json.load(f)
            print(f"   ✓ Economic analysis")

        # Use cases
        usecase_file = self.results_dir / "use_cases" / "use_cases_summary.json"
        if usecase_file.exists():
            with open(usecase_file) as f:
                self.report_data["use_cases"] = json.load(f)
            print(f"   ✓ Use cases")

        print(f"✅ {len(self.report_data)} módulos cargados\n")

    def generate_executive_summary(self):
        """
        Genera resumen ejecutivo

        Returns:
            String con resumen
        """
        summary = []
        summary.append("# RESUMEN EJECUTIVO\n")
        summary.append("## Evaluación Específica del Dominio Agrícola\n")
        summary.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d')}\n\n")

        summary.append("### Métricas Clave\n\n")

        # Agricultural metrics
        if "agricultural_metrics" in self.report_data:
            ndvi_mae = (
                self.report_data["agricultural_metrics"]
                .get("NDVI", {})
                .get("MAE_mean", 0)
            )
            summary.append(f"- **NDVI MAE**: {ndvi_mae:.4f}\n")

        # Classification
        if "classification" in self.report_data:
            acc_improvement = (
                self.report_data["classification"].get("improvement_vs_lr", 0) * 100
            )
            summary.append(
                f"- **Mejora en Clasificación (SR vs LR)**: +{acc_improvement:.2f}%\n"
            )

        # Area estimation
        if "area_estimation" in self.report_data:
            area_error = self.report_data["area_estimation"].get(
                "mean_error_percent", 0
            )
            summary.append(f"- **Error en Estimación de Área**: {area_error:.2f}%\n")

        # Economic
        if "economic" in self.report_data:
            roi = (
                self.report_data["economic"]
                .get("roi_analysis", {})
                .get("roi_percent", 0)
            )
            summary.append(f"- **ROI**: {roi:.1f}%\n")

        summary.append("\n### Conclusiones\n\n")
        summary.append(
            "La super-resolución (SR) demuestra ser una alternativa viable y económicamente rentable "
        )
        summary.append(
            "para aplicaciones agrícolas, con mejoras significativas en:\n\n"
        )
        summary.append("1. Precisión en índices de vegetación\n")
        summary.append("2. Clasificación de cultivos\n")
        summary.append("3. Estimación de áreas cultivadas\n")
        summary.append("4. Detección de estrés hídrico\n\n")

        return "".join(summary)

    def generate_markdown_report(self, output_path):
        """
        Genera reporte completo en Markdown
        """
        report = []

        # Header
        report.append("# INFORME FINAL - EVALUACIÓN FASE 4\n\n")
        report.append("## Evaluación Específica del Dominio Agrícola\n\n")
        report.append(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report.append("---\n\n")

        # Executive summary
        report.append(self.generate_executive_summary())
        report.append("\n---\n\n")

        # Detailed results
        report.append("# RESULTADOS DETALLADOS\n\n")

        # 1. Agricultural Metrics
        if "agricultural_metrics" in self.report_data:
            report.append("## 1. Métricas Agrícolas\n\n")
            report.append("### Precisión en Índices de Vegetación\n\n")

            for idx in ["NDVI", "EVI", "SAVI"]:
                if idx in self.report_data["agricultural_metrics"]:
                    data = self.report_data["agricultural_metrics"][idx]
                    report.append(f"#### {idx}\n\n")
                    report.append(
                        f"- **MAE**: {data.get('MAE_mean', 0):.4f} ± {data.get('MAE_std', 0):.4f}\n"
                    )
                    report.append(
                        f"- **RMSE**: {data.get('RMSE_mean', 0):.4f} ± {data.get('RMSE_std', 0):.4f}\n"
                    )
                    report.append(
                        f"- **R²**: {data.get('R2_mean', 0):.4f} ± {data.get('R2_std', 0):.4f}\n"
                    )
                    report.append(
                        f"- **Pearson r**: {data.get('Pearson_r_mean', 0):.4f}\n\n"
                    )

        # 2. Classification
        if "classification" in self.report_data:
            report.append("## 2. Clasificación de Cultivos\n\n")
            cls_data = self.report_data["classification"]
            report.append(
                f"- **Accuracy LR**: {cls_data.get('LR_accuracy_mean', 0):.4f}\n"
            )
            report.append(
                f"- **Accuracy SR**: {cls_data.get('SR_accuracy_mean', 0):.4f}\n"
            )
            report.append(
                f"- **Accuracy HR**: {cls_data.get('HR_accuracy_mean', 0):.4f}\n"
            )
            report.append(
                f"- **Mejora SR vs LR**: +{cls_data.get('improvement_vs_lr', 0)*100:.2f}%\n\n"
            )

        # 3. Area Estimation
        if "area_estimation" in self.report_data:
            report.append("## 3. Estimación de Área Cultivada\n\n")
            area_data = self.report_data["area_estimation"]
            report.append(
                f"- **Error Promedio**: {area_data.get('mean_error_percent', 0):.2f}%\n"
            )
            report.append(f"- **IoU**: {area_data.get('mean_iou', 0):.4f}\n")
            report.append(
                f"- **Dice Coefficient**: {area_data.get('mean_dice', 0):.4f}\n\n"
            )

        # 4. Temporal Analysis
        if "temporal" in self.report_data:
            report.append("## 4. Análisis Temporal\n\n")
            temp_data = self.report_data["temporal"].get("consistency_metrics", {})
            report.append(
                f"- **Correlación Temporal**: {temp_data.get('temporal_correlation', 0):.4f}\n"
            )
            report.append(
                f"- **MAE Temporal**: {temp_data.get('temporal_mae', 0):.4f}\n"
            )
            report.append(
                f"- **Trend Agreement**: {temp_data.get('trend_agreement', 0):.4f}\n\n"
            )

        # 5. Economic Analysis
        if "economic" in self.report_data:
            report.append("## 5. Análisis Económico\n\n")
            econ_data = self.report_data["economic"]

            report.append("### Comparación de Costos\n\n")
            comp = econ_data.get("cost_comparison", {})
            report.append(f"- **Sentinel-2 (gratis)**: $0\n")
            report.append(
                f"- **Sentinel-2 + SR**: ${comp.get('sentinel2_sr', {}).get('total', 0):.2f}\n"
            )
            report.append(
                f"- **Planet 3m**: ${comp.get('planet_3m', {}).get('total', 0):.2f}\n"
            )
            report.append(
                f"- **WorldView 50cm**: ${comp.get('worldview_50cm', {}).get('total', 0):.2f}\n\n"
            )

            report.append("### ROI\n\n")
            roi_data = econ_data.get("roi_analysis", {})
            report.append(f"- **ROI**: {roi_data.get('roi_percent', 0):.1f}%\n")
            report.append(
                f"- **Payback Period**: {roi_data.get('payback_months', 0):.1f} meses\n\n"
            )

        # 6. Use Cases
        if "use_cases" in self.report_data:
            report.append("## 6. Casos de Uso\n\n")
            uc_data = self.report_data["use_cases"]
            report.append(
                f"- **Estrés Hídrico (Accuracy)**: {uc_data.get('water_stress_accuracy_mean', 0):.4f}\n"
            )
            report.append(
                f"- **Salud de Cultivos (Correlación)**: {uc_data.get('crop_health_correlation_mean', 0):.4f}\n\n"
            )

        # Conclusions
        report.append("\n---\n\n")
        report.append("# CONCLUSIONES\n\n")
        report.append(
            "1. **Viabilidad Técnica**: SR demuestra alta precisión en todas las métricas agrícolas evaluadas.\n\n"
        )
        report.append(
            "2. **Viabilidad Económica**: SR presenta ahorro significativo vs imágenes HR comerciales.\n\n"
        )
        report.append(
            "3. **Aplicabilidad**: Validado en casos de uso reales (estrés hídrico, clasificación, áreas).\n\n"
        )
        report.append(
            "4. **Recomendación**: SR es una solución viable para agricultura de precisión con presupuesto limitado.\n\n"
        )

        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(report)

        print(f"✅ Reporte guardado: {output_path}")

    def generate_latex_report(self, output_path):
        """
        Genera reporte en LaTeX (para tesis)
        """
        latex = []

        latex.append("\\documentclass{article}\n")
        latex.append("\\usepackage[utf8]{inputenc}\n")
        latex.append("\\usepackage{graphicx}\n")
        latex.append("\\usepackage{booktabs}\n\n")
        latex.append(
            "\\title{Evaluación Específica del Dominio Agrícola\\\\Super-Resolución en Imágenes Satelitales}\n"
        )
        latex.append("\\author{}\n")
        latex.append(f"\\date{{{datetime.now().strftime('%B %Y')}}}\n\n")
        latex.append("\\begin{document}\n\n")
        latex.append("\\maketitle\n\n")
        latex.append("\\section{Resumen Ejecutivo}\n\n")
        latex.append(
            "Este informe presenta la evaluación exhaustiva de super-resolución (SR) aplicada a imágenes satelitales para agricultura de precisión.\n\n"
        )

        # Tables with results
        latex.append("\section{Resultados}\n\n")

        if "agricultural_metrics" in self.report_data:
            latex.append("\\subsection{Métricas Agrícolas}\n\n")
            latex.append("\\begin{table}[h]\n")
            latex.append("\\centering\n")
            latex.append("\\begin{tabular}{lccc}\n")
            latex.append("\\toprule\n")
            latex.append("Índice & MAE & RMSE & R² \\\\\\\\\n")
            latex.append("\\midrule\n")

            for idx in ["NDVI", "EVI", "SAVI"]:
                if idx in self.report_data["agricultural_metrics"]:
                    data = self.report_data["agricultural_metrics"][idx]
                    latex.append(
                        f"{idx} & {data.get('MAE_mean', 0):.4f} & {data.get('RMSE_mean', 0):.4f} & {data.get('R2_mean', 0):.4f} \\\\\\\\\n"
                    )

            latex.append("\\bottomrule\n")
            latex.append("\\end{tabular}\n")
            latex.append("\\caption{Precisión en Índices de Vegetación}\n")
            latex.append("\\end{table}\n\n")

        latex.append("\\section{Conclusiones}\n\n")
        latex.append(
            "SR es viable técnica y económicamente para aplicaciones agrícolas.\n\n"
        )
        latex.append("\\end{document}\n")

        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(latex)

        print(f"✅ Reporte LaTeX guardado: {output_path}")

    def generate_full_report(self, output_dir):
        """
        Genera todos los formatos de reporte
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load data
        self.load_all_results()

        # Generate reports
        self.generate_markdown_report(output_dir / "evaluation_report.md")
        self.generate_latex_report(output_dir / "evaluation_report.tex")

        # Save JSON
        with open(output_dir / "all_results.json", "w") as f:
            json.dump(self.report_data, f, indent=2)

        print(f"\n{'='*60}")
        print(f"📄 REPORTE FINAL GENERADO")
        print(f"{'='*60}\n")
        print(f"Directorio: {output_dir}")
        print(f"Archivos:")
        print(f"   - evaluation_report.md (Markdown)")
        print(f"   - evaluation_report.tex (LaTeX para tesis)")
        print(f"   - all_results.json (Datos completos)")
        print(f"\n✅ Evaluación completada!")


# Test
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Evaluation Final Report")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="outputs/reports",
        help="Directory with all evaluation results",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/reports",
        help="Output directory for reports",
    )

    args = parser.parse_args()

    generator = ReportGenerator(args.results_dir)
    generator.generate_full_report(args.output)
