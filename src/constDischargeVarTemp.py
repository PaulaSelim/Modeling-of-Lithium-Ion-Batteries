import os
import logging
from typing import Dict, List, Tuple, Optional
import random

import numpy as np
import pybamm
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BatteryDischargeSimulation")

# Load environment variables if .env file exists
load_dotenv()

# Global configuration variables
NOMINAL_CAPACITY_AH = float(os.getenv("NOMINAL_CAPACITY_AH", "5.0"))
LOWER_VOLTAGE_CUTOFF_V = float(os.getenv("LOWER_VOLTAGE_CUTOFF_V", "3.0"))
UPPER_VOLTAGE_CUTOFF_V = float(os.getenv("UPPER_VOLTAGE_CUTOFF_V", "4.2"))
EXPERIMENT_PERIOD_S = os.getenv("EXPERIMENT_PERIOD_S", "10 seconds")
DEFAULT_1C_CURRENT_A = float(os.getenv("DEFAULT_1C_CURRENT_A", "5.0"))


def celsius_to_kelvin(temp_celsius: float) -> float:
    """
    Convert temperature from Celsius to Kelvin.
    
    Args:
        temp_celsius: Temperature in Celsius
        
    Returns:
        float: Temperature in Kelvin
    """
    return temp_celsius + 273.15


