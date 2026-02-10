"""
Utilidades para guardar y cargar checkpoints
"""
import torch
import os
from pathlib import Path

def save_checkpoint(model, optimizer, epoch, loss, path):
    """
    Guarda checkpoint del modelo
    
    Args:
        model: Modelo PyTorch
        optimizer: Optimizador
        epoch: Número de época
        loss: Loss actual
        path: Ruta donde guardar
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss
    }
    
    torch.save(checkpoint, path)
    print(f"✅ Checkpoint guardado: {path}")

def load_checkpoint(model, optimizer, path):
    """
    Carga checkpoint del modelo
    
    Returns:
        int: Época del checkpoint
    """
    if not os.path.exists(path):
        print(f"⚠️  Checkpoint no encontrado: {path}")
        return 0
    
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    if optimizer is not None:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    epoch = checkpoint['epoch']
    print(f"✅ Checkpoint cargado desde época {epoch}")
    
    return epoch

def save_model(model, path):
    """Guarda solo los pesos del modelo"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"✅ Modelo guardado: {path}")

def load_model(model, path, device):
    """Carga solo los pesos del modelo"""
    model.load_state_dict(torch.load(path, map_location=device))
    print(f"✅ Modelo cargado: {path}")
    return model
