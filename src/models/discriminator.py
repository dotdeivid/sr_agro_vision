"""
Discriminador PatchGAN para SR
Distingue entre imágenes SR y HR reales
"""
import torch
import torch.nn as nn


class PatchGANDiscriminator(nn.Module):
    """
    Discriminador tipo PatchGAN para imágenes multiespectrales
    Clasifica patches de 70×70 como real/fake
    """
    
    def __init__(self, num_channels=4, ndf=64):
        """
        Args:
            num_channels: Canales de entrada (4 para RGB+NIR)
            ndf: Número de filtros base
        """
        super().__init__()
        
        # Arquitectura PatchGAN
        self.model = nn.Sequential(
            # Capa 1: [4, 256, 256] → [64, 128, 128]
            nn.Conv2d(num_channels, ndf, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Capa 2: [64, 128, 128] → [128, 64, 64]
            nn.Conv2d(ndf, ndf * 2, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Capa 3: [128, 64, 64] → [256, 32, 32]
            nn.Conv2d(ndf * 2, ndf * 4, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Capa 4: [256, 32, 32] → [512, 31, 31]
            nn.Conv2d(ndf * 4, ndf * 8, kernel_size=4, stride=1, padding=1),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Capa final: [512, 31, 31] → [1, 30, 30] (patch predictions)
            nn.Conv2d(ndf * 8, 1, kernel_size=4, stride=1, padding=1)
        )
    
    def forward(self, x):
        """
        Args:
            x: [B, C, H, W] imagen
        
        Returns:
            [B, 1, 30, 30] predicciones por patch (real/fake)
        """
        return self.model(x)


class SpectralDiscriminator(nn.Module):
    """
    Discriminador que evalúa consistencia espectral
    Específico para imágenes multiespectrales
    """
    
    def __init__(self, num_channels=4):
        super().__init__()
        
        # Procesamiento por canal (evalúa cada banda)
        self.channel_conv = nn.Conv2d(num_channels, 64, kernel_size=1)
        
        # Discriminador global
        self.global_discriminator = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(512, 1)
        )
    
    def forward(self, x):
        x = self.channel_conv(x)
        return self.global_discriminator(x)


# Test
if __name__ == "__main__":
    print("Testing PatchGAN Discriminator...")
    
    disc = PatchGANDiscriminator(num_channels=4, ndf=64)
    
    # Count parameters
    num_params = sum(p.numel() for p in disc.parameters())
    print(f"Parameters: {num_params:,}")
    
    # Test forward pass
    x = torch.randn(2, 4, 256, 256)
    with torch.no_grad():
        y = disc(x)
    
    print(f"Input: {x.shape}")
    print(f"Output: {y.shape}")
    print(f"Output range: [{y.min():.2f}, {y.max():.2f}]")
    
    print("\n✅ Discriminator test passed!")
