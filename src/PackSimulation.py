import os
import logging
import dotenv
from typing import Dict, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
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
AMBIENT_TEMP = float(os.environ.get("AMBIENT_TEMP", 293.15+40))  # K (20°C)
NUM_PARALLEL = int(os.environ.get("NUM_PARALLEL", 3))
NUM_SERIES = int(os.environ.get("NUM_SERIES", 4))
BUSBAR_RESISTANCE = float(os.environ.get("BUSBAR_RESISTANCE", 1e-3))  # Ohm
CONNECTION_RESISTANCE = float(os.environ.get("CONNECTION_RESISTANCE", 1e-2))  # Ohm
INTERNAL_RESISTANCE = float(os.environ.get("INTERNAL_RESISTANCE", 5e-2))  # Ohm
INITIAL_VOLTAGE = float(os.environ.get("INITIAL_VOLTAGE", 4.0))  # V
CUT_OFF_VOLTAGE = float(os.environ.get("CUT_OFF_VOLTAGE", 2.5))  # V
INITIAL_SOC = float(os.environ.get("INITIAL_SOC", 1))
NOMINAL_CAPACITY = float(os.environ.get("NOMINAL_CAPACITY", 5.0))  # Ah
EXPERIMENT_PERIOD = os.environ.get("EXPERIMENT_PERIOD", "10 second")
EXPERIMENT_TIME = float(os.environ.get("EXPERIMENT_TIME", 15000))  # seconds

# Define test currents with names in format: "name:current_value"
# Can be overridden by environment variable (comma-separated)
DEFAULT_CURRENT_TESTS = "0.5C:7.5,1C:15.0,2C:30.0"  # Format: "name:current,name:current,..."
CURRENT_TESTS_STR = os.environ.get("CURRENT_TESTS", DEFAULT_CURRENT_TESTS)
CURRENT_TESTS = {}
for test in CURRENT_TESTS_STR.split(','):
    if ':' in test:
        name, current = test.split(':', 1)
        CURRENT_TESTS[name.strip()] = float(current.strip())
    else:
        # Fallback for backward compatibility
        CURRENT_TESTS[f"{float(test.strip())}A"] = float(test.strip())

# Circuit diagram settings
DRAW_CIRCUIT = os.environ.get("DRAW_CIRCUIT", "false").lower() == "true"
CIRCUIT_DPI = int(os.environ.get("CIRCUIT_DPI", 1200))
CIRCUIT_CPT_SIZE = float(os.environ.get("CIRCUIT_CPT_SIZE", 1.0))
CIRCUIT_NODE_SPACING = float(os.environ.get("CIRCUIT_NODE_SPACING", 2.5))


def configure_simulation(discharge_current: float) -> Dict[str, Any]:
    """Configure simulation parameters, circuit, experiment, inputs, and solver.
    
    This function sets up all the necessary parameters for the battery pack simulation
    including parameter values, circuit netlist, experiment definition, and
    temperature inputs.
    
    Args:
        discharge_current: The discharge current to use for this simulation.
        
    Returns:
        Dict[str, Any]: A dictionary containing configuration parameters:
            - parameter_values: PyBaMM parameter values
            - netlist: Circuit configuration for the battery pack
            - experiment: PyBaMM experiment definition 
            - initial_soc: Initial state of charge
            - inputs: Additional inputs like temperature
            - nproc: Number of processors for parallel execution
    """
    logger.info(f"Configuring simulation parameters for {discharge_current}A discharge")
    
    # Set up battery parameters using Chen2020
    parameter_values = pybamm.ParameterValues("Chen2020")
    parameter_values.update({"Ambient temperature [K]": AMBIENT_TEMP})
    parameter_values.update({"Initial temperature [K]": 293.15})
    
    
    # Create a pack with specified resistances and initial guesses
    netlist = lp.setup_circuit(
        Np=NUM_PARALLEL,
        Ns=NUM_SERIES,
        Rb=BUSBAR_RESISTANCE,
        Rc=CONNECTION_RESISTANCE,
        Ri=INTERNAL_RESISTANCE,
        V=INITIAL_VOLTAGE,
        I=discharge_current
    )
    
    # Define experiment
    experiment = pybamm.Experiment(
        [f"Discharge at {discharge_current} A for {EXPERIMENT_TIME} s or until {CUT_OFF_VOLTAGE} V"],
        period=EXPERIMENT_PERIOD
    )
    
    # Set input temperatures for each cell with 2°C increments starting from ambient
    htc = 10.0  # W/m²K (example value; adjust based on your system)
    inputs = {
        "Total heat transfer coefficient [W.m-2.K-1]": htc * np.ones(NUM_PARALLEL * NUM_SERIES)
    }
    
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
            sim_func=lp.thermal_simulation,
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
    Truncates all data at the point where voltage reaches the cutoff value or SOC reaches 0.
    
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
    
    # Find the cutoff index based on both voltage and SOC conditions
    cutoff_idx = None
    
    # Check for voltage cutoff
    voltage_cutoff_indices = np.where(voltage_avg <= CUT_OFF_VOLTAGE)[0]
    if len(voltage_cutoff_indices) > 0:
        voltage_cutoff_idx = voltage_cutoff_indices[0]
        cutoff_idx = voltage_cutoff_idx
        cutoff_reason = f"Voltage cutoff ({CUT_OFF_VOLTAGE}V) reached at {time[cutoff_idx]:.1f}s"
        
    # Check for SOC cutoff (SOC = 0)
    soc_cutoff_indices = np.where(SoC <= 0)[0]
    if len(soc_cutoff_indices) > 0:
        soc_cutoff_idx = soc_cutoff_indices[0]
        
        # If we have both cutoffs, take the earlier one
        if cutoff_idx is None or soc_cutoff_idx < cutoff_idx:
            cutoff_idx = soc_cutoff_idx
            cutoff_reason = f"SOC reached 0 at {time[cutoff_idx]:.1f}s"
    
    # Truncate all data arrays if a cutoff was reached
    if cutoff_idx is not None:
        logger.info(cutoff_reason)
        
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


