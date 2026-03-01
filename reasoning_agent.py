import json
from typing import Dict, List, Any
from vision_agents_config import VISION_AGENTS_CFG

class DrivingReasoningAgent:
    """
    Multi-modal reasoning agent for driving assistance.
    Analyzes visual detections, lane position, and driver context
    to provide intelligent, real-time guidance.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.last_guidance = ""
        self.consecutive_warnings = 0
        self.context_memory = {
            'last_objects': [],
            'last_lane_position': 'unknown',
            'speed_estimate': 'moderate',
        }
    
    def analyze_scene(self, detections: List[Dict], lane_info: Dict, driver_query: str = None) -> Dict[str, Any]:
        """
        Analyze driving scene and generate intelligent guidance.
        
        Args:
            detections: Object detection results
            lane_info: Lane detection results
            driver_query: Optional driver voice query
        
        Returns:
            Analysis result with guidance and reasoning
        """
        # Extract critical objects
        critical_objects = [d for d in detections if d.get('is_critical', False)]
        
        # Analyze immediate threats
        threats = self._assess_threats(critical_objects, lane_info)
        
        # Generate guidance
        guidance = self._generate_guidance(threats, lane_info, driver_query)
        
        # Build response
        analysis = {
            'timestamp': None,
            'objects_detected': len(detections),
            'critical_objects': len(critical_objects),
            'threats_identified': threats,
            'lane_status': lane_info.get('lane_position', 'unknown'),
            'guidance': guidance['main'],
            'guidance_priority': guidance['priority'],
            'safety_level': guidance['safety_level'],
            'recommendations': guidance['recommendations'],
            'driver_response_needed': guidance['driver_response_needed'],
        }
        
        if self.verbose:
            print(f"\n[SCENE ANALYSIS]")
            print(f"Objects: {analysis['objects_detected']}, Critical: {analysis['critical_objects']}")
            print(f"Threats: {len(threats)}")
            print(f"Safety Level: {analysis['safety_level']}")
        
        # Update memory
        self.context_memory['last_objects'] = critical_objects
        self.context_memory['last_lane_position'] = lane_info.get('lane_position', 'unknown')
        
        return analysis
    
    def _assess_threats(self, objects: List[Dict], lane_info: Dict) -> List[Dict]:
        """Identify immediate threats in the scene"""
        threats = []
        
        # Check for pedestrians too close
        pedestrians = [o for o in objects if 'pedestrian' in o.get('friendly_label', '').lower()]
        for ped in pedestrians:
            distance = ped.get('distance_estimate', 'far')
            position = ped.get('direction', 'center')
            
            if distance in ['near', 'medium']:
                threats.append({
                    'type': 'pedestrian_crossing',
                    'severity': 'high' if distance == 'near' else 'medium',
                    'position': position,
                    'action': f'Pedestrian {position}. Prepare to brake.',
                })
        
        # Check for vehicles too close
        vehicles = [o for o in objects if any(v in o.get('friendly_label', '').lower() for v in ['vehicle', 'car', 'truck', 'bus'])]
        for veh in vehicles:
            distance = veh.get('distance_estimate', 'far')
            position = veh.get('direction', 'center')
            
            if distance == 'near':
                threats.append({
                    'type': 'vehicle_collision_risk',
                    'severity': 'high',
                    'position': position,
                    'action': f'Vehicle ahead {position}. Maintain safe distance.',
                })
        
        # Check for traffic signs
        traffic_signs = [o for o in objects if 'traffic' in o.get('friendly_label', '').lower() or 'stop' in o.get('friendly_label', '').lower()]
        if traffic_signs:
            threats.append({
                'type': 'traffic_sign',
                'severity': 'medium',
                'action': f'Traffic sign detected: {traffic_signs[0]["friendly_label"]}',
            })
        
        # Check lane drifting
        if lane_info.get('lane_position') != 'center':
            threats.append({
                'type': 'lane_drift',
                'severity': 'low',
                'action': f'Drifting {lane_info["lane_position"]}. Adjust steering.',
            })
        
        return threats
    
    def _generate_guidance(self, threats: List[Dict], lane_info: Dict, driver_query: str = None) -> Dict[str, Any]:
        """
        Generate driving guidance based on threats and context.
        """
        if not threats:
            guidance_text = "Road is clear. Safe to proceed."
            priority = "low"
            safety_level = "safe"
            driver_response = False
            recommendations = ["Maintain current speed and lane position"]
        else:
            # Sort by severity
            critical_threats = [t for t in threats if t.get('severity') == 'high']
            medium_threats = [t for t in threats if t.get('severity') == 'medium']
            
            if critical_threats:
                guidance_text = critical_threats[0]['action']
                priority = "critical"
                safety_level = "warning"
                driver_response = True
                recommendations = [t['action'] for t in critical_threats]
            elif medium_threats:
                guidance_text = medium_threats[0]['action']
                priority = "high"
                safety_level = "caution"
                driver_response = True
                recommendations = [t['action'] for t in medium_threats] + [t['action'] for t in threats if t.get('severity') == 'low']
            else:
                guidance_text = threats[0]['action']
                priority = "medium"
                safety_level = "advisory"
                driver_response = False
                recommendations = [t['action'] for t in threats]
        
        # Handle driver query
        if driver_query:
            guidance_text = self._answer_driver_query(driver_query, threats, lane_info)
        
        return {
            'main': guidance_text,
            'priority': priority,
            'safety_level': safety_level,
            'driver_response_needed': driver_response,
            'recommendations': recommendations[:3],  # Top 3 recommendations
        }
    
    def _answer_driver_query(self, query: str, threats: List[Dict], lane_info: Dict) -> str:
        """
        Answer specific driver questions about the road scene.
        """
        query_lower = query.lower()
        
        if 'turn right' in query_lower or 'turn left' in query_lower:
            # Check for obstacles in that direction
            direction = 'right' if 'right' in query_lower else 'left'
            relevant_threats = [t for t in threats if t.get('position') == direction]
            
            if relevant_threats:
                return f"Do not turn {direction}. {relevant_threats[0]['action']}"
            else:
                return f"Clear to turn {direction}. Check mirrors and signal."
        
        elif 'safe' in query_lower or 'speed' in query_lower:
            critical_count = len([t for t in threats if t.get('severity') == 'high'])
            if critical_count > 0:
                return "Not safe to increase speed. Threats detected ahead."
            else:
                return "Road appears safe. Current speed is appropriate."
        
        elif 'lane' in query_lower:
            return f"You are in {lane_info.get('lane_position', 'unknown')} position. "
        
        elif 'ahead' in query_lower or 'front' in query_lower:
            return f"Road ahead is {'clear' if not threats else 'hazardous'}. {len([t for t in threats if t.get('severity') in ['high', 'medium']])} threats detected."
        
        else:
            return "Road conditions: " + ("Clear" if not threats else f"{len(threats)} threats detected")
    
    def get_summary(self) -> str:
        """Get current driving situation summary"""
        objects = self.context_memory['last_objects']
        lane = self.context_memory['last_lane_position']
        return f"Route Analysis: {len(objects)} objects detected, lane position {lane}"

# Global agent instance
_agent = None

def get_reasoning_agent() -> DrivingReasoningAgent:
    """Get or create reasoning agent"""
    global _agent
    if _agent is None:
        _agent = DrivingReasoningAgent(verbose=True)
    return _agent

def reason_about_scene(detections: List[Dict], lane_info: Dict, driver_query: str = None) -> str:
    """Reason about scene and return guidance string"""
    agent = get_reasoning_agent()
    analysis = agent.analyze_scene(detections, lane_info, driver_query)
    return analysis['guidance']