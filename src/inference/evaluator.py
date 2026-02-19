"""
Evaluación de modelo en contexto agrícola
Compara SR vs HR vs métodos tradicionales
"""

import torch
import argparse
from pathlib import Path
import numpy as np
import rasterio
from tqdm import tqdm
import sys
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))

from src.models.espcn import ESPCNMultispectral
from src.utils.device import get_device
from src.training.metrics_agro import evaluate_satellite_metrics
from src.utils.ndvi import calculate_ndvi
from scipy.ndimage import zoom


def upscale_bicubic(lr_image, scale_factor):
    """
    Upscale usando interpolación bicúbica (baseline)

    Args:
        lr_image: Array [C, H, W]
        scale_factor: Factor de escalado

    Returns:
        Array [C, H*scale, W*scale]
    """
    c, h, w = lr_image.shape
    sr_image = np.zeros((c, h * scale_factor, w * scale_factor), dtype=lr_image.dtype)

    for i in range(c):
        sr_image[i] = zoom(lr_image[i], scale_factor, order=3)  # order=3 = bicubic

    return sr_image


def visualize_comparison(
    lr_img, bicubic_sr, model_sr, hr_img, output_path, num_channels=4
):
    """
    Crea visualización comparativa de LR, Bicúbico, Modelo SR y HR

    Args:
        lr_img: Imagen LR [C, H, W]
        bicubic_sr: SR bicúbico [C, H, W]
        model_sr: SR del modelo [C, H, W]
        hr_img: Ground truth HR [C, H, W]
        output_path: Ruta para guardar visualización
        num_channels: Número de canales
    """
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))

    # Convertir tensors a numpy si es necesario
    if torch.is_tensor(lr_img):
        lr_img = lr_img.cpu().numpy()
    if torch.is_tensor(bicubic_sr):
        bicubic_sr = bicubic_sr.cpu().numpy()
    if torch.is_tensor(model_sr):
        model_sr = model_sr.cpu().numpy()
    if torch.is_tensor(hr_img):
        hr_img = hr_img.cpu().numpy()

    # Usar RGB (primeros 3 canales) para visualización
    lr_rgb = np.clip(lr_img[:3].transpose(1, 2, 0), 0, 1)
    bicubic_rgb = np.clip(bicubic_sr[:3].transpose(1, 2, 0), 0, 1)
    model_rgb = np.clip(model_sr[:3].transpose(1, 2, 0), 0, 1)
    hr_rgb = np.clip(hr_img[:3].transpose(1, 2, 0), 0, 1)

    # Fila 1: Imágenes RGB
    axes[0, 0].imshow(lr_rgb)
    axes[0, 0].set_title("LR (Input)", fontsize=14, fontweight="bold")
    axes[0, 0].axis("off")

    axes[0, 1].imshow(bicubic_rgb)
    axes[0, 1].set_title("Bicubic SR", fontsize=14, fontweight="bold")
    axes[0, 1].axis("off")

    axes[0, 2].imshow(model_rgb)
    axes[0, 2].set_title("Model SR (ESPCN)", fontsize=14, fontweight="bold")
    axes[0, 2].axis("off")

    axes[0, 3].imshow(hr_rgb)
    axes[0, 3].set_title("HR (Ground Truth)", fontsize=14, fontweight="bold")
    axes[0, 3].axis("off")

    # Fila 2: Mapas NDVI (si hay 4 canales)
    if num_channels >= 4:
        # Calcular NDVI para cada imagen (red=canal 0, NIR=canal 3)
        ndvi_lr = calculate_ndvi(lr_img[0], lr_img[3])
        ndvi_bicubic = calculate_ndvi(bicubic_sr[0], bicubic_sr[3])
        ndvi_model = calculate_ndvi(model_sr[0], model_sr[3])
        ndvi_hr = calculate_ndvi(hr_img[0], hr_img[3])

        # Convertir a numpy
        if torch.is_tensor(ndvi_lr):
            ndvi_lr = ndvi_lr.cpu().numpy()
        if torch.is_tensor(ndvi_bicubic):
            ndvi_bicubic = ndvi_bicubic.cpu().numpy()
        if torch.is_tensor(ndvi_model):
            ndvi_model = ndvi_model.cpu().numpy()
        if torch.is_tensor(ndvi_hr):
            ndvi_hr = ndvi_hr.cpu().numpy()

        # Visualizar NDVI con colormap
        im0 = axes[1, 0].imshow(ndvi_lr, cmap="RdYlGn", vmin=-1, vmax=1)
        axes[1, 0].set_title("NDVI - LR", fontsize=12)
        axes[1, 0].axis("off")

        im1 = axes[1, 1].imshow(ndvi_bicubic, cmap="RdYlGn", vmin=-1, vmax=1)
        axes[1, 1].set_title("NDVI - Bicubic", fontsize=12)
        axes[1, 1].axis("off")

        im2 = axes[1, 2].imshow(ndvi_model, cmap="RdYlGn", vmin=-1, vmax=1)
        axes[1, 2].set_title("NDVI - Model SR", fontsize=12)
        axes[1, 2].axis("off")

        im3 = axes[1, 3].imshow(ndvi_hr, cmap="RdYlGn", vmin=-1, vmax=1)
        axes[1, 3].set_title("NDVI - HR (GT)", fontsize=12)
        axes[1, 3].axis("off")

        # Agregar colorbar
        fig.colorbar(
            im3,
            ax=axes[1, :],
            orientation="horizontal",
            fraction=0.05,
            pad=0.05,
            label="NDVI Value",
        )
    else:
        # Si no hay NIR, ocultar segunda fila
        for ax in axes[1, :]:
            ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def evaluate_on_test_set(
    test_dir,
    model_path,
    num_channels=4,
    scale_factor=4,
    device=None,
    visualize=False,
    output_dir=None,
):
    """
    Evalúa modelo en test set y compara con bicúbico

    Args:
        test_dir: Directorio con imágenes de test (LR y HR)
        model_path: Ruta al modelo
        num_channels: Canales
        scale_factor: Factor de escalado
        device: Dispositivo
        visualize: Si True, genera visualizaciones comparativas
        output_dir: Directorio para guardar visualizaciones
    """
    if device is None:
        device = get_device()

    test_dir = Path(test_dir)
    lr_dir = test_dir / "LR"
    hr_dir = test_dir / "HR"

    # Verificar directorios
    if not lr_dir.exists() or not hr_dir.exists():
        print(f"❌ Directorios LR/HR no encontrados en {test_dir}")
        return

    # Cargar modelo
    print(f"🧠 Cargando modelo: {model_path}")
    model = ESPCNMultispectral(
        scale_factor=scale_factor, num_channels=num_channels, num_features=64
    )
    model.load_state_dict(
        torch.load(model_path, map_location=device, weights_only=True)
    )
    model.to(device)
    model.eval()

    # Buscar imágenes de test
    lr_images = sorted(list(lr_dir.glob("*.npy")))

    if len(lr_images) == 0:
        print(f"⚠️  No se encontraron imágenes .npy en {lr_dir}")
        return

    print(f"📊 Evaluando {len(lr_images)} imágenes...")

    # Métricas acumuladas
    results = {
        "model": {"psnr": [], "ssim": [], "ndvi_mae": [], "sam": []},
        "bicubic": {"psnr": [], "ssim": [], "ndvi_mae": [], "sam": []},
    }

    # Preparar directorio de visualizaciones si es necesario
    if visualize and output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📊 Generando visualizaciones en {output_dir}...")
        # Limitar visualizaciones a las primeras 10 imágenes para no saturar
        max_visualizations = 10
        viz_count = 0

    for idx, lr_path in enumerate(tqdm(lr_images)):
        hr_path = hr_dir / lr_path.name

        if not hr_path.exists():
            continue

        # Cargar LR y HR
        lr_img = np.load(lr_path)  # [C, H, W]
        hr_img = np.load(hr_path)

        # SR con modelo
        lr_tensor = torch.from_numpy(lr_img).unsqueeze(0).float().to(device)

        with torch.no_grad():
            sr_model_tensor = model(lr_tensor)

        sr_model = sr_model_tensor.squeeze(0).cpu()

        # SR con bicubic
        sr_bicubic = upscale_bicubic(lr_img, scale_factor)
        sr_bicubic = torch.from_numpy(sr_bicubic).float()

        # Ground truth
        hr_torch = torch.from_numpy(hr_img).float()

        # Evaluar modelo
        metrics_model = evaluate_satellite_metrics(sr_model, hr_torch)
        results["model"]["psnr"].append(metrics_model["psnr"])
        results["model"]["ssim"].append(metrics_model["ssim"])
        results["model"]["ndvi_mae"].append(metrics_model["ndvi_mae"])
        results["model"]["sam"].append(metrics_model["sam"])

        # Evaluar bicubic
        metrics_bicubic = evaluate_satellite_metrics(sr_bicubic, hr_torch)
        results["bicubic"]["psnr"].append(metrics_bicubic["psnr"])
        results["bicubic"]["ssim"].append(metrics_bicubic["ssim"])
        results["bicubic"]["ndvi_mae"].append(metrics_bicubic["ndvi_mae"])
        results["bicubic"]["sam"].append(metrics_bicubic["sam"])

        # Generar visualización si está habilitado
        if visualize and output_dir and viz_count < max_visualizations:
            viz_path = output_dir / f"comparison_{idx:04d}.png"
            visualize_comparison(
                lr_img,
                sr_bicubic,
                sr_model,
                hr_torch,
                viz_path,
                num_channels=num_channels,
            )
            viz_count += 1

    # Calcular promedios
    print("\n" + "=" * 60)
    print("RESULTADOS DE EVALUACIÓN")
    print("=" * 60)

    print("\n📊 Modelo ESPCN Multispectral:")
    print(
        f"   PSNR: {np.mean(results['model']['psnr']):.2f} ± {np.std(results['model']['psnr']):.2f} dB"
    )
    print(
        f"   SSIM: {np.mean(results['model']['ssim']):.4f} ± {np.std(results['model']['ssim']):.4f}"
    )
    print(
        f"   NDVI MAE: {np.mean(results['model']['ndvi_mae']):.4f} ± {np.std(results['model']['ndvi_mae']):.4f}"
    )
    print(
        f"   SAM: {np.mean(results['model']['sam']):.2f} ± {np.std(results['model']['sam']):.2f}°"
    )

    print("\n📊 Baseline (Bicúbico):")
    print(
        f"   PSNR: {np.mean(results['bicubic']['psnr']):.2f} ± {np.std(results['bicubic']['psnr']):.2f} dB"
    )
    print(
        f"   SSIM: {np.mean(results['bicubic']['ssim']):.4f} ± {np.std(results['bicubic']['ssim']):.4f}"
    )
    print(
        f"   NDVI MAE: {np.mean(results['bicubic']['ndvi_mae']):.4f} ± {np.std(results['bicubic']['ndvi_mae']):.4f}"
    )
    print(
        f"   SAM: {np.mean(results['bicubic']['sam']):.2f} ± {np.std(results['bicubic']['sam']):.2f}°"
    )

    print("\n🎯 Mejora del Modelo vs Baseline:")
    psnr_improvement = np.mean(results["model"]["psnr"]) - np.mean(
        results["bicubic"]["psnr"]
    )
    ssim_improvement = np.mean(results["model"]["ssim"]) - np.mean(
        results["bicubic"]["ssim"]
    )
    ndvi_improvement = np.mean(results["bicubic"]["ndvi_mae"]) - np.mean(
        results["model"]["ndvi_mae"]
    )
    sam_improvement = np.mean(results["bicubic"]["sam"]) - np.mean(
        results["model"]["sam"]
    )

    print(f"   PSNR: {psnr_improvement:+.2f} dB")
    print(f"   SSIM: {ssim_improvement:+.4f}")
    print(f"   NDVI MAE: {ndvi_improvement:+.4f} (menor es mejor)")
    print(f"   SAM: {sam_improvement:+.2f}° (menor es mejor)")

    print("=" * 60)

    # Guardar resultados
    import json

    results_summary = {
        "model": {
            "psnr_mean": float(np.mean(results["model"]["psnr"])),
            "psnr_std": float(np.std(results["model"]["psnr"])),
            "ssim_mean": float(np.mean(results["model"]["ssim"])),
            "ssim_std": float(np.std(results["model"]["ssim"])),
            "ndvi_mae_mean": float(np.mean(results["model"]["ndvi_mae"])),
            "ndvi_mae_std": float(np.std(results["model"]["ndvi_mae"])),
            "sam_mean": float(np.mean(results["model"]["sam"])),
            "sam_std": float(np.std(results["model"]["sam"])),
        },
        "bicubic": {
            "psnr_mean": float(np.mean(results["bicubic"]["psnr"])),
            "psnr_std": float(np.std(results["bicubic"]["psnr"])),
            "ssim_mean": float(np.mean(results["bicubic"]["ssim"])),
            "ssim_std": float(np.std(results["bicubic"]["ssim"])),
            "ndvi_mae_mean": float(np.mean(results["bicubic"]["ndvi_mae"])),
            "ndvi_mae_std": float(np.std(results["bicubic"]["ndvi_mae"])),
            "sam_mean": float(np.mean(results["bicubic"]["sam"])),
            "sam_std": float(np.std(results["bicubic"]["sam"])),
        },
        "num_images": len(lr_images),
    }

    results_path = test_dir.parent / "evaluation_results.json"
    with open(results_path, "w") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n📁 Resultados guardados en: {results_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluar modelo satelital")
    parser.add_argument(
        "--test-dir",
        type=str,
        required=True,
        help="Directorio con test set (debe contener LR/ y HR/)",
    )
    parser.add_argument("--model", type=str, required=True, help="Ruta al modelo .pth")
    parser.add_argument("--channels", type=int, default=4, help="Número de canales")
    parser.add_argument(
        "--scale", type=int, default=4, choices=[2, 4, 8], help="Factor de escalado"
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Generar visualizaciones comparativas"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/visualizations",
        help="Directorio para guardar visualizaciones",
    )

    args = parser.parse_args()

    evaluate_on_test_set(
        args.test_dir,
        args.model,
        num_channels=args.channels,
        scale_factor=args.scale,
        visualize=args.visualize,
        output_dir=args.output_dir,
    )
