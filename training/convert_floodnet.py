import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import glob
import cv2
import numpy as np
import shutil
from sklearn.model_selection import train_test_split

def convert_floodnet_to_yolo():
    base_dir = r"d:\datasets_IDM(ADAS)\floodnet\floodnet"
    out_dir = r"d:\datasets_IDM(ADAS)\datasets\floodnet_yolo"
    
    os.makedirs(os.path.join(out_dir, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "labels", "val"), exist_ok=True)
    
    # Class mapping for YOLO:
    # 0: Flood
    # 1: Fire
    # 2: Landslide
    # 3: Road Damage
    FLOOD_CLASS_ID = 0
    
    # FloodNet mask values representing flood inundation:
    # 1: Building-flooded
    # 3: Road-flooded
    # 5: Water
    FLOOD_MASK_CLASSES = {1, 3, 5}
    
    flooded_img_dir = os.path.join(base_dir, "Train", "Labeled", "Flooded", "image")
    flooded_mask_dir = os.path.join(base_dir, "Train", "Labeled", "Flooded", "mask")
    
    non_flooded_img_dir = os.path.join(base_dir, "Train", "Labeled", "Non-Flooded", "image")
    non_flooded_mask_dir = os.path.join(base_dir, "Train", "Labeled", "Non-Flooded", "mask")
    
    image_mask_pairs = []
    
    for img_path in glob.glob(os.path.join(flooded_img_dir, "*.jpg")):
        filename = os.path.splitext(os.path.basename(img_path))[0]
        mask_path = os.path.join(flooded_mask_dir, f"{filename}_lab.png")
        if os.path.exists(mask_path):
            image_mask_pairs.append((img_path, mask_path, True))
            
    for img_path in glob.glob(os.path.join(non_flooded_img_dir, "*.jpg")):
        filename = os.path.splitext(os.path.basename(img_path))[0]
        mask_path = os.path.join(non_flooded_mask_dir, f"{filename}_lab.png")
        if os.path.exists(mask_path):
            image_mask_pairs.append((img_path, mask_path, False))
            
    print(f"Total FloodNet labeled pairs found: {len(image_mask_pairs)}")
    
    train_pairs, val_pairs = train_test_split(image_mask_pairs, test_size=0.2, random_state=42)
    
    def process_split(pairs, split_name):
        processed_count = 0
        bbox_count = 0
        
        for img_path, mask_path, is_flooded in pairs:
            basename = os.path.basename(img_path)
            txt_name = os.path.splitext(basename)[0] + ".txt"
            
            dest_img_path = os.path.join(out_dir, "images", split_name, basename)
            dest_label_path = os.path.join(out_dir, "labels", split_name, txt_name)
            
            shutil.copy(img_path, dest_img_path)
            
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            lines = []
            
            if mask is not None and is_flooded:
                h, w = mask.shape
                binary_flood = np.zeros((h, w), dtype=np.uint8)
                for cls_val in FLOOD_MASK_CLASSES:
                    binary_flood[mask == cls_val] = 255
                    
                contours, _ = cv2.findContours(binary_flood, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < (w * h * 0.001): # Filter tiny noise
                        continue
                    
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    x_center = (x + bw / 2.0) / w
                    y_center = (y + bh / 2.0) / h
                    norm_w = bw / float(w)
                    norm_h = bh / float(h)
                    
                    lines.append(f"{FLOOD_CLASS_ID} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")
                    bbox_count += 1
            
            with open(dest_label_path, "w") as f:
                f.write("\n".join(lines))
                
            processed_count += 1
            
        print(f"Split {split_name}: {processed_count} images, {bbox_count} flood bounding boxes generated.")

    process_split(train_pairs, "train")
    process_split(val_pairs, "val")
    
    # Create data.yaml
    clean_out_dir = out_dir.replace('\\', '/')
    yaml_content = f"""path: {clean_out_dir}
train: images/train
val: images/val

nc: 4
names: ['Flood', 'Fire', 'Landslide', 'Road Damage']
"""
    yaml_path = os.path.join(out_dir, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
        
    print(f"Dataset conversion complete! Created data.yaml at {yaml_path}")
    return yaml_path

if __name__ == "__main__":
    convert_floodnet_to_yolo()
