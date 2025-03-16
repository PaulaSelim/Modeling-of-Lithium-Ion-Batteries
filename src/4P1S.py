import os
import logging
import dotenv
from typing import Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import liionpack as lp
import pybamm

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("battery_pack_simulation")

# Default configuration parameters that can be overridden by environment variables
AMBIENT_TEMP = float(os.environ.get("AMBIENT_TEMP", 293.15))  # K (20°C)
NUM_PARALLEL = int(os.environ.get("NUM_PARALLEL", 4))
NUM_SERIES = int(os.environ.get("NUM_SERIES", 1))
BUSBAR_RESISTANCE = float(os.environ.get("BUSBAR_RESISTANCE", 1e-3))  # Ohm
CONNECTION_RESISTANCE = float(os.environ.get("CONNECTION_RESISTANCE", 1e-2))  # Ohm
INTERNAL_RESISTANCE = float(os.environ.get("INTERNAL_RESISTANCE", 5e-2))  # Ohm
INITIAL_VOLTAGE = float(os.environ.get("INITIAL_VOLTAGE", 4.0))  # V
DISCHARGE_CURRENT = float(os.environ.get("DISCHARGE_CURRENT", 5.0))  # A
CUT_OFF_VOLTAGE = float(os.environ.get("CUT_OFF_VOLTAGE", 3.3))  # V
INITIAL_SOC = float(os.environ.get("INITIAL_SOC", 1))
NOMINAL_CAPACITY = float(os.environ.get("NOMINAL_CAPACITY", 5.0))  # Ah
EXPERIMENT_PERIOD = os.environ.get("EXPERIMENT_PERIOD", "100 second")
EXPERIMENT_TIME = float(os.environ.get("EXPERIMENT_TIME", 15000))  # seconds
# Circuit diagram settings
DRAW_CIRCUIT = os.environ.get("DRAW_CIRCUIT", "False").lower() == "true"
CIRCUIT_DPI = int(os.environ.get("CIRCUIT_DPI", 1200))
CIRCUIT_CPT_SIZE = float(os.environ.get("CIRCUIT_CPT_SIZE", 1.0))
CIRCUIT_NODE_SPACING = float(os.environ.get("CIRCUIT_NODE_SPACING", 2.5))


def configure_simulation() -> Dict[str, Any]:
    """Configure simulation parameters, circuit, experiment, inputs, and solver.
    
    This function sets up all the necessary parameters for the battery pack simulation
    including parameter values, circuit netlist, experiment definition, and
    temperature inputs.
    
    Returns:
        Dict[str, Any]: A dictionary containing configuration parameters:
            - parameter_values: PyBaMM parameter values
            - netlist: Circuit configuration for the battery pack
            - experiment: PyBaMM experiment definition 
            - initial_soc: Initial state of charge
            - inputs: Additional inputs like temperature
            - nproc: Number of processors for parallel execution
    """
    logger.info("Configuring simulation parameters")
    
    # Set up battery parameters using Chen2020
    parameter_values = pybamm.ParameterValues("Chen2020")
    parameter_values.update({"Ambient temperature [K]": AMBIENT_TEMP})
    
    # Create a pack with specified resistances and initial guesses
    netlist = lp.setup_circuit(
        Np=NUM_PARALLEL,
        Ns=NUM_SERIES,
        Rb=BUSBAR_RESISTANCE,
        Rc=CONNECTION_RESISTANCE,
        Ri=INTERNAL_RESISTANCE,
        V=INITIAL_VOLTAGE,
        I=DISCHARGE_CURRENT
    )
    
    # Define experiment
    experiment = pybamm.Experiment(
        [f"Discharge at {DISCHARGE_CURRENT} A for {EXPERIMENT_TIME} s or until {CUT_OFF_VOLTAGE} V"],
        period=EXPERIMENT_PERIOD
    )
    
    # Set input temperatures for each cell with 2°C increments starting from ambient
    temps = AMBIENT_TEMP + 2 * np.arange(NUM_PARALLEL)
    inputs = {"Input temperature [K]": temps}
    
    logger.info(f"Simulation configured: {NUM_PARALLEL}p{NUM_SERIES}s pack at {AMBIENT_TEMP}K")
    
    return {
        "parameter_values": parameter_values,
        "netlist": netlist,
        "experiment": experiment,
        "initial_soc": INITIAL_SOC,
        "inputs": inputs,
        "nproc": os.cpu_count()
    }


def run_simulation(config: Dict[str, Any]) -> Dict[str, np.ndarray]:
    """Run the liionpack simulation using the given configuration.
    
    Args:
        config: Dictionary containing simulation configuration parameters.
    
    Returns:
        Dict[str, np.ndarray]: Simulation output data.
    """
    logger.info("Starting simulation")
    
    try:
        output = lp.solve(
            netlist=config["netlist"],
            sim_func=lp.thermal_external,
            inputs=config["inputs"],
            parameter_values=config["parameter_values"],
            experiment=config["experiment"],
            output_variables=[
                "Volume-averaged cell temperature [K]",
                "Volume-averaged total heating [W.m-3]"
            ],
            initial_soc=config["initial_soc"],
            nproc=config["nproc"],
        )
        logger.info("Simulation completed successfully")
        return output
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise


