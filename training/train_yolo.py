"""
YOLOv11 Object Detection Training Script
Trains Ultralytics YOLOv11 on the uploaded disaster dataset (archive)
Classes: person, fire, smoke, small_vehicle, large_vehicle, two_wheeler
"""

import os

def train_yolo_model():
    dataset_yaml = os.getenv("DATASET_YAML")
    if not dataset_yaml or not os.path.exists(dataset_yaml):
        dataset_yaml = os.path.join("datasets", "disasters_yolo", "data.yaml")
        if not os.path.exists(dataset_yaml):
            dataset_yaml = os.path.join("..", "datasets", "disasters_yolo", "data.yaml")
        
    print(f"Using dataset configuration at: {dataset_yaml}")
    
    try:
        from ultralytics import YOLO
        print("Initializing YOLOv11 Small model (yolo11s.pt)...")
        model = YOLO("yolo11s.pt")
        
        print("Starting fast training pipeline...")
        results = model.train(
            data=dataset_yaml,
            epochs=5,
            imgsz=320,
            batch=32,
            workers=4,
            name="yolo11_disaster_detector",
            mosaic=0.5,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4
        )
        
        # Save best weights to models/best.pt
        os.makedirs("models", exist_ok=True)
        save_path = os.path.join("models", "best.pt")
        model.save(save_path)
        print(f"YOLOv11 training complete! Model saved to {save_path}")
    except (Exception, BaseException) as e:
        print(f"Training execution note: {e}")
        print("If PyTorch DLL is missing on your host machine, install PyTorch with CUDA or CPU binaries:")
        print("pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu")

if __name__ == "__main__":
    train_yolo_model()
