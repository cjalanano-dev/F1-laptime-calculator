# F1 Lap Time Calculator (TUI)

A comprehensive Python tool for calculating and analyzing Formula 1 lap times based on circuit layout, car setup, weather conditions, and driver parameters.

## Features

- **Interactive TUI**: Modern terminal user interface with real-time updates and visual feedback (Make sure your terminal supports curses and is at least 80x24 characters)
- **Circuit Simulation**: Accurate modeling of F1 circuits with sector-by-sector analysis
- **Car Configuration**: Detailed car setup including tires, fuel load, aerodynamics, and engine modes
- **Weather Effects**: Realistic weather impact on grip and lap times
- **Tire Degradation**: Advanced tire wear modeling over multiple laps
- **Strategy Analysis**: Compare different tire compounds and fuel loads
- **Stint Simulation**: Multi-lap race simulation with degradation
- **Setup Optimization**: Get optimal setup suggestions for each circuit
- **Multiple Interfaces**: Choose between TUI, CLI, or interactive command-line modes

## Project Structure

```
f1_lap_time_calculator/
├── main.py                     # Main application with CLI and interactive modes
├── tui_calculator.py           # Terminal User Interface (TUI) with curses
├── data/
│   ├── circuits.json          # Circuit data (Spa, Monaco, Monza, Silverstone)
│   ├── tires.json             # Tire compound specifications
│   └── weather_presets.json   # Weather conditions and effects
├── modules/
│   ├── circuit.py             # Circuit modeling and sector analysis
│   ├── car.py                 # Car setup and performance calculations
│   ├── lap_simulator.py       # Main simulation engine
│   └── utils.py               # Utility functions and helpers
├── tests/
│   └── test_lap_calculator.py # Comprehensive test suite
└── README.md                  # This file
```

## Quick Start

### Installation

1. Clone or download the project
2. No external dependencies required - uses only Python standard library
3. Ensure your terminal supports colors and is at least 80x20 characters for the TUI

### Getting Started

**For the best experience, start with the TUI:**

```bash
python tui_calculator.py
```

**Or use the command-line interface:**

```bash
python main.py
```

### Basic Usage

#### Terminal User Interface (TUI) - Recommended

Launch the interactive curses-based interface for the best experience:

```bash
python tui_calculator.py
```

The TUI provides:
- **Real-time configuration**: Adjust settings and see lap times update instantly
- **Visual interface**: Color-coded panels with easy navigation
- **Quick analysis**: Built-in tire comparison, fuel strategy, and stint simulation
- **Setup suggestions**: AI-powered recommendations for optimal car setup
- **Weather comparison**: Compare different weather conditions side-by-side

**Navigation:**
- Use arrow keys to navigate menus
- Press ENTER to select options
- Press 'q' to quit at any time
- ESC to cancel or go back

**Requirements:** Terminal size of at least 80x20 characters (80x24 recommended)

#### Command Line Interface

```bash
# Basic lap time calculation
python main.py spa medium 50 dry

# Advanced setup with custom parameters
python main.py monaco soft 30 dry --downforce 8 --aggression 0.8

# Compare all tire compounds
python main.py monza medium 60 dry --compare-tires

# Fuel strategy analysis
python main.py silverstone medium 50 dry --fuel-strategy 20 40 60 80

# Multi-lap stint simulation
python main.py spa hard 70 dry --stint 15

# Get setup suggestions
python main.py monaco medium 40 dry --suggestions
```

#### Interactive CLI Mode

Simply run without arguments for guided setup:

```bash
python main.py
```

### Python API Usage

```python
from modules.circuit import Circuit
from modules.car import Car
from modules.lap_simulator import LapSimulator

# Create circuit and car
circuit = Circuit('spa')
car = Car('medium', 50.0)  # Medium tires, 50kg fuel

# Setup car configuration
car.set_setup(downforce=6, engine_mode='race', ers_deployment='auto')

# Create simulator
simulator = LapSimulator(circuit, car, 'dry')
simulator.set_driver_parameters(aggression=0.7, use_drs=True)

# Simulate lap
result = simulator.simulate_full_lap(1)
print(f"Lap time: {result['total_time']:.3f} seconds")
```

## Available Options

### Circuits
- **spa**: Circuit de Spa-Francorchamps (Belgium)
- **monaco**: Circuit de Monaco (Monaco)  
- **monza**: Autodromo Nazionale Monza (Italy)
- **silverstone**: Silverstone Circuit (United Kingdom)

### Tire Compounds
- **soft**: Soft compound (fastest, highest degradation)
- **medium**: Medium compound (balanced performance)
- **hard**: Hard compound (slowest, lowest degradation)
- **intermediate**: For wet conditions
- **wet**: For heavy rain conditions

### Weather Conditions
- **dry**: Perfect dry conditions
- **damp**: Slightly wet track surface
- **light_rain**: Light rain, reduced grip
- **heavy_rain**: Heavy rain, significantly reduced grip
- **extreme_wet**: Extreme conditions, safety car risk

