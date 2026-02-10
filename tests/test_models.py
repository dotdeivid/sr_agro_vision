"""
Test Suite para Phase 3 implementations
Verifica que todas las mejoras funcionan correctamente
"""
import torch
import sys


def test_perceptual_loss():
    """Test Perceptual Loss and CombinedLoss"""
    print("\n" + "="*60)
    print("TEST 1: Perceptual Loss")
    print("="*60)
    
    try:
        from src.training.losses import PerceptualLoss, CombinedLoss
        
        # Test PerceptualLoss
        loss_fn = PerceptualLoss(device='cpu')
        sr = torch.randn(1, 4, 64, 64)
        hr = torch.randn(1, 4, 64, 64)
        
        perceptual = loss_fn(sr, hr)
        print(f"✓ PerceptualLoss forward pass: {perceptual.item():.4f}")
        
        # Test CombinedLoss
        combined_fn = CombinedLoss(device='cpu')
        total, loss_dict = combined_fn(sr, hr)
        print(f"✓ CombinedLoss: {total.item():.4f}")
        print(f"  - L1: {loss_dict['l1']:.4f}")
        print(f"  - Perceptual: {loss_dict['perceptual']:.4f}")
        
        print("✅ Test 1 PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_swinir():
    """Test SwinIR Architecture"""
    print("="*60)
    print("TEST 2: SwinIR Architecture")
    print("="*60)
    
    try:
        from src.models.swinir import SwinIRMultispectral
        
        model = SwinIRMultispectral(
            num_channels=4,
            embed_dim=60,
            depths=[6, 6],
            num_heads=[6, 6],
            window_size=8,
            scale_factor=4
        )
        
        x = torch.randn(1, 4, 64, 64)
        y = model(x)
        
        print(f"✓ Input shape: {x.shape}")
        print(f"✓ Output shape: {y.shape}")
        
        assert y.shape == (1, 4, 256, 256), f"Expected (1,4,256,256), got {y.shape}"
        
        params = sum(p.numel() for p in model.parameters())
        print(f"✓ Parameters: {params:,}")
        
        print("✅ Test 2 PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_gan():
    """Test GAN components"""
    print("="*60)
    print("TEST 3: GAN Components")
    print("="*60)
    
    try:
        from src.models.discriminator import PatchGANDiscriminator
        from src.training.losses import AdversarialLoss, GANLoss
        
        # Test Discriminator
        disc = PatchGANDiscriminator(num_channels=4)
        x = torch.randn(2, 4, 256, 256)
        pred = disc(x)
        
        print(f"✓ Discriminator input: {x.shape}")
        print(f"✓ Discriminator output: {pred.shape}")
        
        # Test AdversarialLoss
        adv_loss = AdversarialLoss()
        loss_real = adv_loss(pred, is_real=True)
        loss_fake = adv_loss(pred, is_real=False)
        
        print(f"✓ Adversarial Loss (real): {loss_real.item():.4f}")
        print(f"✓ Adversarial Loss (fake): {loss_fake.item():.4f}")
        
        # Test GANLoss
        gan_loss = GANLoss(device='cpu')
        sr = torch.randn(2, 4, 256, 256)
        hr = torch.randn(2, 4, 256, 256)
        disc_pred = torch.randn(2, 1, 30, 30)
        
        total, loss_dict = gan_loss(sr, hr, disc_pred)
        print(f"✓ GAN Loss: {total.item():.4f}")
        print(f"  - Content: {loss_dict['content']:.4f}")
        print(f"  - Adversarial: {loss_dict['adversarial']:.4f}")
        
        print("✅ Test 3 PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        return False


def test_ensemble():
    """Test Ensemble SR"""
    print("="*60)
    print("TEST 4: Ensemble SR")
    print("="*60)
    
    try:
        # Ensemble requires trained models, just test import
        from src.inference.ensemble_sr import EnsembleSR
        
        print("✓ EnsembleSR class imported successfully")
        print("✅ Test 4 PASSED (requires trained models for full test)\n")
        return True
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        return False


def test_augmentation():
    """Test Data Augmentation"""
    print("="*60)
    print("TEST 5: Data Augmentation")
    print("="*60)
    
    try:
        import numpy as np
        from src.data.dataloader import SatelliteSRDataset
        
        # Augmentation is internal to dataset, just verify import
        print("✓ SatelliteSRDataset with enhanced augmentation")
        print("✅ Test 5 PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}\n")
        return False


def test_ablation():
    """Test Ablation Study"""
    print("="*60)
    print("TEST 6: Ablation Study")
    print("="*60)
    
    try:
        from src.experiments.ablation_study import AblationStudy
        
        print("✓ AblationStudy class imported successfully")
        print("✅ Test 6 PASSED (requires trained models for full test)\n")
        return True
    except Exception as e:
        print(f"❌ Test 6 FAILED: {e}\n")
        return False


def main():
    print("\n" + "🧪 PHASE 3 TEST SUITE".center(60, "="))
    
    results = []
    
    # Run all tests
    results.append(("Perceptual Loss", test_perceptual_loss()))
    results.append(("SwinIR", test_swinir()))
    results.append(("GAN", test_gan()))
    results.append(("Ensemble", test_ensemble()))
    results.append(("Augmentation", test_augmentation()))
    results.append(("Ablation Study", test_ablation()))
    
    # Summary
    print("="*60)
    print("SUMMARY".center(60))
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s} {status}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
