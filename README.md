# 🌾 SR Agro Vision v2.0

**Super-Resolución en Imágenes Satelitales para Agricultura de Precisión**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Mejora la resolución de imágenes Sentinel-2 (10m) usando Deep Learning para agricultura de precisión sin necesidad de imágenes satelitales de alta resolución costosas.

---

## ✨ Características

- 🛰️ **Procesamiento Satelital Completo**: Descarga, preprocesamiento y SR de Sentinel-2
- 🧠 **Múltiples Arquitecturas**: ESPCN, SwinIR, GAN
- 🌾 **Métricas Agrícolas**: NDVI, EVI, SAVI con evaluación especializada
- 📊 **Evaluación Completa**: Clasificación de cultivos, estimación de área, análisis económico
- 🎯 **Punto de Entrada Único**: CLI intuitivo con `main.py`
- 🚀 **Pipeline Automatizado**: De descarga a evaluación en un comando

---

## 🚀 Inicio Rápido

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/sr-agro-vision.git
cd sr-agro-vision

# 2. Crear entorno (opción 1: conda)
conda env create -f environment_gpu.yaml  # Para NVIDIA GPU
# O
conda env create -f environment_mps.yaml  # Para Apple Silicon

# 3. Activar entorno
conda activate sr-agro-vision

# 4. Configurar credenciales Copernicus
cp .env.example .env
# Editar .env con tus credenciales CDSE
```

### Uso Básico (Menú Interactivo)

```bash
python main.py
```

Aparecerá un menú interactivo:

```
🌾 SR AGRO VISION
    Super-Resolución para Agricultura de Precisión
======================================================================

OPCIONES DISPONIBLES:

📥 DATOS
  1. download    - Descargar imágenes Sentinel-2
  2. preprocess  - Preprocesar imágenes descargadas
  3. dataset     - Crear dataset de entrenamiento
  4. pipeline    - Pipeline completo (download → preprocess → dataset)

🧠 ENTRENAMIENTO
  5. train       - Entrenar modelo (ESPCN, SwinIR, GAN)
  6. resume      - Reanudar entrenamiento
  7. ablation    - Ablation study

🔮 INFERENCIA
  8. predict     - Aplicar SR a imagen
  9. batch       - Procesar múltiples imágenes
  10. ensemble   - Predicción con ensemble

📊 EVALUACIÓN
  11. evaluate   - Evaluación agrícola completa
  12. metrics    - Solo métricas agrícolas
  13. visualize  - Generar visualizaciones

🛠️ UTILIDADES
  14. info       - Información del proyecto
  15. clean      - Limpiar outputs
  16. test       - Ejecutar tests

Ingrese el número de opción o comando:
```

### Uso Directo (CLI)

```bash
# Pipeline completo automatizado
python main.py pipeline --region corrientes_argentina --scale 4

# Entrenar modelo
python main.py train --config configs/training/espcn_x4.yaml

# Aplicar SR a imagen
python main.py predict --input imagen.tif --model outputs/weights/best.pth --output sr.tif

# Evaluación completa
python main.py evaluate --sr-dir outputs/results --hr-dir data/datasets/val/HR
```

---

## 📁 Estructura del Proyecto

```
sr_agro_vision/
├── main.py                    # 🎯 PUNTO DE ENTRADA ÚNICO
├── src/                       # Código fuente
│   ├── models/               # Arquitecturas (ESPCN, SwinIR, GAN)
│   ├── data/                 # DataLoaders
│   ├── training/             # Scripts de entrenamiento
│   ├── inference/            # Inferencia y evaluación
│   ├── evaluation/           # Métricas agrícolas
│   ├── experiments/          # Ablation studies
│   └── utils/                # Utilidades
├── scripts/                   # Scripts externos
│   ├── download_sentinel.py  # Descarga Sentinel-2
│   ├── preprocess_sentinel.py# Preprocesamiento
│   ├── create_dataset.py     # Creación dataset
│   └── pipeline.py           # Pipeline completo
├── configs/                   # Configuraciones
│   ├── training/             # Configs de entrenamiento
│   └── evaluation/           # Configs de evaluación
├── outputs/                   # Outputs del proyecto
│   ├── weights/              # Modelos entrenados
│   ├── logs/                 # TensorBoard logs
│   ├── results/              # Resultados
│   └── reports/              # Reportes finales
├── data/                      # Datos
│   ├── raw/                  # Sentinel-2 descargados
│   ├── preprocessed/         # Procesados (RGB+NIR)
│   └── datasets/             # Pares LR-HR
├── tests/                     # Suite de tests
├── docs/                      # Documentación
└── notebooks/                 # Jupyter notebooks
```

---

## 🎓 Tutoriales

### 1️⃣ Pipeline Completo (Principiantes)

```bash
# Ejecutar pipeline automatizado (6-12 horas)
python main.py pipeline \
    --region corrientes_argentina \
    --scale 4 \
    --max-images 10
```

Esto ejecuta automáticamente:
1. Descarga 10 imágenes Sentinel-2 de Corrientes, Argentina
2. Preprocesa (extrae RGB+NIR, filtra nubes)
3. Crea pares LR-HR para entrenamiento
4. Entrena modelo ESPCN x4
5. Evalúa con métricas agrícolas

### 2️⃣ Entrenamiento Personalizado

```bash
# 1. Descargar datos
python main.py download \
    --region corrientes_argentina \
    --start-date 20230901 \
    --end-date 20240301 \
    --max-images 20

