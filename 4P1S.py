import liionpack as lp
import pybamm
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Set up the simulation parameters
# -----------------------------
# Use the Chen2020 parameter set and update ambient temperature to 20°C (293.15 K)
parameter_values = pybamm.ParameterValues("Chen2020")
parameter_values.update({"Ambient temperature [K]": 293.15})

# Set up a 4p1s pack (4 parallel, 1 series) with typical resistor values
netlist = lp.setup_circuit(
    Np=4,
    Ns=1,
    Rb=1e-3,  # Busbar resistance [Ohm]
    Rc=1e-2,  # Connection resistance [Ohm]
    Ri=5e-2,  # Internal resistance [Ohm]
    V=4.0,    # Initial guess for cell voltage [V]
    I=5.0     # Current used for creating the netlist (5 A for 1C rate)
)

# Define additional output variables
output_variables = [
    "Volume-averaged cell temperature [K]",
    "Volume-averaged total heating [W.m-3]",
]

# Define a discharge experiment:
# Discharge at 5 A for up to 3600 s (1 hour) or until terminal voltage reaches 3.3 V.
experiment = pybamm.Experiment(
    ["Discharge at 5 A for 3600 s or until 3.3 V"],
    period="1 second"  # Time step for simulation (1 s)
)

# Use full initial SoC (1.0) to start from full charge
initial_soc = 1.0

# Define input temperatures for each cell (different starting temperatures)
temps = np.ones(4) * 293.15 + np.arange(4) * 2  # Starting from 20°C with 2°C increments
inputs = {"Input temperature [K]": temps}

# -----------------------------
# Run the simulation with liionpack
# -----------------------------
output = lp.solve(
    netlist=netlist,
    sim_func=lp.thermal_external,  # Use the thermal simulation function
    inputs=inputs,
    parameter_values=parameter_values,
    experiment=experiment,
    output_variables=output_variables,
    initial_soc=initial_soc
)

# -----------------------------
# Process simulation output
# -----------------------------
# Time vector (1D array)
time = output["Time [s]"]

# Get arrays for variables
current = output["Cell current [A]"]  # Discharge current [A]
voltage = output["Terminal voltage [V]"]  # Terminal voltage [V]
temperature = output["Volume-averaged cell temperature [K]"]

# Average over cells if arrays are 2D
current_avg = np.mean(current, axis=1)
voltage_avg = np.mean(voltage, axis=1)
temperature_avg = np.mean(temperature, axis=1)

# Compute the cumulative discharge capacity (in Ah)
capacity_Ah = np.cumsum(current_avg) / 3600  # [Ah]

# Compute the state-of-charge (SoC)
nominal_capacity = 5.0
SoC = initial_soc - capacity_Ah / nominal_capacity

# -----------------------------
# Plot only the requested results
# -----------------------------
plt.figure(figsize=(12, 10))

# Plot 1: Cell voltage distribution
plt.subplot(2, 2, 1)
for i in range(voltage.shape[1]):
    plt.plot(time, voltage[:, i], label=f'Cell {i+1}')
plt.plot(time, voltage_avg, 'k--', label='Average')
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("Cell Voltage Distribution")
plt.legend()
plt.grid(True)

# Plot 2: SoC vs. Time
plt.subplot(2, 2, 2)
plt.plot(time, SoC, 'g-')
plt.xlabel("Time (s)")
plt.ylabel("State of Charge")
plt.title("SoC vs. Time")
plt.grid(True)

# Plot 3: Volume-averaged cell temperature vs. Time (in Kelvin)
plt.subplot(2, 2, 3)
for i in range(temperature.shape[1]):
    plt.plot(time, temperature[:, i], label=f'Cell {i+1}')
plt.plot(time, temperature_avg, 'k--', label='Average')
plt.xlabel("Time (s)")
plt.ylabel("Cell Temperature (K)")
plt.title("Volume-averaged Cell Temperature vs. Time")
plt.legend()
plt.grid(True)

# Plot 4: Discharge Capacity vs. Time
plt.subplot(2, 2, 4)
plt.plot(time, capacity_Ah, 'm-')
plt.xlabel("Time (s)")
plt.ylabel("Discharge Capacity (Ah)")
plt.title("Discharge Capacity vs. Time")
plt.grid(True)

plt.tight_layout()
plt.show()