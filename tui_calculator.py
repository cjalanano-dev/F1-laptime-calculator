#!/usr/bin/env python3
"""
F1 Lap Time Calculator - Terminal User Interface (TUI)

A curses-based interactive terminal interface for the F1 Lap Time Calculator.
Provides real-time configuration and analysis with visual feedback.
"""

import curses
import sys
import os
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.circuit import Circuit
from modules.car import Car
from modules.lap_simulator import LapSimulator
from modules.utils import format_lap_time, format_sector_time


class F1TUI:
    """Terminal User Interface for F1 Lap Time Calculator"""
    
    def __init__(self, stdscr):
        """Initialize the TUI"""
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlighted
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error/Warning
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Special
        
        # Configuration state
        self.config = {
            'circuit': 'spa',
            'tire': 'medium',
            'fuel': 50.0,
            'weather': 'dry',
            'downforce': 5,
            'engine_mode': 'race',
            'aggression': 0.5
        }
        
        # Available options
        self.circuits = Circuit.get_available_circuits()
        self.tires = Car.get_available_tire_compounds()
        self.weather_options = ['dry', 'damp', 'light_rain', 'heavy_rain', 'extreme_wet']
        self.engine_modes = ['quali', 'race', 'conservation']
        
        # Current result
        self.current_result = None
        self.simulator = None
        
        # Menu state
        self.current_menu = 'main'
        self.selected_item = 0
        self.analysis_results = {}
        
        # Initialize simulator
        self.update_simulator()
    
    def update_simulator(self) -> bool:
        """Update simulator with current configuration"""
        try:
            circuit = Circuit(self.config['circuit'])
            car = Car(self.config['tire'], self.config['fuel'])
            car.set_setup(
                downforce=self.config['downforce'],
                engine_mode=self.config['engine_mode'],
                ers_deployment='auto'
            )
            
            self.simulator = LapSimulator(circuit, car, self.config['weather'])
            self.simulator.set_driver_parameters(self.config['aggression'], True)
            
            # Calculate current lap time
            self.current_result = self.simulator.simulate_full_lap(1)
            return True
            
        except Exception as e:
            self.current_result = None
            return False
    
    def draw_header(self) -> None:
        """Draw the main header"""
        title = "F1 LAP TIME CALCULATOR - TUI"
        subtitle = "Use arrow keys to navigate, ENTER to select, 'q' to quit"
        
        # Clear top lines
        self.stdscr.addstr(0, 0, " " * self.width, curses.color_pair(1))
        self.stdscr.addstr(1, 0, " " * self.width, curses.color_pair(1))
        
        # Center the title
        title_x = max(0, (self.width - len(title)) // 2)
        subtitle_x = max(0, (self.width - len(subtitle)) // 2)
        
        self.stdscr.addstr(0, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(1, subtitle_x, subtitle, curses.color_pair(5))
    
    def draw_config_panel(self, start_y: int) -> int:
        """Draw the configuration panel"""
        y = start_y
        
        # Configuration header
        self.stdscr.addstr(y, 2, "CONFIGURATION", curses.color_pair(6) | curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 2, "=" * 40, curses.color_pair(6))
        y += 2
        
        # Circuit
        circuit_display = self.config['circuit'].replace('_', ' ').title()
        self.stdscr.addstr(y, 4, f"Circuit:     {circuit_display}", curses.color_pair(2))
        y += 1
        
        # Tire compound
        tire_display = self.config['tire'].title()
        self.stdscr.addstr(y, 4, f"Tire:        {tire_display}", curses.color_pair(2))
        y += 1
        
        # Fuel load
        self.stdscr.addstr(y, 4, f"Fuel:        {self.config['fuel']:.1f}kg", curses.color_pair(2))
        y += 1
        
        # Weather
        weather_display = self.config['weather'].replace('_', ' ').title()
        self.stdscr.addstr(y, 4, f"Weather:     {weather_display}", curses.color_pair(2))
        y += 1
        
        # Downforce
        self.stdscr.addstr(y, 4, f"Downforce:   {self.config['downforce']}/10", curses.color_pair(2))
        y += 1
        
        # Engine mode
        engine_display = self.config['engine_mode'].title()
        self.stdscr.addstr(y, 4, f"Engine:      {engine_display}", curses.color_pair(2))
        y += 1
        
        # Driver aggression
        self.stdscr.addstr(y, 4, f"Aggression:  {self.config['aggression']:.1f}", curses.color_pair(2))
        y += 2
        
        return y
    
    def draw_results_panel(self, start_y: int) -> int:
        """Draw the results panel"""
        y = start_y
        
        # Results header
        self.stdscr.addstr(y, 48, "CURRENT LAP TIME", curses.color_pair(6) | curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 48, "=" * 30, curses.color_pair(6))
        y += 2
        
        if self.current_result:
            # Total lap time
            lap_time = format_lap_time(self.current_result['total_time'])
            self.stdscr.addstr(y, 50, f"Total Time: {lap_time}", curses.color_pair(3) | curses.A_BOLD)
            y += 2
            
            # Sector times
            self.stdscr.addstr(y, 50, "Sector Breakdown:", curses.color_pair(5))
            y += 1
            
            for i, sector_time in enumerate(self.current_result['sector_times']):
                sector_result = self.current_result['sector_results'][i]
                sector_num = i + 1
                time_str = format_sector_time(sector_time)
                drs_indicator = " (DRS)" if sector_result['has_drs'] else ""
                
                self.stdscr.addstr(y, 52, f"S{sector_num}: {time_str}{drs_indicator}")
                y += 1
            
            y += 1
            
            # Statistics
            stats = self.current_result['lap_statistics']
            self.stdscr.addstr(y, 50, "Statistics:", curses.color_pair(5))
            y += 1
            self.stdscr.addstr(y, 52, f"Fastest: S{stats['fastest_sector']}")
            y += 1
            self.stdscr.addstr(y, 52, f"Tire: {stats['tire_performance_remaining']*100:.1f}%")
            y += 1
            
            # Warnings
            if self.current_result['warnings']:
                y += 1
                self.stdscr.addstr(y, 50, "Warnings:", curses.color_pair(4))
                y += 1
                for warning in self.current_result['warnings']:
                    if y < self.height - 3:
                        warning_text = warning[:25] + "..." if len(warning) > 25 else warning
                        self.stdscr.addstr(y, 52, warning_text, curses.color_pair(4))
                        y += 1
        else:
            self.stdscr.addstr(y, 50, "Error calculating", curses.color_pair(4))
            y += 1
        
        return y
    
    def draw_main_menu(self) -> None:
        """Draw the main menu"""
        # Draw configuration and results panels
        config_end_y = self.draw_config_panel(3)
        results_end_y = self.draw_results_panel(3)
        
        # Draw menu options
        menu_start_y = max(config_end_y, results_end_y) + 1
        
        self.stdscr.addstr(menu_start_y, 2, "MENU OPTIONS", curses.color_pair(6) | curses.A_BOLD)
        menu_start_y += 1
        self.stdscr.addstr(menu_start_y, 2, "=" * 40, curses.color_pair(6))
        menu_start_y += 2
        
        menu_items = [
            "1. Modify Configuration",
            "2. Compare Tire Compounds",
            "3. Fuel Strategy Analysis",
            "4. Multi-Lap Stint Simulation",
            "5. Setup Suggestions",
            "6. Weather Comparison",
            "7. Exit"
        ]
        
        for i, item in enumerate(menu_items):
            if i == self.selected_item:
                self.stdscr.addstr(menu_start_y + i, 4, f"> {item}", curses.color_pair(2) | curses.A_BOLD)
            else:
                self.stdscr.addstr(menu_start_y + i, 4, f"  {item}")
    
    def draw_config_menu(self) -> None:
        """Draw the configuration modification menu"""
        self.stdscr.clear()
        self.draw_header()
        
        y = 4
        self.stdscr.addstr(y, 2, "MODIFY CONFIGURATION", curses.color_pair(6) | curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 2, "=" * 50, curses.color_pair(6))
        y += 3
        
        config_items = [
            f"Circuit:      {self.config['circuit'].replace('_', ' ').title()}",
            f"Tire:         {self.config['tire'].title()}",
            f"Fuel Load:    {self.config['fuel']:.1f}kg",
            f"Weather:      {self.config['weather'].replace('_', ' ').title()}",
            f"Downforce:    {self.config['downforce']}/10",
            f"Engine Mode:  {self.config['engine_mode'].title()}",
            f"Aggression:   {self.config['aggression']:.1f}",
            "Back to Main Menu"
        ]
        
        for i, item in enumerate(config_items):
            if i == self.selected_item:
                self.stdscr.addstr(y + i * 2, 4, f"> {item}", curses.color_pair(2) | curses.A_BOLD)
            else:
                self.stdscr.addstr(y + i * 2, 4, f"  {item}")
        
        # Show available options for selected item
        if self.selected_item < len(config_items) - 1:
            y_options = y + len(config_items) * 2 + 2
            
            self.stdscr.addstr(y_options, 4, "Available options:", curses.color_pair(5))
            y_options += 1
            
            if self.selected_item == 0:  # Circuit
                options = ", ".join([c.replace('_', ' ').title() for c in self.circuits])
            elif self.selected_item == 1:  # Tire
                options = ", ".join([t.title() for t in self.tires])
            elif self.selected_item == 2:  # Fuel
                options = "0.0 - 110.0 kg"
            elif self.selected_item == 3:  # Weather
                options = ", ".join([w.replace('_', ' ').title() for w in self.weather_options])
            elif self.selected_item == 4:  # Downforce
                options = "1 - 10"
            elif self.selected_item == 5:  # Engine mode
                options = ", ".join([e.title() for e in self.engine_modes])
            elif self.selected_item == 6:  # Aggression
                options = "0.0 - 1.0"
            else:
                options = ""
            
            # Wrap long options text
            if len(options) > self.width - 8:
                options = options[:self.width - 11] + "..."
            
            self.stdscr.addstr(y_options, 6, options, curses.color_pair(5))
    
    def draw_analysis_result(self, title: str, content: List[str]) -> None:
        """Draw analysis results"""
        self.stdscr.clear()
        self.draw_header()
        
        y = 4
        self.stdscr.addstr(y, 2, title, curses.color_pair(6) | curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 2, "=" * len(title), curses.color_pair(6))
        y += 3
        
        for line in content:
            if y < self.height - 3:
                # Truncate line if too long
                if len(line) > self.width - 4:
                    line = line[:self.width - 7] + "..."
                self.stdscr.addstr(y, 4, line)
                y += 1
        
        y += 2
        self.stdscr.addstr(y, 4, "Press any key to continue...", curses.color_pair(5))
    
    def modify_config_value(self, config_key: str) -> None:
        """Modify a configuration value"""
        self.stdscr.clear()
        self.draw_header()
        
        y = 6
        current_value = self.config[config_key]
        display_key = config_key.replace('_', ' ').title()
        
        self.stdscr.addstr(y, 4, f"Modify {display_key}", curses.color_pair(6) | curses.A_BOLD)
        y += 1
        self.stdscr.addstr(y, 4, f"Current value: {current_value}")
        y += 2
        
        if config_key == 'circuit':
            self.modify_list_value(config_key, self.circuits, y)
        elif config_key == 'tire':
            self.modify_list_value(config_key, self.tires, y)
        elif config_key == 'weather':
            self.modify_list_value(config_key, self.weather_options, y)
        elif config_key == 'engine_mode':
            self.modify_list_value(config_key, self.engine_modes, y)
        elif config_key in ['fuel', 'downforce', 'aggression']:
            self.modify_numeric_value(config_key, y)
    
    def modify_list_value(self, config_key: str, options: List[str], start_y: int) -> None:
        """Modify a list-based configuration value"""
        current_idx = options.index(self.config[config_key]) if self.config[config_key] in options else 0
        selected_idx = current_idx
        
        while True:
            y = start_y
            self.stdscr.addstr(y, 4, "Select new value (Up/Down to navigate, ENTER to select, ESC to cancel):")
            y += 2
            
            for i, option in enumerate(options):
                display_option = option.replace('_', ' ').title()
                if i == selected_idx:
                    self.stdscr.addstr(y + i, 6, f"> {display_option}", curses.color_pair(2) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y + i, 6, f"  {display_option}")
            
            self.stdscr.refresh()
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                selected_idx = (selected_idx - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected_idx = (selected_idx + 1) % len(options)
            elif key == ord('\n'):
                self.config[config_key] = options[selected_idx]
                self.update_simulator()
                break
            elif key == 27:  # ESC
                break
            
            # Clear previous selections
            for i in range(len(options)):
                self.stdscr.addstr(start_y + 2 + i, 6, " " * 30)
    
    def modify_numeric_value(self, config_key: str, start_y: int) -> None:
        """Modify a numeric configuration value"""
        y = start_y
        
        # Define ranges and steps
        ranges = {
            'fuel': (0.0, 110.0, 5.0),
            'downforce': (1, 10, 1),
            'aggression': (0.0, 1.0, 0.1)
        }
        
        min_val, max_val, step = ranges[config_key]
        current_val = self.config[config_key]
        
        self.stdscr.addstr(y, 4, f"Adjust value (Left/Right to change, ENTER to confirm, ESC to cancel):")
        y += 1
        self.stdscr.addstr(y, 4, f"Range: {min_val} - {max_val}")
        y += 3
        
        while True:
            # Display current value with visual indicator
            if config_key == 'downforce':
                bar_length = 20
                filled = int((current_val / max_val) * bar_length)
                bar = "#" * filled + "-" * (bar_length - filled)
                self.stdscr.addstr(y, 6, f"Value: {current_val:4.1f} [{bar}]", curses.color_pair(2))
            else:
                self.stdscr.addstr(y, 6, f"Value: {current_val:6.1f}", curses.color_pair(2))
            
            self.stdscr.refresh()
            key = self.stdscr.getch()
            
            if key == curses.KEY_LEFT:
                current_val = max(min_val, current_val - step)
            elif key == curses.KEY_RIGHT:
                current_val = min(max_val, current_val + step)
            elif key == ord('\n'):
                self.config[config_key] = current_val
                self.update_simulator()
                break
            elif key == 27:  # ESC
                break
            
            # Clear the line
            self.stdscr.addstr(y, 6, " " * 30)
    
    def run_tire_comparison(self) -> None:
        """Run tire compound comparison"""
        if not self.simulator:
            return
        
        configurations = [
            {'tire': tire, 'fuel': self.config['fuel']}
            for tire in self.tires
        ]
        
        results = self.simulator.compare_configurations(configurations)
        
        content = []
        content.append("Tire Compound Comparison:")
        content.append("")
        
        for i, result in enumerate(results):
            position = "1st" if i == 0 else "2nd" if i == 1 else "3rd" if i == 2 else f"{i+1}th"
            tire = result['configuration']['tire'].title()
            time = format_lap_time(result['total_time'])
            content.append(f"{position:<4} {tire:<12} {time}")
        
        content.append("")
        content.append(f"Fastest: {results[0]['configuration']['tire'].title()} tires")
        
        self.draw_analysis_result("TIRE COMPARISON", content)
    
    def run_fuel_analysis(self) -> None:
        """Run fuel strategy analysis"""
        if not self.simulator:
            return
        
        fuel_loads = [20, 40, 60, 80, 100]
        configurations = [
            {'tire': self.config['tire'], 'fuel': fuel}
            for fuel in fuel_loads
        ]
        
        results = self.simulator.compare_configurations(configurations)
        
        content = []
        content.append("Fuel Load Strategy Analysis:")
        content.append("")
        
        baseline_time = results[0]['total_time']
        
        for result in results:
            fuel = result['configuration']['fuel']
            time = format_lap_time(result['total_time'])
            penalty = result['total_time'] - baseline_time
            
            if penalty == 0:
                content.append(f"Fuel {fuel:3.0f}kg: {time} (baseline)")
            else:
                content.append(f"Fuel {fuel:3.0f}kg: {time} (+{penalty:.3f}s)")
        
        self.draw_analysis_result("FUEL STRATEGY", content)
    
    def run_stint_simulation(self) -> None:
        """Run multi-lap stint simulation"""
        if not self.simulator:
            return
        
        stint_results = self.simulator.simulate_stint(15, 1)
        
        content = []
        content.append("15-Lap Stint Simulation:")
        content.append("")
        content.append("Lap | Lap Time    | Tire Life")
        content.append("----|-------------|----------")
        
        fastest_lap = min(stint_results, key=lambda x: x['total_time'])
        
        for result in stint_results:
            lap_num = result['lap_number']
            lap_time = format_lap_time(result['total_time'])
            tire_life = f"{result['lap_statistics']['tire_performance_remaining']*100:.0f}%"
            
            marker = " *" if result == fastest_lap else ""
            content.append(f"{lap_num:2}  | {lap_time:11} | {tire_life:8}{marker}")
        
        content.append("")
        content.append(f"Fastest: {format_lap_time(fastest_lap['total_time'])} (Lap {fastest_lap['lap_number']})")
        
        self.draw_analysis_result("STINT SIMULATION", content)
    
    def run_setup_suggestions(self) -> None:
        """Show setup suggestions"""
        if not self.simulator:
            return
        
        suggestions = self.simulator.get_optimal_setup_suggestions()
        
        content = []
        content.append("Optimal Setup Suggestions:")
        content.append("")
        
        circuit_info = suggestions['circuit_analysis']
        content.append(f"Circuit Type: {circuit_info['circuit_type']}")
        content.append(f"Difficulty: {circuit_info['difficulty']:.2f}/1.0")
        content.append("")
        
        recommended = suggestions['recommended_setup']
        content.append("Recommended Setup:")
        content.append(f"  Downforce: {recommended.get('downforce', 'N/A')}/10")
        content.append(f"  Engine Mode: {recommended.get('engine_mode', 'N/A').title()}")
        content.append("")
        
        tire_strategy = suggestions.get('tire_strategy', {})
        if tire_strategy:
            content.append("Tire Strategy:")
            for strategy_type, tire in tire_strategy.items():
                strategy_display = strategy_type.replace('_', ' ').title()
                content.append(f"  {strategy_display}: {tire.title()}")
            content.append("")
        
        content.append("Reasoning:")
        for reason in suggestions['reasoning']:
            content.append(f"  - {reason}")
        
        self.draw_analysis_result("SETUP SUGGESTIONS", content)
    
    def run_weather_comparison(self) -> None:
        """Run weather comparison"""
        if not self.simulator:
            return
        
        weather_configs = [
            ('dry', 'medium'),
            ('damp', 'intermediate'),
            ('light_rain', 'intermediate'),
            ('heavy_rain', 'wet')
        ]
        
        content = []
        content.append("Weather Condition Comparison:")
        content.append("")
        content.append("Weather      | Tire         | Lap Time")
        content.append("-------------|--------------|----------")
        
        for weather, tire in weather_configs:
            car = Car(tire, self.config['fuel'])
            car.set_setup(
                downforce=self.config['downforce'],
                engine_mode=self.config['engine_mode']
            )
            
            sim = LapSimulator(self.simulator.circuit, car, weather)
            result = sim.simulate_full_lap(1)
            
            weather_display = weather.replace('_', ' ').title()
            tire_display = tire.title()
            time_display = format_lap_time(result['total_time'])
            
            content.append(f"{weather_display:12} | {tire_display:12} | {time_display}")
            
            if result['warnings']:
                for warning in result['warnings']:
                    if len(warning) > 30:
                        warning = warning[:27] + "..."
                    content.append(f"             WARNING: {warning}")
        
        self.draw_analysis_result("WEATHER COMPARISON", content)
    
    def handle_input(self) -> bool:
        """Handle user input, return False to exit"""
        key = self.stdscr.getch()
        
        if key == ord('q') or key == ord('Q'):
            return False
        
        if self.current_menu == 'main':
            if key == curses.KEY_UP:
                self.selected_item = (self.selected_item - 1) % 7
            elif key == curses.KEY_DOWN:
                self.selected_item = (self.selected_item + 1) % 7
            elif key == ord('\n'):
                if self.selected_item == 0:  # Modify Configuration
                    self.current_menu = 'config'
                    self.selected_item = 0
                elif self.selected_item == 1:  # Compare Tires
                    self.run_tire_comparison()
                    self.stdscr.getch()  # Wait for key press
                elif self.selected_item == 2:  # Fuel Strategy
                    self.run_fuel_analysis()
                    self.stdscr.getch()
                elif self.selected_item == 3:  # Stint Simulation
                    self.run_stint_simulation()
                    self.stdscr.getch()
                elif self.selected_item == 4:  # Setup Suggestions
                    self.run_setup_suggestions()
                    self.stdscr.getch()
                elif self.selected_item == 5:  # Weather Comparison
                    self.run_weather_comparison()
                    self.stdscr.getch()
                elif self.selected_item == 6:  # Exit
                    return False
        
        elif self.current_menu == 'config':
            if key == curses.KEY_UP:
                self.selected_item = (self.selected_item - 1) % 8
            elif key == curses.KEY_DOWN:
                self.selected_item = (self.selected_item + 1) % 8
            elif key == ord('\n'):
                if self.selected_item == 7:  # Back to main menu
                    self.current_menu = 'main'
                    self.selected_item = 0
                else:
                    # Modify configuration
                    config_keys = ['circuit', 'tire', 'fuel', 'weather', 'downforce', 'engine_mode', 'aggression']
                    if self.selected_item < len(config_keys):
                        self.modify_config_value(config_keys[self.selected_item])
        
        return True
    
    def run(self) -> None:
        """Main TUI loop"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(0)  # Blocking input
        
        while True:
            self.stdscr.clear()
            
            if self.current_menu == 'main':
                self.draw_header()
                self.draw_main_menu()
            elif self.current_menu == 'config':
                self.draw_config_menu()
            
            self.stdscr.refresh()
            
            if not self.handle_input():
                break


def main(stdscr):
    """Main entry point for curses application"""
    try:
        tui = F1TUI(stdscr)
        tui.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Clean exit on error
        curses.endwin()
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Check terminal size
    try:
        import shutil
        width, height = shutil.get_terminal_size()
        if width < 80 or height < 20:
            print("Terminal too small! Please resize to at least 80x20 characters.")
            print(f"Current size: {width}x{height}")
            print("\nFor the best experience, use a terminal window of at least 80x24.")
            print("You can also try running 'python main.py' for the CLI version.")
            sys.exit(1)
    except:
        pass
    
    print("F1 Lap Time Calculator TUI")
    print("Initializing interface...")
    print("(Press 'q' to exit once loaded)")
    
    try:
        curses.wrapper(main)
        print("\nTUI session ended.")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Try resizing your terminal or use 'python main.py' for the CLI version.")
