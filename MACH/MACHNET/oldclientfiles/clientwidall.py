import tkinter as tk
from tkinter import messagebox, simpledialog
import json, os, grpc, concurrent.futures
import relay_pb2
import relay_pb2_grpc

SAVE_FILE = "gui_state.json"
GROUPS_FILE = "groups_state.json"
BUFFERSENSOR = 7  # For sensors, numeric fields will be formatted to BUFFERSENSOR characters.
BUFFERVALVE = 7 - 1  # For valves, numeric fields will be formatted to BUFFERVALVE+1 characters.

def format_value(value, buf):
    """
    Format a float value into a string with total length 'buf' (including the decimal point).
    """
    try:
        abs_val = abs(value)
        int_part = str(int(abs_val))
        int_length = len(int_part)
        if value < 0:
            int_length += 1  # include negative sign
        dec_places = buf - int_length - 1  # subtract one for the decimal point
        if dec_places < 0:
            dec_places = 0
        formatted = f"{value:.{dec_places}f}"
        return formatted
    except Exception as e:
        return str(value)

def send_command(command, target="DESKTOP-K4SS8OO:9000"):
    """
    Sends a command via gRPC to the RelayService.
    Returns the response body if successful or an error message.
    """
    print(f"Sending command: {command}")
    channel = grpc.insecure_channel(target)
    try:
        client = relay_pb2_grpc.RelayServiceStub(channel)
        message = relay_pb2.Message(body=command)
        response = client.RelayData(message, timeout=5)
        print(f"Response received: {response.body}")
        return response.body
    except grpc.RpcError as e:
        error_message = f"gRPC error: {e.code()} - {e.details()}"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        return error_message
    finally:
        channel.close()

# --- Advanced Draggable Block with Multi-Select & Group Dragging ---
class DraggableBlock:
    def __init__(self, canvas, x, y, app):
        self.canvas = canvas
        self.app = app
        self.frame = tk.Frame(canvas, bd=2, relief="raised", bg="lightgray")
        self.win = self.canvas.create_window(x, y, window=self.frame, anchor="nw")
        self.canvas.tag_bind(self.win, "<ButtonPress-1>", self.on_click)
        self.canvas.tag_bind(self.win, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.win, "<ButtonRelease-1>", self.on_release)
        self.frame.bind("<ButtonPress-1>", self.on_click)
        self.frame.bind("<B1-Motion>", self.on_drag)
        self.frame.bind("<ButtonRelease-1>", self.on_release)
        self.frame.bind("<Button-3>", self.show_context_menu)
        self.canvas.tag_bind(self.win, "<Button-3>", self.show_context_menu)

    def _get_canvas_coords(self, event):
        return (event.x_root - self.canvas.winfo_rootx() + self.canvas.canvasx(0),
                event.y_root - self.canvas.winfo_rooty() + self.canvas.canvasy(0))

    def on_click(self, event):
        canvas_x, canvas_y = self._get_canvas_coords(event)
        # If already selected, prepare group-drag data.
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

    def get_position(self):
        return self.canvas.coords(self.win)

    def destroy(self):
        self.canvas.delete(self.win)
        self.frame.destroy()

