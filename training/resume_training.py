import os
import sys

# Ensure KMP duplicate settings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

def resume_training():
    checkpoint = r"d:\datasets_IDM(ADAS)\runs\detect\yolo11_master_disaster_detector_retrained\weights\last.pt"
    
    if not os.path.exists(checkpoint):
        print(f"Error: Checkpoint file not found at '{checkpoint}'. Cannot resume.")
        return

    from ultralytics import YOLO
    import shutil
    print(f"Loading checkpoint and resuming YOLOv11s from: {checkpoint}...")
    model = YOLO(checkpoint)
    results = model.train(resume=True)

    os.makedirs("models", exist_ok=True)
    save_path = os.path.join("models", "best.pt")
    train_run_dir = getattr(results, "save_dir", None)
    if train_run_dir and os.path.exists(os.path.join(train_run_dir, "weights", "best.pt")):
        best_weights = os.path.join(train_run_dir, "weights", "best.pt")
        shutil.copy(best_weights, save_path)
        print(f"Unified Master YOLOv11 training complete! Best weights saved to {save_path}")
    else:
        model.save(save_path)
        print(f"Unified Master YOLOv11 training complete! Weights saved to {save_path}")

if __name__ == "__main__":
    resume_training()
