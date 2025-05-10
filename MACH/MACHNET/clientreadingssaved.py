import tkinter as tk
from tkinter import messagebox, simpledialog
import json, os, grpc, concurrent.futures
import relay_pb2
import relay_pb2_grpc
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import threading
import queue
import time

# Constants
SAVE_FILE = "gui_state.json"
GROUPS_FILE = "groups_state.json"
BUFFERSENSOR = 7
BUFFERVALVE = 6
MAX_DEVICES = 100  # Maximum number of devices allowed
REFRESH_INTERVAL = 1.0  # Refresh interval in seconds
MAX_RETRIES = 3  # Maximum number of retries for gRPC calls

# Data classes for better type safety and organization
@dataclass
class DeviceConfig:
    port: str
    name: str
    state: bool = False
    input_voltage: float = 0.0
    value: float = 0.0
    min_val: float = 0.0
    max_val: float = 100.0
    min_voltage: float = 0.0
    max_voltage: float = 5.0

class CommandQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def _process_queue(self):
        while True:
            try:
                cmd, callback = self.queue.get()
                response = send_command(cmd)
                if callback:
                    callback(response)
            except Exception as e:
                print(f"Error processing command: {e}")
            finally:
                self.queue.task_done()
    
    def add_command(self, cmd: str, callback=None):
        self.queue.put((cmd, callback))

# Global command queue
cmd_queue = CommandQueue()

def format_value(value: float, buf: int) -> str:
    """Format a float value into a string with total length 'buf'."""
    try:
        abs_val = abs(value)
        int_part = str(int(abs_val))
        int_length = len(int_part)
        if value < 0:
            int_length += 1
        dec_places = max(0, buf - int_length - 1)
        return f"{value:.{dec_places}f}"
    except Exception:
        return str(value)