# 2. Preprocesar
python main.py preprocess \
    --input data/raw \
    --output data/preprocessed \
    --cloud-threshold 0.2

# 3. Crear dataset
python main.py dataset \
    --input data/preprocessed \
    --output data/datasets \
    --scale 4 \
    --patch-size 256 \
    --stride 128

# 4. Entrenar (selecciona arquitectura)
python main.py train --config configs/training/espcn_x4.yaml        # ESPCN
python main.py train --config configs/training/gan_x4.yaml          # GAN
python main.py train --config configs/training/swinir_x4.yaml       # SwinIR

# 5. Evaluar
python main.py evaluate \
    --sr-dir outputs/results \
    --hr-dir data/datasets/val/HR \
    --visualize
```

### 3️⃣ Inferencia en Nuevas Imágenes

```bash
# Imagen individual
python main.py predict \
    --input mi_imagen.tif \
    --model outputs/weights/best_psnr_x4.pth \
    --output resultado_sr.tif

# Batch processing
python main.py batch \
    --input carpeta_imagenes/ \
    --model outputs/weights/best_psnr_x4.pth \
    --output carpeta_resultados/

# Ensemble (combina múltiples modelos)
python main.py ensemble \
    --input imagen.tif \
    --models outputs/weights/espcn.pth outputs/weights/gan.pth \
    --output ensemble_sr.tif
```

### 4️⃣ Ablation Study (Comparar Configuraciones)

```bash
python main.py ablation \
    --base-config configs/training/espcn_x4.yaml \
    --val-dir data/datasets/val \
    --output-dir outputs/results/ablation
```

Compara automáticamente:
- Baseline (L1 loss)
- Perceptual loss
- GAN
- SwinIR
- Ensemble

---

## 📊 Resultados Esperados

| Modelo | PSNR (dB) | SSIM | NDVI MAE | Tiempo GPU |
|--------|-----------|------|----------|------------|
| Bicubic (baseline) | 36.5 | 0.88 | 0.045 | - |
| ESPCN x4 | 39.8 | 0.91 | 0.028 | ~3h |
| ESPCN + Perceptual | 40.5 | 0.92 | 0.024 | ~5h |
| GAN x4 | 41.2 | 0.93 | 0.022 | ~8h |
| SwinIR x4 | 42.1 | 0.94 | 0.019 | ~12h |
| Ensemble | 42.5 | 0.94 | 0.018 | - |

*Resultados en dataset Sentinel-2 de regiones agrícolas de Argentina*

---

## 🔧 Configuración Avanzada

### Entrenar con Diferentes Arquitecturas

Editar `configs/training/*.yaml`:

```yaml
# configs/training/espcn_x4.yaml
model:
  architecture: "ESPCN"
  scale_factor: 4
  num_channels: 4  # RGB + NIR
  num_features: 64

training:
  epochs: 150
  batch_size: 16
  learning_rate: 0.0005
  loss: "L1"
  
  train_lr_data: "data/datasets/train/LR"
  train_hr_data: "data/datasets/train/HR"
  val_lr_data: "data/datasets/val/LR"
  val_hr_data: "data/datasets/val/HR"
  
  checkpoint_dir: "outputs/weights"
  log_dir: "outputs/logs"
```

### Modificar Evaluación Agrícola

Editar `configs/evaluation/evaluation.yaml`:

```yaml
agricultural_metrics:
  indices: [NDVI, EVI, SAVI]
  thresholds:
    ndvi_healthy: 0.7
    ndvi_stress: 0.3

crop_classification:
  classifier:
    type: "RandomForest"
    n_estimators: 100
  crops:
    0: "Sin Cultivo"
    1: "Soja"
    2: "Maíz"
    3: "Trigo"

area_estimation:
  gsd_meters: 10.0  # Sentinel-2
  ndvi_vegetation_threshold: 0.3
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
python main.py test

# O manualmente
python -m pytest tests/ -v

# Tests específicos
python -m pytest tests/test_models.py -v
python -m pytest tests/test_training.py -v
python -m pytest tests/test_evaluation.py -v
```

---

## 📚 Documentación

- [Instalación](docs/installation.md)
- [Guía Rápida](docs/quickstart.md)
- [Entrenamiento](docs/training.md)
- [Inferencia](docs/inference.md)
- [Evaluación](docs/evaluation.md)

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre Pull Request

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- Sentinel-2 data: [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
- ESPCN: [Real-Time Single Image and Video Super-Resolution](https://arxiv.org/abs/1609.05158)
- SwinIR: [SwinIR: Image Restoration Using Swin Transformer](https://arxiv.org/abs/2108.10257)

---

## 📞 Contacto

- **Autor**: Sandoval, Carlos David
- **Email**: davidsand640@gmail.com
- **GitHub**: [dotdeivid](https://github.com/dotdeivid)
- **Proyecto**: [github.com/dotdeivid/sr-agro-vision](https://github.com/dotdeivid/sr-agro-vision)

---

## ⭐ Star el Proyecto

Si este proyecto te fue útil, considera darle una estrella en GitHub! ⭐

---

**Versión**: 2.0 - Estructura Profesional  
**Última actualización**: 2026-02-09
