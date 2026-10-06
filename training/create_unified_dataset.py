import os
import glob
import shutil

def create_unified_dataset():
    floodnet_dir = r"d:\datasets_IDM(ADAS)\datasets\floodnet_yolo"
    archive_dir = r"C:\Users\nagar\Downloads\archive"
    out_dir = r"d:\datasets_IDM(ADAS)\datasets\unified_disasters_yolo"
    
    os.makedirs(os.path.join(out_dir, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "labels", "val"), exist_ok=True)
    
    # Class mapping from archive to unified:
    # 0: person -> 3 (Person)
    # 1: fire -> 1 (Fire)
    # 2: smoke -> 2 (Smoke)
    # 3: small_vehicle -> 4 (Vehicle)
    # 4: large_vehicle -> 4 (Vehicle)
    # 5: two_wheeler -> 4 (Vehicle)
    ARCHIVE_CLASS_MAP = {
        0: 3, # Person
        1: 1, # Fire
        2: 2, # Smoke
        3: 4, # Vehicle
        4: 4, # Vehicle
        5: 4  # Vehicle
    }
    
    # FloodNet class 0 is Flood -> Unified Class 0 (Flood)
    FLOODNET_CLASS_MAP = {
        0: 0 # Flood
    }
    
    total_imgs = 0
    
    # 1. Copy FloodNet dataset
    for split in ["train", "val"]:
        img_files = glob.glob(os.path.join(floodnet_dir, "images", split, "*.jpg"))
        for img_path in img_files:
            basename = os.path.basename(img_path)
            txt_name = os.path.splitext(basename)[0] + ".txt"
            label_path = os.path.join(floodnet_dir, "labels", split, txt_name)
            
            dest_img = os.path.join(out_dir, "images", split, f"fn_{basename}")
            dest_txt = os.path.join(out_dir, "labels", split, f"fn_{txt_name}")
            
            shutil.copy(img_path, dest_img)
            
            lines = []
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            new_cls = FLOODNET_CLASS_MAP.get(cls_id, 0)
                            lines.append(f"{new_cls} {' '.join(parts[1:])}")
                            
            with open(dest_txt, "w") as f:
                f.write("\n".join(lines))
            total_imgs += 1

    # 2. Copy Archive dataset
    for split in ["train", "val"]:
        img_files = glob.glob(os.path.join(archive_dir, split, "images", "*.jpg"))
        img_files.extend(glob.glob(os.path.join(archive_dir, split, "images", "*.png")))
        
        for img_path in img_files:
            basename = os.path.basename(img_path)
            txt_name = os.path.splitext(basename)[0] + ".txt"
            label_path = os.path.join(archive_dir, split, "labels", txt_name)
            
            dest_img = os.path.join(out_dir, "images", split, f"arch_{basename}")
            dest_txt = os.path.join(out_dir, "labels", split, f"arch_{txt_name}")
            
            shutil.copy(img_path, dest_img)
            
            lines = []
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            new_cls = ARCHIVE_CLASS_MAP.get(cls_id, 0)
                            lines.append(f"{new_cls} {' '.join(parts[1:])}")
                            
            with open(dest_txt, "w") as f:
                f.write("\n".join(lines))
            total_imgs += 1
            
    print(f"Unified dataset creation complete! Merged {total_imgs} total images.")
    
    clean_out_dir = out_dir.replace('\\', '/')
    yaml_content = f"""path: {clean_out_dir}
train: images/train
val: images/val

nc: 6
names: ['Flood', 'Fire', 'Smoke', 'Person', 'Vehicle', 'Road Damage']
"""
    yaml_path = os.path.join(out_dir, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
        
    print(f"Unified data.yaml written to: {yaml_path}")
    return yaml_path

if __name__ == "__main__":
    create_unified_dataset()
