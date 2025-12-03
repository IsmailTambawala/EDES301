import math

# Global state to track max values during session
_max_flexion = 0.0
_max_extension = 0.0
_max_torque = 0.0

def reset_max_values():
    """Reset tracked maximum values (call at start of new session)"""
    global _max_flexion, _max_extension, _max_torque
    _max_flexion = 0.0
    _max_extension = 0.0
    _max_torque = 0.0

def _coalesce_segment(segment):
    defaults = {"pitch": 0.0, "roll": 0.0, "yaw": 0.0}
    if segment is None:
        return defaults.copy()
    return {**defaults, **segment}


def _normalize_angle(angle: float) -> float:
    """
    Wrap an angle in degrees to the [-180, 180) range so differences behave when crossing +/-180.
    """
    wrapped = (angle + 180.0) % 360.0 - 180.0
    return wrapped if wrapped != -180.0 else 180.0


def _angle_delta_deg(a: float, b: float) -> float:
    """Smallest absolute difference between two angles in degrees."""
    return abs(_normalize_angle(a - b))


def calculate_physics(imu_data, muscle_val):
    """
    Calculates biomechanical metrics from raw sensor data.
    
    Args:
        imu_data: Dictionary with 'thigh' and 'shin' IMU readings
        muscle_val: Raw muscle activation value (0-100)
    
    Returns:
        Dictionary with calculated metrics including max values
    """
    global _max_flexion, _max_extension, _max_torque
    
    thigh = _coalesce_segment(imu_data.get("thigh"))
    shin = _coalesce_segment(imu_data.get("shin"))
    
    # 1. Calculate Knee Flexion Angle (angle between thigh and shin)
    # With sensors mounted laterally, flexion corresponds to roll difference.
    flexion_angle = _angle_delta_deg(shin["roll"], thigh["roll"])
    
    # Clamp to realistic range (0-180 degrees)
    flexion_angle = max(0, min(180, flexion_angle))
    
    # Extension angle is complementary (180 - flexion)
    extension_angle = 180 - flexion_angle
    
    # Track maximum values
    _max_flexion = max(_max_flexion, flexion_angle)
    _max_extension = max(_max_extension, extension_angle)
    
    # 2. Estimate Torque
    # Simplified biomechanical model:
    # Torque = Force * Distance from joint
    # Force includes gravitational and dynamic components
    
    # Shin mass approx 4kg, COM distance 0.2m from knee, Gravity 9.8 m/s²
    # Torque due to gravity: τ = m * g * r * sin(θ)
    # where θ is the angle of shin relative to vertical
    
    # Convert shin roll to angle relative to neutral (0° = vertical plane)
    shin_angle_from_vertical = abs(_normalize_angle(shin["roll"]))
    shin_angle_rad = math.radians(shin_angle_from_vertical)
    
    # Gravitational torque component
    gravity_torque = 4.0 * 9.8 * 0.2 * math.sin(shin_angle_rad)
    
    # Add dynamic torque component based on angular acceleration
    # Simplified: assume acceleration is proportional to muscle activation
    # This is a rough approximation - real system would use gyroscope data
    dynamic_torque = (muscle_val / 100.0) * 2.0  # Scale muscle activation to torque
    
    total_torque = abs(gravity_torque) + dynamic_torque
    _max_torque = max(_max_torque, total_torque)
    
    return {
        "flexion_angle": round(flexion_angle, 1),
        "extension_angle": round(extension_angle, 1),
        "max_flexion": round(_max_flexion, 1),
        "max_extension": round(_max_extension, 1),
        "torque": round(total_torque, 2),
        "max_torque": round(_max_torque, 2),
        "muscle_activation": round(muscle_val, 1)
    }
