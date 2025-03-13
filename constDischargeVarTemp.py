import pybamm
import matplotlib.pyplot as plt
import numpy as np

def run_experiment(current_amp, ambient_temp_K):
    """
    Creates and runs a PyBaMM experiment that:
    1) Charges the cell at 1 A until 4.2 V,
    2) Holds at 4.2 V until 50 mA,
    3) Discharges at the specified current_amp (A) until 3.0 V.
    
    Returns time, voltage, capacity, temperature, and SoC for the discharge step.
    """
    # Define the experiment (only discharge step for simplicity)
    experiment = pybamm.Experiment([
        f"Discharge at {current_amp} A until 3.0 V",
    ], period="10 seconds")

    # Use DFN with a lumped thermal model
    options = {"thermal": "lumped"}
    model = pybamm.lithium_ion.DFN(options=options)

    # Choose a more realistic parameter set, e.g., Chen2020
    param = pybamm.ParameterValues("Chen2020")
    # Set nominal capacity, voltage cutoffs, and ambient temperature
    param["Nominal cell capacity [A.h]"] = 5
    param["Lower voltage cut-off [V]"] = 3.0
    param["Upper voltage cut-off [V]"] = 4.2
    param["Ambient temperature [K]"] = ambient_temp_K

    # Create and run the simulation
    sim = pybamm.Simulation(model, parameter_values=param, experiment=experiment)
    solution = sim.solve()

    # Extract data from the final discharge step
    discharge_step = solution.cycles[-1].steps[-1]
    time = discharge_step["Time [s]"].entries
    voltage = discharge_step["Voltage [V]"].entries
    capacity = discharge_step["Discharge capacity [A.h]"].entries
    temperature = discharge_step["Cell temperature [K]"].entries

    # If temperature is 2D, take the first row (or average over spatial points)
    if temperature.ndim > 1:
        temperature = temperature[0]

    # Compute SoC (%) assuming 100% at start of discharge
    nom_cap = param["Nominal cell capacity [A.h]"]
    SoC = 100 * (1 - (capacity / nom_cap))
    
    return time, voltage, capacity, temperature, SoC

# Define ambient temperatures in °C and convert to Kelvin
temps_C = [-20, 20, 40, 60]
temps_K = [t + 273.15 for t in temps_C]

# We'll use 1C discharge, i.e. 5.0 A for a 5 A·h cell
current_amp = 5.0

# Prepare dictionaries to hold results for each temperature
results = {}
for T, T_K in zip(temps_C, temps_K):
    results[T] = run_experiment(current_amp, T_K)

# Define standardized colors for each ambient temperature
color_map = { -20: 'black', 20: 'blue', 40: 'green', 60: 'red' }

# ----- Plotting the results -----
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# 1. Voltage vs. Discharge Capacity
for T in temps_C:
    time, voltage, capacity, temperature, SoC = results[T]
    axs[0, 0].plot(capacity, voltage, color=color_map[T], linestyle='-', linewidth=2, 
                     label=f'{T}°C')
axs[0, 0].set_xlabel("Discharge Capacity (A·h)")
axs[0, 0].set_ylabel("Voltage (V)")
axs[0, 0].set_title("Voltage vs. Discharge Capacity")
axs[0, 0].grid(True)
axs[0, 0].legend()

# 2. State-of-Charge vs. Time
for T in temps_C:
    time, voltage, capacity, temperature, SoC = results[T]
    axs[0, 1].plot(time, SoC, color=color_map[T], linestyle='-', linewidth=2, label=f'{T}°C')
axs[0, 1].set_xlabel("Time (s)")
axs[0, 1].set_ylabel("State of Charge (%)")
axs[0, 1].set_title("SoC vs. Time")
axs[0, 1].grid(True)
axs[0, 1].legend()

# 3. Cell Temperature vs. Time
for T in temps_C:
    time, voltage, capacity, temperature, SoC = results[T]
    axs[1, 0].plot(time, temperature, color=color_map[T], linestyle='-', linewidth=2, label=f'{T}°C')
axs[1, 0].set_xlabel("Time (s)")
axs[1, 0].set_ylabel("Cell Temperature (K)")
axs[1, 0].set_title("Cell Temperature vs. Time")
axs[1, 0].grid(True)
axs[1, 0].legend()

# 4. Discharge Capacity vs. Time
for T in temps_C:
    time, voltage, capacity, temperature, SoC = results[T]
    axs[1, 1].plot(time, capacity, color=color_map[T], linestyle='-', linewidth=2, label=f'{T}°C')
axs[1, 1].set_xlabel("Time (s)")
axs[1, 1].set_ylabel("Discharge Capacity (A·h)")
axs[1, 1].set_title("Discharge Capacity vs. Time")
axs[1, 1].grid(True)
axs[1, 1].legend()

plt.tight_layout()
plt.show()
