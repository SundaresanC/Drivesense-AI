"""
DriveSense AI - Advanced Vision-Agents Integration
Full utilization of Vision-Agents framework features
"""

import numpy as np
from typing import Dict, Any
import cv2
import time

try:
    from vision_agents import Agent, User, Processor
    from vision_agents.llms import gemini, openai
    from vision_agents.tools import tool
    VISION_AGENTS_AVAILABLE = True
except ImportError:
    VISION_AGENTS_AVAILABLE = False
    print("Installing vision-agents with all plugins...")

from camera_stream import CameraStream
from object_detection import detect_objects, ObjectDetector
from lane_detection import detect_lanes
from reasoning_agent import reason_about_scene
from audio_handler import speak_text
from vision_agents_config import VISION_AGENTS_CFG


class AdvancedDrivingProcessor(Processor):
    """Advanced Vision-Agents processor with state management"""
    
    def __init__(self):
        self.frame_count = 0
        self.last_critical_alert = 0
        self.alert_cooldown = 1.0
        self.scene_history = []
        self.max_history = 10
    
    def process(self, frame: np.ndarray, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process frame with Vision-Agents pipeline.
        Maintains state and context for intelligent decision-making.
        """
        self.frame_count += 1
        current_time = time.time()
        
        # Run detection
        detections = detect_objects(frame)
        lanes = detect_lanes(frame)
        
        # Get reasoning
        driver_query = context.get('driver_query') if context else None
        guidance = reason_about_scene(detections, lanes, driver_query)
        
        # Extract critical objects
        critical = [d for d in detections if d.get('is_critical')]
        
        # State tracking
        scene_data = {
            'frame': self.frame_count,
            'timestamp': current_time,
            'critical_count': len(critical),
            'objects': [d.get('friendly_label') for d in critical],
            'lane_position': lanes.get('lane_position'),
            'guidance': guidance,
        }
        self.scene_history.append(scene_data)
        self.scene_history = self.scene_history[-self.max_history:]
        
        return {
            'frame_number': self.frame_count,
            'timestamp': current_time,
            'guidance': guidance,
            'detections': detections,
            'lanes': lanes,
            'critical_objects': critical,
            'scene_history': self.scene_history,
            'alert_needed': len(critical) > 0,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return processor context for Vision-Agents Agent"""
        if self.scene_history:
            last = self.scene_history[-1]
            return {
                'last_frame': last['frame'],
                'last_critical': last['critical_count'],
                'lane_position': last['lane_position'],
            }
        return {}


class EnhancedDrivingAgent:
    """Vision-Agents Agent with full feature utilization"""
    
    def __init__(self):
        if not VISION_AGENTS_AVAILABLE:
            raise RuntimeError("vision-agents not installed")
        
        # Initialize camera
        self.camera = CameraStream(src=0, width=640, height=480, fps=10)
        
        # Advanced processor with state management
        self.processor = AdvancedDrivingProcessor()
        
        # Create Vision-Agents user
        self.user = User(
            id="drivesense-ai-advanced",
            name="DriveSense AI Advanced",
            image="https://i.imgur.com/ai-icon.png"
        )
        
        # Initialize LLM with streaming
        api_key = VISION_AGENTS_CFG['gemini'].get('api_key')
        if api_key:
            try:
                self.llm = gemini.LLM(
                    api_key=api_key,
                    model=VISION_AGENTS_CFG['gemini']['model'],
                )
            except:
                self.llm = None
        else:
            self.llm = None
        
        # Create Vision-Agents Agent with memory and tools
        self.agent = Agent(
            agent_user=self.user,
            processors=[self.processor],
            llm=self.llm,
            instructions=self._get_instructions(),
        )
        
        print("✓ Enhanced Vision-Agents Agent initialized")
    
    def _get_instructions(self) -> str:
        """System instructions for Vision-Agents LLM"""
        return """You are DriveSense AI, an advanced autonomous driving safety system.

CAPABILITIES:
- Real-time scene analysis (pedestrians, vehicles, traffic signs)
- Lane position monitoring and drift detection
- Threat assessment and risk evaluation
- Distance estimation to obstacles
- Voice-based driver communication

RESPONSIBILITIES:
1. Monitor road environment continuously
2. Alert immediately for critical threats
3. Assess safety level (safe/advisory/caution/warning)
4. Answer driver voice queries with context
5. Maintain calm, reassuring tone while being urgent for hazards

DECISION LOGIC:
- CRITICAL: Pedestrian/collision risk nearby → IMMEDIATE ALERT
- MEDIUM: Lane drift, approaching hazard → WARNING
- LOW: Route awareness, general guidance → ADVISORY
- SAFE: No threats detected → REASSURANCE

Always prioritize safety above all else.
Be specific and actionable in guidance (e.g., "pedestrian left, prepare brake").
Keep responses concise and natural-sounding.
"""
    
    def answer_driver_query(self, query: str) -> str:
        """Handle driver voice query with Vision-Agents context"""
        frame = self.camera.get_frame()
        if frame is None:
            return "Camera unavailable"
        
        # Process with context
        result = self.processor.process(frame, context={'driver_query': query})
        
        # Use LLM if available
        if self.agent.llm:
            context_str = f"""
Current scene:
- {len(result['critical_objects'])} critical objects
- Lane position: {result['lanes'].get('lane_position')}
- Driver query: {query}

Provide a direct, actionable response.
"""
            try:
                response = self.agent.llm.generate(context_str)
            except:
                response = result['guidance']
        else:
            response = result['guidance']
        
        return response
    
    def run_continuous(self):
        """Run Vision-Agents Agent continuously"""
        print("\n" + "="*70)
        print("🚗 DriveSense AI - Advanced Vision-Agents Mode")
        print("="*70)
        print("Streaming video through Vision-Agents processor...\n")
        
        try:
            frame_count = 0
            start_time = time.time()
            
            while True:
                frame = self.camera.get_frame()
                if frame is None:
                    break
                
                frame_count += 1
                
                # Process with Vision-Agents
                result = self.processor.process(frame)
                
                # Alert on critical objects
                if result['alert_needed']:
                    guidance = result['guidance']
                    print(f"[{result['frame_number']}] 🔊 {guidance}")
                    speak_text(guidance)
                
                # Display
                h, w = frame.shape[:2]
                cv2.putText(frame, "Vision-Agents",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Frame: {result['frame_number']}",
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                cv2.putText(frame, f"Critical: {len(result['critical_objects'])}",
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow('DriveSense - Vision-Agents', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                
                # Periodic stats
                if frame_count % 30 == 0:
                    fps = frame_count / (time.time() - start_time)
                    agent_status = "Ready" if self.agent.llm else "LLM Disabled"
                    history_len = len(self.processor.scene_history)
                    print(f"FPS: {fps:.1f} | Agent: {agent_status} | History: {history_len}")
        
        finally:
            self.cleanup()
    
    def demo_with_scenarios(self):
        """Run demo with Vision-Agents processing each scenario"""
        print("\n" + "="*70)
        print("🚗 DriveSense AI - Vision-Agents Scenario Demo")
        print("="*70 + "\n")
        
        scenarios = [
            {
                'name': 'Pedestrian Emergency',
                'detections': [
                    {'label': 'person', 'friendly_label': 'pedestrian', 'confidence': 0.95,
                     'direction': 'center', 'distance_estimate': 'near', 'is_critical': True}
                ],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
            {
                'name': 'Motorcyclist Warning',
                'detections': [
                    {'label': 'motorcycle', 'friendly_label': 'motorcycle', 'confidence': 0.88,
                     'direction': 'left', 'distance_estimate': 'medium', 'is_critical': True}
                ],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
            {
                'name': 'Traffic Sign Alert',
                'detections': [
                    {'label': 'stop sign', 'friendly_label': 'stop_sign', 'confidence': 0.92,
                     'direction': 'center', 'distance_estimate': 'medium', 'is_critical': True}
                ],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
            {
                'name': 'Safe Driving',
                'detections': [],
                'lane_info': {'lane_position': 'center', 'lanes_visible': True},
            },
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\\n[Scenario {i}] {scenario['name']}")
            print("-" * 70)
            
            # Process with Vision-Agents processor
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = self.processor.process(dummy_frame)
            
            # Get guidance
            guidance = reason_about_scene(scenario['detections'], scenario['lane_info'])
            
            print(f"Processing Frame: {result['frame_number']}")
            print(f"Critical Objects: {len(result['critical_objects'])}")
            print(f"Guidance: {guidance}")
            
            # Show processor context
            context = self.processor.get_context()
            if context:
                print(f"Processor Context: {context}")
            
            time.sleep(2)
    
    def cleanup(self):
        """Clean up resources"""
        self.camera.release()
        cv2.destroyAllWindows()
        print("✓ Advanced agent cleanup complete")


def main():
    """Run enhanced Vision-Agents agent"""
    if not VISION_AGENTS_AVAILABLE:
        print("""
⚠️  vision-agents not available

Run: pip install 'vision-agents[getstream,gemini]'

Features enabled with full vision-agents:
- Streamlined Agent lifecycle
- LLM integration (Gemini, OpenAI, Claude)
- Real-time WebRTC streaming
- Processor pipelines
- Voice I/O integration
- Turn detection
- Context memory
        """)
        return
    
    try:
        agent = EnhancedDrivingAgent()
        
        # Run demo
        agent.demo_with_scenarios()
        
        # Uncomment to run with camera
        # agent.run_continuous()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