def process_simulation_output(output: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Process simulation output data.
    
    Computes averages, cumulative capacity, and state-of-charge from raw simulation data.
    Truncates all data at the point where voltage reaches the cutoff value.
    
    Args:
        output: Raw simulation output from liionpack.
    
    Returns:
        Dict[str, np.ndarray]: Processed data including time, voltages, currents,
            temperatures, heating, capacities and state of charge.
    """
    logger.info("Processing simulation results")
    
    time = output["Time [s]"]
    current = output["Cell current [A]"]
    voltage = output["Terminal voltage [V]"]
    temperature = output["Volume-averaged cell temperature [K]"]
    heating = output["Volume-averaged total heating [W.m-3]"]

    # Compute averages along the cell axis
    current_avg = np.mean(current, axis=1)
    voltage_avg = np.mean(voltage, axis=1)
    temperature_avg = np.mean(temperature, axis=1)
    heating_avg = np.mean(heating, axis=1)

    # Compute cumulative discharge capacity (Ah)
    delta_t = time[1] - time[0] 
    capacity_Ah = np.cumsum(current_avg * delta_t) / 3600

    # Calculate state-of-charge (SoC)
    SoC = INITIAL_SOC - capacity_Ah / NOMINAL_CAPACITY
    
    # Find when voltage hits cutoff
    cutoff_indices = np.where(voltage_avg <= CUT_OFF_VOLTAGE)[0]
    if len(cutoff_indices) > 0:
        cutoff_idx = cutoff_indices[0]
        cutoff_time = time[cutoff_idx]
        logger.info(f"Cutoff voltage ({CUT_OFF_VOLTAGE}V) reached at {cutoff_time:.1f}s")
        
        # Truncate all data arrays
        time = time[:cutoff_idx+1]
        current = current[:cutoff_idx+1]
        voltage = voltage[:cutoff_idx+1]
        temperature = temperature[:cutoff_idx+1]
        heating = heating[:cutoff_idx+1]
        current_avg = current_avg[:cutoff_idx+1]
        voltage_avg = voltage_avg[:cutoff_idx+1]
        temperature_avg = temperature_avg[:cutoff_idx+1]
        heating_avg = heating_avg[:cutoff_idx+1]
        capacity_Ah = capacity_Ah[:cutoff_idx+1]
        SoC = SoC[:cutoff_idx+1]
    
    logger.info(f"Processing complete - simulation data truncated at {time[-1]:.1f}s")

    return {
        "time": time,
        "current": current,
        "voltage": voltage,
        "temperature": temperature,
        "heating": heating,
        "current_avg": current_avg,
        "voltage_avg": voltage_avg,
        "temperature_avg": temperature_avg,
        "heating_avg": heating_avg,
        "capacity_Ah": capacity_Ah,
        "SoC": SoC
    }


def plot_simulation_results(data: Dict[str, np.ndarray]) -> None:
    """Plot simulation results.
    
    Creates plots for voltage, SoC, temperature, discharge capacity, and heating results.
    
    Args:
        data: Dictionary containing processed simulation data.
    """
    logger.info("Generating plots")
    
    fig, axs = plt.subplots(2, 3, figsize=(10, 7))
    axs = axs.flatten()

    # Plot cell voltage for each cell and the average voltage
    for i in range(data["voltage"].shape[1]):
        axs[0].plot(data["time"], data["voltage"][:, i], label=f"Cell {i + 1}")
    axs[0].plot(data["time"], data["voltage_avg"], "k--", label="Average")
    axs[0].set_xlabel("Time (s)")
    axs[0].set_ylabel("Voltage (V)")
    axs[0].set_title("Cell Voltage Distribution")
    axs[0].legend()
    axs[0].grid(True)

    # Plot state-of-charge vs. time
    axs[1].plot(data["time"], data["SoC"], "g-")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("SoC")
    axs[1].set_title("State of Charge vs Time")
    axs[1].grid(True)

    # Plot cell temperature for each cell and average
    for i in range(data["temperature"].shape[1]):
        axs[2].plot(data["time"], data["temperature"][:, i] - 273.15, label=f"Cell {i + 1}")
    axs[2].plot(data["time"], data["temperature_avg"] - 273.15, "k--", label="Average")
    axs[2].set_xlabel("Time (s)")
    axs[2].set_ylabel("Temperature (°C)")
    axs[2].set_title("Cell Temperature vs Time")
    axs[2].legend()
    axs[2].grid(True)

    # Plot discharge capacity vs. time
    axs[3].plot(data["time"], data["capacity_Ah"]*NUM_PARALLEL, "m-")
    axs[3].set_xlabel("Time (s)")
    axs[3].set_ylabel("Discharge Capacity (Ah)")
    axs[3].set_title("Discharge Capacity vs Time")
    axs[3].grid(True)

    # Plot total heating for each cell and average
    for i in range(data["heating"].shape[1]):
        axs[4].plot(data["time"], data["heating"][:, i], label=f"Cell {i + 1}")
    axs[4].plot(data["time"], data["heating_avg"], "k--", label="Average")
    axs[4].set_xlabel("Time (s)")
    axs[4].set_ylabel("Heating (W/m³)")
    axs[4].set_title("Total Heating vs Time")
    axs[4].legend()
    axs[4].grid(True)

    # Remove unused subplot and adjust layout
    fig.delaxes(axs[5])
    plt.tight_layout()
    
    logger.info("Displaying plots")
    plt.show()


def main() -> None:
    """Main function to run the battery pack simulation."""
    logger.info("Starting battery pack simulation")
    
    try:
        config = configure_simulation()
        output = run_simulation(config)
        
        logger.info("Drawing circuit diagram")

        if DRAW_CIRCUIT:
            lp.draw_circuit(config["netlist"], cpt_size=CIRCUIT_CPT_SIZE, dpi=CIRCUIT_DPI, node_spacing=CIRCUIT_NODE_SPACING)
        
        processed_data = process_simulation_output(output)
        plot_simulation_results(processed_data)

        # Print citations for the tools used in the simulation
        logger.info("Printing citations for the tools used")
        pybamm.print_citations()
        
        logger.info("Simulation workflow completed successfully")
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
