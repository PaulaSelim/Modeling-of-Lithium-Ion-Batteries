import pybamm
import matplotlib.pyplot as plt

# ----- Setup the model with thermal effects -----
# Use the SPMe model with a lumped thermal model
options = {"thermal": "lumped"}
model = pybamm.lithium_ion.SPMe(options=options)

# ----- Update parameter values for our simulation -----
# Get default parameters from the model
param = model.default_parameter_values

# Set the ambient temperature to 30°C (in Kelvin)
param["Ambient temperature [K]"] = 303.15

# Set the nominal capacity and discharge current for a 1C rate.
# Here we use 2.9 A·h as an example nominal capacity,
# so the constant discharge current is 2.9 A.
param["Nominal cell capacity [A.h]"] = 2.9
param["Current function [A]"] = 2.9

# Set a lower voltage cut-off so that the simulation stops when reached
param["Lower voltage cut-off [V]"] = 3.0

# ----- Create and solve the simulation -----
sim = pybamm.Simulation(model, parameter_values=param)
# Solve over a long enough time span; the simulation will terminate when the cutoff voltage is hit.
solution = sim.solve([0, 3600])

# ----- Extract key variables from the solution -----
# ----- Extract key variables from the solution -----
time = solution["Time [s]"].entries                # Time in seconds
voltage = solution["Voltage [V]"].entries           # Terminal voltage in V
# "Discharge capacity [A.h]" gives the integrated capacity during discharge
discharge_capacity = solution["Discharge capacity [A.h]"].entries  
# "Cell temperature [K]" is available because we enabled the thermal model
temperature = solution["Cell temperature [K]"].entries    
# If temperature is a 2D array, extract a 1D array matching time dimension
if temperature.ndim > 1:
	temperature = temperature[0]  # Taking first row/column or averaging might be needed
# Compute state-of-charge (SoC) as a percentage.
# Assume 100% at the start and SoC decreases as capacity is extracted.
# SoC = 100 * (1 - (discharge capacity / nominal capacity))
nom_cap = param["Nominal cell capacity [A.h]"]
SoC = 100 * (1 - (discharge_capacity / nom_cap))

# ----- Plotting the results -----
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# 1. Voltage vs. Discharge Capacity
axs[0, 0].plot(discharge_capacity, voltage, 'b-', linewidth=2)
axs[0, 0].set_xlabel("Discharge Capacity (A·h)")
axs[0, 0].set_ylabel("Voltage (V)")
axs[0, 0].set_title("Voltage vs. Discharge Capacity")
axs[0, 0].grid(True)

# 2. State-of-Charge vs. Time
axs[0, 1].plot(time, SoC, 'g-', linewidth=2)
axs[0, 1].set_xlabel("Time (s)")
axs[0, 1].set_ylabel("State of Charge (%)")
axs[0, 1].set_title("SoC vs. Time")
axs[0, 1].grid(True)

# 3. Cell Temperature vs. Time
axs[1, 0].plot(time, temperature, 'r-', linewidth=2)
axs[1, 0].set_xlabel("Time (s)")
axs[1, 0].set_ylabel("Cell Temperature (K)")
axs[1, 0].set_title("Cell Temperature vs. Time")
axs[1, 0].grid(True)

# 4. Discharge Capacity vs. Time
axs[1, 1].plot(time, discharge_capacity, 'm-', linewidth=2)
axs[1, 1].set_xlabel("Time (s)")
axs[1, 1].set_ylabel("Discharge Capacity (A·h)")
axs[1, 1].set_title("Discharge Capacity vs. Time")
axs[1, 1].grid(True)

plt.tight_layout()
plt.show()
