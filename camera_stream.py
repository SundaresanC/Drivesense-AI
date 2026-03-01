import cv2
import numpy as np
from typing import Optional, Tuple

class CameraStream:
    """Real-time camera stream handler with preprocessing"""
    
    def __init__(self, src: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.cap = cv2.VideoCapture(src)
        self.width = width
        self.height = height
        self.fps = fps
        
        # Configure camera for optimal performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
        
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get next frame from camera"""
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame
    
    def get_frame_rgb(self) -> Optional[np.ndarray]:
        """Get frame in RGB format (for vision models)"""
        frame = self.get_frame()
        if frame is None:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def get_properties(self) -> dict:
        """Get camera properties"""
        return {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
        }
    
    def release(self):
        """Release camera resources"""
        self.cap.release()