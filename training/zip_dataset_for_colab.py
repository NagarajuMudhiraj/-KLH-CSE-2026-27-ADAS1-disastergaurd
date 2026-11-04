"""
Compresses the Unified Master Disaster Dataset into a clean ZIP file
for fast, reliable upload to Google Drive and execution on Google Colab.
"""

import os
import zipfile
import shutil
from tqdm import tqdm

def zip_dataset():
    src_dir = os.path.abspath(r"d:\datasets_IDM(ADAS)\datasets\unified_disasters_yolo")
    out_zip = os.path.abspath(r"d:\datasets_IDM(ADAS)\unified_disasters_yolo.zip")

    if not os.path.exists(src_dir):
        print(f"[Error] Source directory not found: {src_dir}")
        return

    print("=" * 65)
    print(" Packaging Unified Disaster Dataset for Google Colab (85%+ Accuracy)")
    print("=" * 65)
    print(f"Source Folder: {src_dir}")
    print(f"Target Archive: {out_zip}\n")

    # Gather all files to archive
    all_files = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, os.path.dirname(src_dir))
            all_files.append((full_p, rel_p))

    print(f"Total files to compress: {len(all_files)}")

    # Create ZIP archive
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for full_p, rel_p in tqdm(all_files, desc="Compressing", unit="file"):
            zipf.write(full_p, rel_p)

    zip_size_mb = os.path.getsize(out_zip) / (1024 * 1024)
    print("\n" + "=" * 65)
    print("                 COMPRESSION COMPLETE                            ")
    print("=" * 65)
    print(f"File created:     {out_zip}")
    print(f"Compressed size:  {zip_size_mb:.2f} MB")
    print("=" * 65)
    print("\nNext step: Drag and drop 'unified_disasters_yolo.zip' into your Google Drive (My Drive).")

if __name__ == "__main__":
    zip_dataset()