def run_discharge_experiment(
    discharge_current_a: float, 
    ambient_temp_k: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Creates and runs a battery discharge experiment at specified current and temperature.
    
    Args:
        discharge_current_a: Discharge current in amperes
        ambient_temp_k: Ambient temperature in Kelvin
        
    Returns:
        Tuple containing:
            time: Time points in seconds
            voltage: Cell voltage in volts
            capacity: Discharge capacity in ampere-hours
            temperature: Cell temperature in Kelvin
            soc: State of charge as percentage
    """
    logger.info(f"Setting up discharge experiment at {discharge_current_a}A and {ambient_temp_k}K")
    
    # Define the experiment
    experiment = pybamm.Experiment(
        [f"Discharge at {discharge_current_a} A until {LOWER_VOLTAGE_CUTOFF_V} V"],
        period=EXPERIMENT_PERIOD_S,
    )

    # Configure thermal model
    options = {"thermal": "lumped"}
    model = pybamm.lithium_ion.DFN(options=options)

    # Set up parameters
    param = pybamm.ParameterValues("Chen2020")
    param["Nominal cell capacity [A.h]"] = NOMINAL_CAPACITY_AH
    param["Lower voltage cut-off [V]"] = LOWER_VOLTAGE_CUTOFF_V
    param["Upper voltage cut-off [V]"] = UPPER_VOLTAGE_CUTOFF_V
    param["Ambient temperature [K]"] = ambient_temp_k

    # Run simulation
    logger.info("Running simulation...")
    sim = pybamm.Simulation(model, parameter_values=param, experiment=experiment)
    solution = sim.solve()
    logger.info("Simulation complete")

    # Extract data from solution
    discharge_step = solution.cycles[-1].steps[-1]
    time = discharge_step["Time [s]"].entries
    voltage = discharge_step["Voltage [V]"].entries
    capacity = discharge_step["Discharge capacity [A.h]"].entries
    temperature = discharge_step["Cell temperature [K]"].entries

    # Handle multi-dimensional temperature data
    if temperature.ndim > 1:
        temperature = temperature[0]

    # Calculate State of Charge
    soc = 100 * (1 - (capacity / NOMINAL_CAPACITY_AH))

    return time, voltage, capacity, temperature, soc


def collect_temperature_results(
    temps_celsius: List[float], 
    discharge_current_a: Optional[float] = None
) -> Dict[float, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """
    Collect discharge results for different temperatures.
    
    Args:
        temps_celsius: List of temperatures in Celsius to simulate
        discharge_current_a: Discharge current in amperes, defaults to 1C rate
        
    Returns:
        Dictionary mapping temperatures (°C) to experiment results
    """
    if discharge_current_a is None:
        discharge_current_a = DEFAULT_1C_CURRENT_A
    
    logger.info(f"Starting tests at temperatures: {temps_celsius}°C with {discharge_current_a}A discharge")
    
    # Convert temperatures to Kelvin
    temps_kelvin = [celsius_to_kelvin(t) for t in temps_celsius]
    
    # Run experiments for each temperature
    results = {}
    for temp_c, temp_k in zip(temps_celsius, temps_kelvin):
        logger.info(f"Running experiment for {temp_c}°C")
        results[temp_c] = run_discharge_experiment(discharge_current_a, temp_k)
        
    return results


def create_discharge_plots(
    results: Dict[float, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]
) -> None:
    """
    Create plots of discharge characteristics at different temperatures.
    
    Args:
        results: Dictionary mapping temperatures to discharge results
    """
    temps_celsius = list(results.keys())
    
    logger.info("Creating discharge plots")
    
    fig, axs = plt.subplots(2, 2, figsize=(10, 7))
        
    # Plot 1: Voltage vs. Discharge Capacity
    for i, temp_c in enumerate(temps_celsius):
        time, voltage, capacity, temperature, soc = results[temp_c]
        axs[0, 0].plot(
            capacity,
            voltage,
            linestyle="-",
            linewidth=2,
            label=f"{temp_c}°C",
        )
    axs[0, 0].set_xlabel("Discharge Capacity (A·h)")
    axs[0, 0].set_ylabel("Voltage (V)")
    axs[0, 0].set_title("Voltage vs. Discharge Capacity")
    axs[0, 0].grid(True)
    axs[0, 0].legend()

    # Plot 2: State-of-Charge vs. Time
    for i, temp_c in enumerate(temps_celsius):
        time, voltage, capacity, temperature, soc = results[temp_c]
        axs[0, 1].plot(
            time, soc, 
            linestyle="-", 
            linewidth=2, 
            label=f"{temp_c}°C"
        )
    axs[0, 1].set_xlabel("Time (s)")
    axs[0, 1].set_ylabel("State of Charge (%)")
    axs[0, 1].set_title("SoC vs. Time")
    axs[0, 1].grid(True)
    axs[0, 1].legend()

    # Plot 3: Cell Temperature vs. Time
    for i, temp_c in enumerate(temps_celsius):
        time, voltage, capacity, temperature, soc = results[temp_c]
        axs[1, 0].plot(
            time,
            temperature,
            linestyle="-",
            linewidth=2,
            label=f"{temp_c}°C",
        )
    axs[1, 0].set_xlabel("Time (s)")
    axs[1, 0].set_ylabel("Cell Temperature (K)")
    axs[1, 0].set_title("Cell Temperature vs. Time")
    axs[1, 0].grid(True)
    axs[1, 0].legend()

    # Plot 4: Discharge Capacity vs. Time
    for i, temp_c in enumerate(temps_celsius):
        time, voltage, capacity, temperature, soc = results[temp_c]
        axs[1, 1].plot(
            time, 
            capacity, 
            linestyle="-", 
            linewidth=2, 
            label=f"{temp_c}°C"
        )
    axs[1, 1].set_xlabel("Time (s)")
    axs[1, 1].set_ylabel("Discharge Capacity (A·h)")
    axs[1, 1].set_title("Discharge Capacity vs. Time")
    axs[1, 1].grid(True)
    axs[1, 1].legend()

    plt.tight_layout()
    logger.info("Displaying plots")
    plt.show()


def main() -> None:
    """
    Main function to run battery discharge simulations at different temperatures.
    """
    # Define test temperatures
    test_temperatures_celsius = [-20, 20, 40, 60]
    
    # Get results for each temperature
    temperature_results = collect_temperature_results(
        test_temperatures_celsius, 
        discharge_current_a=DEFAULT_1C_CURRENT_A
    )
    
    # Create and display plots
    create_discharge_plots(temperature_results)


if __name__ == "__main__":
    main()
