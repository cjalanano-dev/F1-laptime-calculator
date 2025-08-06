"""
F1 Lap Time Calculator - Modules Package

This package contains the core modules for the F1 Lap Time Calculator:
- circuit: Circuit modeling and sector analysis
- car: Car setup and performance calculations  
- lap_simulator: Main simulation engine
- utils: Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "F1 Lap Time Calculator Team"

from .circuit import Circuit
from .car import Car
from .lap_simulator import LapSimulator
from . import utils

__all__ = ['Circuit', 'Car', 'LapSimulator', 'utils']
