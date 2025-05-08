import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Callable


class BatterySimulatorGUI:
    """A GUI application for configuring and running battery pack simulations."""
    
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the Battery Simulator GUI.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("Battery Pack Simulator")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set theme and styles
        self.setup_styles()
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create frames for each tab
        self.create_tab_frames()
        
        # Setup the different sections in each tab
        self.setup_configuration_tab()
        self.setup_test_setup_tab()
        self.setup_advanced_tab()
        
        # Create bottom control panel with run button, status and save/load
        self.create_control_panel()
        
        # Status bar for messages
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Store for parameters
        self.params = {}
        
        # Initialize default values
        self.init_default_values()
        
    def setup_styles(self) -> None:
        """Configure ttk styles for the application."""
        style = ttk.Style()
        
        # Use a modern theme if available
        try:
            style.theme_use("clam")  # Use a clean, modern theme
        except tk.TclError:
            pass  # Fallback to default theme if clam is not available
        
        # Configure styles
        style.configure(
            "TLabel", 
            font=("Segoe UI", 10),
            padding=2
        )
        style.configure(
            "TButton", 
            font=("Segoe UI", 10),
            padding=6
        )
        style.configure(
            "TEntry", 
            padding=5
        )
        style.configure(
            "TNotebook", 
            padding=5
        )
        style.configure(
            "Section.TFrame", 
            padding=10,
            relief=tk.GROOVE
        )
        style.configure(
            "Header.TLabel", 
            font=("Segoe UI", 12, "bold"),
            padding=5
        )
        style.configure(
            "Subheader.TLabel", 
            font=("Segoe UI", 10, "bold"),
            padding=3
        )
        style.configure(
            "Run.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=10
        )
        
    def create_tab_frames(self) -> None:
        """Create the frames for each tab in the notebook."""
        # Main configuration tab
        self.config_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.config_frame, text="Configuration")
        
        # Add scrolling to config frame
        self.config_canvas = tk.Canvas(self.config_frame)
        self.config_scrollbar = ttk.Scrollbar(
            self.config_frame, 
            orient="vertical", 
            command=self.config_canvas.yview
        )
        self.scrollable_config_frame = ttk.Frame(self.config_canvas)
        
        self.scrollable_config_frame.bind(
            "<Configure>",
            lambda e: self.config_canvas.configure(
                scrollregion=self.config_canvas.bbox("all")
            )
        )
        
        self.config_canvas.create_window(
            (0, 0), 
            window=self.scrollable_config_frame, 
            anchor="nw"
        )
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)
        
        self.config_canvas.pack(side="left", fill="both", expand=True)
        self.config_scrollbar.pack(side="right", fill="y")
        
        # Test setup tab
        self.test_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.test_frame, text="Current Tests")
        
        # Advanced settings tab
        self.advanced_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.advanced_frame, text="Advanced")
    
    def setup_configuration_tab(self) -> None:
        """Setup the widgets in the main configuration tab."""
        frame = self.scrollable_config_frame
        row = 0
        
        # Title and description
        title_label = ttk.Label(
            frame, 
            text="Battery Pack Configuration",
            style="Header.TLabel"
        )
        title_label.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="w", 
            padx=5, 
            pady=(5, 10)
        )
        row += 1
        
        description = ttk.Label(
            frame,
            text="Configure the basic parameters for your battery pack simulation.",
            wraplength=600
        )
        description.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="w", 
            padx=5, 
            pady=(0, 15)
        )
        row += 1
        
        # Create sections for different parameter groups
        # Pack Configuration Section
        pack_frame = ttk.LabelFrame(frame, text="Pack Configuration", padding=10)
        pack_frame.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Number of parallel cells
        self.num_parallel = self.add_parameter(
            pack_frame,
            "Number of Parallel Cells",
            3,
            0,
            param_type=int,
            tooltip="Number of cells connected in parallel"
        )
        
        # Number of series cells
        self.num_series = self.add_parameter(
            pack_frame,
            "Number of Series Cells",
            4,
            1,
            param_type=int,
            tooltip="Number of cells connected in series"
        )
        
        row += 1
        
        # Voltage and Capacity Section
        voltage_frame = ttk.LabelFrame(
            frame, 
            text="Voltage and Capacity", 
            padding=10
        )
        voltage_frame.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Initial voltage
        self.initial_voltage = self.add_parameter(
            voltage_frame,
            "Initial Voltage (V)",
            4.0,
            0,
            tooltip="Starting voltage of each cell"
        )
        
        # Cut-off voltage
        self.cut_off_voltage = self.add_parameter(
            voltage_frame,
            "Cut-off Voltage (V)",
            2.5,
            1,
            tooltip="Minimum voltage before simulation stops"
        )
        
        # Initial state of charge
        self.initial_soc = self.add_parameter(
            voltage_frame,
            "Initial State of Charge",
            1.0,
            2,
            tooltip="Initial SoC from 0 to 1.0"
        )
        
        # Nominal capacity
        self.nominal_capacity = self.add_parameter(
            voltage_frame,
            "Nominal Capacity (Ah)",
            5.0,
            3,
            tooltip="Rated capacity of each cell in Amp-hours"
        )
        
        row += 1
        
        # Temperature Settings Section
        temp_frame = ttk.LabelFrame(frame, text="Temperature Settings", padding=10)
        temp_frame.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Ambient temperature
        self.ambient_temp = self.add_parameter(
            temp_frame,
            "Ambient Temperature (°C)",
            40.0,
            0,
            tooltip="Initial ambient temperature in Celsius"
        )
        
        row += 1
        
        # Resistance Settings Section
        resistance_frame = ttk.LabelFrame(
            frame, 
            text="Resistance Settings", 
            padding=10
        )
        resistance_frame.grid(
            row=row, 
            column=0, 
            columnspan=2, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Busbar resistance
        self.busbar_resistance = self.add_parameter(
            resistance_frame,
            "Busbar Resistance (Ω)",
            1e-3,
            0,
            tooltip="Resistance of the busbar in Ohms"
        )
        
        # Connection resistance
        self.connection_resistance = self.add_parameter(
            resistance_frame,
            "Connection Resistance (Ω)",
            1e-2,
            1,
            tooltip="Resistance of connections in Ohms"
        )
        
        # Internal resistance
        self.internal_resistance = self.add_parameter(
            resistance_frame,
            "Internal Resistance (Ω)",
            5e-2,
            2,
            tooltip="Internal resistance of cells in Ohms"
        )
    
    def setup_test_setup_tab(self) -> None:
        """Setup the current tests tab."""
        frame = self.test_frame
        
        # Title and description
        title_label = ttk.Label(
            frame, 
            text="Current Test Configuration",
            style="Header.TLabel"
        )
        title_label.grid(
            row=0, 
            column=0, 
            columnspan=3, 
            sticky="w", 
            padx=5, 
            pady=(5, 10)
        )
        
        description = ttk.Label(
            frame,
            text="Define different current test scenarios for your simulation.",
            wraplength=600
        )
        description.grid(
            row=1, 
            column=0, 
            columnspan=3, 
            sticky="w", 
            padx=5, 
            pady=(0, 15)
        )
        
        # Current Tests Container
        tests_container = ttk.LabelFrame(
            frame, 
            text="Current Tests", 
            padding=10
        )
        tests_container.grid(
            row=2, 
            column=0, 
            columnspan=3, 
            sticky="nsew", 
            padx=5, 
            pady=5
        )
        
        # Configure frame to expand with window
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        tests_container.columnconfigure(0, weight=1)
        
        # Current tests frame
        self.current_tests_frame = ttk.Frame(tests_container, padding=5)
        self.current_tests_frame.grid(
            row=0, 
            column=0, 
            sticky="nsew", 
            padx=5, 
            pady=5
        )
        
        # Button frame for add/remove buttons
        button_frame = ttk.Frame(tests_container)
        button_frame.grid(
            row=1, 
            column=0, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Add test button with icon
        add_test_button = ttk.Button(
            button_frame,
            text="Add Test",
            command=self.add_current_test
        )
        add_test_button.pack(side=tk.LEFT, padx=5)
        
        # Default current tests
        self.current_tests = [
            {"name": "0.5C", "current": 7.5},
            {"name": "1C", "current": 15.0},
            {"name": "2C", "current": 30.0}
        ]
        
        # Experiment settings
        experiment_frame = ttk.LabelFrame(
            frame, 
            text="Experiment Settings", 
            padding=10
        )
        experiment_frame.grid(
            row=3, 
            column=0, 
            columnspan=3, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Experiment period
        period_label = ttk.Label(
            experiment_frame, 
            text="Experiment Period:"
        )
        period_label.grid(
            row=0, 
            column=0, 
            sticky="w", 
            padx=5, 
            pady=5
        )
        
        self.experiment_period = tk.StringVar(value="10 second")
        period_entry = ttk.Entry(
            experiment_frame, 
            textvariable=self.experiment_period, 
            width=20
        )
        period_entry.grid(
            row=0, 
            column=1, 
            sticky="w", 
            padx=5, 
            pady=5
        )
        self.create_tooltip(
            period_entry, 
            "Time period for each experiment step (e.g., '10 second')"
        )
        
        # Experiment time
        time_label = ttk.Label(
            experiment_frame, 
            text="Experiment Time (s):"
        )
        time_label.grid(
            row=1, 
            column=0, 
            sticky="w", 
            padx=5, 
            pady=5
        )
        
        self.experiment_time_var = tk.StringVar(value="15000")
        time_entry = ttk.Entry(
            experiment_frame, 
            textvariable=self.experiment_time_var, 
            width=20
        )
        time_entry.grid(
            row=1, 
            column=1, 
            sticky="w", 
            padx=5, 
            pady=5
        )
        self.create_tooltip(
            time_entry, 
            "Total time for the simulation in seconds"
        )
        
        # Initialize the current tests UI
        self.update_current_tests_ui()
    
    def setup_advanced_tab(self) -> None:
        """Setup the advanced settings tab."""
        frame = self.advanced_frame
        
        # Title and description
        title_label = ttk.Label(
            frame, 
            text="Advanced Settings",
            style="Header.TLabel"
        )
        title_label.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            sticky="w", 
            padx=5, 
            pady=(5, 10)
        )
        
        description = ttk.Label(
            frame,
            text="Configure advanced visualization and output settings.",
            wraplength=600
        )
        description.grid(
            row=1, 
            column=0, 
            columnspan=2, 
            sticky="w", 
            padx=5, 
            pady=(0, 15)
        )
        
        # Circuit Diagram Settings
        circuit_frame = ttk.LabelFrame(
            frame, 
            text="Circuit Diagram Settings", 
            padding=10
        )
        circuit_frame.grid(
            row=2, 
            column=0, 
            columnspan=2, 
            sticky="ew", 
            padx=5, 
            pady=5
        )
        
        # Draw circuit checkbox
        self.draw_circuit = tk.BooleanVar(value=False)
        draw_circuit_check = ttk.Checkbutton(
            circuit_frame, 
            text="Generate Circuit Diagram", 
            variable=self.draw_circuit
        )
        draw_circuit_check.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            sticky="w", 
            padx=5, 
            pady=5
        )
        
        # Circuit DPI
        dpi_label = ttk.Label(circuit_frame, text="Circuit DPI:")
        dpi_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.circuit_dpi_var = tk.StringVar(value="1200")
        dpi_entry = ttk.Entry(
            circuit_frame, 
            textvariable=self.circuit_dpi_var, 
            width=10
        )
        dpi_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.create_tooltip(
            dpi_entry, 
            "Dots per inch - controls the resolution of the circuit diagram"
        )
        
        # Component size
        cpt_label = ttk.Label(circuit_frame, text="Component Size:")
        cpt_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.circuit_cpt_size_var = tk.StringVar(value="1.0")
        cpt_entry = ttk.Entry(
            circuit_frame, 
            textvariable=self.circuit_cpt_size_var, 
            width=10
        )
        cpt_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.create_tooltip(
            cpt_entry, 
            "Size factor for circuit components"
        )
        
        # Node spacing
        node_label = ttk.Label(circuit_frame, text="Node Spacing:")
        node_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        self.circuit_node_spacing_var = tk.StringVar(value="2.5")
        node_entry = ttk.Entry(
            circuit_frame, 
            textvariable=self.circuit_node_spacing_var, 
            width=10
        )
        node_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.create_tooltip(
            node_entry, 
            "Spacing between nodes in the circuit diagram"
        )
    
    def create_control_panel(self) -> None:
        """Create the bottom control panel with buttons and status."""
        control_frame = ttk.Frame(self.main_frame, padding="5")
        control_frame.pack(fill=tk.X, pady=10)
        
        # Save configuration button
        save_button = ttk.Button(
            control_frame,
            text="Save Config",
            command=self.save_configuration
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Load configuration button
        load_button = ttk.Button(
            control_frame,
            text="Load Config",
            command=self.load_configuration
        )
        load_button.pack(side=tk.LEFT, padx=5)
        
        # Run button
        run_button = ttk.Button(
            control_frame,
            text="Run Simulation",
            command=self.run_simulation,
            style="Run.TButton"
        )
        run_button.pack(side=tk.RIGHT, padx=5)
    
    def init_default_values(self) -> None:
        """Initialize the default values for the simulation parameters."""
        # These are now set directly during widget creation
        pass
    
    def add_parameter(
        self, 
        parent: ttk.Frame, 
        label_text: str, 
        default_value: Union[int, float, str],
        row: int, 
        param_type: Callable = float, 
        tooltip: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a parameter input row with label and entry.
        
        Args:
            parent: Parent frame to add the parameter to
            label_text: Text for the parameter label
            default_value: Default value for the parameter
            row: Row position in the parent grid
            param_type: Type function for the parameter (float, int, etc.)
            tooltip: Optional tooltip text
            
        Returns:
            Dictionary with variable and type for the parameter
        """
        label = ttk.Label(parent, text=f"{label_text}:")
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        var = tk.StringVar(value=str(default_value))
        entry = ttk.Entry(parent, textvariable=var, width=20)
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        
        # Add validation to ensure correct input types
        if param_type == int:
            entry.config(validate="key", validatecommand=(
                parent.register(lambda s: s.isdigit() or s == ""), '%P'
            ))
        elif param_type == float:
            entry.config(validate="key", validatecommand=(
                parent.register(
                    lambda s: s == "" or s == "." or
                    s.replace('.', '', 1).isdigit() or
                    (s.startswith('-') and 
                     s[1:].replace('.', '', 1).isdigit() or
                     s[1:] == "")
                ), '%P'
            ))
        
        if tooltip:
            self.create_tooltip(label, tooltip)
            self.create_tooltip(entry, tooltip)
        
        return {"var": var, "type": param_type, "entry": entry}
    
    def update_current_tests_ui(self) -> None:
        """Update the current tests UI with the current test data."""
        # Clear existing widgets
        for widget in self.current_tests_frame.winfo_children():
            widget.destroy()
        
        # Create header row with column labels
        headers = ["Test Name", "Current (A)", ""]
        for col, header in enumerate(headers):
            label = ttk.Label(
                self.current_tests_frame, 
                text=header, 
                style="Subheader.TLabel"
            )
            label.grid(row=0, column=col, padx=5, pady=(0, 10), sticky="w")
        
        # Set column weights
        self.current_tests_frame.columnconfigure(0, weight=1)
        self.current_tests_frame.columnconfigure(1, weight=1)
        
        # Add each test
        for i, test in enumerate(self.current_tests):
            row = i + 1
            
            # Test name entry
            name_var = tk.StringVar(value=test.get("name", ""))
            name_entry = ttk.Entry(
                self.current_tests_frame, 
                textvariable=name_var, 
                width=15
            )
            name_entry.grid(row=row, column=0, padx=5, pady=5, sticky="w")
            test["name_var"] = name_var
            
            # Current value entry with validation
            current_var = tk.StringVar(value=str(test.get("current", 0)))
            current_entry = ttk.Entry(
                self.current_tests_frame, 
                textvariable=current_var, 
                width=15
            )
            current_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            current_entry.config(validate="key", validatecommand=(
                self.current_tests_frame.register(
                    lambda s: s == "" or s == "." or
                    s.replace('.', '', 1).isdigit() or
                    (s.startswith('-') and 
                     s[1:].replace('.', '', 1).isdigit() or
                     s[1:] == "")
                ), '%P'
            ))
            test["current_var"] = current_var
            
            # Delete button with improved styling
            delete_btn = ttk.Button(
                self.current_tests_frame, 
                text="✕",
                width=2,
                command=lambda idx=i: self.delete_current_test(idx)
            )
            delete_btn.grid(row=row, column=2, padx=5, pady=5)
    
    def add_current_test(self) -> None:
        """Add a new current test to the list."""
        self.current_tests.append({
            "name": f"Test {len(self.current_tests)+1}", 
            "current": 10.0
        })
        self.update_current_tests_ui()
        self.status_var.set(f"Added new current test: Test {len(self.current_tests)}")
    
    def delete_current_test(self, index: int) -> None:
        """Delete a current test from the list.
        
        Args:
            index: Index of the test to delete
        """
        if len(self.current_tests) > 1:  # Keep at least one test
            test_name = self.current_tests[index].get("name_var", tk.StringVar()).get()
            del self.current_tests[index]
            self.update_current_tests_ui()
            self.status_var.set(f"Removed test: {test_name}")
        else:
            messagebox.showwarning(
                "Warning", 
                "You must have at least one current test."
            )
    
    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Create a tooltip for a widget.
        
        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text
        """
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height() + 1
            
            # Creates a toplevel window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Modern tooltip style
            frame = ttk.Frame(tooltip, relief="solid", borderwidth=1)
            frame.pack(fill="both", expand=True)
            
            label = ttk.Label(
                frame, 
                text=text, 
                background="#FFFFEA", 
                padding=5,
                wraplength=250
            )
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def save_configuration(self) -> None:
        """Save the current configuration to a JSON file."""
        try:
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Configuration"
            )
            
            if not file_path:
                return  # User canceled
            
            # Collect all configuration data
            config = {
                # Pack configuration
                "num_parallel": int(self.num_parallel["var"].get()),
                "num_series": int(self.num_series["var"].get()),
                
                # Voltage and capacity
                "initial_voltage": float(self.initial_voltage["var"].get()),
                "cut_off_voltage": float(self.cut_off_voltage["var"].get()),
                "initial_soc": float(self.initial_soc["var"].get()),
                "nominal_capacity": float(self.nominal_capacity["var"].get()),
                
                # Temperature
                "ambient_temp": float(self.ambient_temp["var"].get()),
                
                # Resistances
                "busbar_resistance": float(self.busbar_resistance["var"].get()),
                "connection_resistance": float(self.connection_resistance["var"].get()),
                "internal_resistance": float(self.internal_resistance["var"].get()),
                
                # Experiment settings
                "experiment_period": self.experiment_period.get(),
                "experiment_time": int(self.experiment_time_var.get()),
                
                # Current tests
                "current_tests": [
                    {
                        "name": test["name_var"].get(),
                        "current": float(test["current_var"].get())
                    }
                    for test in self.current_tests
                ],
                
                # Circuit diagram
                "draw_circuit": self.draw_circuit.get(),
                "circuit_dpi": int(self.circuit_dpi_var.get()),
                "circuit_cpt_size": float(self.circuit_cpt_size_var.get()),
                "circuit_node_spacing": float(self.circuit_node_spacing_var.get())
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.status_var.set(f"Configuration saved to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving configuration: {str(e)}")
    
    def load_configuration(self) -> None:
        """Load configuration from a JSON file."""
        try:
            # Get file path from user
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Configuration"
            )
            
            if not file_path:
                return  # User canceled
            
            # Load from file
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Apply configuration
            # Pack configuration
            self.num_parallel["var"].set(str(config.get("num_parallel", 3)))
            self.num_series["var"].set(str(config.get("num_series", 4)))
            
            # Voltage and capacity
            self.initial_voltage["var"].set(str(config.get("initial_voltage", 4.0)))
            self.cut_off_voltage["var"].set(str(config.get("cut_off_voltage", 2.5)))
            self.initial_soc["var"].set(str(config.get("initial_soc", 1.0)))
            self.nominal_capacity["var"].set(str(config.get("nominal_capacity", 5.0)))
            
            # Temperature
            self.ambient_temp["var"].set(str(config.get("ambient_temp", 40.0)))
            
            # Resistances
            self.busbar_resistance["var"].set(str(config.get("busbar_resistance", 1e-3)))
            self.connection_resistance["var"].set(str(config.get("connection_resistance", 1e-2)))
            self.internal_resistance["var"].set(str(config.get("internal_resistance", 5e-2)))
            
            # Experiment settings
            self.experiment_period.set(config.get("experiment_period", "10 second"))
            self.experiment_time_var.set(str(config.get("experiment_time", 15000)))
            
            # Current tests
            if "current_tests" in config and config["current_tests"]:
                self.current_tests = [
                    {"name": test["name"], "current": test["current"]}
                    for test in config["current_tests"]
                ]
                self.update_current_tests_ui()
            
            # Circuit diagram
            self.draw_circuit.set(config.get("draw_circuit", False))
            self.circuit_dpi_var.set(str(config.get("circuit_dpi", 1200)))
            self.circuit_cpt_size_var.set(str(config.get("circuit_cpt_size", 1.0)))
            self.circuit_node_spacing_var.set(str(config.get("circuit_node_spacing", 2.5)))
            
            self.status_var.set(f"Configuration loaded from {file_path}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading configuration: {str(e)}")
    
    def validate_inputs(self) -> bool:
        """Validate all inputs before running the simulation.
        
        Returns:
            True if all inputs are valid, False otherwise
        """
        try:
            # Validate pack configuration
            if int(self.num_parallel["var"].get()) <= 0:
                raise ValueError("Number of parallel cells must be positive")
            if int(self.num_series["var"].get()) <= 0:
                raise ValueError("Number of series cells must be positive")
            
            # Validate voltage and capacity
            if float(self.initial_voltage["var"].get()) <= 0:
                raise ValueError("Initial voltage must be positive")
            if float(self.cut_off_voltage["var"].get()) <= 0:
                raise ValueError("Cut-off voltage must be positive")
            if not 0 <= float(self.initial_soc["var"].get()) <= 1:
                raise ValueError("Initial SoC must be between 0 and 1")
            if float(self.nominal_capacity["var"].get()) <= 0:
                raise ValueError("Nominal capacity must be positive")
                
            # Validate resistances (allow zero)
            if float(self.busbar_resistance["var"].get()) < 0:
                raise ValueError("Busbar resistance cannot be negative")
            if float(self.connection_resistance["var"].get()) < 0:
                raise ValueError("Connection resistance cannot be negative")
            if float(self.internal_resistance["var"].get()) < 0:
                raise ValueError("Internal resistance cannot be negative")
            
            # Validate experiment settings
            if not self.experiment_period.get().strip():
                raise ValueError("Experiment period cannot be empty")
            if int(self.experiment_time_var.get()) <= 0:
                raise ValueError("Experiment time must be positive")
            
            # Validate current tests
            for i, test in enumerate(self.current_tests):
                if not test["name_var"].get().strip():
                    raise ValueError(f"Test #{i+1} name cannot be empty")
                if float(test["current_var"].get()) == 0:
                    raise ValueError(f"Test #{i+1} current cannot be zero")
            
            # Validate circuit diagram settings if enabled
            if self.draw_circuit.get():
                if int(self.circuit_dpi_var.get()) <= 0:
                    raise ValueError("Circuit DPI must be positive")
                if float(self.circuit_cpt_size_var.get()) <= 0:
                    raise ValueError("Circuit component size must be positive")
                if float(self.circuit_node_spacing_var.get()) <= 0:
                    raise ValueError("Circuit node spacing must be positive")
            
            return True
        
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False
    
    def run_simulation(self) -> None:
        """Run the battery pack simulation with the current configuration."""
        # Validate inputs first
        if not self.validate_inputs():
            return
        
        try:
            # Update status
            self.status_var.set("Preparing simulation...")
            self.root.update()
            
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
            env["EXPERIMENT_TIME"] = str(int(self.experiment_time_var.get()))
            
            # Current tests
            current_tests_str = []
            for test in self.current_tests:
                name = test["name_var"].get()
                current = float(test["current_var"].get())
                current_tests_str.append(f"{name}:{current}")
            env["CURRENT_TESTS"] = ",".join(current_tests_str)
            
            # Circuit diagram settings
            env["DRAW_CIRCUIT"] = "true" if self.draw_circuit.get() else "false"
            env["CIRCUIT_DPI"] = str(int(self.circuit_dpi_var.get()))
            env["CIRCUIT_CPT_SIZE"] = str(float(self.circuit_cpt_size_var.get()))
            env["CIRCUIT_NODE_SPACING"] = str(float(self.circuit_node_spacing_var.get()))
            
            # Get the path to the simulation script
            script_path = Path(__file__).parent / "4P1S.py"
            
            # Show progress dialog
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Simulation Progress")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Center the progress window
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Progress message
            message_label = ttk.Label(
                progress_window,
                text=f"Starting simulation with {len(self.current_tests)} current tests.\n"
                     f"This may take a while depending on your settings.",
                wraplength=350,
                justify=tk.CENTER
            )
            message_label.pack(pady=(20, 10))
            
            # Add an indeterminate progress bar
            progress = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                length=300
            )
            progress.pack(pady=10)
            progress.start()
            
            # Update status
            self.status_var.set("Simulation running...")
            
            # Run the simulation script with the environment variables
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env
            )
            
            # Function to check if process has completed
            def check_process():
                if process.poll() is not None:
                    # Process finished
                    progress_window.destroy()
                    if process.returncode == 0:
                        messagebox.showinfo(
                            "Simulation Complete",
                            "Simulation has completed successfully."
                        )
                        self.status_var.set("Simulation completed successfully")
                    else:
                        messagebox.showerror(
                            "Simulation Error",
                            f"Simulation terminated with error code {process.returncode}"
                        )
                        self.status_var.set("Simulation failed")
                else:
                    # Process still running, check again in 500ms
                    self.root.after(500, check_process)
            
            # Start checking process status
            self.root.after(500, check_process)
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please check your inputs: {str(e)}")
            self.status_var.set("Simulation setup failed - input error")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Simulation failed - unknown error")


if __name__ == "__main__":
    root = tk.Tk()
    app = BatterySimulatorGUI(root)
    root.mainloop()