"""
Entrenamiento GAN para super-resolución satelital
Generator: ESPCN o SwinIR
Discriminator: PatchGAN
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
from src.models.discriminator import PatchGANDiscriminator
from src.data.dataloader import create_satellite_dataloaders
from src.training.losses import GANLoss, AdversarialLoss
from src.training.metrics_agriculture import AgricultureMetricsTracker
from src.training.metrics import AverageMeter
from src.utils.device import get_device, enable_cudnn_benchmark
from src.utils.checkpoint import save_checkpoint


def train_one_epoch_gan(generator, discriminator, train_loader, 
                        criterion_G, criterion_D, 
                        optimizer_G, optimizer_D, 
                        device, epoch):
    """
    Entrena una época con GAN
    
    Returns:
        dict: Métricas promedio del generador
    """
    generator.train()
    discriminator.train()
    
    loss_g_meter = AverageMeter()
    loss_d_meter = AverageMeter()
    metrics_tracker = AgricultureMetricsTracker()
    
    pbar = tqdm(train_loader, desc=f"Epoch {epoch} [GAN]")
    
    for lr_imgs, hr_imgs in pbar:
        batch_size = lr_imgs.size(0)
        lr_imgs = lr_imgs.to(device)
        hr_imgs = hr_imgs.to(device)
        
        # =================== Train Discriminator ===================
        optimizer_D.zero_grad()
        
        # Generar SR
        with torch.no_grad():
            sr_imgs = generator(lr_imgs)
        
        # Discriminador en HR real
        pred_real = discriminator(hr_imgs)
        loss_real = criterion_D(pred_real, is_real=True)
        
        # Discriminador en SR fake
        pred_fake = discriminator(sr_imgs.detach())
        loss_fake = criterion_D(pred_fake, is_real=False)
        
        # Total Discriminator loss
        loss_D = (loss_real + loss_fake) * 0.5
        loss_D.backward()
        optimizer_D.step()
        
        # =================== Train Generator ===================
        optimizer_G.zero_grad()
        
        # Generar SR
        sr_imgs = generator(lr_imgs)
        
        # Discriminador en SR (queremos que crea que es real)
        pred_sr = discriminator(sr_imgs)
        
        # Generator loss (content + adversarial)
        loss_G, loss_dict_G = criterion_G(sr_imgs, hr_imgs, pred_sr)
        loss_G.backward()
        optimizer_G.step()
        
        # Métricas
        with torch.no_grad():
            metrics_tracker.update(sr_imgs, hr_imgs)
        
        loss_g_meter.update(loss_G.item(), batch_size)
        loss_d_meter.update(loss_D.item(), batch_size)
        
        # Progress bar
        avg_metrics = metrics_tracker.get_averages()
        pbar.set_postfix({
            'G': f'{loss_g_meter.avg:.4f}',
            'D': f'{loss_d_meter.avg:.4f}',
            'PSNR': f'{avg_metrics["psnr"]:.2f}',
            'Adv': f'{loss_dict_G["adversarial"]:.4f}'
        })
    
    avg_metrics = metrics_tracker.get_averages()
    avg_metrics['loss_G'] = loss_g_meter.avg
    avg_metrics['loss_D'] = loss_d_meter.avg
    
    return avg_metrics


def validate_gan(generator, discriminator, val_loader, criterion_G, criterion_D, device):
    """Validación del modelo GAN"""
    generator.eval()
    discriminator.eval()
    
    loss_g_meter = AverageMeter()
    loss_d_meter = AverageMeter()
    metrics_tracker = AgricultureMetricsTracker()
    
    with torch.no_grad():
        for lr_imgs, hr_imgs in val_loader:
            lr_imgs = lr_imgs.to(device)
            hr_imgs = hr_imgs.to(device)
            
            # Generator forward
            sr_imgs = generator(lr_imgs)
            
            # Discriminator predictions
            pred_real = discriminator(hr_imgs)
            pred_sr = discriminator(sr_imgs)
            
            # Losses
            loss_real = criterion_D(pred_real, is_real=True)
            loss_fake = criterion_D(pred_sr, is_real=False)
            loss_D = (loss_real + loss_fake) * 0.5
            
            loss_G, _ = criterion_G(sr_imgs, hr_imgs, pred_sr)
            
            # Métricas
            batch_size = lr_imgs.size(0)
            loss_g_meter.update(loss_G.item(), batch_size)
            loss_d_meter.update(loss_D.item(), batch_size)
            metrics_tracker.update(sr_imgs, hr_imgs)
    
    avg_metrics = metrics_tracker.get_averages()
    avg_metrics['loss_G'] = loss_g_meter.avg
    avg_metrics['loss_D'] = loss_d_meter.avg
    
    return avg_metrics


def main():
    parser = argparse.ArgumentParser(description='GAN Training for Satellite SR')
    parser.add_argument('--config', type=str, required=True, 
                       help='Path to config file')
    args = parser.parse_args()
    
    # Cargar config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Device
    device = get_device()
    enable_cudnn_benchmark()
    print(f"🚀 Usando: {device}")
    
    # Crear Generator
    print("\\n🎨 Creando Generator...")
    generator = ESPCNMultispectral(
        scale_factor=config['model']['scale_factor'],
        num_channels=config['model']['num_channels'],
        num_features=config['model']['num_features']
    ).to(device)
    
    num_params_g = sum(p.numel() for p in generator.parameters())
    print(f"✅ Generator: {num_params_g:,} parámetros")
    
    #  Crear Discriminator
    print("\\n👁️ Creando Discriminator...")
    discriminator = PatchGANDiscriminator(
        num_channels=config['model']['num_channels'],
        ndf=64
    ).to(device)
    
    num_params_d = sum(p.numel() for p in discriminator.parameters())
    print(f"✅ Discriminator: {num_params_d:,} parámetros")
    
    # Dataloaders
    print("\\n🛰️ Cargando datos...")
    train_loader, val_loader = create_satellite_dataloaders(
        lr_train_dir=config["training"]["train_lr_data"],
        hr_train_dir=config["training"]["train_hr_data"],
        lr_val_dir=config["training"]["val_lr_data"],
        hr_val_dir=config["training"]["val_hr_data"],
        batch_size=config["training"]["batch_size"],
        num_channels=config["data"]["num_channels"],
        device=device,
    )
    
    # Loss functions
    criterion_G = GANLoss(
        content_weight=1.0,
        adversarial_weight=0.001,
        device=device
    )
    criterion_D = AdversarialLoss()
    
    # Optimizers
    optimizer_G = optim.Adam(generator.parameters(), 
                             lr=config["training"]["learning_rate"])
    optimizer_D = optim.Adam(discriminator.parameters(),
                             lr=config["training"]["learning_rate"])
    
    # TensorBoard
    log_dir = Path(config["training"]["log_dir"])
    writer = SummaryWriter(log_dir)
    print(f"\\n📊 TensorBoard: {log_dir}")
    
    # Checkpoints
    checkpoint_dir = Path(config["training"]["checkpoint_dir"])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Training loop
    print("\\n🚀 Iniciando entrenamiento GAN...\\n")
    best_psnr = 0.0
    
    for epoch in range(config["training"]["epochs"]):
        print(f"\n{'='*60}")
        print(f"EPOCH {epoch+1}/{config['training']['epochs']}")
        print(f"{'='*60}")
        
        # Train
        train_metrics = train_one_epoch_gan(
            generator, discriminator, train_loader,
            criterion_G, criterion_D,
            optimizer_G, optimizer_D,
            device, epoch + 1
        )
        
        # Log training
        writer.add_scalar('Train/Loss_G', train_metrics['loss_G'], epoch)
        writer.add_scalar('Train/Loss_D', train_metrics['loss_D'], epoch)
        writer.add_scalar('Train/PSNR', train_metrics['psnr'], epoch)
        
        # Validate
        if (epoch + 1) % config["training"]["validate_every"] == 0:
            val_metrics = validate_gan(
                generator, discriminator, val_loader,
                criterion_G, criterion_D, device
            )
            
            print(f"\\n📊 Validation - Loss_G: {val_metrics['loss_G']:.4f} | "
                  f"Loss_D: {val_metrics['loss_D']:.4f} | "
                  f"PSNR: {val_metrics['psnr']:.2f} dB")
            
            # Log validation
            writer.add_scalar('Val/Loss_G', val_metrics['loss_G'], epoch)
            writer.add_scalar('Val/PSNR', val_metrics['psnr'], epoch)
            
            # Save best
            if val_metrics['psnr'] > best_psnr:
                best_psnr = val_metrics['psnr']
                save_path = checkpoint_dir / f'best_psnr_x{config["model"]["scale_factor"]}.pth'
                torch.save(generator.state_dict(), save_path)
                print(f"💾 Mejor modelo guardado: {save_path}")
        
        # Save periodic
        if (epoch + 1) % config["training"]["save_every"] == 0:
            save_path = checkpoint_dir / f'epoch_{epoch+1}.pth'
            torch.save(generator.state_dict(), save_path)
    
    writer.close()
    print(f"\\n✅ Entrenamiento completado! Mejor PSNR: {best_psnr:.2f} dB")


if __name__ == "__main__":
    main()
