import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import torch
import sys
import shutil

# Ensure training module import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from training.create_unified_dataset import create_unified_dataset

def train_unified_yolo():
    yaml_path = r"d:\datasets_IDM(ADAS)\datasets\unified_disasters_yolo\data.yaml"
    epochs = int(os.getenv("YOLO_EPOCHS", "50"))
    run_name = os.getenv("YOLO_RUN_NAME", "yolo11_master_disaster_detector_retrained")
    
    if not os.path.exists(yaml_path):
        print("Creating Unified Master Disaster Dataset...")
        yaml_path = create_unified_dataset()
    else:
        print(f"Using existing Unified Disaster Dataset configuration at: {yaml_path}")

    last_weights = os.path.join("runs", "detect", run_name, "weights", "last.pt")
    is_resume = "--resume" in sys.argv or os.getenv("YOLO_RESUME", "").lower() in ("1", "true")

    try:
        from ultralytics import YOLO
        
        if is_resume and os.path.exists(last_weights):
            print(f"Resuming YOLOv11s training from last checkpoint: {last_weights}...")
            model = YOLO(last_weights)
            results = model.train(resume=True)
        else:
            print("Initializing YOLOv11 Small model (yolo11s.pt)...")
            model = YOLO("yolo11s.pt")

            print(f"Starting {epochs}-epoch Unified Master Disaster YOLOv11s training pipeline on CPU...")
            results = model.train(
                data=yaml_path,
                epochs=epochs,
                imgsz=320,
                batch=16,
                workers=2,
                name=run_name,
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
            print(f"Unified Master YOLOv11 training complete! Best weights saved to {save_path}")
        else:
            model.save(save_path)
            print(f"Unified Master YOLOv11 training complete! Weights saved to {save_path}")

    except Exception as e:
        print(f"Training error: {e}")

if __name__ == "__main__":
    train_unified_yolo()