# --- Valve Block (with networking commands) ---
class ValveBlock(DraggableBlock):
    def __init__(self, canvas, x, y, app, port="", name="", state=False, input_voltage=0.0):
        super().__init__(canvas, x, y, app)
        self.type = "valve"
        self.state = state
        self.frame.config(bg="lightblue")
        self.header = tk.Label(self.frame, text="Valve", bg="lightblue", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        self.header.bind("<ButtonPress-1>", self.on_click)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.on_release)
        self.header.bind("<Button-3>", self.show_context_menu)
        
        tk.Label(self.frame, text="Port:", bg="lightblue").grid(row=1, column=0, sticky="e")
        self.port_entry = tk.Entry(self.frame, width=10)
        self.port_entry.grid(row=1, column=1, padx=(2,4), pady=2)
        self.port_entry.insert(0, port)
        
        tk.Label(self.frame, text="Name:", bg="lightblue").grid(row=2, column=0, sticky="e")
        self.name_entry = tk.Entry(self.frame, width=10)
        self.name_entry.grid(row=2, column=1, padx=(2,4), pady=2)
        self.name_entry.insert(0, name)
        
        tk.Label(self.frame, text="Input Voltage:", bg="lightblue").grid(row=3, column=0, sticky="e")
        self.input_voltage_entry = tk.Entry(self.frame, width=10)
        self.input_voltage_entry.grid(row=3, column=1, padx=(2,4), pady=2)
        self.input_voltage_entry.insert(0, str(input_voltage))
        
        self.toggle_button = tk.Button(self.frame, text="Off", width=8,
                                       command=self.toggle_state, bg="red", fg="white")
        self.toggle_button.grid(row=4, column=0, columnspan=2, pady=(4,2))
        if self.state:
            self.toggle_button.config(text="On", bg="green")
    
    def toggle_state(self):
        # Toggle state and send command via gRPC.
        self.state = not self.state
        state_str = "1" if self.state else "0"
        if self.state:
            self.toggle_button.config(text="On", bg="green")
        else:
            self.toggle_button.config(text="Off", bg="red")
        port = self.port_entry.get().strip()
        try:
            voltage = float(self.input_voltage_entry.get().strip())
        except ValueError:
            voltage = 0.0
        voltage_str = format_value(voltage, BUFFERVALVE + 1)
        cmd = f"w{port}{state_str}{voltage_str}"
        response = send_command(cmd)
        print(f"Toggle command sent: {cmd}\nResponse: {response}")
    
    def get_data(self):
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
    
    def get_command(self):
        port = self.port_entry.get().strip()
        state_str = "1" if self.state else "0"
        try:
            voltage = float(self.input_voltage_entry.get().strip())
        except ValueError:
            voltage = 0.0
        voltage_str = format_value(voltage, BUFFERVALVE + 1)
        return f"v{port}{state_str}{voltage_str}"
    
    def get_query_command(self):
        port = self.port_entry.get().strip()
        return f"qv{port}"
    
    def update_from_response(self, response):
        try:
            if not response.startswith("v"):
                return
            resp_port = response[1:5]  # assume 4-char port
            new_state = response[5]
            new_voltage = response[6:6 + (BUFFERVALVE + 1)]
            if resp_port == self.port_entry.get().strip():
                self.state = (new_state == "1")
                self.toggle_button.config(text="On" if self.state else "Off",
                                          bg="green" if self.state else "red")
                self.input_voltage_entry.delete(0, tk.END)
                self.input_voltage_entry.insert(0, new_voltage)
        except Exception as e:
            print("Error updating ValveBlock:", e)

