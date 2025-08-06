#!/usr/bin/env python3
"""
F1 Lap Time Calculator - Main Application

A comprehensive tool for calculating and analyzing F1 lap times based on
circuit layout, car setup, weather conditions, and driver parameters.

Author: F1 Lap Time Calculator
Version: 1.0.0
"""

import sys
import argparse
from typing import Dict, List, Any, Optional
from modules.circuit import Circuit
from modules.car import Car
from modules.lap_simulator import LapSimulator
from modules.utils import (format_lap_time, format_sector_time, validate_inputs,
                          print_comparison_table, log_calculation_details)


class F1LapTimeCalculator:
    """Main application class for F1 Lap Time Calculator"""
    
    def __init__(self):
        """Initialize the calculator"""
        self.simulator = None
        self.verbose = False
    
    def setup_simulation(self, circuit_name: str, tire_compound: str = 'medium',
                        fuel_load: float = 50.0, weather: str = 'dry',
                        downforce: int = 5, engine_mode: str = 'race',
                        driver_aggression: float = 0.5) -> bool:
        """
        Setup simulation with given parameters
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Validate inputs
            is_valid, error_msg = validate_inputs(circuit_name, tire_compound, fuel_load, weather)
            if not is_valid:
                print(f"❌ Input Error: {error_msg}")
                return False
            
            # Create circuit
            circuit = Circuit(circuit_name)
            
            # Create car
            car = Car(tire_compound, fuel_load)
            car.set_setup(downforce, engine_mode, 'auto')
            
            # Create simulator
            self.simulator = LapSimulator(circuit, car, weather)
            self.simulator.set_driver_parameters(driver_aggression, True)
            
            if self.verbose:
                print(f"✅ Simulation setup complete:")
                print(f"   Circuit: {circuit}")
                print(f"   Car: {car}")
                print(f"   Weather: {weather}")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup Error: {str(e)}")
            return False
    
    def calculate_single_lap(self, lap_number: int = 1) -> Optional[Dict[str, Any]]:
        """Calculate a single lap time"""
        if not self.simulator:
            print("❌ Simulator not setup. Run setup_simulation first.")
            return None
        
        try:
            result = self.simulator.simulate_full_lap(lap_number)
            return result
        except Exception as e:
            print(f"❌ Calculation Error: {str(e)}")
            return None
    
    def print_lap_result(self, result: Dict[str, Any]) -> None:
        """Print formatted lap result"""
        if not result:
            return
        
        print("\n" + "="*60)
        print(f"🏁 F1 LAP TIME CALCULATION - LAP {result['lap_number']}")
        print("="*60)
        
        # Main lap time
        print(f"⏱️  TOTAL LAP TIME: {format_lap_time(result['total_time'])}")
        print()
        
        # Sector breakdown
        print("📊 SECTOR BREAKDOWN:")
        for i, (sector_time, sector_result) in enumerate(zip(result['sector_times'], result['sector_results'])):
            sector_num = i + 1
            drs_indicator = " (DRS)" if sector_result['has_drs'] else ""
            print(f"   Sector {sector_num}: {format_sector_time(sector_time)}{drs_indicator}")
        print()
        
        # Conditions
        conditions = result['conditions']
        print("🌍 CONDITIONS:")
        print(f"   Circuit: {conditions['circuit'].replace('_', ' ').title()}")
        print(f"   Weather: {conditions['weather'].replace('_', ' ').title()}")
        print(f"   Tires: {conditions['tire_compound'].title()}")
        print(f"   Fuel: {conditions['fuel_load']}kg")
        print()
        
        # Statistics
        stats = result['lap_statistics']
        print("📈 LAP STATISTICS:")
        print(f"   Fastest Sector: S{stats['fastest_sector']}")
        print(f"   Slowest Sector: S{stats['slowest_sector']}")
        print(f"   Theoretical Best: {format_lap_time(stats['theoretical_best'])}")
        print(f"   Time Loss: +{stats['time_delta_to_theoretical']:.3f}s")
        print(f"   Tire Life: {stats['tire_performance_remaining']*100:.1f}%")
        print()
        
        # Warnings
        if result['warnings']:
            print("⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"   • {warning}")
            print()
        
        if self.verbose:
            log_calculation_details(stats, True)
    
    def compare_tire_compounds(self) -> None:
        """Compare all tire compounds on current circuit"""
        if not self.simulator:
            print("❌ Simulator not setup.")
            return
        
        print("\n🔍 TIRE COMPOUND COMPARISON")
        print("="*50)
        
        tire_compounds = Car.get_available_tire_compounds()
        configurations = [
            {'tire': compound, 'fuel': self.simulator.car.fuel_load}
            for compound in tire_compounds
        ]
        
        results = self.simulator.compare_configurations(configurations)
        
        comparison_data = []
        for result in results:
            comparison_data.append({
                'tire': result['configuration']['tire'],
                'fuel': result['configuration']['fuel'],
                'total_time': result['total_time'],
                'sector_times': result['sector_times'],
                'warnings': '; '.join(result['warnings'])
            })
        
        print_comparison_table(comparison_data)
        
        # Winner announcement
        fastest = results[0]
        print(f"\n🏆 FASTEST: {fastest['configuration']['tire'].title()} tires")
        print(f"   Lap Time: {format_lap_time(fastest['total_time'])}")
    
    def simulate_fuel_strategy(self, fuel_loads: List[float]) -> None:
        """Compare different fuel loads"""
        if not self.simulator:
            print("❌ Simulator not setup.")
            return
        
        print("\n⛽ FUEL LOAD COMPARISON")
        print("="*50)
        
        configurations = [
            {'tire': self.simulator.car.tire_compound, 'fuel': fuel}
            for fuel in fuel_loads
        ]
        
        results = self.simulator.compare_configurations(configurations)
        
        comparison_data = []
        for result in results:
            comparison_data.append({
                'tire': f"{result['configuration']['tire']}/{result['configuration']['fuel']}kg",
                'fuel': result['configuration']['fuel'],
                'total_time': result['total_time'],
                'sector_times': result['sector_times'],
                'warnings': '; '.join(result['warnings'])
            })
        
        print_comparison_table(comparison_data)
    
    def simulate_stint(self, num_laps: int) -> None:
        """Simulate a multi-lap stint"""
        if not self.simulator:
            print("❌ Simulator not setup.")
            return
        
        print(f"\n🏁 STINT SIMULATION ({num_laps} laps)")
        print("="*50)
        
        stint_results = self.simulator.simulate_stint(num_laps, 1)
        
        print(f"{'Lap':<4} {'Lap Time':<12} {'S1':<10} {'S2':<10} {'S3':<10} {'Tire Life':<10}")
        print("-"*60)
        
        for result in stint_results:
            lap_num = result['lap_number']
            lap_time = format_lap_time(result['total_time'])
            s1 = format_sector_time(result['sector_times'][0])
            s2 = format_sector_time(result['sector_times'][1]) if len(result['sector_times']) > 1 else "N/A"
            s3 = format_sector_time(result['sector_times'][2]) if len(result['sector_times']) > 2 else "N/A"
            tire_life = f"{result['lap_statistics']['tire_performance_remaining']*100:.1f}%"
            
            print(f"{lap_num:<4} {lap_time:<12} {s1:<10} {s2:<10} {s3:<10} {tire_life:<10}")
        
        # Stint summary
        total_stint_time = sum(result['total_time'] for result in stint_results)
        fastest_lap = min(stint_results, key=lambda x: x['total_time'])
        slowest_lap = max(stint_results, key=lambda x: x['total_time'])
        
        print("\n📊 STINT SUMMARY:")
        print(f"   Total Time: {format_lap_time(total_stint_time)}")
        print(f"   Average Lap: {format_lap_time(total_stint_time / num_laps)}")
        print(f"   Fastest Lap: {format_lap_time(fastest_lap['total_time'])} (Lap {fastest_lap['lap_number']})")
        print(f"   Slowest Lap: {format_lap_time(slowest_lap['total_time'])} (Lap {slowest_lap['lap_number']})")
    
    def get_setup_suggestions(self) -> None:
        """Get optimal setup suggestions for current circuit"""
        if not self.simulator:
            print("❌ Simulator not setup.")
            return
        
        suggestions = self.simulator.get_optimal_setup_suggestions()
        
        print("\n🔧 SETUP SUGGESTIONS")
        print("="*50)
        
        circuit_analysis = suggestions['circuit_analysis']
        print(f"Circuit Type: {circuit_analysis['circuit_type']}")
        print(f"Difficulty: {circuit_analysis['difficulty']:.2f}/1.0")
        print(f"Total Length: {circuit_analysis['length']}m")
        print(f"DRS Zones: {circuit_analysis['drs_zones']}")
        print()
        
        recommended = suggestions['recommended_setup']
        print("🎯 RECOMMENDED SETUP:")
        print(f"   Downforce: {recommended.get('downforce', 'N/A')}/10")
        print(f"   Engine Mode: {recommended.get('engine_mode', 'N/A').title()}")
        print(f"   ERS Deployment: {recommended.get('ers_deployment', 'N/A').title()}")
        print()
        
        tire_strategy = suggestions['tire_strategy']
        if tire_strategy:
            print("🏁 TIRE STRATEGY:")
            for strategy_type, tire in tire_strategy.items():
                print(f"   {strategy_type.replace('_', ' ').title()}: {tire.title()}")
            print()
        
        print("💡 REASONING:")
        for reason in suggestions['reasoning']:
            print(f"   • {reason}")


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='F1 Lap Time Calculator - Calculate and analyze F1 lap times',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py spa medium 50 dry
  python main.py monaco soft 30 dry --downforce 8 --aggression 0.8
  python main.py monza hard 80 damp --compare-tires
  python main.py silverstone medium 60 dry --stint 10
        """
    )
    
    # Required arguments
    parser.add_argument('circuit', help='Circuit name (spa, monaco, monza, silverstone)')
    parser.add_argument('tire', help='Tire compound (soft, medium, hard, intermediate, wet)')
    parser.add_argument('fuel', type=float, help='Fuel load in kg (0-110)')
    parser.add_argument('weather', help='Weather condition (dry, damp, light_rain, heavy_rain)')
    
    # Optional car setup
    parser.add_argument('--downforce', type=int, default=5, 
                       help='Downforce level 1-10 (default: 5)')
    parser.add_argument('--engine-mode', choices=['quali', 'race', 'conservation'], 
                       default='race', help='Engine mode (default: race)')
    parser.add_argument('--aggression', type=float, default=0.5,
                       help='Driver aggression 0.0-1.0 (default: 0.5)')
    
    # Analysis options
    parser.add_argument('--compare-tires', action='store_true',
                       help='Compare all tire compounds')
    parser.add_argument('--fuel-strategy', nargs='+', type=float,
                       help='Compare different fuel loads (e.g., --fuel-strategy 20 40 60)')
    parser.add_argument('--stint', type=int,
                       help='Simulate multi-lap stint (number of laps)')
    parser.add_argument('--suggestions', action='store_true',
                       help='Get optimal setup suggestions')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output with detailed calculations')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output (lap time only)')
    
    return parser


