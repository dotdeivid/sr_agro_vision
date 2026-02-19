"""
Script de entrenamiento para imágenes satelitales multiespectrales
"""

import torch
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
import yaml
import argparse
from pathlib import Path
from tqdm import tqdm
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.models.espcn import ESPCNMultispectral
from src.data.dataloader import create_satellite_dataloaders
from src.training.losses import get_loss_function, CombinedLoss
from src.training.metrics_agro import AgricultureMetricsTracker
from src.utils.device import get_device, enable_cudnn_benchmark
from src.utils.checkpoint import save_checkpoint


def train_one_epoch(
    model,
    train_loader,
    criterion,
    optimizer,
    device,
    epoch,
    dataset_type="multiespectral",
):
    """
    Entrena una época con métricas

    Args:
        dataset_type: Tipo de dataset ('multiespectral' o 'rgb')

    Returns:
        dict: Métricas promedio de la época
    """
    model.train()

    from src.training.metrics import AverageMeter

    loss_meter = AverageMeter()
    metrics_tracker = AgricultureMetricsTracker(dataset_type=dataset_type)

    pbar = tqdm(train_loader, desc=f"Epoch {epoch}")

    for lr_imgs, hr_imgs in pbar:
        lr_imgs = lr_imgs.to(device)
        hr_imgs = hr_imgs.to(device)

        # Forward pass
        sr_imgs = model(lr_imgs)

        # Calculate loss (handle both simple and combined losses)
        loss_output = criterion(sr_imgs, hr_imgs)
        if isinstance(loss_output, tuple):  # CombinedLoss returns (loss, dict)
            loss, loss_dict = loss_output
        else:  # Simple losses return scalar
            loss = loss_output
            loss_dict = None

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Calcular métricas
        with torch.no_grad():
            metrics_tracker.update(sr_imgs, hr_imgs)

        # Actualizar meters
        batch_size = lr_imgs.size(0)
        loss_meter.update(loss.item(), batch_size)

        # Actualizar progress bar
        avg_metrics = metrics_tracker.get_averages()
        postfix_dict = {
            "loss": f"{loss_meter.avg:.4f}",
            "PSNR": f'{avg_metrics["psnr"]:.2f}',
            "NDVI_MAE": f'{avg_metrics["ndvi_mae"]:.4f}',
        }
        # Add individual loss components if available
        if loss_dict:
            postfix_dict["L1"] = f"{loss_dict['l1']:.4f}"
            postfix_dict["Perc"] = f"{loss_dict['perceptual']:.4f}"
        pbar.set_postfix(postfix_dict)

    avg_metrics = metrics_tracker.get_averages()
    avg_metrics["loss"] = loss_meter.avg

    return avg_metrics


def validate(model, val_loader, criterion, device, dataset_type="multiespectral"):
    """
    Validación del modelo con métricas

    Args:
        dataset_type: Tipo de dataset ('multiespectral' o 'rgb')

    Returns:
        dict: Métricas de validación
    """
    model.eval()

    from src.training.metrics import AverageMeter

    loss_meter = AverageMeter()
    metrics_tracker = AgricultureMetricsTracker(dataset_type=dataset_type)

    with torch.no_grad():
        for lr_imgs, hr_imgs in tqdm(val_loader, desc="Validating"):
            lr_imgs = lr_imgs.to(device)
            hr_imgs = hr_imgs.to(device)

            # Forward pass
            sr_imgs = model(lr_imgs)

            # Handle both simple and combined losses (CombinedLoss returns tuple)
            loss_output = criterion(sr_imgs, hr_imgs)
            if isinstance(loss_output, tuple):
                loss, _ = loss_output
            else:
                loss = loss_output

            # Calcular métricas
            metrics_tracker.update(sr_imgs, hr_imgs)

            # Actualizar meters
            batch_size = lr_imgs.size(0)
            loss_meter.update(loss.item(), batch_size)

    avg_metrics = metrics_tracker.get_averages()
    avg_metrics["loss"] = loss_meter.avg

    return avg_metrics