# --- Sensor Block (with networking commands) ---
class SensorBlock(DraggableBlock):
    def __init__(self, canvas, x, y, app, port="", name="", value=0.0,
                 min_val=0.0, max_val=100.0, min_voltage=0.0, max_voltage=5.0):
        super().__init__(canvas, x, y, app)
        self.type = "sensor"
        self.frame.config(bg="lightgreen")
        self.header = tk.Label(self.frame, text="Sensor", bg="lightgreen", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        self.header.bind("<ButtonPress-1>", self.on_click)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.on_release)
        self.header.bind("<Button-3>", self.show_context_menu)
        
        tk.Label(self.frame, text="Port:", bg="lightgreen").grid(row=1, column=0, sticky="e")
        self.port_entry = tk.Entry(self.frame, width=10)
        self.port_entry.grid(row=1, column=1, padx=(2,4), pady=2)
        self.port_entry.insert(0, port)
        
        tk.Label(self.frame, text="Name:", bg="lightgreen").grid(row=2, column=0, sticky="e")
        self.name_entry = tk.Entry(self.frame, width=10)
        self.name_entry.grid(row=2, column=1, padx=(2,4), pady=2)
        self.name_entry.insert(0, name)
        
        tk.Label(self.frame, text="Value:", bg="lightgreen").grid(row=3, column=0, sticky="e")
        self.value_var = tk.DoubleVar(value=value)
        self.value_label = tk.Label(self.frame, textvariable=self.value_var, bg="white", width=8)
        self.value_label.grid(row=3, column=1, padx=(2,4), pady=2)
        
        tk.Label(self.frame, text="Min Reading:", bg="lightgreen").grid(row=4, column=0, sticky="e")
        self.min_entry = tk.Entry(self.frame, width=10)
        self.min_entry.grid(row=4, column=1, padx=(2,4), pady=2)
        self.min_entry.insert(0, str(min_val))
        
        tk.Label(self.frame, text="Max Reading:", bg="lightgreen").grid(row=5, column=0, sticky="e")
        self.max_entry = tk.Entry(self.frame, width=10)
        self.max_entry.grid(row=5, column=1, padx=(2,4), pady=2)
        self.max_entry.insert(0, str(max_val))
        
        tk.Label(self.frame, text="Min Voltage:", bg="lightgreen").grid(row=6, column=0, sticky="e")
        self.min_v_entry = tk.Entry(self.frame, width=10)
        self.min_v_entry.grid(row=6, column=1, padx=(2,4), pady=2)
        self.min_v_entry.insert(0, str(min_voltage))
        
        tk.Label(self.frame, text="Max Voltage:", bg="lightgreen").grid(row=7, column=0, sticky="e")
        self.max_v_entry = tk.Entry(self.frame, width=10)
        self.max_v_entry.grid(row=7, column=1, padx=(2,4), pady=2)
        self.max_v_entry.insert(0, str(max_voltage))
    
    def get_data(self):
        pos = self.get_position()
        return {
            "type": self.type,
            "x": pos[0],
            "y": pos[1],
            "port": self.port_entry.get(),
            "name": self.name_entry.get(),
            "value": self.value_var.get(),
            "min": float(self.min_entry.get() or 0.0),
            "max": float(self.max_entry.get() or 0.0),
            "min_voltage": float(self.min_v_entry.get() or 0.0),
            "max_voltage": float(self.max_v_entry.get() or 0.0)
        }
    
    def get_command(self):
        """
        Build the sensor configuration command.
        Format: s{port}{min_voltage}{max_voltage}{min_reading}{max_reading}
        with each numeric field formatted to exactly BUFFERSENSOR characters.
        """
        port = self.port_entry.get().strip()
        try:
            min_voltage = float(self.min_v_entry.get() or 0.0)
            max_voltage = float(self.max_v_entry.get() or 0.0)
            min_reading = float(self.min_entry.get() or 0.0)
            max_reading = float(self.max_entry.get() or 0.0)
        except ValueError:
            min_voltage = max_voltage = min_reading = max_reading = 0.0
        min_voltage_str = format_value(min_voltage, BUFFERSENSOR)
        max_voltage_str = format_value(max_voltage, BUFFERSENSOR)
        min_reading_str = format_value(min_reading, BUFFERSENSOR)
        max_reading_str = format_value(max_reading, BUFFERSENSOR)
        return f"s{port}{min_voltage_str}{max_voltage_str}{min_reading_str}{max_reading_str}"
    
    def get_query_command(self):
        port = self.port_entry.get().strip()
        return f"s{port}"
    
    def update_from_response(self, response):
        try:
            if response.startswith("rs") and len(response) >= (2 + 4 + 5 * BUFFERSENSOR):
                resp_port = response[2:6]
                new_value = response[6:6 + BUFFERSENSOR]
                new_min_voltage = response[6 + BUFFERSENSOR:6 + 2 * BUFFERSENSOR]
                new_max_voltage = response[6 + 2 * BUFFERSENSOR:6 + 3 * BUFFERSENSOR]
                new_min_reading = response[6 + 3 * BUFFERSENSOR:6 + 4 * BUFFERSENSOR]
                new_max_reading = response[6 + 4 * BUFFERSENSOR:6 + 5 * BUFFERSENSOR]
                if resp_port == self.port_entry.get().strip():
                    self.value_var.set(float(new_value))
                    self.min_v_entry.delete(0, tk.END)
                    self.min_v_entry.insert(0, new_min_voltage)
                    self.max_v_entry.delete(0, tk.END)
                    self.max_v_entry.insert(0, new_max_voltage)
                    self.min_entry.delete(0, tk.END)
                    self.min_entry.insert(0, new_min_reading)
                    self.max_entry.delete(0, tk.END)
                    self.max_entry.insert(0, new_max_reading)
            elif response.startswith("s") and not response.startswith("rs") and len(response) >= (1 + 4 + BUFFERSENSOR):
                resp_port = response[1:5]
                new_value = response[5:5 + BUFFERSENSOR]
                if resp_port == self.port_entry.get().strip():
                    self.value_var.set(float(new_value))
        except Exception as e:
            print("Error updating SensorBlock:", e)

