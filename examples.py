#!/usr/bin/env python3
"""
F1 Lap Time Calculator - Example Usage Script

This script demonstrates various ways to use the F1 Lap Time Calculator API
for different analysis scenarios.
"""

from modules.circuit import Circuit
from modules.car import Car
from modules.lap_simulator import LapSimulator
from modules.utils import format_lap_time, print_comparison_table


def basic_lap_calculation():
    """Example 1: Basic lap time calculation"""
    print("🏁 Example 1: Basic Lap Time Calculation")
    print("="*50)
    
    # Create circuit and car
    circuit = Circuit('spa')
    car = Car('medium', 50.0)
    
    # Create simulator
    simulator = LapSimulator(circuit, car, 'dry')
    
    # Calculate lap time
    result = simulator.simulate_full_lap(1)
    
    print(f"Circuit: {circuit.full_name}")
    print(f"Setup: {car.tire_compound.title()} tires, {car.fuel_load}kg fuel")
    print(f"Lap Time: {format_lap_time(result['total_time'])}")
    print(f"Sector 1: {result['sector_times'][0]:.3f}s")
    print(f"Sector 2: {result['sector_times'][1]:.3f}s") 
    print(f"Sector 3: {result['sector_times'][2]:.3f}s")
    print()


def tire_compound_comparison():
    """Example 2: Compare different tire compounds"""
    print("🏁 Example 2: Tire Compound Comparison")
    print("="*50)
    
    circuit = Circuit('monaco')
    base_car = Car('medium', 40.0)
    simulator = LapSimulator(circuit, base_car, 'dry')
    
    # Test different tire compounds
    tire_compounds = ['soft', 'medium', 'hard']
    results = []
    
    for tire in tire_compounds:
        car = Car(tire, 40.0)
        sim = LapSimulator(circuit, car, 'dry')
        result = sim.simulate_full_lap(1)
        
        results.append({
            'tire': tire,
            'lap_time': result['total_time'],
            'formatted_time': format_lap_time(result['total_time'])
        })
    
    # Sort by lap time
    results.sort(key=lambda x: x['lap_time'])
    
    print(f"Circuit: {circuit.full_name}")
    print(f"Fuel Load: 40kg")
    print()
    for i, result in enumerate(results):
        position = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        print(f"{position} {result['tire'].title()}: {result['formatted_time']}")
    print()


def fuel_strategy_analysis():
    """Example 3: Fuel strategy analysis"""
    print("🏁 Example 3: Fuel Strategy Analysis")
    print("="*50)
    
    circuit = Circuit('monza')
    fuel_loads = [20, 40, 60, 80]
    results = []
    
    for fuel in fuel_loads:
        car = Car('medium', fuel)
        sim = LapSimulator(circuit, car, 'dry')
        result = sim.simulate_full_lap(1)
        
        results.append({
            'fuel_load': fuel,
            'lap_time': result['total_time'],
            'time_penalty': result['total_time'] - results[0]['lap_time'] if results else 0
        })
    
    print(f"Circuit: {circuit.full_name}")
    print(f"Tire: Medium compound")
    print()
    
    for i, result in enumerate(results):
        if i == 0:
            print(f"Fuel {result['fuel_load']:2}kg: {format_lap_time(result['lap_time'])} (baseline)")
        else:
            penalty = result['time_penalty']
            print(f"Fuel {result['fuel_load']:2}kg: {format_lap_time(result['lap_time'])} (+{penalty:.3f}s)")
    print()


def weather_impact_analysis():
    """Example 4: Weather impact analysis"""
    print("🏁 Example 4: Weather Impact Analysis")
    print("="*50)
    
    circuit = Circuit('silverstone')
    weather_conditions = [
        ('dry', 'medium'),
        ('damp', 'intermediate'), 
        ('light_rain', 'intermediate'),
        ('heavy_rain', 'wet')
    ]
    
    results = []
    
    for weather, tire in weather_conditions:
        car = Car(tire, 50.0)
        sim = LapSimulator(circuit, car, weather)
        result = sim.simulate_full_lap(1)
        
        results.append({
            'weather': weather,
            'tire': tire,
            'lap_time': result['total_time'],
            'warnings': result['warnings']
        })
    
    print(f"Circuit: {circuit.full_name}")
    print(f"Fuel Load: 50kg")
    print()
    
    for result in results:
        weather_display = result['weather'].replace('_', ' ').title()
        tire_display = result['tire'].title()
        time_display = format_lap_time(result['lap_time'])
        
        print(f"{weather_display:12} | {tire_display:12} | {time_display}")
        
        if result['warnings']:
            for warning in result['warnings']:
                print(f"              ⚠️  {warning}")
    print()


