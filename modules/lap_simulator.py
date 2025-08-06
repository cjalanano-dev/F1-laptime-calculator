"""
Lap Simulator module for F1 Lap Time Calculator
Combines circuit, car, and weather data to simulate lap times
"""
import random
from typing import Dict, List, Any, Optional, Tuple
from .circuit import Circuit
from .car import Car
from .utils import (load_json_data, apply_weather_effect, calculate_drs_benefit,
                   calculate_driver_effect, format_lap_time, format_sector_time)


class LapSimulator:
    """Main lap time simulation engine"""
    
    def __init__(self, circuit: Circuit, car: Car, weather: str = 'dry'):
        """
        Initialize lap simulator
        
        Args:
            circuit: Circuit object
            car: Car object
            weather: Weather condition string
        """
        self.circuit = circuit
        self.car = car
        self.weather = weather
        
        # Load weather data
        self.weather_data = load_json_data('weather_presets.json')
        
        if weather not in self.weather_data['weather_conditions']:
            available_weather = list(self.weather_data['weather_conditions'].keys())
            raise ValueError(f"Weather '{weather}' not found. Available: {available_weather}")
        
        self.current_weather = self.weather_data['weather_conditions'][weather]
        
        # Simulation parameters
        self.driver_aggression = 0.5  # 0.0 to 1.0
        self.track_condition = 'rubbered_in'  # from weather_presets.json
        self.use_drs = True
        self.simulation_variance = 0.02  # 2% random variance for realism
    
    def set_driver_parameters(self, aggression: float = 0.5, use_drs: bool = True) -> None:
        """
        Set driver behavior parameters
        
        Args:
            aggression: Driver aggression level (0.0 conservative to 1.0 maximum attack)
            use_drs: Whether DRS is available/used
        """
        if not 0.0 <= aggression <= 1.0:
            raise ValueError("Driver aggression must be between 0.0 and 1.0")
        
        self.driver_aggression = aggression
        self.use_drs = use_drs
    
    def set_track_condition(self, condition: str = 'rubbered_in') -> None:
        """Set track condition (green, rubbered_in, dusty)"""
        if condition not in self.weather_data['track_conditions']:
            available_conditions = list(self.weather_data['track_conditions'].keys())
            raise ValueError(f"Track condition '{condition}' not found. Available: {available_conditions}")
        
        self.track_condition = condition
    
    def calculate_sector_time(self, sector_number: int, lap_number: int = 1) -> Dict[str, Any]:
        """
        Calculate time for a specific sector
        
        Args:
            sector_number: Sector number (1, 2, 3)
            lap_number: Current lap number (affects tire degradation)
        
        Returns:
            Dictionary with sector time and breakdown
        """
        # Get base sector time from circuit
        base_sector_time = self.circuit.get_sector_base_time(sector_number)
        sector_data = self.circuit.get_sector_data(sector_number)
        
        if not sector_data:
            raise ValueError(f"Sector {sector_number} not found in circuit")
        
        # Update car tire state
        self.car.update_tire_state(lap_number, sector_data.get('type', 'medium_speed'))
        
        # Get performance factors
        tire_performance = self.car.get_tire_performance(lap_number)
        engine_performance = self.car.get_engine_performance()
        aero_balance = self.car.get_aerodynamic_balance()
        fuel_effect = self.car.get_fuel_effect(self.circuit.length)
        
        # Calculate modifiers
        modifiers = self._calculate_all_modifiers(sector_data, tire_performance, 
                                                engine_performance, aero_balance, fuel_effect)
        
        # Apply modifiers to base time
        sector_time = base_sector_time
        
        # Tire grip effect (most important factor)
        sector_time /= tire_performance['effective_grip']
        
        # Fuel weight effect
        sector_time += fuel_effect['time_penalty'] / self.circuit.get_total_sectors()
        
        # Aerodynamic effects (sector type dependent)
        if sector_data.get('type') == 'high_speed':
            # Straight line speed more important
            sector_time *= aero_balance['drag_multiplier']
        elif sector_data.get('type') == 'low_speed':
            # Cornering speed more important
            sector_time /= aero_balance['cornering_multiplier']
        else:
            # Balanced effect
            drag_effect = (aero_balance['drag_multiplier'] - 1.0) * 0.5
            corner_effect = (aero_balance['cornering_multiplier'] - 1.0) * 0.5
            sector_time *= (1.0 + drag_effect - corner_effect)
        
        # Engine performance effect
        power_factor = engine_performance['total_power'] / 1000  # Normalize to 1000hp baseline
        sector_time /= (0.95 + power_factor * 0.05)  # Small effect, mostly for straights
        
        # DRS effect (if available and applicable)
        if self.use_drs and self.circuit.has_drs_in_sector(sector_number):
            drs_benefit = calculate_drs_benefit(sector_data, True)
            sector_time -= drs_benefit
        
        # Weather effects
        sector_time, weather_warning = apply_weather_effect(
            sector_time, self.current_weather, self.car.tire_compound
        )
        
        # Track condition effect
        track_modifier = self.weather_data['track_conditions'][self.track_condition]['grip_modifier']
        sector_time /= track_modifier
        
        # Driver aggression effect
        driver_time_mod, mistake_prob = calculate_driver_effect(self.driver_aggression)
        sector_time *= driver_time_mod
        
        # Random variance for realism
        if self.simulation_variance > 0:
            variance = random.uniform(-self.simulation_variance, self.simulation_variance)
            sector_time *= (1.0 + variance)
        
        # Driver mistake simulation
        if random.random() < mistake_prob:
            mistake_time = sector_time * random.uniform(0.05, 0.15)  # 5-15% time loss
            sector_time += mistake_time
            modifiers['driver_mistake'] = mistake_time
        
        return {
            'sector_number': sector_number,
            'time': max(0, sector_time),  # Ensure non-negative
            'base_time': base_sector_time,
            'modifiers': modifiers,
            'warnings': [weather_warning] if weather_warning else [],
            'has_drs': self.circuit.has_drs_in_sector(sector_number),
            'sector_data': sector_data
        }
    
    def _calculate_all_modifiers(self, sector_data: Dict, tire_perf: Dict, 
                               engine_perf: Dict, aero_balance: Dict, 
                               fuel_effect: Dict) -> Dict[str, float]:
        """Calculate all performance modifiers for detailed breakdown"""
        return {
            'tire_grip': tire_perf['effective_grip'],
            'tire_degradation': tire_perf['degradation_multiplier'],
            'tire_temperature': tire_perf['temperature_effect'],
            'fuel_penalty': fuel_effect['time_penalty'],
            'downforce_level': self.car.downforce_level,
            'engine_power': engine_perf['total_power'],
            'weather_grip': self.current_weather['grip_modifier'],
            'track_condition': self.weather_data['track_conditions'][self.track_condition]['grip_modifier'],
            'driver_aggression': self.driver_aggression
        }
    
    def simulate_full_lap(self, lap_number: int = 1) -> Dict[str, Any]:
        """
        Simulate a complete lap
        
        Args:
            lap_number: Current lap number
        
        Returns:
            Complete lap simulation results
        """
        sector_results = []
        total_time = 0.0
        all_warnings = []
        
        # Simulate each sector
        for sector_num in range(1, self.circuit.get_total_sectors() + 1):
            sector_result = self.calculate_sector_time(sector_num, lap_number)
            sector_results.append(sector_result)
            total_time += sector_result['time']
            all_warnings.extend(sector_result['warnings'])
        
        # Calculate lap statistics
        lap_stats = self._calculate_lap_statistics(sector_results, total_time)
        
        return {
            'lap_number': lap_number,
            'total_time': total_time,
            'sector_times': [s['time'] for s in sector_results],
            'sector_results': sector_results,
            'lap_statistics': lap_stats,
            'warnings': list(set(all_warnings)),  # Remove duplicates
            'conditions': {
                'circuit': self.circuit.name,
                'weather': self.weather,
                'track_condition': self.track_condition,
                'tire_compound': self.car.tire_compound,
                'fuel_load': self.car.fuel_load
            }
        }
    
    def _calculate_lap_statistics(self, sector_results: List[Dict], total_time: float) -> Dict[str, Any]:
        """Calculate comprehensive lap statistics"""
        # Find fastest and slowest sectors
        sector_times = [s['time'] for s in sector_results]
        fastest_sector = min(range(len(sector_times)), key=lambda i: sector_times[i])
        slowest_sector = max(range(len(sector_times)), key=lambda i: sector_times[i])
        
        # Calculate theoretical best (sum of best sector times)
        best_possible_sectors = [s['base_time'] for s in sector_results]
        theoretical_best = sum(best_possible_sectors)
        
        # Performance analysis
        tire_perf = self.car.get_tire_performance()
        time_loss_breakdown = {
            'tire_degradation': total_time * (1 - tire_perf['degradation_multiplier']) * 0.1,
            'fuel_weight': sum(s['modifiers']['fuel_penalty'] for s in sector_results) / len(sector_results),
            'weather_conditions': total_time * (1 - self.current_weather['grip_modifier']) * 0.05,
            'suboptimal_setup': 0  # Could be calculated based on circuit vs car setup
        }
        
        return {
            'fastest_sector': fastest_sector + 1,
            'slowest_sector': slowest_sector + 1,
            'sector_balance': max(sector_times) - min(sector_times),
            'theoretical_best': theoretical_best,
            'time_delta_to_theoretical': total_time - theoretical_best,
            'average_sector_time': total_time / len(sector_results),
            'tire_performance_remaining': tire_perf['tire_life_remaining'],
            'estimated_fuel_remaining': max(0, self.car.fuel_load - (2.8 * self.car.current_lap)),
            'time_loss_breakdown': time_loss_breakdown
        }
    
    def simulate_stint(self, num_laps: int, start_lap: int = 1) -> List[Dict[str, Any]]:
        """
        Simulate multiple laps (a stint)
        
        Args:
            num_laps: Number of laps to simulate
            start_lap: Starting lap number
        
        Returns:
            List of lap results
        """
        stint_results = []
        
        for lap in range(start_lap, start_lap + num_laps):
            lap_result = self.simulate_full_lap(lap)
            stint_results.append(lap_result)
            
            # Update car state for next lap
            self.car.current_lap = lap
        
        return stint_results
    
    def compare_configurations(self, configurations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compare different car configurations on the same circuit
        
        Args:
            configurations: List of config dicts with keys like 'tire', 'fuel', 'downforce', etc.
        
        Returns:
            List of results sorted by lap time
        """
        results = []
        
        for i, config in enumerate(configurations):
            # Create temporary car with this configuration
            temp_car = Car(
                tire_compound=config.get('tire', 'medium'),
                fuel_load=config.get('fuel', 50.0)
            )
            
            if 'downforce' in config or 'engine_mode' in config or 'ers' in config:
                temp_car.set_setup(
                    downforce=config.get('downforce', 5),
                    engine_mode=config.get('engine_mode', 'race'),
                    ers_deployment=config.get('ers', 'auto')
                )
            
            # Create temporary simulator
            temp_sim = LapSimulator(self.circuit, temp_car, self.weather)
            temp_sim.set_driver_parameters(self.driver_aggression, self.use_drs)
            temp_sim.set_track_condition(self.track_condition)
            
            # Simulate lap
            result = temp_sim.simulate_full_lap(1)
            result['configuration'] = config
            result['config_index'] = i
            
            results.append(result)
        
        # Sort by lap time
        results.sort(key=lambda x: x['total_time'])
        
        return results
    
    def get_optimal_setup_suggestions(self) -> Dict[str, Any]:
        """
        Suggest optimal setup based on circuit characteristics
        """
        circuit_info = self.circuit.get_circuit_info()
        circuit_type = circuit_info['circuit_type']
        
        suggestions = {
            'circuit_analysis': circuit_info,
            'recommended_setup': {},
            'tire_strategy': {},
            'reasoning': []
        }
        
        # Downforce recommendations
        if 'High-speed' in circuit_type:
            suggestions['recommended_setup']['downforce'] = 3
            suggestions['reasoning'].append("Low downforce for high-speed circuit")
        elif 'Street' in circuit_type or 'Technical' in circuit_type:
            suggestions['recommended_setup']['downforce'] = 8
            suggestions['reasoning'].append("High downforce for technical circuit")
        else:
            suggestions['recommended_setup']['downforce'] = 5
            suggestions['reasoning'].append("Balanced downforce for mixed circuit")
        
        # Tire recommendations based on weather
        if self.weather == 'dry':
            if circuit_info['difficulty'] > 0.8:
                suggestions['tire_strategy']['qualifying'] = 'soft'
                suggestions['tire_strategy']['race_start'] = 'medium'
            else:
                suggestions['tire_strategy']['qualifying'] = 'soft'
                suggestions['tire_strategy']['race_start'] = 'medium'
        else:
            optimal_tire = self.current_weather['optimal_tire'][0]
            suggestions['tire_strategy']['recommended'] = optimal_tire
        
        # Engine mode recommendations
        suggestions['recommended_setup']['engine_mode'] = 'race'
        suggestions['recommended_setup']['ers_deployment'] = 'auto'
        
        return suggestions
    
    def __str__(self) -> str:
        """String representation of the simulator"""
        return (f"LapSimulator: {self.circuit.name} | {self.car.tire_compound} tires | "
                f"{self.weather} weather | Aggression: {self.driver_aggression:.1f}")
    
    def __repr__(self) -> str:
        """Detailed representation of the simulator"""
        return (f"LapSimulator(circuit='{self.circuit.name}', "
                f"tire='{self.car.tire_compound}', weather='{self.weather}')")
