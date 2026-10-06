# AI Models Training Guide

This guide details how to train both AI models used in the system:
1. **YOLOv11 Object Detection Model** for images (`best.pt`)
2. **XGBoost Road Safety Classifier** (`road_model.pkl`)

---

## 1. XGBoost Model Training

The XGBoost model predicts road safety status based on sensor/environmental inputs:
- `Rainfall` (mm/hour)
- `Traffic Level` (1-10 scale)
- `Water Level` (cm depth)

Outputs: `0: Safe`, `1: Risky`, `2: Blocked`

### How to Run Training:
```bash
# From workspace root
python training/train_xgboost.py
```
This script will:
- Synthesize 2,500 labeled road telemetry data points under physical disaster physics equations.
- Perform an 80/20 train-test split with stratified sampling.
- Train an `xgboost.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)`.
- Print classification matrix & accuracy metrics.
- Save the trained model to `models/road_model.pkl`.

---

## 2. YOLOv11 Object Detection Training

The YOLOv11 model detects 4 disaster hazard classes from input images:
1. `Flood`
2. `Fire`
3. `Landslide`
4. `Road Damage`

### Datasets Required:
- **RDD2022**: Multi-national Road Damage Detection dataset.
- **FloodNet**: Drone imagery dataset for flood assessment.
- **FLAME**: Aerial image dataset for wild fire detection.

### Dataset Directory Layout:
Format datasets into standard YOLO format under `datasets/disasters_yolo`:
```
datasets/disasters_yolo/
├── data.yaml
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### `data.yaml` Configuration:
```yaml
path: ../datasets/disasters_yolo
train: images/train
val: images/val

nc: 4
names: ['Flood', 'Fire', 'Landslide', 'Road Damage']
```

### How to Run YOLOv11 Training:
```bash
# From workspace root
python training/train_yolo.py
```
This script runs Ultralytics YOLOv11 (`yolo11s.pt`) fine-tuning with Mosaic augmentations, HSV shifts, and outputs `models/best.pt`.

---

## 3. Training Output & Result Visualizations

Trained dataset results, batch label visualizations, and class distribution plots are stored in:
- Workspace Results Directory: `trained_results/`
- Archive Results Directory: `C:\Users\nagar\Downloads\archive\trained_results\`

### Contents of `trained_results/`:
- `labels.jpg`: Class distribution, label bounding box dimensions, and spatial position heatmaps.
- `train_batch0.jpg`, `train_batch1.jpg`, `train_batch2.jpg`: Mosaic-augmented training batch images with bounding box ground truth annotations.
- `args.yaml`: Training hyperparameter configuration.

