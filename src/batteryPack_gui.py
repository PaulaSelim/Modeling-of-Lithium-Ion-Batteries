import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import sys
from pathlib import Path

class BatterySimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battery Pack Simulator")
        self.root.geometry("800x700")
        
        # Create a main frame with scrollbar
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=1)
        
        # Add a canvas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        
        # Add scrollbar to the canvas
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Create a frame inside the canvas
        self.settings_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.settings_frame, anchor="nw")
        
        # Initialize all configuration widgets
        self.init_widgets()
        
    def init_widgets(self):
        # Title and description
        tk.Label(self.settings_frame, text="Battery Pack Simulation Configuration", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10
        )
        
        tk.Label(self.settings_frame, text="Adjust simulation parameters and click 'Run Simulation' to start.", 
                 font=("Arial", 10)).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )
        
        # Parameters
        self.params = {}
        row = 2
        
        # Temperature Settings
        self.add_section_header("Temperature Settings", row)
        row += 1
        self.ambient_temp = self.add_parameter("Ambient Temperature (°C)", 40.0, row, tooltip="Initial ambient temperature in Celsius")
        row += 1
        
        # Pack Configuration
        self.add_section_header("Pack Configuration", row)
        row += 1
        self.num_parallel = self.add_parameter("Number of Parallel Cells", 3, row, param_type=int)
        row += 1
        self.num_series = self.add_parameter("Number of Series Cells", 4, row, param_type=int)
        row += 1
        
        # Resistance Settings
        self.add_section_header("Resistance Settings", row)
        row += 1
        self.busbar_resistance = self.add_parameter("Busbar Resistance (Ω)", 1e-3, row, tooltip="Resistance of the busbar in Ohms")
        row += 1
        self.connection_resistance = self.add_parameter("Connection Resistance (Ω)", 1e-2, row, tooltip="Resistance of connections in Ohms")
        row += 1
        self.internal_resistance = self.add_parameter("Internal Resistance (Ω)", 5e-2, row, tooltip="Internal resistance of cells in Ohms")
        row += 1
        
        # Voltage and Capacity Settings
        self.add_section_header("Voltage and Capacity Settings", row)
        row += 1
        self.initial_voltage = self.add_parameter("Initial Voltage (V)", 4.0, row)
        row += 1
        self.cut_off_voltage = self.add_parameter("Cut-off Voltage (V)", 2.5, row, tooltip="Minimum voltage before simulation stops")
        row += 1
        self.initial_soc = self.add_parameter("Initial State of Charge", 1.0, row, tooltip="Initial SoC from 0 to 1.0")
        row += 1
        self.nominal_capacity = self.add_parameter("Nominal Capacity (Ah)", 5.0, row)
        row += 1
        
        # Experiment Settings
        self.add_section_header("Experiment Settings", row)
        row += 1
        
        # Experiment period as string
        experiment_period_label = tk.Label(self.settings_frame, text="Experiment Period:")
        experiment_period_label.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.experiment_period = tk.StringVar(value="10 second")
        experiment_period_entry = tk.Entry(self.settings_frame, textvariable=self.experiment_period, width=20)
        experiment_period_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        self.experiment_time = self.add_parameter("Experiment Time (s)", 15000, row, param_type=int)
        row += 1
        
        # Current Tests
        tk.Label(self.settings_frame, text="Current Tests:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        row += 1
        
        self.current_tests_frame = tk.Frame(self.settings_frame)
        self.current_tests_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=30, pady=5)
        
        # Default current tests
        self.current_tests = [
            {"name": "0.5C", "current": 7.5},
            {"name": "1C", "current": 15.0},
            {"name": "2C", "current": 30.0}
        ]
        
        self.update_current_tests_ui()
        row += 1
        
        # Button to add more current tests
        add_test_button = tk.Button(self.settings_frame, text="Add Current Test", command=self.add_current_test)
        add_test_button.grid(row=row, column=0, sticky="w", padx=30, pady=5)
        row += 1
        
        # Circuit Diagram Settings
        self.add_section_header("Circuit Diagram Settings", row)
        row += 1
        
        # Checkbox for drawing circuit
        self.draw_circuit = tk.BooleanVar(value=False)
        draw_circuit_check = tk.Checkbutton(self.settings_frame, text="Draw Circuit Diagram", 
                                         variable=self.draw_circuit)
        draw_circuit_check.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        row += 1
        
        self.circuit_dpi = self.add_parameter("Circuit DPI", 1200, row, param_type=int)
        row += 1
        self.circuit_cpt_size = self.add_parameter("Circuit Component Size", 1.0, row)
        row += 1
        self.circuit_node_spacing = self.add_parameter("Circuit Node Spacing", 2.5, row)
        row += 1
        
        # Add some spacing
        tk.Label(self.settings_frame, text="").grid(row=row, column=0, pady=10)
        row += 1
        
        # Run button
        run_button = tk.Button(self.settings_frame, text="Run Simulation", command=self.run_simulation,
                            font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=10, pady=5)
        run_button.grid(row=row, column=0, columnspan=2, pady=20)
    
    def add_section_header(self, text, row):
        tk.Label(self.settings_frame, text=text, font=("Arial", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
    
    def add_parameter(self, label_text, default_value, row, param_type=float, tooltip=None):
        label = tk.Label(self.settings_frame, text=label_text + ":")
        label.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        
        var = tk.StringVar(value=str(default_value))
        entry = tk.Entry(self.settings_frame, textvariable=var, width=20)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        
        if tooltip:
            self.create_tooltip(label, tooltip)
            self.create_tooltip(entry, tooltip)
        
        return {"var": var, "type": param_type}
    
    def update_current_tests_ui(self):
        # Clear existing widgets
        for widget in self.current_tests_frame.winfo_children():
            widget.destroy()
        
        # Create header
        tk.Label(self.current_tests_frame, text="Name").grid(row=0, column=0, padx=5)
        tk.Label(self.current_tests_frame, text="Current (A)").grid(row=0, column=1, padx=5)
        
        # Add each test
        for i, test in enumerate(self.current_tests):
            row = i + 1
            
            name_var = tk.StringVar(value=test["name"])
            name_entry = tk.Entry(self.current_tests_frame, textvariable=name_var, width=10)
            name_entry.grid(row=row, column=0, padx=5, pady=2)
            test["name_var"] = name_var
            
            current_var = tk.StringVar(value=str(test["current"]))
            current_entry = tk.Entry(self.current_tests_frame, textvariable=current_var, width=10)
            current_entry.grid(row=row, column=1, padx=5, pady=2)
            test["current_var"] = current_var
            
            # Delete button
            delete_btn = tk.Button(self.current_tests_frame, text="X", 
                                 command=lambda idx=i: self.delete_current_test(idx))
            delete_btn.grid(row=row, column=2, padx=5, pady=2)
    
    def add_current_test(self):
        self.current_tests.append({"name": f"Test {len(self.current_tests)+1}", "current": 10.0})
        self.update_current_tests_ui()
    
    def delete_current_test(self, index):
        if len(self.current_tests) > 1:  # Keep at least one test
            del self.current_tests[index]
            self.update_current_tests_ui()
        else:
            messagebox.showwarning("Warning", "You must have at least one current test.")
    
    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Creates a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
        
        def hide_tooltip(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def run_simulation(self):
        try:
            # Prepare environment variables
            env = os.environ.copy()
            
            # Temperature (convert from Celsius to Kelvin)
            env["AMBIENT_TEMP"] = str(float(self.ambient_temp["var"].get()) + 273.15)
            
            # Pack configuration
            env["NUM_PARALLEL"] = str(int(self.num_parallel["var"].get()))
            env["NUM_SERIES"] = str(int(self.num_series["var"].get()))
            
            # Resistances
            env["BUSBAR_RESISTANCE"] = str(float(self.busbar_resistance["var"].get()))
            env["CONNECTION_RESISTANCE"] = str(float(self.connection_resistance["var"].get()))
            env["INTERNAL_RESISTANCE"] = str(float(self.internal_resistance["var"].get()))
            
            # Voltage and capacity
            env["INITIAL_VOLTAGE"] = str(float(self.initial_voltage["var"].get()))
            env["CUT_OFF_VOLTAGE"] = str(float(self.cut_off_voltage["var"].get()))
            env["INITIAL_SOC"] = str(float(self.initial_soc["var"].get()))
            env["NOMINAL_CAPACITY"] = str(float(self.nominal_capacity["var"].get()))
            
            # Experiment settings
            env["EXPERIMENT_PERIOD"] = self.experiment_period.get()
            env["EXPERIMENT_TIME"] = str(int(self.experiment_time["var"].get()))
            
            # Current tests
            current_tests_str = []
            for test in self.current_tests:
                name = test["name_var"].get()
                current = float(test["current_var"].get())
                current_tests_str.append(f"{name}:{current}")
            env["CURRENT_TESTS"] = ",".join(current_tests_str)
            
            # Circuit diagram settings
            env["DRAW_CIRCUIT"] = "true" if self.draw_circuit.get() else "false"
            env["CIRCUIT_DPI"] = str(int(self.circuit_dpi["var"].get()))
            env["CIRCUIT_CPT_SIZE"] = str(float(self.circuit_cpt_size["var"].get()))
            env["CIRCUIT_NODE_SPACING"] = str(float(self.circuit_node_spacing["var"].get()))
            
            # Get the path to the simulation script
            script_path = Path(__file__).parent / "4P1S.py"
            
            # Notify user
            messagebox.showinfo("Simulation Started", 
                              f"Starting simulation with {len(self.current_tests)} current tests.\n"
                              f"This may take a while depending on your settings.")
            
            # Run the simulation script with the environment variables
            subprocess.Popen([sys.executable, str(script_path)], env=env)
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please check your inputs: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BatterySimulatorGUI(root)
    root.mainloop()