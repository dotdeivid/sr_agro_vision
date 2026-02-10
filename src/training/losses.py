"""
Funciones de pérdida para super resolución
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class L1Loss(nn.Module):
    """L1 Loss (Mean Absolute Error)"""
    def __init__(self):
        super(L1Loss, self).__init__()
        self.loss = nn.L1Loss()
    
    def forward(self, pred, target):
        return self.loss(pred, target)

class MSELoss(nn.Module):
    """MSE Loss (Mean Squared Error)"""
    def __init__(self):
        super(MSELoss, self).__init__()
        self.loss = nn.MSELoss()
    
    def forward(self, pred, target):
        return self.loss(pred, target)

class CharbonnierLoss(nn.Module):
    """
    Charbonnier Loss (suavizado de L1)
    Más robusto a outliers que MSE
    """
    def __init__(self, epsilon=1e-3):
        super(CharbonnierLoss, self).__init__()
        self.epsilon = epsilon
    
    def forward(self, pred, target):
        diff = pred - target
        loss = torch.sqrt(diff * diff + self.epsilon * self.epsilon)
        return torch.mean(loss)

def get_loss_function(loss_name):
    """
    Factory para obtener función de pérdida
    
    Args:
        loss_name: "L1", "MSE", o "Charbonnier"
        
    Returns:
        Loss function
    """
    losses = {
        'L1': L1Loss,
        'MSE': MSELoss,
        'Charbonnier': CharbonnierLoss
    }
    
    if loss_name not in losses:
        raise ValueError(f"Loss '{loss_name}' no soportado. Opciones: {list(losses.keys())}")
    
    return losses[loss_name]()

class PerceptualLoss(nn.Module):
    """
    Perceptual Loss usando VGG16
    Útil para preservar textura y detalles de alto nivel
    
    Nota: Solo usa los primeros 3 canales (RGB) para compatibilidad con VGG16.
    El canal NIR (índice 3) no se usa en el cálculo perceptual.
    """
    
    def __init__(self, layers=[3, 8, 15], device='cuda'):
        """
        Args:
            layers: Índices de capas VGG16 para extraer features
                    [3] = relu1_2, [8] = relu2_2, [15] = relu3_3
            device: Dispositivo para VGG16
        """
        super().__init__()
        
        # Cargar VGG16 pre-entrenado
        vgg = models.vgg16(pretrained=True).features
        
        # Congelar parámetros
        for param in vgg.parameters():
            param.requires_grad = False
        
        # Extraer capas específicas
        self.features = nn.ModuleList()
        prev = 0
        for layer_idx in layers:
            self.features.append(vgg[prev:layer_idx+1])
            prev = layer_idx + 1
        
        self.features = self.features.to(device)
        
        # Normalización ImageNet
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
    
    def normalize_rgb(self, x):
        """Normalizar solo canales RGB para VGG"""
        # x: [B, 4, H, W] → tomar primeros 3 canales
        rgb = x[:, :3, :, :]
        return (rgb - self.mean) / self.std
    
    def forward(self, sr, hr):
        """
        Args:
            sr: Super-resolución [B, 4, H, W]
            hr: Ground truth [B, 4, H, W]
        
        Returns:
            Perceptual loss (scalar)
        """
        # Normalizar
        sr_rgb = self.normalize_rgb(sr)
        hr_rgb = self.normalize_rgb(hr)
        
        loss = 0.0
        
        # Extraer features de cada capa
        for feat_extractor in self.features:
            sr_rgb = feat_extractor(sr_rgb)
            hr_rgb = feat_extractor(hr_rgb)
            
            # MSE entre features
            loss += F.mse_loss(sr_rgb, hr_rgb)
        
        return loss

class CombinedLoss(nn.Module):
    """
    Combina L1 + Perceptual Loss
    Mejora tanto calidad pixel-wise como perceptual
    """
    
    def __init__(self, alpha=1.0, beta=0.006, device='cuda'):
        """
        Args:
            alpha: Peso de L1 loss (default: 1.0)
            beta: Peso de perceptual loss (default: 0.006, típico en SR)
            device: Dispositivo para computación
        """
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        
        self.l1_loss = nn.L1Loss()
        self.perceptual_loss = PerceptualLoss(device=device)
    
    def forward(self, sr, hr):
        """
        Args:
            sr: Super-resolución [B, C, H, W]
            hr: Ground truth [B, C, H, W]
        
        Returns:
            total_loss: Pérdida combinada
            loss_dict: Diccionario con pérdidas individuales
        """
        l1 = self.l1_loss(sr, hr)
        perceptual = self.perceptual_loss(sr, hr)
        
        total = self.alpha * l1 + self.beta * perceptual
        
        return total, {'l1': l1.item(), 'perceptual': perceptual.item()}

class AdversarialLoss(nn.Module):
    """
    Adversarial Loss para SR-GAN
    Basado en BCE (Binary Cross Entropy)
    """
    
    def __init__(self):
        super().__init__()
        self.criterion = nn.BCEWithLogitsLoss()
    
    def forward(self, prediction, is_real):
        """
        Args:
            prediction: Salida del discriminador [B, 1, H, W]
            is_real: True si las imágenes son reales, False si son fake
        
        Returns:
            Adversarial loss
        """
        if is_real:
            labels = torch.ones_like(prediction)
        else:
            labels = torch.zeros_like(prediction)
        
        return self.criterion(prediction, labels)


class GANLoss(nn.Module):
    """
    Pérdida combinada para entrenamiento GAN
    Generator Loss = Content Loss + Adversarial Loss
    """
    
    def __init__(self, content_weight=1.0, adversarial_weight=0.001, device='cuda'):
        """
        Args:
            content_weight: Peso de content loss (L1 + Perceptual)
            adversarial_weight: Peso de adversarial loss (típico: 0.001)
        """
        super().__init__()
        self.content_weight = content_weight
        self.adversarial_weight = adversarial_weight
        
        self.content_loss = CombinedLoss(device=device)
        self.adversarial_loss = AdversarialLoss()
    
    def forward(self, sr, hr, disc_sr_pred):
        """
        Args:
            sr: Super-resolución generada
            hr: Ground truth
            disc_sr_pred: Predicción del discriminador para SR
        
        Returns:
            total_loss, loss_dict
        """
        # Content loss
        content, content_dict = self.content_loss(sr, hr)
        
        # Adversarial loss (queremos engañar al discriminador)
        adversarial = self.adversarial_loss(disc_sr_pred, is_real=True)
        
        # Total
        total = self.content_weight * content + self.adversarial_weight * adversarial
        
        loss_dict = {
            'content': content.item(),
            'l1': content_dict['l1'],
            'perceptual': content_dict['perceptual'],
            'adversarial': adversarial.item()
        }
        
        return total, loss_dict

# Test
if __name__ == "__main__":
    pred = torch.randn(4, 3, 64, 64)
    target = torch.randn(4, 3, 64, 64)
    
    l1_loss = L1Loss()
    mse_loss = MSELoss()
    char_loss = CharbonnierLoss()
    
    print(f"L1 Loss: {l1_loss(pred, target):.4f}")
    print(f"MSE Loss: {mse_loss(pred, target):.4f}")
    print(f"Charbonnier Loss: {char_loss(pred, target):.4f}")
    print("✅ Loss functions test OK")