def train_satellite(config_path):
    """
    Función principal de entrenamiento satelital

    Args:
        config_path: Ruta al archivo de configuración YAML
    """
    # Cargar configuración
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    print("=" * 60)
    print("ENTRENAMIENTO SATELITAL - IMÁGENES MULTIESPECTRALES")
    print("=" * 60)
    print(yaml.dump(config, default_flow_style=False))

    # Setup device
    device = get_device()
    enable_cudnn_benchmark()

    # Crear modelo multiespectral
    print("\n📡 Creando modelo multiespectral...")

    if config["model"]["architecture"] == "ESPCNMultispectral":
        model = ESPCNMultispectral(
            scale_factor=config["model"]["scale_factor"],
            num_channels=config["model"]["num_channels"],
            num_features=config["model"]["num_features"],
        ).to(device)
    elif config["model"]["architecture"] == "SwinIRMultispectral":
        from src.models.swinir import SwinIRMultispectral

        model = SwinIRMultispectral(
            num_channels=config["model"]["num_channels"],
            embed_dim=config["model"]["embed_dim"],
            depths=config["model"]["depths"],
            num_heads=config["model"]["num_heads"],
            window_size=config["model"]["window_size"],
            scale_factor=config["model"]["scale_factor"],
        ).to(device)
    else:
        raise ValueError(
            f"Arquitectura no soportada: {config['model']['architecture']}"
        )

    # Contar parámetros
    num_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Modelo creado: {num_params:,} parámetros")
    print(f"   Canales: {config['model']['num_channels']} (RGB + NIR)")
    print(f"   Scale: x{config['model']['scale_factor']}")

    # Crear dataloaders
    print("\n🛰️ Cargando datos satelitales...")
    train_loader, val_loader = create_satellite_dataloaders(
        lr_train_dir=config["training"]["train_lr_data"],
        hr_train_dir=config["training"]["train_hr_data"],
        lr_val_dir=config["training"]["val_lr_data"],
        hr_val_dir=config["training"]["val_hr_data"],
        batch_size=config["training"]["batch_size"],
        num_channels=config["data"]["num_channels"],
        device=device,
    )
    print(f"✅ Train: {len(train_loader)} batches")
    print(f"✅ Val: {len(val_loader)} batches")

    # Loss y optimizer
    if config["training"]["loss"] == "CombinedLoss":
        print("\n🎨 Usando Perceptual Loss (VGG16)...")
        criterion = CombinedLoss(alpha=1.0, beta=0.006, device=device)
    else:
        criterion = get_loss_function(config["training"]["loss"])
    optimizer = optim.Adam(model.parameters(), lr=config["training"]["learning_rate"])

    # Learning rate scheduler
    if (
        config["training"].get("lr_scheduler")
        and config["training"]["lr_scheduler"]["type"] == "StepLR"
    ):
        scheduler = optim.lr_scheduler.StepLR(
            optimizer,
            step_size=config["training"]["lr_scheduler"]["step_size"],
            gamma=config["training"]["lr_scheduler"]["gamma"],
        )
    elif (
        config["training"].get("lr_scheduler")
        and config["training"]["lr_scheduler"]["type"] == "CosineAnnealingLR"
    ):
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=config["training"]["lr_scheduler"]["T_max"],
        )
    else:
        scheduler = None

    # TensorBoard
    log_dir = (
        Path(config["training"]["log_dir"])
        / f"scale_x{config['model']['scale_factor']}"
    )
    writer = SummaryWriter(log_dir)
    print(f"\n📊 TensorBoard: {log_dir}")

    # Directorio de checkpoints
    checkpoint_dir = Path(config["training"]["checkpoint_dir"])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Detectar tipo de dataset
    dataset_type = config["data"].get("dataset_type", "multiespectral")
    print(f"\n🌿 Dataset type: {dataset_type.upper()}")
    if dataset_type == "multiespectral":
        print("   📡 Métricas agrícolas habilitadas (NDVI, SAM)")
    else:
        print("   🖼️  Métricas estándar únicamente (PSNR, SSIM)")

    # Entrenar
    print("\n🚀 Iniciando entrenamiento...\n")

    best_psnr = 0.0
    best_ndvi_mae = float("inf")
    start_epoch = 0

    for epoch in range(start_epoch, config["training"]["epochs"]):
        print(f"\n{'='*60}")
        print(f"EPOCH {epoch+1}/{config['training']['epochs']}")
        print(f"{'='*60}")

        # Entrenar
        train_metrics = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            epoch + 1,
            dataset_type=dataset_type,
        )

        # Log training
        writer.add_scalar("Train/Loss", train_metrics["loss"], epoch)
        writer.add_scalar("Train/PSNR", train_metrics["psnr"], epoch)
        writer.add_scalar("Train/SSIM", train_metrics["ssim"], epoch)
        writer.add_scalar("Train/NDVI_MAE", train_metrics["ndvi_mae"], epoch)
        writer.add_scalar("Train/SAM", train_metrics["sam"], epoch)
        writer.add_scalar("LR", optimizer.param_groups[0]["lr"], epoch)

        # Validar periódicamente
        if (epoch + 1) % config["training"]["validate_every"] == 0:
            print("\n🔍 Validando...")
            val_metrics = validate(
                model, val_loader, criterion, device, dataset_type=dataset_type
            )

            print(f"\n📊 Resultados Validación:")
            print(f"   Loss: {val_metrics['loss']:.4f}")
            print(f"   PSNR: {val_metrics['psnr']:.2f} dB")
            print(f"   SSIM: {val_metrics['ssim']:.4f}")
            print(f"   NDVI MAE: {val_metrics['ndvi_mae']:.4f} ⭐")
            print(f"   SAM: {val_metrics['sam']:.2f}°")

            # Log validation
            writer.add_scalar("Val/Loss", val_metrics["loss"], epoch)
            writer.add_scalar("Val/PSNR", val_metrics["psnr"], epoch)
            writer.add_scalar("Val/SSIM", val_metrics["ssim"], epoch)
            writer.add_scalar("Val/NDVI_MAE", val_metrics["ndvi_mae"], epoch)
            writer.add_scalar("Val/SAM", val_metrics["sam"], epoch)

            # Guardar mejor modelo (por PSNR)
            if val_metrics["psnr"] > best_psnr:
                best_psnr = val_metrics["psnr"]
                best_path = (
                    checkpoint_dir / f"best_psnr_x{config['model']['scale_factor']}.pth"
                )
                torch.save(model.state_dict(), best_path)
                print(f"✅ Mejor PSNR guardado: {best_psnr:.2f} dB")

            # Guardar mejor modelo (por NDVI MAE)
            if val_metrics["ndvi_mae"] < best_ndvi_mae:
                best_ndvi_mae = val_metrics["ndvi_mae"]
                best_path = (
                    checkpoint_dir / f"best_ndvi_x{config['model']['scale_factor']}.pth"
                )
                torch.save(model.state_dict(), best_path)
                print(f"✅ Mejor NDVI MAE guardado: {best_ndvi_mae:.4f}")

        # Guardar checkpoint periódicamente
        if (epoch + 1) % config["training"]["save_every"] == 0:
            checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch+1}.pth"
            save_checkpoint(
                model, optimizer, epoch + 1, train_metrics["loss"], checkpoint_path
            )

        # Update learning rate
        if scheduler is not None:
            scheduler.step()

    # Guardar modelo final
    final_path = checkpoint_dir / f"final_model_x{config['model']['scale_factor']}.pth"
    torch.save(model.state_dict(), final_path)

    print(f"\n{'='*60}")
    print("✅ ENTRENAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"📦 Modelo final: {final_path}")
    print(f"🏆 Mejor PSNR: {best_psnr:.2f} dB")
    print(f"🌾 Mejor NDVI MAE: {best_ndvi_mae:.4f}")
    print(f"{'='*60}")

    writer.close()


def main(args=None):
    """
    Función main para ser llamada desde main.py o directamente

    Args:
        args: Argumentos parseados (opcional, si None se parsean desde consola)
    """
    if args is None:
        # Si se llama directamente desde consola, parsear argumentos
        parser = argparse.ArgumentParser(description="Entrenar modelo satelital")
        parser.add_argument(
            "--config",
            type=str,
            required=True,
            help="Ruta al archivo de configuración YAML",
        )
        args = parser.parse_args()

    # Ejecutar entrenamiento
    train_satellite(args.config)


if __name__ == "__main__":
    main()
