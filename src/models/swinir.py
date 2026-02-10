"""
SwinIR adaptado para imágenes multiespectrales
Basado en: https://github.com/JingyunLiang/SwinIR
Arquitectura simplificada para GPU limitada (GTX 1660 6GB)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class WindowAttention(nn.Module):
    """Window-based Multi-head Self Attention"""
    
    def __init__(self, dim, window_size, num_heads):
        super().__init__()
        self.dim = dim
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5
        
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
    
    def forward(self, x):
        B_, N, C = x.shape
        
        qkv = self.qkv(x).reshape(B_, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        q = q * self.scale
        attn = (q @ k.transpose(-2, -1))
        attn = attn.softmax(dim=-1)
        
        x = (attn @ v).transpose(1, 2).reshape(B_, N, C)
        x = self.proj(x)
        
        return x


class SwinTransformerBlock(nn.Module):
    """Swin Transformer Block"""
    
    def __init__(self, dim, num_heads, window_size=8, mlp_ratio=4.0):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.window_size = window_size
        
        self.norm1 = nn.LayerNorm(dim)
        self.attn = WindowAttention(dim, window_size, num_heads)
        
        self.norm2 = nn.LayerNorm(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Linear(mlp_hidden_dim, dim)
        )
    
    def forward(self, x):
        # x: [B, C, H, W]
        B, C, H, W = x.shape
        
        # Flatten
        x = x.flatten(2).transpose(1, 2)  # [B, H*W, C]
        
        # Attention
        shortcut = x
        x = self.norm1(x)
        x = self.attn(x)
        x = shortcut + x
        
        # MLP
        x = x + self.mlp(self.norm2(x))
        
        # Reshape back
        x = x.transpose(1, 2).reshape(B, C, H, W)
        
        return x


class SwinIRMultispectral(nn.Module):
    """
    SwinIR adaptado para imágenes multiespectrales
    Arquitectura simplificada para GPU limitada
    """
    
    def __init__(self, num_channels=4, embed_dim=60, depths=[6, 6, 6, 6], 
                 num_heads=[6, 6, 6, 6], window_size=8, scale_factor=4):
        super().__init__()
        
        self.scale_factor = scale_factor
        self.num_channels = num_channels
        
        # Shallow feature extraction
        self.conv_first = nn.Conv2d(num_channels, embed_dim, 3, padding=1)
        
        # Deep feature extraction (Swin Transformer blocks)
        self.layers = nn.ModuleList()
        for i_layer in range(len(depths)):
            layer = nn.ModuleList([
                SwinTransformerBlock(
                    dim=embed_dim,
                    num_heads=num_heads[i_layer],
                    window_size=window_size
                )
                for _ in range(depths[i_layer])
            ])
            self.layers.append(layer)
        
        # Reconstruction
        self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, padding=1)
        
        # Upsampling
        self.conv_before_upsample = nn.Conv2d(embed_dim, embed_dim, 3, padding=1)
        self.upsample = nn.Sequential(
            nn.Conv2d(embed_dim, embed_dim * (scale_factor ** 2), 3, padding=1),
            nn.PixelShuffle(scale_factor)
        )
        self.conv_last = nn.Conv2d(embed_dim, num_channels, 3, padding=1)
    
    def forward(self, x):
        # Shallow features
        x_first = self.conv_first(x)
        
        # Deep features
        res = x_first
        for layer in self.layers:
            for blk in layer:
                res = blk(res)
        
        res = self.conv_after_body(res)
        res = res + x_first  # Global residual
        
        # Upsampling
        x = self.conv_before_upsample(res)
        x = self.upsample(x)
        x = self.conv_last(x)
        
        return x


# Test
if __name__ == "__main__":
    print("Testing SwinIR Multispectral...")
    
    model = SwinIRMultispectral(
        num_channels=4,
        embed_dim=60,
        depths=[6, 6, 6, 6],
        num_heads=[6, 6, 6, 6],
        window_size=8,
        scale_factor=4
    )
    
    # Count parameters
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {num_params:,}")
    
    # Test forward pass
    x = torch.randn(1, 4, 64, 64)
    with torch.no_grad():
        y = model(x)
    
    print(f"Input: {x.shape}")
    print(f"Output: {y.shape}")
    assert y.shape == (1, 4, 256, 256), f"Expected (1, 4, 256, 256), got {y.shape}"
    
    print("✅ SwinIR test passed!")
