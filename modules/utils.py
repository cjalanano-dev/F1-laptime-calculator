"""
Utility functions for F1 Lap Time Calculator
"""
import json
import os
import math
from typing import Dict, Any, Tuple


def load_json_data(filename: str) -> Dict[str, Any]:
    """Load JSON data from the data directory"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    file_path = os.path.join(data_dir, filename)
    
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file {filename} not found in {data_dir}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in {filename}")


def format_lap_time(seconds: float) -> str:
    """Convert seconds to mm:ss.sss format"""
    if seconds < 0:
        return "N/A"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes}:{remaining_seconds:06.3f}"
    else:
        return f"{remaining_seconds:.3f}s"


def format_sector_time(seconds: float) -> str:
    """Format sector time in seconds with 3 decimal places"""
    if seconds < 0:
        return "N/A"
    return f"{seconds:.3f}s"


def kmh_to_ms(speed_kmh: float) -> float:
    """Convert km/h to m/s"""
    return speed_kmh / 3.6


def ms_to_kmh(speed_ms: float) -> float:
    """Convert m/s to km/h"""
    return speed_ms * 3.6


def calculate_corner_speed(radius: float, grip_coefficient: float = 1.0) -> float:
    """
    Calculate theoretical corner speed based on radius and grip
    Using simplified physics: v = sqrt(μ * g * r)
    """
    g = 9.81  # gravity
    max_speed = math.sqrt(grip_coefficient * g * radius)
    return max_speed


def fuel_weight_to_lap_time(fuel_kg: float, circuit_length: float) -> float:
    """
    Calculate time penalty per kg of fuel
    Roughly 0.035 seconds per kg per km of track
    """
    time_penalty_per_kg_per_km = 0.035
    return fuel_kg * (circuit_length / 1000) * time_penalty_per_kg_per_km


def calculate_tire_degradation(current_lap: int, tire_data: Dict[str, Any]) -> float:
    """
    Calculate tire performance based on lap number and tire characteristics
    Returns a multiplier (1.0 = peak performance, <1.0 = degraded)
    """
    peak_laps = tire_data.get('peak_performance_laps', 10)
    degradation_rate = tire_data.get('degradation_rate', 0.05)
    
    if current_lap <= peak_laps:
        # Performance improves slightly as tires warm up
        return min(1.0, 0.95 + (current_lap / peak_laps) * 0.05)
    else:
        # Performance degrades after peak
        laps_past_peak = current_lap - peak_laps
        degradation = 1.0 - (laps_past_peak * degradation_rate)
        return max(0.7, degradation)  # Minimum 70% performance


def calculate_drs_benefit(sector_data: Dict[str, Any], has_drs: bool = True) -> float:
    """
    Calculate DRS time benefit for a sector
    DRS provides more benefit on longer straights
    """
    if not has_drs:
        return 0.0
    
    sector_type = sector_data.get('type', 'medium_speed')
    base_benefit = {
        'high_speed': 0.8,    # More benefit on high-speed circuits
        'medium_speed': 0.4,
        'low_speed': 0.1      # Minimal benefit on slow circuits
    }
    
    return base_benefit.get(sector_type, 0.4)


def apply_weather_effect(base_time: float, weather_data: Dict[str, Any], 
                        tire_compound: str) -> Tuple[float, str]:
    """
    Apply weather effects to lap time
    Returns modified time and any warnings
    """
    grip_modifier = weather_data.get('grip_modifier', 1.0)
    speed_modifier = weather_data.get('speed_modifier', 1.0)
    mistake_prob = weather_data.get('mistake_probability', 0.0)
    
    # Base weather effect
    modified_time = base_time / (grip_modifier * speed_modifier)
    
    # Check if tire is suitable for conditions
    optimal_tires = weather_data.get('optimal_tire', [])
    warning = ""
    
    if tire_compound not in optimal_tires:
        # Wrong tire compound penalty
        modified_time *= 1.15
        warning = f"Suboptimal tire compound for {weather_data.get('name', 'current')} conditions"
    
    # Add potential mistake time (simplified as average effect)
    mistake_time = base_time * mistake_prob * 0.1
    modified_time += mistake_time
    
    return modified_time, warning


def calculate_driver_effect(aggression_level: float) -> Tuple[float, float]:
    """
    Calculate driver aggression effects on lap time and mistake probability
    aggression_level: 0.0 (conservative) to 1.0 (maximum attack)
    Returns: (time_modifier, mistake_probability)
    """
    # More aggressive = faster but higher mistake risk
    time_modifier = 1.0 - (aggression_level * 0.08)  # Up to 8% faster
    mistake_probability = aggression_level * 0.15     # Up to 15% chance of mistake
    
    return time_modifier, mistake_probability


def validate_inputs(circuit: str, tire_compound: str, fuel_load: float, 
                   weather: str) -> Tuple[bool, str]:
    """
    Validate user inputs
    Returns: (is_valid, error_message)
    """
    # Load data for validation
    circuits_data = load_json_data('circuits.json')
    tires_data = load_json_data('tires.json')
    weather_data = load_json_data('weather_presets.json')
    
    if circuit not in circuits_data.get('circuits', {}):
        return False, f"Circuit '{circuit}' not found. Available: {list(circuits_data['circuits'].keys())}"
    
    if tire_compound not in tires_data.get('tire_compounds', {}):
        return False, f"Tire compound '{tire_compound}' not found. Available: {list(tires_data['tire_compounds'].keys())}"
    
    if weather not in weather_data.get('weather_conditions', {}):
        return False, f"Weather condition '{weather}' not found. Available: {list(weather_data['weather_conditions'].keys())}"
    
    if not 0 <= fuel_load <= 110:
        return False, "Fuel load must be between 0 and 110 kg"
    
    return True, ""


def print_comparison_table(results: list) -> None:
    """
    Print a formatted comparison table of lap time results
    """
    if not results:
        return
    
    print("\n" + "="*80)
    print("LAP TIME COMPARISON")
    print("="*80)
    print(f"{'Config':<20} {'Lap Time':<12} {'S1':<10} {'S2':<10} {'S3':<10} {'Notes':<15}")
    print("-"*80)
    
    for result in results:
        config = f"{result.get('tire', 'N/A')}/{result.get('fuel', 0)}kg"
        lap_time = format_lap_time(result.get('total_time', 0))
        s1 = format_sector_time(result.get('sector_times', [0])[0] if result.get('sector_times') else 0)
        s2 = format_sector_time(result.get('sector_times', [0, 0])[1] if len(result.get('sector_times', [])) > 1 else 0)
        s3 = format_sector_time(result.get('sector_times', [0, 0, 0])[2] if len(result.get('sector_times', [])) > 2 else 0)
        notes = result.get('warnings', '')[:15]
        
        print(f"{config:<20} {lap_time:<12} {s1:<10} {s2:<10} {s3:<10} {notes:<15}")
    
    print("="*80)


def log_calculation_details(details: Dict[str, Any], verbose: bool = False) -> None:
    """
    Log detailed calculation breakdown
    """
    if not verbose:
        return
    
    print("\n" + "-"*50)
    print("CALCULATION DETAILS")
    print("-"*50)
    
    for key, value in details.items():
        if isinstance(value, float):
            print(f"{key.replace('_', ' ').title()}: {value:.3f}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("-"*50)