def send_command(command: str, target: str = "192.168.1.51:9000") -> str:
    """Sends a command via gRPC to the RelayService with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            with grpc.insecure_channel(target) as channel:
                client = relay_pb2_grpc.RelayServiceStub(channel)
                message = relay_pb2.Message(body=command)
                response = client.RelayData(message, timeout=5)
                return response.body
        except grpc.RpcError as e:
            if attempt == MAX_RETRIES - 1:
                return f"gRPC error: {e.code()} - {e.details()}"
            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
        except Exception as e:
            return f"Unexpected error: {str(e)}"

# --- Advanced Draggable Block with Multi-Select & Group Dragging ---
class DraggableBlock:
    def __init__(self, canvas: tk.Canvas, x: int, y: int, app):
        self.canvas = canvas
        self.app = app
        self.frame = tk.Frame(canvas, bd=2, relief="raised", bg="lightgray")
        self.win = self.canvas.create_window(x, y, window=self.frame, anchor="nw")
        
        # Bind events
        for widget in [self.win, self.frame]:
            widget.bind("<ButtonPress-1>", self.on_click)
            widget.bind("<B1-Motion>", self.on_drag)
            widget.bind("<ButtonRelease-1>", self.on_release)
            widget.bind("<Button-3>", self.show_context_menu)

    def _get_canvas_coords(self, event) -> Tuple[int, int]:
        return (
            event.x_root - self.canvas.winfo_rootx() + self.canvas.canvasx(0),
            event.y_root - self.canvas.winfo_rooty() + self.canvas.canvasy(0)
        )

    def on_click(self, event):
        canvas_x, canvas_y = self._get_canvas_coords(event)
        if self in self.app.selected_blocks:
            self.app.group_drag_start_mouse = (canvas_x, canvas_y)
            self.app.group_drag_start_positions = {b: b.get_position() for b in self.app.selected_blocks}
        else:
            self.app.clear_selection()
            self.canvas.tag_raise(self.win)
            self.start_x, self.start_y = self.canvas.coords(self.win)
            self.offset_x = canvas_x - self.start_x
            self.offset_y = canvas_y - self.start_y

    def on_drag(self, event):
        canvas_x, canvas_y = self._get_canvas_coords(event)
        if self in self.app.selected_blocks and self.app.group_drag_start_mouse:
            dx = canvas_x - self.app.group_drag_start_mouse[0]
            dy = canvas_y - self.app.group_drag_start_mouse[1]
            for b, pos in self.app.group_drag_start_positions.items():
                new_x = pos[0] + dx
                new_y = pos[1] + dy
                self.canvas.coords(b.win, new_x, new_y)
        else:
            new_x = canvas_x - self.offset_x
            new_y = canvas_y - self.offset_y
            self.canvas.coords(self.win, new_x, new_y)

    def on_release(self, event):
        if self in self.app.selected_blocks:
            self.app.group_drag_start_mouse = None
            self.app.group_drag_start_positions = {}
        self.app.update_canvas_bounds()

    def show_context_menu(self, event):
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="Delete", command=self.delete_block)
        menu.tk_popup(event.x_root, event.y_root)

    def delete_block(self):
        if self in self.app.selected_blocks:
            self.app.delete_selected_by_context_menu()
        else:
            self.app.clear_selection()
            self.app.delete_block_single(self)

    def get_position(self) -> Tuple[int, int]:
        return self.canvas.coords(self.win)

    def destroy(self):
        self.canvas.delete(self.win)
        self.frame.destroy()

# --- Valve Block (with networking commands) ---
class ValveBlock(DraggableBlock):
    def __init__(self, canvas: tk.Canvas, x: int, y: int, app, config: DeviceConfig):
        super().__init__(canvas, x, y, app)
        self.type = "valve"
        self.state = config.state
        self.frame.config(bg="lightblue")
        
        # Create header
        self.header = tk.Label(self.frame, text="Valve", bg="lightblue", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        self.header.bind("<ButtonPress-1>", self.on_click)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.on_release)
        self.header.bind("<Button-3>", self.show_context_menu)
        
        # Create entries
        self.port_entry = self._create_entry("Port:", config.port, 1)
        self.name_entry = self._create_entry("Name:", config.name, 2)
        self.input_voltage_entry = self._create_entry("Input Voltage:", str(config.input_voltage), 3)
        
        # Create toggle button
        self.toggle_button = tk.Button(
            self.frame, text="Off", width=8,
            command=self.toggle_state, bg="red", fg="white"
        )
        self.toggle_button.grid(row=4, column=0, columnspan=2, pady=(4,2))
        if self.state:
            self.toggle_button.config(text="On", bg="green")

    def _create_entry(self, label_text: str, default_value: str, row: int) -> tk.Entry:
        tk.Label(self.frame, text=label_text, bg="lightblue").grid(row=row, column=0, sticky="e")
        entry = tk.Entry(self.frame, width=10)
        entry.grid(row=row, column=1, padx=(2,4), pady=2)
        entry.insert(0, default_value)
        return entry

    def toggle_state(self):
        self.state = not self.state
        state_str = "1" if self.state else "0"
        self.toggle_button.config(
            text="On" if self.state else "Off",
            bg="green" if self.state else "red"
        )
        
        try:
            voltage = float(self.input_voltage_entry.get().strip())
        except ValueError:
            voltage = 0.0
            
        voltage_str = format_value(voltage, BUFFERVALVE + 1)
        port = self.port_entry.get().strip()
        cmd = f"w{port}{state_str}{voltage_str}"
        
        cmd_queue.add_command(cmd)

    def get_data(self) -> dict:
        pos = self.get_position()
        return {
            "type": self.type,
            "x": pos[0],
            "y": pos[1],
            "port": self.port_entry.get(),
            "name": self.name_entry.get(),
            "state": self.state,
            "input_voltage": float(self.input_voltage_entry.get() or 0.0)
        }

    def get_command(self) -> str:
        port = self.port_entry.get().strip()
        state_str = "1" if self.state else "0"
        try:
            voltage = float(self.input_voltage_entry.get().strip())
        except ValueError:
            voltage = 0.0
        voltage_str = format_value(voltage, BUFFERVALVE + 1)
        return f"v{port}{state_str}{voltage_str}"

    def get_query_command(self) -> str:
        return f"qv{self.port_entry.get().strip()}"

    def update_from_response(self, response: str):
        try:
            if not response.startswith("v"):
                return
            resp_port = response[1:5]
            if resp_port == self.port_entry.get().strip():
                self.state = (response[5] == "1")
                self.toggle_button.config(
                    text="On" if self.state else "Off",
                    bg="green" if self.state else "red"
                )
                self.input_voltage_entry.delete(0, tk.END)
                self.input_voltage_entry.insert(0, response[6:6 + (BUFFERVALVE + 1)])
        except Exception as e:
            print(f"Error updating ValveBlock: {e}")

# --- Sensor Block (with networking commands) ---
class SensorBlock(DraggableBlock):
    def __init__(self, canvas: tk.Canvas, x: int, y: int, app, config: DeviceConfig):
        super().__init__(canvas, x, y, app)
        self.type = "sensor"
        self.frame.config(bg="lightgreen")
        
        # Create header
        self.header = tk.Label(self.frame, text="Sensor", bg="lightgreen", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        self.header.bind("<ButtonPress-1>", self.on_click)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.on_release)
        self.header.bind("<Button-3>", self.show_context_menu)
        
        # Create entries
        self.port_entry = self._create_entry("Port:", config.port, 1)
        self.name_entry = self._create_entry("Name:", config.name, 2)
        
        # Create value display
        self.value_var = tk.DoubleVar(value=config.value)
        self.value_label = tk.Label(self.frame, textvariable=self.value_var, bg="white", width=8)
        self.value_label.grid(row=3, column=1, padx=(2,4), pady=2)
        
        # Create range entries
        self.min_val_entry = self._create_entry("Min Reading:", str(config.min_val), 4)
        self.max_val_entry = self._create_entry("Max Reading:", str(config.max_val), 5)
        self.min_voltage_entry = self._create_entry("Min Voltage:", str(config.min_voltage), 6)
        self.max_voltage_entry = self._create_entry("Max Voltage:", str(config.max_voltage), 7)

    def _create_entry(self, label_text: str, default_value: str, row: int) -> tk.Entry:
        tk.Label(self.frame, text=label_text, bg="lightgreen").grid(row=row, column=0, sticky="e")
        entry = tk.Entry(self.frame, width=10)
        entry.grid(row=row, column=1, padx=(2,4), pady=2)
        entry.insert(0, default_value)
        return entry

    def get_data(self) -> dict:
        pos = self.get_position()
        return {
            "type": self.type,
            "x": pos[0],
            "y": pos[1],
            "port": self.port_entry.get(),
            "name": self.name_entry.get(),
            "value": self.value_var.get(),
            "min_val": float(self.min_val_entry.get() or 0.0),
            "max_val": float(self.max_val_entry.get() or 100.0),
            "min_voltage": float(self.min_voltage_entry.get() or 0.0),
            "max_voltage": float(self.max_voltage_entry.get() or 5.0)
        }

    def get_command(self) -> str:
        port = self.port_entry.get().strip()
        min_vol = format_value(float(self.min_voltage_entry.get() or 0.0), BUFFERSENSOR)
        max_vol = format_value(float(self.max_voltage_entry.get() or 5.0), BUFFERSENSOR)
        min_reading = format_value(float(self.min_val_entry.get() or 0.0), BUFFERSENSOR)
        max_reading = format_value(float(self.max_val_entry.get() or 100.0), BUFFERSENSOR)
        return f"s{port}{min_vol}{max_vol}{min_reading}{max_reading}"

    def get_query_command(self) -> str:
        return f"qs{self.port_entry.get().strip()}"

    def update_from_response(self, response: str):
        try:
            if not response.startswith("s"):
                return
            resp_port = response[1:5]
            if resp_port == self.port_entry.get().strip():
                value = float(response[5:5 + BUFFERSENSOR])
                self.value_var.set(value)
        except Exception as e:
            print(f"Error updating SensorBlock: {e}")

# --- Group Container Block ---
class GroupBlock:
    def __init__(self, canvas: tk.Canvas, x: int, y: int, width: int = 200, height: int = 200, name: str = "Group"):
        self.canvas = canvas
        self.rect = canvas.create_rectangle(x, y, x + width, y + height, fill="", outline="blue", width=2)
        self.name = name
        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.start_x = x
        self.start_y = y

    def on_click(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def on_drag(self, event):
        dx = self.canvas.canvasx(event.x) - self.start_x
        dy = self.canvas.canvasy(event.y) - self.start_y
        self.canvas.move(self.rect, dx, dy)
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def get_data(self) -> dict:
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        return {
            "type": "group",
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1,
            "name": self.name
        }

    def destroy(self):
        self.canvas.delete(self.rect)

# --- Main Application ---
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Device Control Panel")
        
        # Initialize variables
        self.selected_blocks = set()
        self.group_drag_start_mouse = None
        self.group_drag_start_positions = {}
        self.refresh_running = False
        self.record_running = False
        
        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create canvas with scrollbar
        self.create_canvas()
        
        # Load saved state
        self.load_state()
        self.load_groups()
        
        # Start refresh loop
        self.toggle_refresh()

    def create_toolbar(self):
        toolbar = tk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons
        tk.Button(toolbar, text="Add Valve", command=self.add_valve).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Add Sensor", command=self.add_sensor).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Add Group", command=self.add_group).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Send All", command=self.send_all_commands).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="All Valves Off", command=self.all_valves_off).pack(side=tk.LEFT, padx=2)
        
        # Add refresh toggle
        self.refresh_button = tk.Button(toolbar, text="Stop Refresh", command=self.toggle_refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=2)
        
        # Add record toggle
        self.record_button = tk.Button(toolbar, text="Start Record", command=self.toggle_record)
        self.record_button.pack(side=tk.LEFT, padx=2)

    def create_canvas(self):
        # Create canvas frame
        canvas_frame = tk.Frame(self.main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        y_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = tk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure canvas
        self.canvas.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Bind events
        self.canvas.bind("<Configure>", self.update_canvas_bounds)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self.canvas_left_press)
        self.canvas.bind("<B1-Motion>", self.canvas_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_left_release)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_canvas_bounds(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def extend_page(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_valve(self, x: int = 50, y: int = 50):
        if len(self.selected_blocks) >= MAX_DEVICES:
            messagebox.showwarning("Warning", "Maximum number of devices reached!")
            return
            
        config = DeviceConfig(port="", name="")
        valve = ValveBlock(self.canvas, x, y, self, config)
        self.selected_blocks.add(valve)
        self.update_canvas_bounds()

    def add_sensor(self, x: int = 200, y: int = 50):
        if len(self.selected_blocks) >= MAX_DEVICES:
            messagebox.showwarning("Warning", "Maximum number of devices reached!")
            return
            
        config = DeviceConfig(port="", name="")
        sensor = SensorBlock(self.canvas, x, y, self, config)
        self.selected_blocks.add(sensor)
        self.update_canvas_bounds()

    def add_group(self):
        group = GroupBlock(self.canvas, 50, 50)
        self.selected_blocks.add(group)
        self.update_canvas_bounds()

    def delete_block_single(self, block):
        if block in self.selected_blocks:
            self.selected_blocks.remove(block)
        block.destroy()
        self.update_canvas_bounds()

    def delete_selected_by_context_menu(self):
        for block in list(self.selected_blocks):
            block.destroy()
        self.selected_blocks.clear()
        self.update_canvas_bounds()

    def clear_selection(self):
        self.selected_blocks.clear()

    def canvas_left_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicked on a block
        clicked_block = None
        for block in self.selected_blocks:
            if isinstance(block, (ValveBlock, SensorBlock)):
                if block.frame.winfo_containing(event.x_root, event.y_root):
                    clicked_block = block
                    break
        
        if not clicked_block:
            self.clear_selection()

    def canvas_left_drag(self, event):
        pass

    def canvas_left_release(self, event):
        pass

    def save_state(self):
        state = {
            "blocks": [block.get_data() for block in self.selected_blocks]
        }
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save state: {e}")

    def load_state(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r") as f:
                    state = json.load(f)
                    for block_data in state.get("blocks", []):
                        if block_data["type"] == "valve":
                            config = DeviceConfig(
                                port=block_data.get("port", ""),
                                name=block_data.get("name", ""),
                                state=block_data.get("state", False),
                                input_voltage=block_data.get("input_voltage", 0.0)
                            )
                            self.add_valve(block_data["x"], block_data["y"])
                        elif block_data["type"] == "sensor":
                            config = DeviceConfig(
                                port=block_data.get("port", ""),
                                name=block_data.get("name", ""),
                                value=block_data.get("value", 0.0),
                                min_val=block_data.get("min_val", 0.0),
                                max_val=block_data.get("max_val", 100.0),
                                min_voltage=block_data.get("min_voltage", 0.0),
                                max_voltage=block_data.get("max_voltage", 5.0)
                            )
                            self.add_sensor(block_data["x"], block_data["y"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load state: {e}")

    def load_groups(self):
        try:
            if os.path.exists(GROUPS_FILE):
                with open(GROUPS_FILE, "r") as f:
                    groups = json.load(f)
                    for group_data in groups:
                        group = GroupBlock(
                            self.canvas,
                            group_data["x"],
                            group_data["y"],
                            group_data["width"],
                            group_data["height"],
                            group_data["name"]
                        )
                        self.selected_blocks.add(group)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load groups: {e}")

    def send_all_commands(self):
        for block in self.selected_blocks:
            if isinstance(block, (ValveBlock, SensorBlock)):
                cmd = block.get_command()
                cmd_queue.add_command(cmd)

    def all_valves_off(self):
        for block in self.selected_blocks:
            if isinstance(block, ValveBlock):
                block.state = False
                block.toggle_button.config(text="Off", bg="red")
                port = block.port_entry.get().strip()
                cmd = f"w{port}00.000"
                cmd_queue.add_command(cmd)

    def toggle_refresh(self):
        self.refresh_running = not self.refresh_running
        self.refresh_button.config(text="Stop Refresh" if self.refresh_running else "Start Refresh")
        if self.refresh_running:
            self.refresh_loop()

    def refresh_loop(self):
        if not self.refresh_running:
            return
            
        for block in self.selected_blocks:
            if isinstance(block, (ValveBlock, SensorBlock)):
                cmd = block.get_query_command()
                cmd_queue.add_command(cmd, block.update_from_response)
        
        self.root.after(int(REFRESH_INTERVAL * 1000), self.refresh_loop)

    def toggle_record(self):
        self.record_running = not self.record_running
        self.record_button.config(text="Stop Record" if self.record_running else "Start Record")
        # Add recording functionality here if needed

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