def setup_optimization():
    """Example 5: Setup optimization for different circuits"""
    print("🏁 Example 5: Setup Optimization")
    print("="*50)
    
    circuits = ['monaco', 'monza']
    
    for circuit_name in circuits:
        circuit = Circuit(circuit_name)
        car = Car('soft', 30.0)
        
        print(f"\n{circuit.full_name}:")
        print("-" * 40)
        
        # Test different downforce settings
        downforce_settings = [3, 5, 8] if circuit_name == 'monza' else [6, 8, 10]
        
        best_time = float('inf')
        best_setup = None
        
        for downforce in downforce_settings:
            car.set_setup(downforce=downforce)
            sim = LapSimulator(circuit, car, 'dry')
            result = sim.simulate_full_lap(1)
            
            print(f"Downforce {downforce}/10: {format_lap_time(result['total_time'])}")
            
            if result['total_time'] < best_time:
                best_time = result['total_time']
                best_setup = downforce
        
        print(f"🏆 Optimal: {best_setup}/10 downforce")


def stint_simulation():
    """Example 6: Multi-lap stint simulation"""
    print("🏁 Example 6: Stint Simulation (Tire Degradation)")
    print("="*50)
    
    circuit = Circuit('spa')
    car = Car('soft', 60.0)  # Soft tires degrade faster
    simulator = LapSimulator(circuit, car, 'dry')
    
    # Simulate 15 laps
    stint_results = simulator.simulate_stint(15, 1)
    
    print(f"Circuit: {circuit.full_name}")
    print(f"Tire: {car.tire_compound.title()} compound")
    print(f"Fuel: {car.fuel_load}kg starting load")
    print()
    
    print("Lap | Lap Time    | Tire Life | Notes")
    print("----|-------------|-----------|-------")
    
    fastest_lap = min(stint_results, key=lambda x: x['total_time'])
    
    for result in stint_results:
        lap_num = result['lap_number']
        lap_time = format_lap_time(result['total_time'])
        tire_life = f"{result['lap_statistics']['tire_performance_remaining']*100:.0f}%"
        
        notes = ""
        if result == fastest_lap:
            notes = "🏆 Fastest"
        elif result['lap_statistics']['tire_performance_remaining'] < 0.7:
            notes = "⚠️ Degraded"
        
        print(f"{lap_num:2}  | {lap_time:11} | {tire_life:8} | {notes}")
    
    print(f"\nFastest Lap: {format_lap_time(fastest_lap['total_time'])} (Lap {fastest_lap['lap_number']})")
    print()


def advanced_comparison():
    """Example 7: Advanced multi-factor comparison"""
    print("🏁 Example 7: Advanced Multi-Factor Comparison")
    print("="*50)
    
    circuit = Circuit('spa')
    
    # Different strategies to compare
    strategies = [
        {'name': 'Qualifying', 'tire': 'soft', 'fuel': 20, 'downforce': 5, 'engine': 'quali'},
        {'name': 'Race Start', 'tire': 'medium', 'fuel': 70, 'downforce': 5, 'engine': 'race'},
        {'name': 'Low Fuel Sprint', 'tire': 'soft', 'fuel': 35, 'downforce': 4, 'engine': 'race'},
        {'name': 'Conservation', 'tire': 'hard', 'fuel': 80, 'downforce': 6, 'engine': 'conservation'}
    ]
    
    results = []
    
    for strategy in strategies:
        car = Car(strategy['tire'], strategy['fuel'])
        car.set_setup(
            downforce=strategy['downforce'],
            engine_mode=strategy['engine']
        )
        
        sim = LapSimulator(circuit, car, 'dry')
        result = sim.simulate_full_lap(1)
        
        results.append({
            'strategy': strategy['name'],
            'setup': f"{strategy['tire']}/{strategy['fuel']}kg",
            'lap_time': result['total_time'],
            'downforce': strategy['downforce'],
            'engine_mode': strategy['engine']
        })
    
    # Sort by lap time
    results.sort(key=lambda x: x['lap_time'])
    
    print(f"Circuit: {circuit.full_name}")
    print()
    print("Strategy         | Setup       | Lap Time    | DF | Engine")
    print("-----------------|-------------|-------------|----|-----------")
    
    for result in results:
        strategy = result['strategy'][:15].ljust(15)
        setup = result['setup'][:10].ljust(10)
        lap_time = format_lap_time(result['lap_time'])
        downforce = f"{result['downforce']}/10"
        engine = result['engine_mode'][:11]
        
        print(f"{strategy} | {setup} | {lap_time:11} | {downforce:2} | {engine}")
    print()


def main():
    """Run all examples"""
    print("🏁 F1 LAP TIME CALCULATOR - EXAMPLE USAGE")
    print("="*60)
    print()
    
    # Run all examples
    basic_lap_calculation()
    tire_compound_comparison()
    fuel_strategy_analysis()
    weather_impact_analysis()
    setup_optimization()
    stint_simulation()
    advanced_comparison()
    
    print("🏆 All examples completed successfully!")
    print("\nTry running the main application with different parameters:")
    print("  python main.py spa medium 50 dry")
    print("  python main.py monaco soft 30 dry --compare-tires")
    print("  python main.py monza medium 60 dry --stint 20")


if __name__ == "__main__":
    main()