# --- Group Container Block ---
class GroupBlock:
    def __init__(self, canvas, x, y, width=200, height=200, name="Group"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.rect = self.canvas.create_rectangle(x, y, x+width, y+height,
                                                   dash=(4, 2), outline="purple", width=2)
        self.label = self.canvas.create_text(x+10, y+10, anchor="nw", text=name, fill="purple")
        self.resize_handle = self.canvas.create_rectangle(x+width-10, y+height-10, x+width, y+height, fill="purple")
        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<ButtonPress-1>", self.on_click)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.resize_handle, "<ButtonPress-1>", self.on_resize_start)
        self.canvas.tag_bind(self.resize_handle, "<B1-Motion>", self.on_resizing)
        self.drag_data = {"x": 0, "y": 0}
        self.resize_data = {"x": 0, "y": 0, "width": width, "height": height}

    def on_click(self, event):
        self.drag_data["x"] = event.x - self.x
        self.drag_data["y"] = event.y - self.y

    def on_drag(self, event):
        new_x = event.x - self.drag_data["x"]
        new_y = event.y - self.drag_data["y"]
        dx = new_x - self.x
        dy = new_y - self.y
        self.x = new_x
        self.y = new_y
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.label, dx, dy)
        self.canvas.move(self.resize_handle, dx, dy)
        self.canvas.master.update_idletasks()
        self.canvas.master.event_generate("<<CanvasExtended>>")

    def on_resize_start(self, event):
        self.resize_data["x"] = event.x
        self.resize_data["y"] = event.y
        self.resize_data["width"] = self.width
        self.resize_data["height"] = self.height

    def on_resizing(self, event):
        dx = event.x - self.resize_data["x"]
        dy = event.y - self.resize_data["y"]
        new_width = max(50, self.resize_data["width"] + dx)
        new_height = max(50, self.resize_data["height"] + dy)
        self.width = new_width
        self.height = new_height
        self.canvas.coords(self.rect, self.x, self.y, self.x+self.width, self.y+self.height)
        self.canvas.coords(self.resize_handle,
                           self.x+self.width-10, self.y+self.height-10,
                           self.x+self.width, self.y+self.height)
        self.canvas.master.update_idletasks()
        self.canvas.master.event_generate("<<CanvasExtended>>")

    def get_data(self):
        return {"name": self.name, "x": self.x, "y": self.y,
                "width": self.width, "height": self.height}

    def destroy(self):
        self.canvas.delete(self.rect)
        self.canvas.delete(self.label)
        self.canvas.delete(self.resize_handle)

