"""
ESPCN adaptado para imágenes multiespectrales (4+ canales)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ESPCNMultispectral(nn.Module):
    """
    ESPCN adaptado para N canales (no solo RGB)

    Modificaciones:
    - Input/output pueden ser 4+ canales
    - Mantiene información espectral durante procesamiento
    """

    def __init__(self, scale_factor=2, num_channels=4, num_features=64):
        """
        Args:
            scale_factor: Factor de escalado (2, 3, 4)
            num_channels: Canales de entrada/salida (4 para RGB+NIR)
            num_features: Features en capas ocultas
        """
        super(ESPCNMultispectral, self).__init__()

        self.scale_factor = scale_factor
        self.num_channels = num_channels

        # Feature extraction (acepta N canales)
        self.conv1 = nn.Conv2d(num_channels, num_features, kernel_size=5, padding=2)
        self.conv2 = nn.Conv2d(
            num_features, num_features // 2, kernel_size=3, padding=1
        )

        # Sub-pixel convolution (genera N canales)
        self.conv3 = nn.Conv2d(
            num_features // 2,
            num_channels * (scale_factor**2),
            kernel_size=3,
            padding=1,
        )
        self.pixel_shuffle = nn.PixelShuffle(scale_factor)

        # Inicialización
        self._initialize_weights()

    def _initialize_weights(self):
        """Inicialización de pesos"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.normal_(m.weight, mean=0, std=0.001)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        """
        Args:
            x: Tensor [B, C, H, W] - Imagen LR multiespectral

        Returns:
            Tensor [B, C, H*scale, W*scale] - Imagen HR multiespectral
        """
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.pixel_shuffle(self.conv3(x))
        return x

    @staticmethod
    def load_pretrained(path, num_channels=4, scale_factor=2, device="cpu"):
        """Carga modelo pre-entrenado"""
        model = ESPCNMultispectral(
            scale_factor=scale_factor, num_channels=num_channels, num_features=64
        )
        model.load_state_dict(torch.load(path, map_location=device))
        model.to(device)
        model.eval()

        return model


# Test del modelo
if __name__ == "__main__":
    # Test con 4 canales (RGB + NIR)
    model = ESPCNMultispectral(scale_factor=4, num_channels=4)

    # Input: 4 canales, 64x64
    x = torch.randn(1, 4, 64, 64)
    y = model(x)

    print(f"Input shape: {x.shape}")  # [1, 4, 64, 64]
    print(f"Output shape: {y.shape}")  # [1, 4, 256, 256]

    assert y.shape == (1, 4, 256, 256), "Error en dimensiones"

    # Contar parámetros
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Parámetros: {num_params:,}")

    # Test con 6 canales (RGB + NIR + SWIR)
    model_6ch = ESPCNMultispectral(scale_factor=2, num_channels=6)
    x_6ch = torch.randn(1, 6, 128, 128)
    y_6ch = model_6ch(x_6ch)

    print(f"\n6 canales:")
    print(f"Input shape: {x_6ch.shape}")  # [1, 6, 128, 128]
    print(f"Output shape: {y_6ch.shape}")  # [1, 6, 256, 256]

    print("\n✅ Multispectral model test OK")
