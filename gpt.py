import pybamm
import matplotlib.pyplot as plt
import numpy as np

def run_experiment(current_amp):
    """
    Creates and runs a PyBaMM experiment that:
    1) Charges the cell at 1 A until 4.2 V,
    2) Holds at 4.2 V until 50 mA,
    3) Discharges at the specified current_amp (A) until 3.0 V.
    
    Returns time, voltage, capacity, temperature, and SoC for the discharge step.
    """
    # Define the experiment
    experiment = pybamm.Experiment([
        f"Discharge at {current_amp} A until 3.0 V",
    ], period="10 seconds")

    # Use SPMe with a lumped thermal model
    options = {"thermal": "lumped"}
    model = pybamm.lithium_ion.DFN(options=options)

    # Choose a more realistic parameter set, e.g., Chen2020
    param = pybamm.ParameterValues("Chen2020")
    # Set nominal capacity, cutoffs, and ambient temperature
    param["Nominal cell capacity [A.h]"] = 5
    param["Lower voltage cut-off [V]"] = 3.0
    param["Upper voltage cut-off [V]"] = 4.2
    param["Ambient temperature [K]"] = 293.15  # 20°C

    # Create and run the simulation
    sim = pybamm.Simulation(model, parameter_values=param, experiment=experiment)
    solution = sim.solve()

    # The experiment has multiple steps (charge, hold, discharge).
    # We extract data from the *final discharge step*.
    discharge_step = solution.cycles[-1].steps[-1]
    
    time = discharge_step["Time [s]"].entries
    voltage = discharge_step["Voltage [V]"].entries
    capacity = discharge_step["Discharge capacity [A.h]"].entries
    temperature = discharge_step["Cell temperature [K]"].entries

    # If temperature is a 2D array, convert to 1D (e.g., take the first row)
    if temperature.ndim > 1:
        temperature = temperature[0]

    # Compute SoC (%), assuming 100% at start of discharge
    nom_cap = param["Nominal cell capacity [A.h]"]
    SoC = 100 * (1 - (capacity / nom_cap))

    return time, voltage, capacity, temperature, SoC

# Run the experiment at different C-rates
# 0.5C = 1.45 A, 1C = 2.9 A, 2C = 5.8 A
time_05C, volt_05C, cap_05C, temp_05C, SoC_05C = run_experiment(2.5)
time_1C,  volt_1C,  cap_1C,  temp_1C,  SoC_1C  = run_experiment(5)
time_2C,  volt_2C,  cap_2C,  temp_2C,  SoC_2C  = run_experiment(10)

# ----- Plotting the results -----
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# 1. Voltage vs. Discharge Capacity
axs[0, 0].plot(cap_05C, volt_05C, 'k:', linewidth=2, label='0.5C (2.5 A)')
axs[0, 0].plot(cap_1C,  volt_1C,  'b-', linewidth=2, label='1C (5.0 A)')
axs[0, 0].plot(cap_2C,  volt_2C,  'c--', linewidth=2, label='2C (10.0 A)')
axs[0, 0].set_xlabel("Discharge Capacity (A·h)")
axs[0, 0].set_ylabel("Voltage (V)")
axs[0, 0].set_title("Voltage vs. Discharge Capacity")
axs[0, 0].grid(True)
axs[0, 0].legend()

# 2. State-of-Charge vs. Time
axs[0, 1].plot(time_05C, SoC_05C, 'k:', linewidth=2, label='0.5C (2.5 A)')
axs[0, 1].plot(time_1C,  SoC_1C,  'g-', linewidth=2, label='1C (5.0 A)')
axs[0, 1].plot(time_2C,  SoC_2C,  'k--', linewidth=2, label='2C (10.0 A)')
axs[0, 1].set_xlabel("Time (s)")
axs[0, 1].set_ylabel("State of Charge (%)")
axs[0, 1].set_title("SoC vs. Time")
axs[0, 1].grid(True)
axs[0, 1].legend()

# 3. Cell Temperature vs. Time
axs[1, 0].plot(time_05C, temp_05C, 'r:', linewidth=2, label='0.5C (2.5 A)')
axs[1, 0].plot(time_1C,  temp_1C,  'r-', linewidth=2, label='1C (5.0 A)')
axs[1, 0].plot(time_2C,  temp_2C,  'y--', linewidth=2, label='2C (10.0 A)')
axs[1, 0].set_xlabel("Time (s)")
axs[1, 0].set_ylabel("Cell Temperature (K)")
axs[1, 0].set_title("Cell Temperature vs. Time")
axs[1, 0].grid(True)
axs[1, 0].legend()

# 4. Discharge Capacity vs. Time
axs[1, 1].plot(time_05C, cap_05C, 'm:', linewidth=2, label='0.5C (2.5 A)')
axs[1, 1].plot(time_1C,  cap_1C,  'm-', linewidth=2, label='1C (5.0 A)')
axs[1, 1].plot(time_2C,  cap_2C,  color='orange', linestyle='--', linewidth=2, label='2C (10.0 A)')
axs[1, 1].set_xlabel("Time (s)")
axs[1, 1].set_ylabel("Discharge Capacity (A·h)")
axs[1, 1].set_title("Discharge Capacity vs. Time")
axs[1, 1].grid(True)
axs[1, 1].legend()

plt.tight_layout()
plt.show()
