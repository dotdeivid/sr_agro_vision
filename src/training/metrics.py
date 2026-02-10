"""
Métricas para evaluar super resolución
"""
import torch
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim
from skimage.metrics import peak_signal_noise_ratio as compare_psnr

def calculate_psnr(img1, img2, max_value=1.0):
    """
    Calcula PSNR entre dos imágenes
    
    Args:
        img1, img2: Tensors [B, C, H, W] o numpy arrays
        max_value: Valor máximo de los píxeles (1.0 o 255.0)
        
    Returns:
        float: PSNR en dB
    """
    if isinstance(img1, torch.Tensor):
        img1 = img1.detach().cpu().numpy()
    if isinstance(img2, torch.Tensor):
        img2 = img2.detach().cpu().numpy()
    
    # Calcular MSE
    mse = np.mean((img1 - img2) ** 2)
    
    if mse == 0:
        return float('inf')
    
    psnr = 20 * np.log10(max_value / np.sqrt(mse))
    return psnr

def calculate_ssim(img1, img2, max_value=1.0):
    """
    Calcula SSIM entre dos imágenes
    
    Args:
        img1, img2: Tensors [B, C, H, W] o numpy arrays
        max_value: Valor máximo de los píxeles
        
    Returns:
        float: SSIM (0-1)
    """
    if isinstance(img1, torch.Tensor):
        img1 = img1.detach().cpu().numpy()
    if isinstance(img2, torch.Tensor):
        img2 = img2.detach().cpu().numpy()
    
    # Si es batch, promediar
    if len(img1.shape) == 4:
        ssim_values = []
        for i in range(img1.shape[0]):
            # Transponer de [C, H, W] a [H, W, C]
            img1_i = np.transpose(img1[i], (1, 2, 0))
            img2_i = np.transpose(img2[i], (1, 2, 0))
            
            ssim = compare_ssim(img1_i, img2_i, 
                              data_range=max_value,
                              channel_axis=2)
            ssim_values.append(ssim)
        
        return np.mean(ssim_values)
    
    else:
        # Imagen única
        img1 = np.transpose(img1, (1, 2, 0))
        img2 = np.transpose(img2, (1, 2, 0))
        
        return compare_ssim(img1, img2, 
                          data_range=max_value,
                          channel_axis=2)

def calculate_psnr_batch(pred_batch, target_batch, max_value=1.0):
    """
    Calcula PSNR promedio para un batch
    
    Args:
        pred_batch: Tensor [B, C, H, W]
        target_batch: Tensor [B, C, H, W]
        max_value: Valor máximo
        
    Returns:
        float: PSNR promedio
    """
    psnr_values = []
    
    for i in range(pred_batch.shape[0]):
        psnr = calculate_psnr(pred_batch[i:i+1], target_batch[i:i+1], max_value)
        psnr_values.append(psnr)
    
    return np.mean(psnr_values)

def calculate_ssim_batch(pred_batch, target_batch, max_value=1.0):
    """
    Calcula SSIM promedio para un batch
    
    Args:
        pred_batch: Tensor [B, C, H, W]
        target_batch: Tensor [B, C, H, W]
        max_value: Valor máximo
        
    Returns:
        float: SSIM promedio
    """
    return calculate_ssim(pred_batch, target_batch, max_value)

class AverageMeter:
    """Utilidad para trackear métricas promedio"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0
    
    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

# Test
if __name__ == "__main__":
    # Test con imágenes sintéticas
    img1 = torch.rand(2, 3, 128, 128)
    img2 = img1 + torch.randn(2, 3, 128, 128) * 0.1  # Agregar ruido
    
    psnr = calculate_psnr_batch(img1, img2)
    ssim = calculate_ssim_batch(img1, img2)
    
    print(f"PSNR: {psnr:.2f} dB")
    print(f"SSIM: {ssim:.4f}")
    print("✅ Metrics test OK")
