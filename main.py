"""
DriveSense AI - Real-time Driving Companion
Maximum Vision-Agents Framework Integration
"""

import cv2
import time
import sys
import os
import numpy as np
from typing import Optional, Dict, Any

# Vision-Agents Framework Integration
try:
    from vision_agents import Agent, User, Processor
    from vision_agents.llms import gemini
    VISION_AGENTS_AVAILABLE = True
except ImportError:
    VISION_AGENTS_AVAILABLE = False
    class Processor:
        def process(self, frame, context=None):
            return frame

from camera_stream import CameraStream
from object_detection import detect_objects
from lane_detection import detect_lanes
from reasoning_agent import reason_about_scene
from audio_handler import speak_text
from vision_agents_config import VISION_AGENTS_CFG


class DrivingSafetyProcessor(Processor):
    """Vision-Agents compatible processor for driving analysis"""
    
    def __init__(self):
        self.frame_count = 0
    
    def process(self, frame: np.ndarray, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process frame with Vision-Agents pipeline"""
        self.frame_count += 1
        
        detections = detect_objects(frame)
        lanes = detect_lanes(frame)
        guidance = reason_about_scene(detections, lanes)
        
        return {
            'frame_number': self.frame_count,
            'guidance': guidance,
            'detections': detections,
            'lanes': lanes,
        }


class DrivingCompanion:
    """Main AI Driving Companion with Vision-Agents Integration"""
    
    def __init__(self, use_camera: bool = True, use_vision_agents: bool = True, video_path: Optional[str] = None):
        self.use_camera = use_camera
        self.use_vision_agents = use_vision_agents and VISION_AGENTS_AVAILABLE
        self.running = False
        self.last_guidance_time = 0
        self.guidance_interval = 2.0
        self.vision_agents_ready = False
        self.video_path = video_path
        
        # Initialize camera or video
        if self.video_path:
            print(f"✓ Video mode: {self.video_path}")
            self.use_camera = False
        elif self.use_camera:
            try:
                self.camera = CameraStream(src=0, width=640, height=480, fps=10)
                print("✓ Camera initialized")
            except Exception as e:
                print(f"✗ Camera failed: {e}")
                self.use_camera = False
        
        # Initialize Vision-Agents
        if self.use_vision_agents:
            self._initialize_vision_agents()
        else:
            print("⚠️  Vision-Agents disabled (using local processing)")
    
    def _initialize_vision_agents(self):
        """Initialize Vision-Agents framework"""
        try:
            # Create processor
            self.processor = DrivingSafetyProcessor()
            
            # Create agent user
            self.agent_user = User(
                id="drivesense-ai",
                name="DriveSense AI"
            )
            
            # Initialize LLM
            api_key = VISION_AGENTS_CFG['gemini'].get('api_key', '')
            if api_key:
                try:
                    self.llm = gemini.LLM(
                        api_key=api_key,
                        model=VISION_AGENTS_CFG['gemini']['model']
                    )
                except Exception as e:
                    print(f"⚠️  Gemini LLM init failed: {e}")
                    self.llm = None
            else:
                self.llm = None
            
            # Create Vision-Agents Agent
            self.agent = Agent(
                agent_user=self.agent_user,
                processors=[self.processor],
                llm=self.llm,
                instructions="""You are DriveSense AI, an advanced driving assistant.
Analyze road scenes and provide real-time safety guidance.
Alert about pedestrians, vehicles, and traffic signs.
Assess lane position and warn of drifts.
Prioritize immediate safety warnings."""
            )
            
            print("✓ Vision-Agents Agent initialized")
            self.vision_agents_ready = True
            
        except Exception as e:
            print(f"⚠️  Vision-Agents initialization failed: {e}")
            self.vision_agents_ready = False
    
    def run_demo(self):
        """Run demonstration with Vision-Agents"""
        print("\n" + "="*70)
        print("🚗 DriveSense AI - Hackathon Demo")
        print("="*70)
        print(f"Vision-Agents: {'✓ Active' if self.vision_agents_ready else '⚠️ Disabled'}\n")
        
        scenarios = [
            {
                'name': 'Pedestrian Crossing (CRITICAL)',
                'detections': [
                    {
                        'label': 'person',
                        'friendly_label': 'pedestrian',
                        'confidence': 0.92,
                        'direction': 'center',
                        'distance_estimate': 'near',
                        'is_critical': True,
                    }
                ],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
            {
                'name': 'Vehicle Collision Risk (CRITICAL)',
                'detections': [
                    {
                        'label': 'car',
                        'friendly_label': 'car',
                        'confidence': 0.88,
                        'direction': 'center',
                        'distance_estimate': 'near',
                        'is_critical': True,
                    }
                ],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
            {
                'name': 'Lane Drift Warning (MEDIUM)',
                'detections': [],
                'lane_info': {'lane_position': 'left', 'lanes_visible': True},
            },
            {
                'name': 'Clear Road (SAFE)',
                'detections': [],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
        ]
        
        for scenario in scenarios:
            print(f"📋 {scenario['name']}")
            print("-" * 70)
            
            # Process with Vision-Agents processor if available
            if self.vision_agents_ready:
                dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                result = self.processor.process(dummy_frame)
                print(f"Processor Frame: {result['frame_number']}")
            
            guidance = reason_about_scene(scenario['detections'], scenario['lane_info'])
            
            print(f"Lane Position: {scenario['lane_info']['lane_position']}")
            if scenario['detections']:
                print(f"Objects Detected: {len(scenario['detections'])}")
            
            print(f"\n🔊 Guidance: {guidance}\n")
            time.sleep(2)
    
    def run_realtime(self):
        """Run with real camera input and Vision-Agents"""
        if not self.use_camera:
            print("Camera not available. Running demo mode.")
            self.run_demo()
            return
        
        print("\n" + "="*70)
        print("🚗 DriveSense AI - Real-Time Mode")
        print("="*70)
        print("Press 'q' to quit | 's' for screenshot\n")
        
        self.running = True
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                frame = self.camera.get_frame()
                if frame is None:
                    break
                
                frame_count += 1
                
                # Process with Vision-Agents if available
                if self.vision_agents_ready and hasattr(self, 'processor'):
                    result = self.processor.process(frame)
                    detections = result['detections']
                    lanes = result['lanes']
                    guidance = result['guidance']
                else:
                    detections = detect_objects(frame)
                    lanes = detect_lanes(frame)
                    guidance = reason_about_scene(detections, lanes)
                
                # Periodic guidance
                current_time = time.time()
                if current_time - self.last_guidance_time >= self.guidance_interval:
                    if any(d.get('is_critical') for d in detections if d):
                        print(f"🔊 {guidance}")
                        speak_text(guidance)
                    self.last_guidance_time = current_time
                
                # Display info
                h, w = frame.shape[:2]
                cv2.putText(frame, f"Lane: {lanes.get('lane_position')}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, f"Objects: {len(detections)}",
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(frame, f"Vision-Agents: {'✓' if self.vision_agents_ready else '⚠'}",
                           (w-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow('DriveSense AI', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"drivesense_{int(time.time())}.png"
                    cv2.imwrite(filename, frame)
                    print(f"✓ Screenshot: {filename}")
                
                # FPS
                if frame_count % 30 == 0:
                    fps = frame_count / (time.time() - start_time)
                    print(f"FPS: {fps:.1f} | Objects: {len(detections)} | Mode: {'Vision-Agents' if self.vision_agents_ready else 'Local'}")
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def run_video(self):
        """Run with video file input and Vision-Agents"""
        if not self.video_path or not os.path.exists(self.video_path):
            print(f"✗ Video file not found: {self.video_path}")
            return
        
        print("\n" + "="*70)
        print(f"🎥 DriveSense AI - Video Simulation Mode")
        print(f"📽️  Video: {self.video_path}")
        print("="*70)
        print(f"Vision-Agents: {'✓ Active' if self.vision_agents_ready else '⚠️ Disabled'}\n")
        
        # Open video file
        video = cv2.VideoCapture(self.video_path)
        if not video.isOpened():
            print(f"✗ Cannot open video: {self.video_path}")
            return
        
        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Resolution: {width}x{height} | FPS: {fps:.1f} | Total Frames: {frame_count}")
        print(f"Duration: {frame_count/fps:.1f}s")
        print("Press 'q' to quit | 's' for screenshot\n")
        
        self.running = True
        frame_idx = 0
        start_time = time.time()
        analyzed_frames = 0
        
        try:
            while self.running:
                ret, frame = video.read()
                if not ret:
                    print("\n✓ Video ended")
                    break
                
                frame_idx += 1
                
                # Resize frame for consistent processing
                frame = cv2.resize(frame, (640, 480))
                
                # Process with Vision-Agents if available
                if self.vision_agents_ready and hasattr(self, 'processor'):
                    result = self.processor.process(frame)
                    detections = result['detections']
                    lanes = result['lanes']
                    guidance = result['guidance']
                else:
                    detections = detect_objects(frame)
                    lanes = detect_lanes(frame)
                    guidance = reason_about_scene(detections, lanes)
                
                analyzed_frames += 1
                
                # Count threats
                critical_count = sum(1 for d in detections if d and d.get('is_critical'))
                
                # Periodic guidance
                current_time = time.time()
                if current_time - self.last_guidance_time >= self.guidance_interval:
                    if critical_count > 0:
                        print(f"⏱️  Frame {frame_idx}: 🔊 {guidance}")
                        speak_text(guidance)
                    self.last_guidance_time = current_time
                
                # Display info on frame
                h, w = frame.shape[:2]
                
                # Background for text
                cv2.rectangle(frame, (5, 5), (w-5, 120), (0, 0, 0), -1)
                cv2.rectangle(frame, (5, 5), (w-5, 120), (100, 255, 0), 2)
                
                # Text info
                info = [
                    f"Video: {self.video_path.split('/')[-1]} | Frame: {frame_idx}/{frame_count}",
                    f"Lane: {lanes.get('lane_position', 'unknown').upper()} | Objects: {len(detections)} | Critical: {critical_count}",
                    f"Vision-Agents: {'✓' if self.vision_agents_ready else '⚠'} | Time: {current_time - start_time:.1f}s",
                    f"Guidance: {guidance[:50]}..."
                ]
                
                for i, text in enumerate(info):
                    cv2.putText(frame, text, (15, 30 + i*20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Draw detection boxes
                for detection in detections:
                    if detection:
                        label = detection.get('friendly_label', 'object')
                        conf = detection.get('confidence', 0)
                        is_critical = detection.get('is_critical', False)
                        color = (0, 0, 255) if is_critical else (0, 255, 0)
                        
                        # Draw a box in the center (simplified)
                        center_x, center_y = w // 2, h // 2
                        box_size = 80
                        cv2.rectangle(frame, 
                                     (center_x - box_size, center_y - box_size),
                                     (center_x + box_size, center_y + box_size),
                                     color, 2)
                        cv2.putText(frame, f"{label} ({conf:.2f})", 
                                   (center_x - box_size, center_y - box_size - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Try to display, handle headless scenarios
                try:
                    cv2.imshow('🚗 DriveSense AI - Video Simulation', frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        filename = f"screenshot_{frame_idx}.png"
                        cv2.imwrite(filename, frame)
                        print(f"✓ Screenshot: {filename}")
                except cv2.error as e:
                    # No display available, skip visualization but continue processing
                    pass
                
                # Progress every 30 frames
                if frame_idx % 30 == 0:
                    elapsed = time.time() - start_time
                    progress = (frame_idx / frame_count) * 100
                    print(f"Progress: {progress:.0f}% | Frame: {frame_idx}/{frame_count} | Threats detected: {critical_count}")
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            video.release()
            self.cleanup()
    

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.use_camera:
            self.camera.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            # Display not available, that's okay
            pass
        print("✓ Cleanup complete")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='DriveSense AI - Vision-Agents Powered')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    parser.add_argument('--camera', action='store_true', help='Use camera')
    parser.add_argument('--video', type=str, help='Path to video file to process')
    args = parser.parse_args()
    
    # Determine mode
    if args.video:
        # Video mode
        companion = DrivingCompanion(use_camera=False, use_vision_agents=True, video_path=args.video)
        companion.run_video()
    else:
        # Camera or demo mode
        use_camera = args.camera or (not args.demo)
        companion = DrivingCompanion(use_camera=use_camera, use_vision_agents=True)
        
        if args.demo or not use_camera:
            companion.run_demo()
        else:
            companion.run_realtime()


if __name__ == "__main__":
    main()