def main():
    """Main application entry point"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Create calculator instance
    calculator = F1LapTimeCalculator()
    calculator.verbose = args.verbose
    
    # Setup simulation
    success = calculator.setup_simulation(
        circuit_name=args.circuit,
        tire_compound=args.tire,
        fuel_load=args.fuel,
        weather=args.weather,
        downforce=args.downforce,
        engine_mode=args.engine_mode,
        driver_aggression=args.aggression
    )
    
    if not success:
        print("\n❌ Failed to setup simulation. Check your inputs and try again.")
        print("\nAvailable options:")
        print(f"   Circuits: {Circuit.get_available_circuits()}")
        print(f"   Tires: {Car.get_available_tire_compounds()}")
        sys.exit(1)
    
    # Run analysis based on arguments
    if args.compare_tires:
        calculator.compare_tire_compounds()
    elif args.fuel_strategy:
        calculator.simulate_fuel_strategy(args.fuel_strategy)
    elif args.stint:
        calculator.simulate_stint(args.stint)
    elif args.suggestions:
        calculator.get_setup_suggestions()
    else:
        # Standard single lap calculation
        result = calculator.calculate_single_lap(1)
        if result:
            if args.quiet:
                print(format_lap_time(result['total_time']))
            else:
                calculator.print_lap_result(result)


def interactive_mode():
    """Interactive mode for easier use"""
    print("🏁 F1 Lap Time Calculator - Interactive Mode")
    print("="*50)
    
    calculator = F1LapTimeCalculator()
    
    try:
        # Get circuit
        print(f"\nAvailable circuits: {', '.join(Circuit.get_available_circuits())}")
        circuit = input("Enter circuit name: ").strip().lower()
        
        # Get tire compound
        print(f"\nAvailable tires: {', '.join(Car.get_available_tire_compounds())}")
        tire = input("Enter tire compound: ").strip().lower()
        
        # Get fuel load
        fuel = float(input("Enter fuel load (kg, 0-110): ").strip())
        
        # Get weather
        print(f"\nWeather options: dry, damp, light_rain, heavy_rain, extreme_wet")
        weather = input("Enter weather condition: ").strip().lower()
        
        # Optional advanced settings
        advanced = input("\nConfigure advanced settings? (y/n): ").strip().lower() == 'y'
        
        downforce = 5
        engine_mode = 'race'
        aggression = 0.5
        
        if advanced:
            downforce = int(input("Downforce level (1-10, default 5): ") or "5")
            engine_mode = input("Engine mode (quali/race/conservation, default race): ") or "race"
            aggression = float(input("Driver aggression (0.0-1.0, default 0.5): ") or "0.5")
        
        # Setup and run
        if calculator.setup_simulation(circuit, tire, fuel, weather, downforce, engine_mode, aggression):
            result = calculator.calculate_single_lap(1)
            if result:
                calculator.print_lap_result(result)
                
                # Offer additional analysis
                while True:
                    print("\nAdditional analysis options:")
                    print("1. Compare tire compounds")
                    print("2. Fuel strategy analysis")
                    print("3. Stint simulation")
                    print("4. Setup suggestions")
                    print("5. Exit")
                    
                    choice = input("\nEnter choice (1-5): ").strip()
                    
                    if choice == '1':
                        calculator.compare_tire_compounds()
                    elif choice == '2':
                        fuel_loads = input("Enter fuel loads to compare (e.g., 20 40 60): ").split()
                        fuel_loads = [float(f) for f in fuel_loads]
                        calculator.simulate_fuel_strategy(fuel_loads)
                    elif choice == '3':
                        num_laps = int(input("Number of laps to simulate: "))
                        calculator.simulate_stint(num_laps)
                    elif choice == '4':
                        calculator.get_setup_suggestions()
                    elif choice == '5':
                        break
                    else:
                        print("Invalid choice. Please enter 1-5.")
        else:
            print("Failed to setup simulation.")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run interactive mode
        interactive_mode()
    else:
        # Command line arguments provided
        main()
