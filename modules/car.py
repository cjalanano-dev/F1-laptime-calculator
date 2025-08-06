"""
Car module for F1 Lap Time Calculator
Handles car setup, tire compounds, fuel loads, and performance calculations
"""
from typing import Dict, Any, Optional, Tuple
from .utils import load_json_data, calculate_tire_degradation, fuel_weight_to_lap_time


class Car:
    """Represents an F1 car with all its performance characteristics"""
    
    def __init__(self, tire_compound: str = 'medium', fuel_load: float = 50.0):
        """
        Initialize car with basic setup
        
        Args:
            tire_compound: Tire type (soft, medium, hard, intermediate, wet)
            fuel_load: Fuel weight in kg (0-110kg)
        """
        self.tire_data = load_json_data('tires.json')
        
        # Validate tire compound
        if tire_compound not in self.tire_data['tire_compounds']:
            available_tires = list(self.tire_data['tire_compounds'].keys())
            raise ValueError(f"Tire compound '{tire_compound}' not found. Available: {available_tires}")
        
        # Validate fuel load
        if not 0 <= fuel_load <= 110:
            raise ValueError("Fuel load must be between 0 and 110 kg")
        
        # Basic car setup
        self.tire_compound = tire_compound
        self.fuel_load = fuel_load
        
        # Performance settings
        self.downforce_level = 5  # 1-10 scale (1=low downforce, 10=high downforce)
        self.engine_mode = 'race'  # 'quali', 'race', 'conservation'
        self.ers_deployment = 'auto'  # 'auto', 'aggressive', 'conservative'
        
        # Car characteristics
        self.base_weight = 798  # 2023 minimum weight without fuel (kg)
        self.power_unit_power = 1000  # HP (approximate)
        self.drag_coefficient = 1.0  # Relative to baseline
        
        # Track current tire state
        self.current_lap = 1
        self.tire_temperature = 90  # Celsius
        
    def set_setup(self, downforce: int = 5, engine_mode: str = 'race', 
                  ers_deployment: str = 'auto') -> None:
        """
        Configure car setup
        
        Args:
            downforce: Downforce level 1-10 (affects cornering vs straight line speed)
            engine_mode: 'quali', 'race', 'conservation'
            ers_deployment: 'auto', 'aggressive', 'conservative'
        """
        if not 1 <= downforce <= 10:
            raise ValueError("Downforce level must be between 1 and 10")
        
        valid_engine_modes = ['quali', 'race', 'conservation']
        if engine_mode not in valid_engine_modes:
            raise ValueError(f"Engine mode must be one of: {valid_engine_modes}")
        
        valid_ers_modes = ['auto', 'aggressive', 'conservative']
        if ers_deployment not in valid_ers_modes:
            raise ValueError(f"ERS deployment must be one of: {valid_ers_modes}")
        
        self.downforce_level = downforce
        self.engine_mode = engine_mode
        self.ers_deployment = ers_deployment
        
        # Update drag coefficient based on downforce
        self.drag_coefficient = 0.7 + (downforce / 10) * 0.6  # 0.7 to 1.3 range
    
    def get_tire_performance(self, lap_number: Optional[int] = None) -> Dict[str, float]:
        """
        Calculate current tire performance
        
        Args:
            lap_number: Current lap number (uses self.current_lap if None)
        
        Returns:
            Dictionary with tire performance metrics
        """
        if lap_number is None:
            lap_number = self.current_lap
        
        tire_info = self.tire_data['tire_compounds'][self.tire_compound]
        
        # Base grip level
        base_grip = tire_info['grip_modifier']
        
        # Degradation effect
        degradation_multiplier = calculate_tire_degradation(lap_number, tire_info)
        
        # Temperature effect
        temp_effect = self._calculate_temperature_effect()
        
        # Calculate effective grip
        effective_grip = base_grip * degradation_multiplier * temp_effect
        
        return {
            'base_grip': base_grip,
            'degradation_multiplier': degradation_multiplier,
            'temperature_effect': temp_effect,
            'effective_grip': effective_grip,
            'compound': self.tire_compound,
            'lap_number': lap_number,
            'tire_life_remaining': max(0, 1 - (lap_number / tire_info['life_span']))
        }
    
    def _calculate_temperature_effect(self) -> float:
        """Calculate tire performance based on temperature"""
        tire_info = self.tire_data['tire_compounds'][self.tire_compound]
        temp_effects = self.tire_data['tire_temperature_effects']
        
        optimal_range = tire_info['optimal_temp_range']
        
        if optimal_range[0] <= self.tire_temperature <= optimal_range[1]:
            # In optimal range
            return 1.0
        elif self.tire_temperature < temp_effects['cold']['temp_threshold']:
            # Too cold
            return 1.0 - temp_effects['cold']['grip_loss']
        elif self.tire_temperature > temp_effects['overheated']['temp_threshold']:
            # Overheated
            return 1.0 - temp_effects['overheated']['grip_loss']
        else:
            # Slightly outside optimal but not extreme
            if self.tire_temperature < optimal_range[0]:
                # Cool but not cold
                temp_diff = optimal_range[0] - self.tire_temperature
                return 1.0 - (temp_diff / 20) * 0.05  # Linear interpolation
            else:
                # Warm but not overheated
                temp_diff = self.tire_temperature - optimal_range[1]
                return 1.0 - (temp_diff / 20) * 0.05
    
    def get_engine_performance(self) -> Dict[str, float]:
        """Calculate engine performance based on mode and ERS"""
        base_power = self.power_unit_power
        
        # Engine mode effects
        engine_modifiers = {
            'quali': {'power': 1.08, 'fuel_consumption': 1.5, 'reliability': 0.95},
            'race': {'power': 1.0, 'fuel_consumption': 1.0, 'reliability': 1.0},
            'conservation': {'power': 0.92, 'fuel_consumption': 0.85, 'reliability': 1.05}
        }
        
        # ERS deployment effects
        ers_modifiers = {
            'aggressive': {'power_boost': 50, 'deployment_time': 0.8},
            'auto': {'power_boost': 35, 'deployment_time': 0.6},
            'conservative': {'power_boost': 25, 'deployment_time': 0.4}
        }
        
        engine_mod = engine_modifiers[self.engine_mode]
        ers_mod = ers_modifiers[self.ers_deployment]
        
        effective_power = base_power * engine_mod['power']
        ers_contribution = ers_mod['power_boost'] * ers_mod['deployment_time']
        
        return {
            'base_power': base_power,
            'engine_mode_multiplier': engine_mod['power'],
            'effective_power': effective_power,
            'ers_contribution': ers_contribution,
            'total_power': effective_power + ers_contribution,
            'fuel_consumption_rate': engine_mod['fuel_consumption'],
            'reliability_factor': engine_mod['reliability']
        }
    
    def get_aerodynamic_balance(self) -> Dict[str, float]:
        """Calculate aerodynamic performance"""
        # Downforce affects cornering speed vs straight line speed
        downforce_efficiency = self.downforce_level / 10
        
        # More downforce = better cornering but more drag
        cornering_benefit = 1.0 + (downforce_efficiency * 0.15)  # Up to 15% better cornering
        straight_line_penalty = 1.0 + (downforce_efficiency * 0.08)  # Up to 8% more drag
        
        return {
            'downforce_level': self.downforce_level,
            'cornering_multiplier': cornering_benefit,
            'drag_multiplier': straight_line_penalty,
            'drag_coefficient': self.drag_coefficient,
            'balance_type': self._get_aero_balance_description()
        }
    
    def _get_aero_balance_description(self) -> str:
        """Get description of aerodynamic balance"""
        if self.downforce_level <= 3:
            return "Low downforce (Monza-style)"
        elif self.downforce_level <= 7:
            return "Medium downforce (Balanced)"
        else:
            return "High downforce (Monaco-style)"
    
    def get_total_weight(self) -> float:
        """Calculate total car weight"""
        return self.base_weight + self.fuel_load
    
    def get_fuel_effect(self, circuit_length: float) -> Dict[str, float]:
        """Calculate fuel load effects on performance"""
        time_penalty = fuel_weight_to_lap_time(self.fuel_load, circuit_length)
        
        # Fuel affects weight distribution and handling
        handling_effect = 1.0 + (self.fuel_load / 1000)  # Heavier = slightly worse handling
        
        return {
            'fuel_load': self.fuel_load,
            'total_weight': self.get_total_weight(),
            'time_penalty': time_penalty,
            'handling_multiplier': handling_effect,
            'laps_remaining': self._estimate_fuel_laps()
        }
    
    def _estimate_fuel_laps(self) -> int:
        """Estimate how many laps the current fuel will last"""
        # Rough estimate: 2.5-3.5 kg per lap depending on engine mode
        consumption_rates = {
            'quali': 3.5,
            'race': 2.8,
            'conservation': 2.3
        }
        
        consumption_per_lap = consumption_rates[self.engine_mode]
        return int(self.fuel_load / consumption_per_lap)
    
    def update_tire_state(self, lap_number: int, sector_type: str = 'medium_speed') -> None:
        """
        Update tire state after completing a sector/lap
        
        Args:
            lap_number: Current lap number
            sector_type: Type of sector completed (affects tire temperature)
        """
        self.current_lap = lap_number
        
        # Update tire temperature based on sector type
        temp_changes = {
            'low_speed': -2,     # Cooling in slow sections
            'medium_speed': 0,   # Neutral
            'high_speed': +3     # Heating in fast sections
        }
        
        temp_change = temp_changes.get(sector_type, 0)
        self.tire_temperature = max(60, min(140, self.tire_temperature + temp_change))
    
    def get_car_summary(self) -> Dict[str, Any]:
        """Get comprehensive car information"""
        tire_perf = self.get_tire_performance()
        engine_perf = self.get_engine_performance()
        aero_balance = self.get_aerodynamic_balance()
        
        return {
            'tire_compound': self.tire_compound,
            'tire_performance': tire_perf,
            'fuel_load': self.fuel_load,
            'total_weight': self.get_total_weight(),
            'engine_performance': engine_perf,
            'aerodynamic_balance': aero_balance,
            'current_lap': self.current_lap,
            'tire_temperature': self.tire_temperature,
            'setup_summary': {
                'downforce': self.downforce_level,
                'engine_mode': self.engine_mode,
                'ers_deployment': self.ers_deployment
            }
        }
    
    @classmethod
    def get_available_tire_compounds(cls) -> list:
        """Get list of available tire compounds"""
        tire_data = load_json_data('tires.json')
        return list(tire_data['tire_compounds'].keys())
    
    def __str__(self) -> str:
        """String representation of the car"""
        return (f"F1 Car: {self.tire_compound.title()} tires, {self.fuel_load}kg fuel, "
                f"Downforce: {self.downforce_level}/10, Mode: {self.engine_mode}")
    
    def __repr__(self) -> str:
        """Detailed representation of the car"""
        return (f"Car(tire='{self.tire_compound}', fuel={self.fuel_load}, "
                f"downforce={self.downforce_level}, mode='{self.engine_mode}')")
