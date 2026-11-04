"""
Benchmark script: Standard YOLOv11 vs. SAHI-Enhanced YOLOv11 Multi-Scale Slicing.
Evaluates disaster detection recall, detection counts, and generates side-by-side
visualizations for research verification.
"""

import os
import glob
import pandas as pd
from pipeline.sahi_inference import SahiDisasterDetector

def run_benchmark(num_samples: int = 20, output_dir: str = "docs/sahi_comparisons"):
    print("=" * 65)
    print("  YOLOv11 Master Disaster Detector: Standard vs. SAHI Benchmark  ")
    print("=" * 65)

    detector = SahiDisasterDetector(
        model_path="models/best.pt",
        confidence_threshold=0.25,
        device="cpu"
    )

    val_images = sorted(glob.glob("datasets/unified_disasters_yolo/images/val/*.jpg"))
    if not val_images:
        print("[Error] No validation images found in datasets/unified_disasters_yolo/images/val/")
        return

    selected_images = val_images[:num_samples]
    os.makedirs(output_dir, exist_ok=True)

    records = []

    print(f"Evaluating {len(selected_images)} validation images...\n")

    for idx, img_path in enumerate(selected_images, 1):
        filename = os.path.basename(img_path)
        vis_out = os.path.join(output_dir, f"comparison_{filename}")
        
        res = detector.compare_and_visualize(
            image_path=img_path,
            output_path=vis_out if idx <= 8 else None, # Save first 8 visual comparisons
            slice_size=320
        )

        std_cnt = res["standard_count"]
        sahi_cnt = res["sahi_count"]
        diff = sahi_cnt - std_cnt

        records.append({
            "image": filename,
            "standard_count": std_cnt,
            "sahi_count": sahi_cnt,
            "additional_hazards_caught": diff,
            "gain_pct": res["recall_gain_pct"]
        })

        tag = f"(+{diff} extra hazards detected)" if diff > 0 else "(Equal)"
        print(f"[{idx:02d}/{len(selected_images):02d}] {filename:15s} | Standard: {std_cnt} -> SAHI: {sahi_cnt} {tag}")

    df = pd.DataFrame(records)
    total_std = df["standard_count"].sum()
    total_sahi = df["sahi_count"].sum()
    total_gain = total_sahi - total_std
    overall_gain_pct = (total_gain / max(1, total_std)) * 100

    print("\n" + "=" * 65)
    print("                 BENCHMARK ACCURACY SUMMARY                      ")
    print("=" * 65)
    print(f"Total Evaluated Images:         {len(df)}")
    print(f"Total Standard YOLO Detections: {total_std}")
    print(f"Total SAHI Sliced Detections:   {total_sahi}")
    print(f"Net Additional Hazards Caught:  +{total_gain}")
    print(f"Detection Recall Boost:         +{overall_gain_pct:.1f}%")
    print(f"Visual Comparisons Saved To:    {output_dir}/")
    print("=" * 65)

    summary_csv = os.path.join(output_dir, "sahi_benchmark_results.csv")
    df.to_csv(summary_csv, index=False)
    print(f"Saved metrics CSV to: {summary_csv}")

if __name__ == "__main__":
    run_benchmark(num_samples=15)
