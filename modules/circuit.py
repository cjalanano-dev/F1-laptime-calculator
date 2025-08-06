"""
Circuit module for F1 Lap Time Calculator
Handles circuit data, sector information, and track-specific calculations
"""
from typing import Dict, List, Any, Optional
from .utils import load_json_data


class Circuit:
    """Represents an F1 circuit with all its characteristics"""
    
    def __init__(self, circuit_name: str):
        """Initialize circuit with data from JSON file"""
        self.circuits_data = load_json_data('circuits.json')
        
        if circuit_name not in self.circuits_data['circuits']:
            available_circuits = list(self.circuits_data['circuits'].keys())
            raise ValueError(f"Circuit '{circuit_name}' not found. Available: {available_circuits}")
        
        self.name = circuit_name
        self.data = self.circuits_data['circuits'][circuit_name]
        
        # Extract basic circuit info
        self.full_name = self.data['name']
        self.country = self.data['country']
        self.length = self.data['length']  # meters
        self.sectors = self.data['sectors']
        self.drs_zones = self.data.get('drs_zones', [])
        self.lap_record = self.data.get('lap_record', 0)
        self.base_lap_time = self.data.get('base_lap_time', 0)
        self.difficulty = self.data.get('difficulty', 0.7)
    
    def get_sector_data(self, sector_number: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific sector"""
        for sector in self.sectors:
            if sector['number'] == sector_number:
                return sector
        return None
    
    def get_total_sectors(self) -> int:
        """Get number of sectors in the circuit"""
        return len(self.sectors)
    
    def has_drs_in_sector(self, sector_number: int) -> bool:
        """Check if a sector has DRS zones"""
        for drs_zone in self.drs_zones:
            if drs_zone['sector'] == sector_number:
                return True
        return False
    
    def get_drs_zones_in_sector(self, sector_number: int) -> List[Dict[str, Any]]:
        """Get all DRS zones in a specific sector"""
        return [zone for zone in self.drs_zones if zone['sector'] == sector_number]
    
    def calculate_sector_difficulty(self, sector_number: int) -> float:
        """
        Calculate sector difficulty based on turns, length, and type
        Returns value between 0.5 (easy) and 1.2 (very difficult)
        """
        sector = self.get_sector_data(sector_number)
        if not sector:
            return 1.0
        
        base_difficulty = 0.8
        
        # Turn density effect
        turn_density = sector['turns'] / (sector['length'] / 1000)  # turns per km
        turn_effect = min(0.3, turn_density * 0.1)
        
        # Sector type effect
        type_modifiers = {
            'low_speed': 0.2,      # Monaco-style tight sections
            'medium_speed': 0.1,   # Balanced sections
            'high_speed': -0.1     # Monza-style fast sections
        }
        type_effect = type_modifiers.get(sector.get('type', 'medium_speed'), 0.1)
        
        # Elevation change effect
        elevation_effect = abs(sector.get('elevation_change', 0)) * 0.005
        
        difficulty = base_difficulty + turn_effect + type_effect + elevation_effect
        return max(0.5, min(1.2, difficulty))
    
    def get_sector_base_time(self, sector_number: int) -> float:
        """
        Calculate base time for a sector based on length and characteristics
        """
        sector = self.get_sector_data(sector_number)
        if not sector:
            return 0.0
        
        # Estimate base time from sector characteristics
        sector_ratio = sector['length'] / self.length
        base_sector_time = self.base_lap_time * sector_ratio
        
        # Apply difficulty modifier
        difficulty_modifier = self.calculate_sector_difficulty(sector_number)
        
        return base_sector_time * difficulty_modifier
    
    def get_average_speed_estimate(self, sector_number: int) -> float:
        """
        Estimate average speed for a sector in km/h
        """
        sector = self.get_sector_data(sector_number)
        if not sector:
            return 200.0
        
        # Base speeds by sector type
        base_speeds = {
            'low_speed': 120,    # Monaco-style
            'medium_speed': 180, # Mixed sections
            'high_speed': 280    # Monza-style straights
        }
        
        base_speed = base_speeds.get(sector.get('type', 'medium_speed'), 180)
        
        # Adjust for turn density
        turn_density = sector['turns'] / (sector['length'] / 1000)
        speed_reduction = min(50, turn_density * 15)
        
        return max(80, base_speed - speed_reduction)
    
    def get_circuit_info(self) -> Dict[str, Any]:
        """Get comprehensive circuit information"""
        sector_info = []
        total_turns = 0
        
        for i in range(1, self.get_total_sectors() + 1):
            sector = self.get_sector_data(i)
            if sector:
                sector_info.append({
                    'sector': i,
                    'length': sector['length'],
                    'turns': sector['turns'],
                    'type': sector.get('type', 'unknown'),
                    'has_drs': self.has_drs_in_sector(i),
                    'difficulty': self.calculate_sector_difficulty(i),
                    'base_time': self.get_sector_base_time(i),
                    'avg_speed_estimate': self.get_average_speed_estimate(i)
                })
                total_turns += sector['turns']
        
        return {
            'name': self.full_name,
            'country': self.country,
            'length': self.length,
            'total_turns': total_turns,
            'sectors': sector_info,
            'drs_zones': len(self.drs_zones),
            'lap_record': self.lap_record,
            'base_lap_time': self.base_lap_time,
            'difficulty': self.difficulty,
            'circuit_type': self._classify_circuit_type()
        }
    
    def _classify_circuit_type(self) -> str:
        """Classify circuit type based on characteristics"""
        avg_speed = sum(self.get_average_speed_estimate(i) for i in range(1, self.get_total_sectors() + 1)) / self.get_total_sectors()
        
        if avg_speed > 220:
            return "High-speed circuit"
        elif avg_speed < 140:
            return "Street/Technical circuit"
        else:
            return "Mixed circuit"
    
    @classmethod
    def get_available_circuits(cls) -> List[str]:
        """Get list of available circuits"""
        circuits_data = load_json_data('circuits.json')
        return list(circuits_data['circuits'].keys())
    
    @classmethod
    def create_custom_circuit(cls, name: str, length: float, sectors: List[Dict]) -> 'Circuit':
        """
        Create a custom circuit (not saved to file)
        
        sectors format: [
            {"number": 1, "length": 2000, "turns": 5, "type": "medium_speed"},
            ...
        ]
        """
        # Create temporary circuit data
        custom_data = {
            'name': name,
            'country': 'Custom',
            'length': length,
            'sectors': sectors,
            'drs_zones': [],
            'base_lap_time': length / 70,  # Rough estimate
            'difficulty': 0.8
        }
        
        # Create a new Circuit instance with custom data
        circuit = cls.__new__(cls)
        circuit.circuits_data = {'circuits': {'custom': custom_data}}
        circuit.name = 'custom'
        circuit.data = custom_data
        circuit.full_name = custom_data['name']
        circuit.country = custom_data['country']
        circuit.length = custom_data['length']
        circuit.sectors = custom_data['sectors']
        circuit.drs_zones = custom_data['drs_zones']
        circuit.lap_record = 0
        circuit.base_lap_time = custom_data['base_lap_time']
        circuit.difficulty = custom_data['difficulty']
        
        return circuit
    
    def __str__(self) -> str:
        """String representation of the circuit"""
        return f"{self.full_name} ({self.country}) - {self.length}m, {self.get_total_sectors()} sectors"
    
    def __repr__(self) -> str:
        """Detailed representation of the circuit"""
        return f"Circuit(name='{self.name}', length={self.length}, sectors={self.get_total_sectors()})"