def plot_simulation_results(data_dict: Dict[str, Dict[str, np.ndarray]]) -> None:
    """Plot simulation results for multiple current tests.
    
    Creates plots comparing multiple current tests for overall pack voltage, 
    SoC, temperature, and discharge capacity.
    
    Args:
        data_dict: Dictionary with test names as keys and processed simulation data as values.
    """
    logger.info("Generating plots for multiple current tests")
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    axs = axs.flatten()
    
    # Get a color map based on the number of tests
    colors = plt.cm.viridis(np.linspace(0, 1, len(data_dict)))
    
    # Plot pack voltage vs discharge capacity
    for i, (test_name, data) in enumerate(data_dict.items()):
        total_capacity = data["capacity_Ah"] * NUM_PARALLEL
        axs[0].plot(total_capacity, data["voltage_avg"] * NUM_SERIES, 
                   color=colors[i], label=test_name, linewidth=2)
    axs[0].set_xlabel("Discharge Capacity (Ah)")
    axs[0].set_ylabel("Voltage (V)")
    axs[0].set_title("Pack Voltage vs Discharge Capacity")
    axs[0].legend()
    axs[0].grid(True)

    # Plot state-of-charge vs. time as percentage
    for i, (test_name, data) in enumerate(data_dict.items()):
        axs[1].plot(data["time"], data["SoC"] * 100, 
                   color=colors[i], label=test_name, linewidth=2)
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("SoC (%)")
    axs[1].set_title("Pack State of Charge vs Time")
    axs[1].legend()
    axs[1].grid(True)

    # Plot average pack temperature
    for i, (test_name, data) in enumerate(data_dict.items()):
        axs[2].plot(data["time"], data["temperature_avg"] - 273.15, 
                   color=colors[i], label=test_name, linewidth=2)
    axs[2].set_xlabel("Time (s)")
    axs[2].set_ylabel("Temperature (°C)")
    axs[2].set_title("Pack Average Temperature vs Time")
    axs[2].legend()
    axs[2].grid(True)

    # Plot total pack discharge capacity vs. time
    for i, (test_name, data) in enumerate(data_dict.items()):
        axs[3].plot(data["time"], data["capacity_Ah"] * NUM_PARALLEL, 
                   color=colors[i], label=test_name, linewidth=2)
    axs[3].set_xlabel("Time (s)")
    axs[3].set_ylabel("Discharge Capacity (Ah)")
    axs[3].set_title("Pack Discharge Capacity vs Time")
    axs[3].legend()
    axs[3].grid(True)
    
    plt.tight_layout()
    
    logger.info("Displaying plots")
    fig = plt.gcf()        # current figure
    if matplotlib.get_backend().lower().endswith('agg'):
        fig.savefig("plot.png")   # no GUI: save figure to PNG file
    else:
        plt.show()               # GUI available: display the window



def main() -> None:
    """Main function to run battery pack simulations for multiple current tests."""
    logger.info(f"Starting battery pack simulations for multiple currents: {list(CURRENT_TESTS.keys())}")
    
    try:
        # Store simulation results for each current test
        all_results = {}
        first_netlist = None
        
        # Run simulations for each current test
        for test_name, current in CURRENT_TESTS.items():
            logger.info(f"Running simulation for {test_name} at {current}A")
            
            # Configure and run simulation for this current
            config = configure_simulation(discharge_current=current)
            
            # Save first netlist for circuit diagram
            if first_netlist is None:
                first_netlist = config["netlist"]
                
            # Run simulation and process results
            output = run_simulation(config)
            processed_data = process_simulation_output(output)
            
            # Store processed data with test name
            all_results[test_name] = processed_data
            
            logger.info(f"Completed simulation for {test_name}")
        
        # Draw circuit diagram using first configuration
        if DRAW_CIRCUIT and first_netlist:
            logger.info("Drawing circuit diagram")
            lp.draw_circuit(first_netlist, cpt_size=CIRCUIT_CPT_SIZE, 
                           dpi=CIRCUIT_DPI, node_spacing=CIRCUIT_NODE_SPACING)
        
        # Plot results from all current tests
        plot_simulation_results(all_results)

        # Print citations for the tools used in the simulation
        logger.info("Printing citations for the tools used")
        pybamm.print_citations()
        
        logger.info("All simulation workflows completed successfully")
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
