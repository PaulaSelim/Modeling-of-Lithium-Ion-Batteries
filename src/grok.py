import pybamm
import matplotlib.pyplot as plt

# Define the model with lumped thermal effects
options = {"thermal": "lumped"}
model = pybamm.lithium_ion.DFN(options)

# Load base parameter values
parameter_values_base = pybamm.ParameterValues("Chen2020")
parameter_values_base["Lower voltage cut-off [V]"] = 3.0


# Set ambient and initial temperatures to 40°C (313.15 K)
T_ambient = 40 + 273.15
parameter_values_base["Initial temperature [K]"] = T_ambient
parameter_values_base["Ambient temperature [K]"] = T_ambient

nominal_capacity = 5.0  # or 4.85, depending on the exact cell
C_rates = [1, 2]
currents = [5.0, 10.0]  # A


# Run simulations for 1C and 2C
solutions = []
for current in currents:
    # Copy base parameters and set the discharge current
    parameter_values = parameter_values_base.copy()
    parameter_values["Current function [A]"] = current
    # Create and solve the simulation
    sim = pybamm.Simulation(model, parameter_values=parameter_values)
    solution = sim.solve([0, 7200])  # Up to 3600 s, stops at voltage cutoff
    solutions.append(solution)

# Extract data for 1C (first simulation)
time_1C = solutions[0]["Time [s]"].entries
voltage_1C = solutions[0]["Terminal voltage [V]"].entries
discharge_capacity_1C = solutions[0]["Discharge capacity [A.h]"].entries
temperature_1C = solutions[0]["Cell temperature [K]"].entries
# Average temperature if 2D (spatial × time)
if len(temperature_1C.shape) == 2:
    temperature_1C = temperature_1C.mean(axis=0)
soc_1C = 1 - (discharge_capacity_1C / nominal_capacity)

# Extract data for 2C (second simulation)
time_2C = solutions[1]["Time [s]"].entries
voltage_2C = solutions[1]["Terminal voltage [V]"].entries
discharge_capacity_2C = solutions[1]["Discharge capacity [A.h]"].entries
temperature_2C = solutions[1]["Cell temperature [K]"].entries
# Average temperature if 2D
if len(temperature_2C.shape) == 2:
    temperature_2C = temperature_2C.mean(axis=0)
soc_2C = 1 - (discharge_capacity_2C / nominal_capacity)

# Create a 2x2 subplot grid
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Voltage vs. Discharge Capacity
axes[0, 0].plot(discharge_capacity_1C, voltage_1C, label="1C")
axes[0, 0].plot(discharge_capacity_2C, voltage_2C, label="2C")
axes[0, 0].set_title("Voltage vs. Discharge Capacity")
axes[0, 0].set_xlabel("Discharge Capacity [A.h]")
axes[0, 0].set_ylabel("Voltage [V]")
axes[0, 0].legend()

# SoC vs. Time
axes[0, 1].plot(time_1C, soc_1C, label="1C")
axes[0, 1].plot(time_2C, soc_2C, label="2C")
axes[0, 1].set_title("SoC vs. Time")
axes[0, 1].set_xlabel("Time [s]")
axes[0, 1].set_ylabel("State of Charge")
axes[0, 1].legend()

# Temperature vs. Time
axes[1, 0].plot(time_1C, temperature_1C, label="1C")
axes[1, 0].plot(time_2C, temperature_2C, label="2C")
axes[1, 0].set_title("Temperature vs. Time")
axes[1, 0].set_xlabel("Time [s]")
axes[1, 0].set_ylabel("Temperature [K]")
axes[1, 0].legend()

# Discharge Capacity vs. Time
axes[1, 1].plot(time_1C, discharge_capacity_1C, label="1C")
axes[1, 1].plot(time_2C, discharge_capacity_2C, label="2C")
axes[1, 1].set_title("Discharge Capacity vs. Time")
axes[1, 1].set_xlabel("Time [s]")
axes[1, 1].set_ylabel("Discharge Capacity [A.h]")
axes[1, 1].legend()

# Adjust layout and display the plots
plt.tight_layout()
plt.show()
