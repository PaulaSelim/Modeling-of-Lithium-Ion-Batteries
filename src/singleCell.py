import pybamm
import numpy as np

import matplotlib.pyplot as plt

# Set up the model (Doyle-Fuller-Newman model)
model = pybamm.lithium_ion.DFN()

# Set parameter values
param = model.default_parameter_values
param["Initial temperature [K]"] = 273.15 + 40  # 40°C
param["Ambient temperature [K]"] = 273.15 + 40  # 40°C
param.update({"C-rate": 1.0}, check_already_exists=False)  # 1C discharge rate

# Create simulation
sim = pybamm.Simulation(model, parameter_values=param)

# Run simulation for 1 hour
solution = sim.solve(t_eval=np.linspace(0, 3600, 1000))

# Extract data
time = solution["Time [h]"].entries
voltage = solution["Terminal voltage [V]"].entries
soc = solution[
    "Negative electrode stoichiometry"
].entries  # Correct variable name for SOC
temperature = (
    np.mean(solution["Cell temperature [K]"].entries, axis=0) - 273.15
)  # Average across spatial points and convert to Celsius
capacity = solution["Discharge capacity [A.h]"].entries

# Set up plots
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle("Battery Simulation Results (40°C, 1C Discharge)", fontsize=16)

# Plot 1: Voltage vs Time
axs[0, 0].plot(time, voltage)
axs[0, 0].set_xlabel("Time (h)")
axs[0, 0].set_ylabel("Voltage (V)")
axs[0, 0].set_title("Voltage vs Time")
axs[0, 0].grid(True)

# Plot 2: SoC vs Time
axs[0, 1].plot(time, soc)
axs[0, 1].set_xlabel("Time (h)")
axs[0, 1].set_ylabel("State of Charge")
axs[0, 1].set_title("State of Charge vs Time")
axs[0, 1].grid(True)

# Plot 3: Temperature vs Time
axs[1, 0].plot(time, temperature)
axs[1, 0].set_xlabel("Time (h)")
axs[1, 0].set_ylabel("Temperature (°C)")
axs[1, 0].set_title("Battery Temperature vs Time")
axs[1, 0].grid(True)

# Plot 4: Capacity vs Time
axs[1, 1].plot(time, capacity)
axs[1, 1].set_xlabel("Time (h)")
axs[1, 1].set_ylabel("Capacity (A.h)")
axs[1, 1].set_title("Battery Capacity vs Time")
axs[1, 1].grid(True)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()
