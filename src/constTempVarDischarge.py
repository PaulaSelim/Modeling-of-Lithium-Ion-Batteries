import os
import logging
from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt
import pybamm

# ===== Global Configuration =====
# Environment variables can override these default values.
NOMINAL_CELL_CAPACITY: float = float(os.getenv("NOMINAL_CELL_CAPACITY", "5.0"))
UPPER_VOLTAGE_CUTOFF: float = float(os.getenv("UPPER_VOLTAGE_CUTOFF", "4.2"))
LOWER_VOLTAGE_CUTOFF: float = float(os.getenv("LOWER_VOLTAGE_CUTOFF", "2.5"))
AMBIENT_TEMPERATURE: float = float(os.getenv("AMBIENT_TEMPERATURE", "333.15"))
SIMULATION_PERIOD: str = os.getenv("SIMULATION_PERIOD", "10 seconds")

# Experiment currents (in A)
CURRENT_AMPS = {"0.5C": 2.5, "1C": 5.0, "2C": 10.0}

# ===== Logging Configuration =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_experiment(current_amp: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Run a PyBaMM experiment for a given discharge current.
    ...
    """
    logger.info("Setting up experiment for discharge current: %s A", current_amp)
    
    experiment = pybamm.Experiment(
        [f"Discharge at {current_amp} A until {LOWER_VOLTAGE_CUTOFF} V"],
        period=SIMULATION_PERIOD,
    )

    model_options = {"thermal": "lumped"}
    model = pybamm.lithium_ion.DFN(options=model_options)

    params = pybamm.ParameterValues("Chen2020")
    params["Nominal cell capacity [A.h]"] = NOMINAL_CELL_CAPACITY
    params["Lower voltage cut-off [V]"] = LOWER_VOLTAGE_CUTOFF
    params["Upper voltage cut-off [V]"] = UPPER_VOLTAGE_CUTOFF
    params["Ambient temperature [K]"] = AMBIENT_TEMPERATURE

    simulation = pybamm.Simulation(model, parameter_values=params, experiment=experiment)
    solution = simulation.solve()
    logger.info("Simulation complete for discharge current: %s A", current_amp)

    discharge_step = solution.cycles[-1].steps[-1]

    time_data = discharge_step["Time [s]"].entries
    voltage_data = discharge_step["Voltage [V]"].entries
    capacity_data = discharge_step["Discharge capacity [A.h]"].entries
    temperature_data = discharge_step["Cell temperature [K]"].entries
    if temperature_data.ndim > 1:
        temperature_data = temperature_data[0]

    soc = 100 * (1 - (capacity_data / NOMINAL_CELL_CAPACITY))

    return time_data, voltage_data, capacity_data, temperature_data, soc


def run_all_experiments() -> dict:
    """Run experiments for predefined C-rates and collect the results.
    """
    results = {}
    for c_rate, current in CURRENT_AMPS.items():
        logger.info("Running experiment for %s (current: %s A)", c_rate, current)
        results[c_rate] = run_experiment(current)
    return results


def configure_subplot(
    ax: plt.Axes,
    xlabel: str,
    ylabel: str,
    title: str,
) -> None:
    """Configure a subplot with labels, title, and grid.
    """
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True)


def plot_experiment_results(results: dict) -> None:
    """Plot the results of the experiments on four subplots.
    """
    logger.info("Generating plots for experiment results.")
    fig, axs = plt.subplots(2, 2, figsize=(10, 7))

    # Plot 1: Voltage vs. Discharge Capacity
    ax_v_cap = axs[0, 0]
    for c_rate, data in results.items():
        _, voltage_data, capacity_data, _, _ = data
        ax_v_cap.plot(
            capacity_data,
            voltage_data,
            label=f"{c_rate} ({CURRENT_AMPS[c_rate]} A)",
        )
    configure_subplot(
        ax_v_cap,
        xlabel="Discharge Capacity (A·h)",
        ylabel="Voltage (V)",
        title="Voltage vs. Discharge Capacity",
    )
    ax_v_cap.legend()

    # Plot 2: State-of-Charge vs. Time
    ax_soc_time = axs[0, 1]
    for c_rate, data in results.items():
        time_data, _, _, _, soc = data
        ax_soc_time.plot(
            time_data,
            soc,
            label=f"{c_rate} ({CURRENT_AMPS[c_rate]} A)",
        )
    configure_subplot(
        ax_soc_time,
        xlabel="Time (s)",
        ylabel="State of Charge (%)",
        title="SoC vs. Time",
    )
    ax_soc_time.legend()

    # Plot 3: Cell Temperature vs. Time
    ax_temp_time = axs[1, 0]
    for c_rate, data in results.items():
        time_data, _, _, temperature_data, _ = data
        ax_temp_time.plot(
            time_data,
            temperature_data,
            label=f"{c_rate} ({CURRENT_AMPS[c_rate]} A)",
        )
    configure_subplot(
        ax_temp_time,
        xlabel="Time (s)",
        ylabel="Cell Temperature (K)",
        title="Cell Temperature vs. Time",
    )
    ax_temp_time.legend()

    # Plot 4: Discharge Capacity vs. Time
    ax_cap_time = axs[1, 1]
    for c_rate, data in results.items():
        time_data, _, capacity_data, _, _ = data
        ax_cap_time.plot(
            time_data,
            capacity_data,
            label=f"{c_rate} ({CURRENT_AMPS[c_rate]} A)",
        )
    configure_subplot(
        ax_cap_time,
        xlabel="Time (s)",
        ylabel="Discharge Capacity (A·h)",
        title="Discharge Capacity vs. Time",
    )
    ax_cap_time.legend()

    plt.tight_layout()
    plt.show()
    logger.info("Plot generation complete.")


def main() -> None:
    """Main function to execute the simulation experiments and plotting."""
    logger.info("Starting simulation experiments.")
    experiment_results = run_all_experiments()
    plot_experiment_results(experiment_results)
    logger.info("All operations completed successfully.")


if __name__ == "__main__":
    main()
