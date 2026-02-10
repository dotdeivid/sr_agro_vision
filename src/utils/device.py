"""
Detección automática de hardware disponible
"""
import torch

def get_device(prefer_cuda=True):
    """
    Detecta y retorna el mejor dispositivo disponible
    
    Args:
        prefer_cuda: Si es True, prefiere CUDA sobre MPS
        
    Returns:
        torch.device: Dispositivo a utilizar
    """
    if torch.cuda.is_available() and prefer_cuda:
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ Usando NVIDIA GPU: {gpu_name}")
        print(f"   VRAM disponible: {vram_gb:.2f} GB")
        
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("✅ Usando Apple Silicon GPU (MPS)")
        
    else:
        device = torch.device("cpu")
        print("⚠️  Usando CPU (entrenamiento será lento)")
    
    return device

def get_optimal_batch_size(device, scale_factor=2):
    """
    Sugiere batch size óptimo según hardware
    
    Args:
        device: torch.device
        scale_factor: Factor de escalado (2 o 4)
        
    Returns:
        int: Batch size recomendado
    """
    if device.type == "cuda":
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        if vram_gb >= 8:
            return 16 if scale_factor == 2 else 8
        elif vram_gb >= 6:
            return 12 if scale_factor == 2 else 6
        else:
            return 8 if scale_factor == 2 else 4
            
    elif device.type == "mps":
        return 8 if scale_factor == 2 else 4
        
    else:  # CPU
        return 4

def enable_cudnn_benchmark():
    """Optimiza CUDNN si está disponible"""
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        print("✅ cuDNN benchmark habilitado")
