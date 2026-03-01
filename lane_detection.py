import cv2
import numpy as np
from typing import Dict, Any, List

class LaneDetector:
    """Advanced lane detection for driving assistance"""
    
    def __init__(self, roi_height_ratio: float = 0.6):
        self.roi_height_ratio = roi_height_ratio
    
    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect lanes and provide guidance"""
        h, w = frame.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blur, 50, 150)
        
        # Focus on lower portion of image (where lanes are)
        roi_y_start = int(h * (1 - self.roi_height_ratio))
        roi = edges[roi_y_start:, :]
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            roi,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=50,
            maxLineGap=50
        )
        
        lane_info = {
            'edges_detected': edges,
            'lines_raw': lines,
            'line_count': len(lines) if lines is not None else 0,
            'lanes_visible': lines is not None and len(lines) > 0,
        }
        
        if lines is not None:
            # Analyze lane position
            left_lines = []
            right_lines = []
            center_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                mid_x = (x1 + x2) / 2
                
                if mid_x < w / 2 - 50:
                    left_lines.append(line)
                elif mid_x > w / 2 + 50:
                    right_lines.append(line)
                else:
                    center_lines.append(line)
            
            lane_info['left_lane_visible'] = len(left_lines) > 0
            lane_info['right_lane_visible'] = len(right_lines) > 0
            lane_info['centered'] = len(center_lines) > len(left_lines) or len(center_lines) > len(right_lines)
            lane_info['lane_position'] = 'center' if lane_info['centered'] else 'left' if len(left_lines) > 0 else 'right'
        else:
            lane_info['left_lane_visible'] = False
            lane_info['right_lane_visible'] = False
            lane_info['centered'] = False
            lane_info['lane_position'] = 'unknown'
        
        return lane_info
    
    def get_guidance(self, lane_info: Dict[str, Any]) -> str:
        """Generate lane guidance based on detection"""
        if not lane_info['lanes_visible']:
            return "Warning: No lane markings detected. Proceed with caution."
        
        if not lane_info['left_lane_visible'] and not lane_info['right_lane_visible']:
            return "Caution: Only center lane detected."
        
        if lane_info['centered']:
            return "You are centered in your lane."
        elif lane_info['lane_position'] == 'left':
            return "You are drifting left. Steer right gently."
        elif lane_info['lane_position'] == 'right':
            return "You are drifting right. Steer left gently."
        
        return "Lane position normal."

# Global detector instance
_detector = None

def get_detector() -> LaneDetector:
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = LaneDetector()
    return _detector

def detect_lanes(frame: np.ndarray) -> Dict[str, Any]:
    """Detect lanes in frame"""
    detector = get_detector()
    return detector.detect(frame)