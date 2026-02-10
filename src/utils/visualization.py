"""
Utilidades para visualizar resultados
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def visualize_comparison(lr_img, sr_img, hr_img, save_path=None):
    """
    Visualiza comparación LR vs SR vs HR
    
    Args:
        lr_img: Imagen de baja resolución
        sr_img: Imagen super resuelta
        hr_img: Imagen de alta resolución (ground truth)
        save_path: Ruta para guardar figura (opcional)
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Normalizar si es necesario
    if lr_img.max() <= 1.0:
        lr_img = (lr_img * 255).astype(np.uint8)
    if sr_img.max() <= 1.0:
        sr_img = (sr_img * 255).astype(np.uint8)
    if hr_img.max() <= 1.0:
        hr_img = (hr_img * 255).astype(np.uint8)
    
    # Low Resolution
    axes[0].imshow(lr_img)
    axes[0].set_title(f'Low Resolution\n{lr_img.shape[1]}x{lr_img.shape[0]}')
    axes[0].axis('off')
    
    # Super Resolution
    axes[1].imshow(sr_img)
    axes[1].set_title(f'Super Resolution\n{sr_img.shape[1]}x{sr_img.shape[0]}')
    axes[1].axis('off')
    
    # High Resolution (Ground Truth)
    axes[2].imshow(hr_img)
    axes[2].set_title(f'Ground Truth\n{hr_img.shape[1]}x{hr_img.shape[0]}')
    axes[2].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ Visualización guardada: {save_path}")
    else:
        plt.show()
    
    plt.close()

def plot_training_curves(log_file, save_path=None):
    """
    Grafica curvas de entrenamiento desde TensorBoard logs
    
    Args:
        log_file: Archivo de log de TensorBoard
        save_path: Ruta para guardar figura
    """
    # Esta función requeriría parsear los logs de TensorBoard
    # Por ahora es un placeholder
    print("⚠️  Función plot_training_curves no implementada aún")
    print("   Usar TensorBoard para visualizar: tensorboard --logdir runs/")

def create_comparison_grid(images, titles, save_path=None):
    """
    Crea una grid de comparación de múltiples imágenes
    
    Args:
        images: Lista de imágenes numpy
        titles: Lista de títulos
        save_path: Ruta para guardar
    """
    n = len(images)
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols*4, rows*4))
    
    if rows == 1 and cols == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    elif cols == 1:
        axes = [[ax] for ax in axes]
    
    for idx, (img, title) in enumerate(zip(images, titles)):
        row = idx // cols
        col = idx % cols
        
        # Normalizar si es necesario
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        
        axes[row][col].imshow(img)
        axes[row][col].set_title(title)
        axes[row][col].axis('off')
    
    # Ocultar axes sobrantes
    for idx in range(n, rows * cols):
        row = idx // cols
        col = idx % cols
        axes[row][col].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ Grid guardada: {save_path}")
    else:
        plt.show()
    
    plt.close()

# Test
if __name__ == "__main__":
    # Crear imágenes de prueba
    lr = np.random.rand(64, 64, 3)
    sr = np.random.rand(128, 128, 3)
    hr = np.random.rand(128, 128, 3)
    
    visualize_comparison(lr, sr, hr)
    print("✅ Visualization test OK")