### Car Setup Options
- **Downforce**: 1-10 scale (1=low/Monza-style, 10=high/Monaco-style)
- **Engine Mode**: quali, race, conservation
- **ERS Deployment**: auto, aggressive, conservative
- **Driver Aggression**: 0.0-1.0 (conservative to maximum attack)

## Sample Output

```
 F1 LAP TIME CALCULATION - LAP 1
============================================================
⏱ TOTAL LAP TIME: 1:43.524

SECTOR BREAKDOWN:
   Sector 1: 32.145s (DRS)
   Sector 2: 38.891s (DRS)
   Sector 3: 32.488s

CONDITIONS:
   Circuit: Spa
   Weather: Dry
   Tires: Medium
   Fuel: 50kg

LAP STATISTICS:
   Fastest Sector: S1
   Slowest Sector: S2
   Theoretical Best: 1:41.234
   Time Loss: +2.290s
   Tire Life: 95.2%
```

## Advanced Features

### TUI Analysis Tools

The Terminal User Interface provides quick access to all analysis features:

1. **Configuration Panel**: Real-time lap time updates as you modify settings
2. **Tire Comparison**: Compare all tire compounds instantly
3. **Fuel Strategy**: Analyze different fuel loads and their impact
4. **Stint Simulation**: Visualize tire degradation over multiple laps
5. **Setup Suggestions**: Get AI-powered recommendations
6. **Weather Comparison**: Compare performance across all weather conditions

### Command-Line Analysis

### Command-Line Analysis

#### Tire Strategy Analysis

Compare different tire compounds:

```bash
python main.py spa medium 50 dry --compare-tires
```

#### Fuel Effect Analysis

See how fuel load affects performance:

```bash
python main.py monza medium 50 dry --fuel-strategy 20 40 60 80
```

#### Multi-Lap Stint Simulation

Simulate tire degradation over multiple laps:

```bash
python main.py spa soft 60 dry --stint 20
```

#### Setup Optimization

Get AI-powered setup suggestions:

```bash
python main.py monaco medium 40 dry --suggestions
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_lap_calculator.py
```

Tests include:
- Unit tests for all modules
- Realistic lap time validation
- Performance comparison tests
- Edge case handling

## Technical Details

### Physics Model

The simulator uses simplified but realistic physics:

- **Sector Times**: Based on track length, turn density, and elevation changes
- **Tire Performance**: Grip degradation modeling with temperature effects
- **Fuel Impact**: Weight penalty calculations (≈0.035s per kg per km)
- **Aerodynamics**: Downforce vs drag trade-offs for different circuit types
- **Weather Effects**: Grip reduction and mistake probability modeling

### Validation

Lap times are validated against real F1 data:
- Spa: ~103-110 seconds (depending on conditions)
- Monaco: ~70-78 seconds
- Monza: ~80-87 seconds  
- Silverstone: ~85-92 seconds

### Accuracy

The simulator provides realistic relative comparisons rather than absolute precision. Factors affecting accuracy:
- Tire compound differences
- Fuel load effects
- Weather impact
- Setup optimization
- Absolute lap times (±5% variance)

## Future Enhancements

### Planned Features
- [ ] Enhanced TUI with graphical charts
- [ ] Web interface with Streamlit
- [ ] Real telemetry data integration
- [ ] Visual track maps
- [ ] Save/load configuration presets

### Contributing

Feel free to contribute by:
1. Adding new circuits to `data/circuits.json`
2. Improving physics calculations
3. Adding new analysis features
4. Creating visualization tools

## Example Use Cases

### Using the TUI (Recommended)

1. **Launch TUI**: `python tui_calculator.py`
2. **Navigate**: Use arrow keys to explore menu options
3. **Modify Settings**: Select "Modify Configuration" to adjust circuit, tires, fuel, etc.
4. **Quick Analysis**: Access tire comparison, fuel strategy, and stint simulation with one click
5. **Real-time Updates**: See lap times change instantly as you modify settings

### Command-Line Examples

#### Race Strategy Planning
```bash
# Compare tire strategies for a 20-lap stint
python main.py spa soft 60 dry --stint 20
python main.py spa medium 60 dry --stint 20
python main.py spa hard 60 dry --stint 20
```

#### Qualifying Setup Optimization
```bash
# Find optimal downforce for qualifying
python main.py monza soft 20 dry --downforce 3 --engine-mode quali
python main.py monaco soft 20 dry --downforce 9 --engine-mode quali
```

#### Weather Strategy
```bash
# Compare tire choices in wet conditions
python main.py silverstone intermediate 40 light_rain
python main.py silverstone wet 40 heavy_rain
```

#### Fuel Saving Analysis
```bash
# Compare fuel conservation vs race pace
python main.py spa medium 70 dry --engine-mode conservation
python main.py spa medium 70 dry --engine-mode race
```

## Acknowledgments

- Circuit data based on official F1 circuit specifications
- Tire performance data inspired by Pirelli compound characteristics
- Physics calculations based on motorsport engineering principles
- Lap time validation against real F1 timing data

---

**Disclaimer**: This is a simulation tool for educational and entertainment purposes. Actual F1 performance depends on many additional factors not modeled here.

Enjoy calculating those lap times! 
