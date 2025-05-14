# Modeling of Lithium-Ion Batteries

This project provides tools for simulating and analyzing the behavior of lithium-ion batteries under various conditions. It includes multiple simulation scripts and a graphical user interface for easy experimentation.

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
  - [What is UV?](#what-is-uv)
  - [Installing UV](#installing-uv)
  - [Setting Up the Project](#setting-up-the-project)
- [Running the Simulations](#running-the-simulations)
  - [Using the GUI](#using-the-gui)
  - [Running Individual Simulations](#running-individual-simulations)
- [Simulation Types](#simulation-types)
- [File Structure](#file-structure)
- [Contributing](#contributing)

## Project Overview

This project allows you to simulate lithium-ion battery behaviors using the PyBaMM (Python Battery Mathematical Modelling) framework. It can model both individual cells and battery packs with various configurations. The simulations can analyze how batteries perform under different:
- Discharge rates
- Temperature conditions
- Cell configurations (series and parallel arrangements)

The results are visualized through graphs showing voltage, current, temperature, and state of charge over time.

## Features

- **Graphical User Interface**: Easy-to-use interface for configuring and running simulations
- **Multiple Simulation Types**:
  - Constant discharge rate with varying temperatures
  - Constant temperature with varying discharge rates
  - Battery pack simulations with parallel and series configurations
- **Visualization**: Automatic generation of plots showing key battery parameters
- **Configurable Parameters**: Easily adjust battery capacity, internal resistance, ambient temperature, etc.

## Installation

### What is UV?

UV is a Python package installer and resolver. It works like pip but is much faster and has better dependency resolution. We'll use UV to set up and run this project.

### Installing UV

If you've never coded before, don't worry! Here's how to install UV step by step:

#### For Windows:
1. Open Command Prompt (search for "cmd" in the start menu)
2. Copy and paste this command:
```
curl -sSf https://install.pydantic.dev | python3 -
```

#### For macOS or Linux:
1. Open Terminal
2. Copy and paste this command:
```
curl -sSf https://install.pydantic.dev | python3 -
```

After running the command, UV should be installed on your computer. You can verify it by typing:
```
uv --version
```

If it shows a version number, you've successfully installed UV!

### Setting Up the Project

Now that you have UV installed, follow these steps to set up the project:

1. **Download the Project**: 
   - If you received it as a ZIP file, extract it to a folder
   - If you're using Git: `git clone [repository-url]`

2. **Open Terminal/Command Prompt**:
   - Navigate to the project folder:
   ```
   cd path/to/Modeling-of-Lithium-Ion-Batteries
   ```

3. **Install Required Packages**:
   ```
   uv pip install -e .
   ```
   This command tells UV to install all the required packages listed in the project.

4. **Verify Installation**:
   ```
   uv pip list
   ```
   This will show all installed packages. Make sure you see packages like `pybamm`, `liionpack`, and `matplotlib`.

## Running the Simulations

### Using the GUI

The easiest way to run simulations is through the graphical user interface:

1. Open Terminal/Command Prompt
2. Navigate to the project folder
3. Run:
   ```
   uv run src/batteryPack_gui.py
   ```
4. The GUI will open, allowing you to:
   - Configure battery parameters
   - Set up test conditions
   - Run simulations
   - View and save results

### Running Individual Simulations

If you prefer to run specific simulations directly:

#### Battery Pack Simulation:
```
uv run src/4P1S.py
```
This simulates a battery pack with cells in parallel and series configurations.

#### Constant Discharge with Varying Temperature:
```
uv run src/constDischargeVarTemp.py
```
This simulates a battery cell at a fixed discharge rate across different temperatures.

#### Constant Temperature with Varying Discharge Rates:
```
uv run src/constTempVarDischarge.py
```
This simulates a battery cell at a fixed temperature across different discharge rates.

## Simulation Types

### Battery Pack Simulation (4P1S.py)
Simulates a battery pack with configurable parallel and series cell arrangements. You can control:
- Number of cells in parallel and series
- Busbar and connection resistances
- Ambient temperature
- Initial state of charge
- Cutoff voltages

### Constant Discharge, Variable Temperature (constDischargeVarTemp.py)
Tests how a battery cell performs at a fixed discharge rate but varying ambient temperatures:
- Set fixed discharge current
- Run simulation at multiple temperatures
- Compare voltage curves and discharge capacity

### Constant Temperature, Variable Discharge (constTempVarDischarge.py)
Tests how a battery cell performs at different discharge rates at a constant temperature:
- Set fixed ambient temperature
- Run simulation at multiple discharge rates (0.5C, 1C, 2C)
- Compare voltage curves and discharge times

## File Structure

- `src/`: Contains all the Python source code
  - `batteryPack_gui.py`: The graphical user interface
  - `4P1S.py`: Battery pack simulation
  - `constDischargeVarTemp.py`: Constant discharge, variable temperature simulation
  - `constTempVarDischarge.py`: Constant temperature, variable discharge simulation
- `pyproject.toml`: Project dependencies and configuration
- `README.md`: This documentation file

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Add your changes
4. Submit a pull request