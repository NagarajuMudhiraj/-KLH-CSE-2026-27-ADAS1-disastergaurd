"""
SAHI (Slicing Aided Hyper Inference) Integration for YOLOv11 Master Disaster Detector.
Provides high-resolution multi-scale slicing to detect subtle, distant, and small-scale
hazards (submerged road boundaries, distant pedestrians, small road fissures, isolated flames).
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Union, Optional
from ultralytics import YOLO

try:
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction
    SAHI_AVAILABLE = True
except ImportError:
    SAHI_AVAILABLE = False


class SahiDisasterDetector:
    """
    Enhanced disaster hazard detection combining global full-frame inference
    with multi-patch overlapping window slicing (SAHI).
    """

    def __init__(
        self,
        model_path: str = "models/best.pt",
        confidence_threshold: float = 0.25,
        device: str = "cpu"
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Load baseline standard YOLO
        self.standard_model = YOLO(model_path)
        self.class_names = self.standard_model.names
        
        # Load SAHI Model Wrapper
        if SAHI_AVAILABLE:
            self.sahi_model = AutoDetectionModel.from_pretrained(
                model_type="ultralytics",
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device
            )
        else:
            self.sahi_model = None
            print("[Warning] SAHI package not detected. Falling back to standard YOLOv11.")

    def predict_standard(
        self,
        image: Union[str, np.ndarray],
        conf: Optional[float] = None,
        imgsz: int = 640
    ) -> List[Dict[str, Any]]:
        """Run standard single-pass full-frame YOLOv11 detection."""
        confidence = conf if conf is not None else self.confidence_threshold
        results = self.standard_model(image, conf=confidence, imgsz=imgsz, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            score = float(box.conf[0])
            xyxy = [float(v) for v in box.xyxy[0].cpu().numpy()]
            detections.append({
                "class_id": cls_id,
                "class_name": self.class_names.get(cls_id, f"Hazard_{cls_id}"),
                "confidence": round(score, 3),
                "bbox": [round(x, 1) for x in xyxy]
            })
        return detections

    def predict_sahi(
        self,
        image: Union[str, np.ndarray],
        slice_height: int = 320,
        slice_width: int = 320,
        overlap_height_ratio: float = 0.2,
        overlap_width_ratio: float = 0.2,
        perform_standard_pred: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run multi-scale sliced inference (SAHI).
        Slices the input frame into overlapping tiles, evaluates each at full resolution,
        and fuses results with full-image macro predictions.
        """
        if not SAHI_AVAILABLE or self.sahi_model is None:
            return self.predict_standard(image)

        # Convert numpy array to RGB if needed (SAHI expects RGB / file path)
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_img = image
            input_data = rgb_img
        else:
            input_data = image

        result = get_sliced_prediction(
            input_data,
            self.sahi_model,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_height_ratio=overlap_height_ratio,
            overlap_width_ratio=overlap_width_ratio,
            perform_standard_pred=perform_standard_pred,
            verbose=0
        )

        detections = []
        for pred in result.object_prediction_list:
            cls_name = pred.category.name
            cls_id = pred.category.id
            score = float(pred.score.value)
            xyxy = [float(v) for v in pred.bbox.to_xyxy()]
            detections.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": round(score, 3),
                "bbox": [round(x, 1) for x in xyxy]
            })
            
        return detections

    def compare_and_visualize(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        slice_size: int = 320
    ) -> Dict[str, Any]:
        """
        Produce a side-by-side visual comparison between Standard YOLO and SAHI Sliced YOLO.
        """
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        h, w = img_bgr.shape[:2]
        
        # Standard Run
        dets_std = self.predict_standard(img_bgr, imgsz=640)
        # SAHI Run
        dets_sahi = self.predict_sahi(img_bgr, slice_height=slice_size, slice_width=slice_size)

        # Draw Standard Frame
        frame_std = img_bgr.copy()
        cv2.putText(frame_std, f"Standard YOLOv11 (Count: {len(dets_std)})", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        for d in dets_std:
            x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
            cv2.rectangle(frame_std, (x1, y1), (x2, y2), (0, 0, 240), 2)
            tag = f"{d['class_name']} {d['confidence']:.2f}"
            cv2.putText(frame_std, tag, (x1, max(y1 - 6, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 240), 1)

        # Draw SAHI Frame
        frame_sahi = img_bgr.copy()
        cv2.putText(frame_sahi, f"SAHI Multi-Scale Sliced (Count: {len(dets_sahi)})", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 200, 0), 2)
        for d in dets_sahi:
            x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
            cv2.rectangle(frame_sahi, (x1, y1), (x2, y2), (0, 200, 0), 2)
            tag = f"{d['class_name']} {d['confidence']:.2f}"
            cv2.putText(frame_sahi, tag, (x1, max(y1 - 6, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)

        # Concatenate side by side
        side_by_side = np.hstack([frame_std, frame_sahi])

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            cv2.imwrite(output_path, side_by_side)

        return {
            "image_path": image_path,
            "standard_count": len(dets_std),
            "sahi_count": len(dets_sahi),
            "recall_gain_pct": round(((len(dets_sahi) - len(dets_std)) / max(1, len(dets_std))) * 100, 1),
            "standard_detections": dets_std,
            "sahi_detections": dets_sahi,
            "output_visualization": output_path
        }
