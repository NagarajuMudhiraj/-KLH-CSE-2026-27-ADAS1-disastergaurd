import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import torch
import sys
import shutil

# Ensure training module import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training.convert_floodnet import convert_floodnet_to_yolo

def train_floodnet():
    yaml_path = r"d:\datasets_IDM(ADAS)\datasets\floodnet_yolo\data.yaml"
    
    if not os.path.exists(yaml_path):
        print("Preparing and converting FloodNet dataset to YOLO format...")
        yaml_path = convert_floodnet_to_yolo()
    else:
        print(f"Using existing FloodNet dataset configuration at: {yaml_path}")

    try:
        from ultralytics import YOLO
        print("Initializing YOLOv11 Small model (yolo11s.pt)...")
        model = YOLO("yolo11s.pt")

        print("Starting FloodNet YOLOv11s training pipeline on CPU...")
        results = model.train(
            data=yaml_path,
            epochs=5,
            imgsz=320,
            batch=16,
            workers=2,
            name="yolo11_floodnet_detector",
            mosaic=0.5,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4
        )

        os.makedirs("models", exist_ok=True)
        save_path = os.path.join("models", "best.pt")
        
        # Locate best weights from training output
        train_run_dir = getattr(results, "save_dir", None)
        if train_run_dir and os.path.exists(os.path.join(train_run_dir, "weights", "best.pt")):
            best_weights = os.path.join(train_run_dir, "weights", "best.pt")
            shutil.copy(best_weights, save_path)
            print(f"FloodNet YOLOv11 training complete! Best weights saved to {save_path}")
        else:
            model.save(save_path)
            print(f"FloodNet YOLOv11 training complete! Weights saved to {save_path}")

    except Exception as e:
        print(f"Training error: {e}")

if __name__ == "__main__":
    train_floodnet()