# --- Main Application ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("GUI Demo")
        self.canvas_width = 800
        self.canvas_height = 600
        self.blocks = []    # Sensor and valve blocks.
        self.groups = []    # Group containers.
        self.selected_blocks = []
        self.group_drag_start_mouse = None
        self.group_drag_start_positions = {}

        # Menu bar with Groups menu.
        self.menu_bar = tk.Menu(root)
        self.groups_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Groups", menu=self.groups_menu)
        root.config(menu=self.menu_bar)

        # Control panel.
        ctrl = tk.Frame(root)
        ctrl.pack(side="top", fill="x", padx=5, pady=5)
        tk.Button(ctrl, text="Add Valve", command=self.add_valve).pack(side="left", padx=2)
        tk.Button(ctrl, text="Add Sensor", command=self.add_sensor).pack(side="left", padx=2)
        tk.Button(ctrl, text="Add Group", command=self.add_group).pack(side="left", padx=2)
        tk.Button(ctrl, text="Extend Page", command=self.extend_page).pack(side="left", padx=2)
        tk.Button(ctrl, text="Delete Selected", command=self.delete_selected_by_context_menu).pack(side="left", padx=2)
        tk.Button(ctrl, text="Save", command=self.save_state).pack(side="left", padx=2)
        tk.Button(ctrl, text="Reset", command=self.reset_state).pack(side="left", padx=2)
        tk.Button(ctrl, text="Send Commands", command=self.send_all_commands).pack(side="left", padx=2)
        tk.Button(ctrl, text="Read", command=self.read_sensors).pack(side="left", padx=2)
        self.refresh_button = tk.Button(ctrl, text="Refresh", command=self.toggle_refresh)
        self.refresh_button.pack(side="left", padx=2)
        self.recording = False
        self.record_button = tk.Button(ctrl, text="Start Rec", command=self.toggle_record)
        self.record_button.pack(side="left", padx=2)

        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)  # Linux scroll up.
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)  # Linux scroll down.
        self.canvas.bind("<ButtonPress-1>", self.canvas_left_press)
        self.canvas.bind("<B1-Motion>", self.canvas_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_left_release)
        self.canvas.bind("<<CanvasExtended>>", lambda e: self.update_canvas_bounds())

        # Networking: persistent thread pool for refresh tasks.
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.refresh_running = False

        if os.path.exists(SAVE_FILE):
            self.load_state()
        if os.path.exists(GROUPS_FILE):
            self.load_groups()

    def on_mousewheel(self, event):
        if hasattr(event, 'delta'):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def update_canvas_bounds(self):
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
        self.canvas.config(scrollregion=(0, 0, self.canvas_width, self.canvas_height))

    def extend_page(self):
        self.canvas_height += 200
        self.update_canvas_bounds()

    def add_valve(self, port="", name="", state=False, input_voltage=0.0, x=50, y=50):
        block = ValveBlock(self.canvas, x, y, self, port, name, state, input_voltage)
        self.blocks.append(block)
        self.update_canvas_bounds()

    def add_sensor(self, port="", name="", value=0.0, x=200, y=50):
        block = SensorBlock(self.canvas, x, y, self, port, name, value)
        self.blocks.append(block)
        self.update_canvas_bounds()

    def add_group(self):
        group_name = simpledialog.askstring("Group Name", "Enter group name:")
        if not group_name:
            group_name = f"Group {len(self.groups)+1}"
        group = GroupBlock(self.canvas, 100, 100, 200, 200, name=group_name)
        self.groups.append(group)
        self.update_groups_menu()
        self.update_canvas_bounds()

    def update_groups_menu(self):
        self.groups_menu.delete(0, tk.END)
        for group in self.groups:
            self.groups_menu.add_command(label=group.name,
                                          command=lambda g=group: self.canvas.yview_moveto(g.y / float(self.canvas_height)))

    def delete_block_single(self, block):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this block?"):
            block.destroy()
            try:
                self.blocks.remove(block)
            except ValueError:
                pass

    def delete_selected_by_context_menu(self):
        if not self.selected_blocks:
            messagebox.showinfo("Delete", "No blocks selected.")
            return
        if messagebox.askyesno("Delete", "Are you sure you want to delete the selected block(s)?"):
            for block in self.selected_blocks[:]:
                block.destroy()
                try:
                    self.blocks.remove(block)
                except ValueError:
                    pass
            self.clear_selection()

    def clear_selection(self):
        for b in self.selected_blocks:
            b.frame.config(highlightthickness=0)
        self.selected_blocks = []

    def canvas_left_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        clicked_items = self.canvas.find_overlapping(x, y, x, y)
        for block in self.blocks:
            if block.win in clicked_items:
                return
        for group in self.groups:
            if group.label in clicked_items:
                return
        self.select_start_x = x
        self.select_start_y = y
        self.select_rect = self.canvas.create_rectangle(x, y, x, y,
                                                         outline="blue", dash=(2, 2))

    def canvas_left_drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if hasattr(self, "select_rect"):
            self.canvas.coords(self.select_rect, self.select_start_x, self.select_start_y, x, y)

    def canvas_left_release(self, event):
        if hasattr(self, "select_rect"):
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            x_min, x_max = sorted([self.select_start_x, x])
            y_min, y_max = sorted([self.select_start_y, y])
            self.clear_selection()
            for block in self.blocks:
                bx, by = block.get_position()
                bw = block.frame.winfo_width()
                bh = block.frame.winfo_height()
                cx = bx + bw/2
                cy = by + bh/2
                if x_min <= cx <= x_max and y_min <= cy <= y_max:
                    self.selected_blocks.append(block)
                    block.frame.config(highlightthickness=2, highlightbackground="red")
            self.canvas.delete(self.select_rect)
            del self.select_rect
            self.update_canvas_bounds()

    def save_state(self):
        # Save blocks to SAVE_FILE.
        blocks_data = [block.get_data() for block in self.blocks]
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(blocks_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving blocks: {e}")
        # Save canvas bounds and groups to GROUPS_FILE.
        groups_data = {
            "canvas": {"width": self.canvas_width, "height": self.canvas_height},
            "groups": [group.get_data() for group in self.groups]
        }
        try:
            with open(GROUPS_FILE, "w") as f:
                json.dump(groups_data, f, indent=4)
            messagebox.showinfo("Save", "State saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving groups: {e}")

    def load_state(self):
        try:
            with open(SAVE_FILE, "r") as f:
                blocks_data = json.load(f)
            for block in self.blocks:
                block.destroy()
            self.blocks.clear()
            for item in blocks_data:
                x = item.get("x", 50)
                y = item.get("y", 50)
                if item.get("type") == "valve":
                    self.add_valve(item.get("port", ""), item.get("name", ""),
                                   item.get("state", False),
                                   item.get("input_voltage", 0.0), x, y)
                elif item.get("type") == "sensor":
                    self.add_sensor(item.get("port", ""), item.get("name", ""),
                                    item.get("value", 0.0), x, y)
            messagebox.showinfo("Load", "Blocks loaded successfully!")
            self.update_canvas_bounds()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading blocks: {e}")

    def load_groups(self):
        try:
            with open(GROUPS_FILE, "r") as f:
                groups_data = json.load(f)
            canvas_state = groups_data.get("canvas", {})
            self.canvas_width = canvas_state.get("width", self.canvas_width)
            self.canvas_height = canvas_state.get("height", self.canvas_height)
            self.update_canvas_bounds()
            for grp in groups_data.get("groups", []):
                group = GroupBlock(
                    self.canvas,
                    grp.get("x", 100),
                    grp.get("y", 100),
                    grp.get("width", 200),
                    grp.get("height", 200),
                    grp.get("name", "Group")
                )
                self.groups.append(group)
            self.update_groups_menu()
            messagebox.showinfo("Load", "Groups loaded successfully!")
            self.update_canvas_bounds()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading groups: {e}")

    def reset_state(self):
        if messagebox.askyesno("Reset", "Are you sure you want to reset?"):
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            if os.path.exists(GROUPS_FILE):
                os.remove(GROUPS_FILE)
            for block in self.blocks:
                block.destroy()
            self.blocks.clear()
            for group in self.groups:
                group.destroy()
            self.groups.clear()
            self.update_groups_menu()
            self.canvas_width = 800
            self.canvas_height = 600
            self.update_canvas_bounds()

    def send_all_commands(self):
        responses = []
        for block in self.blocks:
            if hasattr(block, "get_command"):
                command = block.get_command()
                if not command.startswith("w"):
                    command = "m" + command
                response = send_command(command)
                print(f"Send Commands - Block type: {block.type}, Command: {command}")
                print(f"Response: {response}\n")
                responses.append(f"Sent: {command}\nResponse: {response}")
                if hasattr(block, "update_from_response"):
                    block.update_from_response(response)
        if responses:
            messagebox.showinfo("Command Responses", "\n\n".join(responses))
        else:
            messagebox.showinfo("Info", "No commands to send.")

    def read_sensors(self):
        responses = []
        for block in self.blocks:
            if block.type == "sensor":
                command = "r" + block.get_command()
                response = send_command(command)
                print(f"Read - Sensor Block, Command: {command}")
                print(f"Response: {response}\n")
                responses.append(f"Sent: {command}\nResponse: {response}")
                if hasattr(block, "update_from_response"):
                    block.update_from_response(response)
        if responses:
            messagebox.showinfo("Read Responses", "\n\n".join(responses))
        else:
            messagebox.showinfo("Info", "No sensor commands sent.")

    def toggle_refresh(self):
        if not self.refresh_running:
            self.refresh_running = True
            self.refresh_button.config(text="Stop Refresh")
            self.refresh_loop()
        else:
            self.refresh_running = False
            self.refresh_button.config(text="Refresh")

    def refresh_loop(self):
        if not self.refresh_running:
            return
        sensor_blocks = [block for block in self.blocks if block.type == "sensor"]
        for block in sensor_blocks:
            future = self.executor.submit(send_command, "r" + block.get_command())
            # Attach a callback so that when the response arrives, the sensor block is updated.
            future.add_done_callback(lambda fut, b=block: self.root.after(0, b.update_from_response, fut.result() if not fut.cancelled() else ""))
        self.root.after(100, self.refresh_loop)

    def toggle_record(self):
        if not self.recording:
            response = send_command("Rec")
            print(f"Record started. Command: Rec, Response: {response}")
            self.recording = True
            self.record_button.config(text="Stop Rec")
        else:
            response = send_command("End")
            print(f"Record stopped. Command: End, Response: {response}")
            self.recording = False
            self.record_button.config(text="Start Rec")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
