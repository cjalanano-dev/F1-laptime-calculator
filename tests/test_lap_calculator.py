"""
Unit tests for F1 Lap Time Calculator
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.circuit import Circuit
from modules.car import Car
from modules.lap_simulator import LapSimulator
from modules.utils import (format_lap_time, format_sector_time, kmh_to_ms, ms_to_kmh,
                          fuel_weight_to_lap_time, calculate_tire_degradation, validate_inputs)


class TestCircuit(unittest.TestCase):
    """Test Circuit class functionality"""
    
    def setUp(self):
        """Set up test circuit"""
        self.circuit = Circuit('spa')
    
    def test_circuit_initialization(self):
        """Test circuit loads correctly"""
        self.assertEqual(self.circuit.name, 'spa')
        self.assertEqual(self.circuit.full_name, 'Circuit de Spa-Francorchamps')
        self.assertEqual(self.circuit.country, 'Belgium')
        self.assertGreater(self.circuit.length, 0)
    
    def test_invalid_circuit(self):
        """Test invalid circuit raises error"""
        with self.assertRaises(ValueError):
            Circuit('invalid_circuit')
    
    def test_sector_data(self):
        """Test sector data retrieval"""
        sector1 = self.circuit.get_sector_data(1)
        self.assertIsNotNone(sector1)
        self.assertEqual(sector1['number'], 1)
        self.assertIn('length', sector1)
        self.assertIn('turns', sector1)
    
    def test_drs_zones(self):
        """Test DRS zone detection"""
        # Spa should have DRS zones
        self.assertGreater(len(self.circuit.drs_zones), 0)
        
        # Check if sector has DRS
        has_drs = any(self.circuit.has_drs_in_sector(i) for i in range(1, 4))
        self.assertTrue(has_drs)
    
    def test_sector_difficulty(self):
        """Test sector difficulty calculation"""
        for sector_num in range(1, self.circuit.get_total_sectors() + 1):
            difficulty = self.circuit.calculate_sector_difficulty(sector_num)
            self.assertGreaterEqual(difficulty, 0.5)
            self.assertLessEqual(difficulty, 1.2)
    
    def test_available_circuits(self):
        """Test available circuits list"""
        circuits = Circuit.get_available_circuits()
        self.assertIsInstance(circuits, list)
        self.assertIn('spa', circuits)
        self.assertIn('monaco', circuits)
        self.assertIn('monza', circuits)
    
    def test_custom_circuit(self):
        """Test custom circuit creation"""
        sectors = [
            {"number": 1, "length": 2000, "turns": 5, "type": "medium_speed"},
            {"number": 2, "length": 1500, "turns": 3, "type": "high_speed"}
        ]
        custom = Circuit.create_custom_circuit("Test Track", 3500, sectors)
        self.assertEqual(custom.full_name, "Test Track")
        self.assertEqual(custom.length, 3500)
        self.assertEqual(custom.get_total_sectors(), 2)


class TestCar(unittest.TestCase):
    """Test Car class functionality"""
    
    def setUp(self):
        """Set up test car"""
        self.car = Car('medium', 50.0)
    
    def test_car_initialization(self):
        """Test car initializes correctly"""
        self.assertEqual(self.car.tire_compound, 'medium')
        self.assertEqual(self.car.fuel_load, 50.0)
        self.assertEqual(self.car.downforce_level, 5)
        self.assertEqual(self.car.engine_mode, 'race')
    
    def test_invalid_tire_compound(self):
        """Test invalid tire compound raises error"""
        with self.assertRaises(ValueError):
            Car('invalid_tire', 50.0)
    
    def test_invalid_fuel_load(self):
        """Test invalid fuel load raises error"""
        with self.assertRaises(ValueError):
            Car('medium', -10)  # Negative fuel
        with self.assertRaises(ValueError):
            Car('medium', 150)  # Too much fuel
    
    def test_setup_configuration(self):
        """Test car setup configuration"""
        self.car.set_setup(downforce=8, engine_mode='quali', ers_deployment='aggressive')
        self.assertEqual(self.car.downforce_level, 8)
        self.assertEqual(self.car.engine_mode, 'quali')
        self.assertEqual(self.car.ers_deployment, 'aggressive')
    
    def test_tire_performance(self):
        """Test tire performance calculation"""
        perf = self.car.get_tire_performance(1)
        self.assertIn('base_grip', perf)
        self.assertIn('degradation_multiplier', perf)
        self.assertIn('effective_grip', perf)
        self.assertGreater(perf['effective_grip'], 0)
        self.assertLessEqual(perf['effective_grip'], 1.5)
    
    def test_tire_degradation_over_laps(self):
        """Test tire degradation increases over laps"""
        perf_lap1 = self.car.get_tire_performance(1)
        perf_lap20 = self.car.get_tire_performance(20)
        
        # Tire should degrade (lower multiplier) over time
        self.assertLessEqual(perf_lap20['degradation_multiplier'], 
                           perf_lap1['degradation_multiplier'])
    
    def test_engine_performance(self):
        """Test engine performance calculation"""
        perf = self.car.get_engine_performance()
        self.assertIn('total_power', perf)
        self.assertIn('fuel_consumption_rate', perf)
        self.assertGreater(perf['total_power'], 0)
    
    def test_aerodynamic_balance(self):
        """Test aerodynamic balance calculation"""
        aero = self.car.get_aerodynamic_balance()
        self.assertIn('cornering_multiplier', aero)
        self.assertIn('drag_multiplier', aero)
        self.assertGreater(aero['cornering_multiplier'], 0)
        self.assertGreater(aero['drag_multiplier'], 0)
    
    def test_total_weight(self):
        """Test total weight calculation"""
        total_weight = self.car.get_total_weight()
        expected_weight = self.car.base_weight + self.car.fuel_load
        self.assertEqual(total_weight, expected_weight)
    
    def test_available_tire_compounds(self):
        """Test available tire compounds"""
        compounds = Car.get_available_tire_compounds()
        self.assertIsInstance(compounds, list)
        self.assertIn('soft', compounds)
        self.assertIn('medium', compounds)
        self.assertIn('hard', compounds)


class TestLapSimulator(unittest.TestCase):
    """Test LapSimulator class functionality"""
    
    def setUp(self):
        """Set up test simulator"""
        self.circuit = Circuit('spa')
        self.car = Car('medium', 50.0)
        self.simulator = LapSimulator(self.circuit, self.car, 'dry')
    
    def test_simulator_initialization(self):
        """Test simulator initializes correctly"""
        self.assertEqual(self.simulator.circuit.name, 'spa')
        self.assertEqual(self.simulator.car.tire_compound, 'medium')
        self.assertEqual(self.simulator.weather, 'dry')
    
    def test_invalid_weather(self):
        """Test invalid weather raises error"""
        with self.assertRaises(ValueError):
            LapSimulator(self.circuit, self.car, 'invalid_weather')
    
    def test_driver_parameters(self):
        """Test driver parameter setting"""
        self.simulator.set_driver_parameters(0.8, True)
        self.assertEqual(self.simulator.driver_aggression, 0.8)
        self.assertTrue(self.simulator.use_drs)
    
    def test_invalid_driver_aggression(self):
        """Test invalid driver aggression raises error"""
        with self.assertRaises(ValueError):
            self.simulator.set_driver_parameters(-0.1)  # Too low
        with self.assertRaises(ValueError):
            self.simulator.set_driver_parameters(1.1)   # Too high
    
    def test_sector_time_calculation(self):
        """Test sector time calculation"""
        sector_result = self.simulator.calculate_sector_time(1, 1)
        
        self.assertIn('time', sector_result)
        self.assertIn('sector_number', sector_result)
        self.assertIn('base_time', sector_result)
        self.assertIn('modifiers', sector_result)
        
        self.assertGreater(sector_result['time'], 0)
        self.assertEqual(sector_result['sector_number'], 1)
    
    def test_full_lap_simulation(self):
        """Test full lap simulation"""
        result = self.simulator.simulate_full_lap(1)
        
        self.assertIn('total_time', result)
        self.assertIn('sector_times', result)
        self.assertIn('lap_statistics', result)
        self.assertIn('conditions', result)
        
        self.assertGreater(result['total_time'], 0)
        self.assertEqual(len(result['sector_times']), self.circuit.get_total_sectors())
        
        # Total time should equal sum of sector times
        sector_sum = sum(result['sector_times'])
        self.assertAlmostEqual(result['total_time'], sector_sum, places=3)
    
    def test_stint_simulation(self):
        """Test multi-lap stint simulation"""
        stint_results = self.simulator.simulate_stint(3, 1)
        
        self.assertEqual(len(stint_results), 3)
        
        for i, result in enumerate(stint_results):
            self.assertEqual(result['lap_number'], i + 1)
            self.assertGreater(result['total_time'], 0)
    
    def test_configuration_comparison(self):
        """Test configuration comparison"""
        configs = [
            {'tire': 'soft', 'fuel': 30},
            {'tire': 'medium', 'fuel': 50},
            {'tire': 'hard', 'fuel': 70}
        ]
        
        results = self.simulator.compare_configurations(configs)
        
        self.assertEqual(len(results), 3)
        
        # Results should be sorted by lap time (fastest first)
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]['total_time'], results[i + 1]['total_time'])
    
    def test_setup_suggestions(self):
        """Test setup suggestions"""
        suggestions = self.simulator.get_optimal_setup_suggestions()
        
        self.assertIn('circuit_analysis', suggestions)
        self.assertIn('recommended_setup', suggestions)
        self.assertIn('tire_strategy', suggestions)
        self.assertIn('reasoning', suggestions)


class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_format_lap_time(self):
        """Test lap time formatting"""
        # Test seconds only
        self.assertEqual(format_lap_time(45.123), "45.123s")
        
        # Test minutes and seconds
        self.assertEqual(format_lap_time(75.456), "1:15.456")
        
        # Test negative time
        self.assertEqual(format_lap_time(-5), "N/A")
    
    def test_format_sector_time(self):
        """Test sector time formatting"""
        self.assertEqual(format_sector_time(25.123), "25.123s")
        self.assertEqual(format_sector_time(-5), "N/A")
    
    def test_speed_conversions(self):
        """Test speed unit conversions"""
        # Test km/h to m/s
        self.assertAlmostEqual(kmh_to_ms(360), 100, places=2)
        self.assertAlmostEqual(kmh_to_ms(0), 0, places=2)
        
        # Test m/s to km/h
        self.assertAlmostEqual(ms_to_kmh(100), 360, places=2)
        self.assertAlmostEqual(ms_to_kmh(0), 0, places=2)
        
        # Test round trip
        original_speed = 250  # km/h
        converted = ms_to_kmh(kmh_to_ms(original_speed))
        self.assertAlmostEqual(converted, original_speed, places=2)
    
    def test_fuel_weight_penalty(self):
        """Test fuel weight to lap time penalty"""
        # More fuel should result in more time penalty
        penalty_50kg = fuel_weight_to_lap_time(50, 5000)
        penalty_100kg = fuel_weight_to_lap_time(100, 5000)
        
        self.assertGreater(penalty_100kg, penalty_50kg)
        self.assertGreater(penalty_50kg, 0)
    
    def test_tire_degradation(self):
        """Test tire degradation calculation"""
        tire_data = {
            'peak_performance_laps': 10,
            'degradation_rate': 0.05
        }
        
        # Early laps should have good performance
        early_performance = calculate_tire_degradation(5, tire_data)
        self.assertGreaterEqual(early_performance, 0.95)
        
        # Later laps should have degraded performance
        late_performance = calculate_tire_degradation(25, tire_data)
        self.assertLess(late_performance, early_performance)
        
        # Should never go below 70%
        extreme_performance = calculate_tire_degradation(100, tire_data)
        self.assertGreaterEqual(extreme_performance, 0.7)
    
    def test_input_validation(self):
        """Test input validation"""
        # Valid inputs
        is_valid, msg = validate_inputs('spa', 'medium', 50, 'dry')
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")
        
        # Invalid circuit
        is_valid, msg = validate_inputs('invalid', 'medium', 50, 'dry')
        self.assertFalse(is_valid)
        self.assertIn('Circuit', msg)
        
        # Invalid tire
        is_valid, msg = validate_inputs('spa', 'invalid', 50, 'dry')
        self.assertFalse(is_valid)
        self.assertIn('Tire', msg)
        
        # Invalid fuel load
        is_valid, msg = validate_inputs('spa', 'medium', -10, 'dry')
        self.assertFalse(is_valid)
        self.assertIn('Fuel', msg)
        
        # Invalid weather
        is_valid, msg = validate_inputs('spa', 'medium', 50, 'invalid')
        self.assertFalse(is_valid)
        self.assertIn('Weather', msg)


class TestRealisticLapTimes(unittest.TestCase):
    """Test that calculated lap times are realistic"""
    
    def test_spa_lap_times(self):
        """Test Spa lap times are realistic"""
        circuit = Circuit('spa')
        car = Car('medium', 50)
        simulator = LapSimulator(circuit, car, 'dry')
        
        result = simulator.simulate_full_lap(1)
        lap_time = result['total_time']
        
        # Spa lap times should be roughly 100-110 seconds for a reasonable setup
        self.assertGreater(lap_time, 95)   # Faster than current record would be unrealistic
        self.assertLess(lap_time, 120)     # Slower than this would be too slow
    
    def test_monaco_lap_times(self):
        """Test Monaco lap times are realistic"""
        circuit = Circuit('monaco')
        car = Car('soft', 40)
        simulator = LapSimulator(circuit, car, 'dry')
        
        result = simulator.simulate_full_lap(1)
        lap_time = result['total_time']
        
        # Monaco lap times should be roughly 70-85 seconds
        self.assertGreater(lap_time, 68)
        self.assertLess(lap_time, 90)
    
    def test_monza_lap_times(self):
        """Test Monza lap times are realistic"""
        circuit = Circuit('monza')
        car = Car('medium', 50)
        simulator = LapSimulator(circuit, car, 'dry')
        
        result = simulator.simulate_full_lap(1)
        lap_time = result['total_time']
        
        # Monza lap times should be roughly 80-90 seconds
        self.assertGreater(lap_time, 78)
        self.assertLess(lap_time, 95)
    
    def test_fuel_effect_on_lap_time(self):
        """Test that fuel load affects lap time realistically"""
        circuit = Circuit('spa')
        
        # Low fuel car
        car_light = Car('medium', 20)
        sim_light = LapSimulator(circuit, car_light, 'dry')
        result_light = sim_light.simulate_full_lap(1)
        
        # High fuel car
        car_heavy = Car('medium', 80)
        sim_heavy = LapSimulator(circuit, car_heavy, 'dry')
        result_heavy = sim_heavy.simulate_full_lap(1)
        
        # Heavy car should be slower
        self.assertGreater(result_heavy['total_time'], result_light['total_time'])
        
        # Difference should be reasonable (not too extreme)
        time_diff = result_heavy['total_time'] - result_light['total_time']
        self.assertLess(time_diff, 10)  # Less than 10 seconds difference
    
    def test_weather_effect_on_lap_time(self):
        """Test that weather affects lap time realistically"""
        circuit = Circuit('spa')
        car = Car('medium', 50)
        
        # Dry conditions
        sim_dry = LapSimulator(circuit, car, 'dry')
        result_dry = sim_dry.simulate_full_lap(1)
        
        # Wet conditions with appropriate tire
        car_wet = Car('wet', 50)
        sim_wet = LapSimulator(circuit, car_wet, 'heavy_rain')
        result_wet = sim_wet.simulate_full_lap(1)
        
        # Wet should be significantly slower
        self.assertGreater(result_wet['total_time'], result_dry['total_time'])
        
        # But not impossibly slow
        time_diff = result_wet['total_time'] - result_dry['total_time']
        self.assertLess(time_diff, 30)  # Less than 30 seconds difference


def run_performance_tests():
    """Run performance comparison tests"""
    print("\n🏁 F1 LAP TIME CALCULATOR - PERFORMANCE TESTS")
    print("="*60)
    
    circuits = ['spa', 'monaco', 'monza', 'silverstone']
    tires = ['soft', 'medium', 'hard']
    
    for circuit_name in circuits:
        print(f"\n📍 {circuit_name.upper()}")
        print("-" * 30)
        
        circuit = Circuit(circuit_name)
        
        for tire in tires:
            car = Car(tire, 50)
            simulator = LapSimulator(circuit, car, 'dry')
            result = simulator.simulate_full_lap(1)
            
            print(f"{tire.capitalize():<8}: {format_lap_time(result['total_time'])}")


if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], verbosity=2, exit=False)
    
    # Run performance tests
    run_performance_tests()
