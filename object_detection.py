import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any
from vision_agents_config import VISION_AGENTS_CFG

class ObjectDetector:
    """YOLO-based object detection for driving scenarios"""
    
    # Driving-critical objects
    CRITICAL_CLASSES = {
        'person': 'pedestrian',
        'bicycle': 'bicycle',
        'car': 'vehicle',
        'motorcycle': 'motorcycle',
        'bus': 'bus',
        'truck': 'truck',
        'traffic light': 'traffic_light',
        'stop sign': 'stop_sign',
    }
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or VISION_AGENTS_CFG['yolo']['model']
        self.conf_threshold = VISION_AGENTS_CFG['yolo']['conf_threshold']
        self.device = VISION_AGENTS_CFG['yolo']['device']
        self.model = YOLO(self.model_name)
        
        # Try to use specified device, fallback to CPU if not available
        try:
            self.model.to(self.device)
        except (AssertionError, RuntimeError) as e:
            print(f"⚠️  Device '{self.device}' not available: {str(e)[:50]}... using CPU")
            self.device = 'cpu'
            self.model.to('cpu')
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in frame with driving context"""
        results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]
        detections = []
        
        h, w = frame.shape[:2]
        
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = self.model.names[cls_id]
            
            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            x_center = (x1 + x2) / 2 / w  # Normalized
            y_center = (y1 + y2) / 2 / h  # Normalized
            
            # Calculate relative position
            if x_center < 0.33:
                position = 'left'
            elif x_center > 0.67:
                position = 'right'
            else:
                position = 'center'
            
            # Estimate distance based on size (simplified)
            box_area = (x2 - x1) * (y2 - y1)
            normalized_area = box_area / (w * h)
            estimated_distance = 'far' if normalized_area < 0.05 else 'near' if normalized_area > 0.2 else 'medium'
            
            detection = {
                'label': label,
                'confidence': conf,
                'bbox': {'x1': float(x1), 'y1': float(y1), 'x2': float(x2), 'y2': float(y2)},
                'normalized_position': {'x': float(x_center), 'y': float(y_center)},
                'direction': position,
                'distance_estimate': estimated_distance,
                'is_critical': label in self.CRITICAL_CLASSES,
                'friendly_label': self.CRITICAL_CLASSES.get(label, label),
            }
            detections.append(detection)
        
        return detections
    
    def get_critical_objects(self, detections: List[Dict]) -> List[Dict]:
        """Filter for driving-critical objects"""
        return [d for d in detections if d['is_critical']]

# Global detector instance
_detector = None

def get_detector() -> ObjectDetector:
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = ObjectDetector()
    return _detector

def detect_objects(frame: np.ndarray) -> List[Dict[str, Any]]:
    """Detect objects in frame"""
    detector = get_detector()
    return detector.detect(frame)