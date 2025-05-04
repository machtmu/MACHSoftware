# import tkinter as tk
# from tkinter import messagebox
# import json, os
# import grpc
# import relay_pb2
# import relay_pb2_grpc

# SAVE_FILE = "gui_state.json"
# BUFFERSENSOR = 7  # For sensors, numeric fields will be formatted to BUFFERSENSOR characters.
# BUFFERVALVE = 7 - 1   # For valves, the numeric field will be formatted to BUFFERVALVE+1 characters.

# def format_value(value, buf):
#     """
#     Format a float value into a string with total length 'buf' (including the decimal point).
#     The number of decimal places is calculated as: buf - (length of integer part) - 1.
#     If the value is negative, the sign is taken into account.
#     """
#     try:
#         abs_val = abs(value)
#         int_part = str(int(abs_val))
#         int_length = len(int_part)
#         if value < 0:
#             int_length += 1  # account for negative sign
#         dec_places = buf - int_length - 1  # subtract one for the decimal point
#         if dec_places < 0:
#             dec_places = 0
#         formatted = f"{value:.{dec_places}f}"
#         return formatted
#     except Exception as e:
#         return str(value)

# def send_command(command, target="localhost:9000"):
#     """
#     Sends a command via gRPC to the RelayService.
#     Returns the response body if successful.
#     If an error occurs, returns a string describing the error.
#     """
#     print(f"Sending command: {command}")  # Log the command
#     channel = grpc.insecure_channel(target)
#     try:
#         client = relay_pb2_grpc.RelayServiceStub(channel)
#         message = relay_pb2.Message(body=command)
#         response = client.RelayData(message, timeout=5)
#         print(f"Response received: {response.body}")  # Log the response
#         return response.body
#     except grpc.RpcError as e:
#         error_message = f"gRPC error: {e.code()} - {e.details()}"
#         print(error_message)
#         return error_message
#     except Exception as e:
#         error_message = f"Unexpected error: {str(e)}"
#         print(error_message)
#         return error_message
#     finally:
#         channel.close()

# # Base draggable block for use on the canvas.
# class DraggableBlock:
#     def __init__(self, canvas, x, y, delete_callback=None):
#         self.canvas = canvas
#         self.delete_callback = delete_callback
#         self.frame = tk.Frame(canvas, bd=2, relief="raised", bg="lightgray")
#         self.win = canvas.create_window(x, y, window=self.frame, anchor="nw")
#         for event_type in ("<ButtonPress-1>", "<B1-Motion>"):
#             handler = getattr(self, "on" + event_type.replace("<", "").replace(">", "").replace("-", "_"))
#             canvas.tag_bind(self.win, event_type, handler)
#             self.frame.bind(event_type, handler)
#         self.frame.bind("<Button-3>", self.show_context_menu)
#         canvas.tag_bind(self.win, "<Button-3>", self.show_context_menu)
    
#     def onButtonPress_1(self, event):
#         self.canvas.tag_raise(self.win)
#         self.start_x, self.start_y = self.canvas.coords(self.win)
#         self.mouse_x, self.mouse_y = event.x_root, event.y_root
#     on_click = onButtonPress_1

#     def onB1_Motion(self, event):
#         dx = event.x_root - self.mouse_x
#         dy = event.y_root - self.mouse_y
#         self.canvas.coords(self.win, self.start_x + dx, self.start_y + dy)
#     on_drag = onB1_Motion

#     def show_context_menu(self, event):
#         menu = tk.Menu(self.frame, tearoff=0)
#         menu.add_command(label="Delete", command=self.delete_block)
#         menu.tk_popup(event.x_root, event.y_root)

#     def delete_block(self):
#         if self.delete_callback:
#             self.delete_callback(self)
#         else:
#             self.destroy()

#     def get_position(self):
#         return self.canvas.coords(self.win)

#     def destroy(self):
#         self.canvas.delete(self.win)
#         self.frame.destroy()

# # Valve block
# class ValveBlock(DraggableBlock):
#     def __init__(self, canvas, x, y, port="", name="", state=False, input_voltage=0.0, delete_callback=None):
#         super().__init__(canvas, x, y, delete_callback)
#         self.type = "valve"
#         self.state = state
#         self.frame.config(bg="lightblue")
#         self.header = tk.Label(self.frame, text="Valve", bg="lightblue", font=("Arial", 10, "bold"))
#         self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
#         for et in ("<ButtonPress-1>", "<B1-Motion>"):
#             self.header.bind(et, getattr(self, "on" + et.replace("<", "").replace(">", "").replace("-", "_")))
#         self.header.bind("<Button-3>", self.show_context_menu)

#         tk.Label(self.frame, text="Port:", bg="lightblue").grid(row=1, column=0, sticky="e")
#         self.port_entry = tk.Entry(self.frame, width=10)
#         self.port_entry.grid(row=1, column=1, padx=(2,4), pady=2)
#         self.port_entry.insert(0, port)

#         tk.Label(self.frame, text="Name:", bg="lightblue").grid(row=2, column=0, sticky="e")
#         self.name_entry = tk.Entry(self.frame, width=10)
#         self.name_entry.grid(row=2, column=1, padx=(2,4), pady=2)
#         self.name_entry.insert(0, name)

#         tk.Label(self.frame, text="Input Voltage:", bg="lightblue").grid(row=3, column=0, sticky="e")
#         self.input_voltage_entry = tk.Entry(self.frame, width=10)
#         self.input_voltage_entry.grid(row=3, column=1, padx=(2,4), pady=2)
#         self.input_voltage_entry.insert(0, str(input_voltage))

#         self.toggle_button = tk.Button(self.frame, text="Off", width=8,
#                                        command=self.toggle_state, bg="red", fg="white")
#         self.toggle_button.grid(row=4, column=0, columnspan=2, pady=(4,2))
#         if self.state:
#             self.toggle_button.config(text="On", bg="green")

#     def toggle_state(self):
#         # When toggled, send a "w" command to update valve state.
#         self.state = not self.state
#         state_str = "1" if self.state else "0"
#         if self.state:
#             self.toggle_button.config(text="On", bg="green")
#         else:
#             self.toggle_button.config(text="Off", bg="red")
#         port = self.port_entry.get().strip()
#         try:
#             voltage = float(self.input_voltage_entry.get().strip())
#         except ValueError:
#             voltage = 0.0
#         # Format voltage using BUFFERVALVE+1 digits.
#         voltage_str = format_value(voltage, BUFFERVALVE + 1)
#         cmd = f"w{port}{state_str}{voltage_str}"
#         response = send_command(cmd)
#         print(f"Toggle command sent: {cmd}\nResponse: {response}")

#     def get_data(self):
#         pos = self.get_position()
#         return {"type": self.type,
#                 "x": pos[0],
#                 "y": pos[1],
#                 "port": self.port_entry.get(),
#                 "name": self.name_entry.get(),
#                 "state": self.state,
#                 "input_voltage": float(self.input_voltage_entry.get() or 0.0)}

#     def get_command(self):
#         port = self.port_entry.get().strip()
#         state_str = "1" if self.state else "0"
#         try:
#             voltage = float(self.input_voltage_entry.get().strip())
#         except ValueError:
#             voltage = 0.0
#         # For valve commands, format voltage using BUFFERVALVE+1 digits.
#         voltage_str = format_value(voltage, BUFFERVALVE + 1)
#         return f"v{port}{state_str}{voltage_str}"
    
#     def get_query_command(self):
#         port = self.port_entry.get().strip()
#         return f"qv{port}"

#     def update_from_response(self, response):
#         # Expect valve response in the format: v{port}{state}{voltage} (voltage: BUFFERVALVE+1 digits)
#         try:
#             if not response.startswith("v"):
#                 return
#             resp_port = response[1:5]  # assume port is 4 characters
#             new_state = response[5]    # 1 character for state
#             new_voltage = response[6:6 + (BUFFERVALVE + 1)]  # next BUFFERVALVE+1 characters
#             if resp_port == self.port_entry.get().strip():
#                 self.state = (new_state == "1")
#                 self.toggle_button.config(text="On" if self.state else "Off",
#                                             bg="green" if self.state else "red")
#                 self.input_voltage_entry.delete(0, tk.END)
#                 self.input_voltage_entry.insert(0, new_voltage)
#         except Exception as e:
#             print("Error updating ValveBlock:", e)

# # Sensor block
# class SensorBlock(DraggableBlock):
#     def __init__(self, canvas, x, y, port="", name="", value=0.0,
#                  min_val=0.0, max_val=100.0, min_voltage=0.0, max_voltage=5.0,
#                  delete_callback=None):
#         super().__init__(canvas, x, y, delete_callback)
#         self.type = "sensor"
#         self.frame.config(bg="lightgreen")
#         self.header = tk.Label(self.frame, text="Sensor", bg="lightgreen", font=("Arial", 10, "bold"))
#         self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
#         for et in ("<ButtonPress-1>", "<B1-Motion>"):
#             self.header.bind(et, getattr(self, "on" + et.replace("<", "").replace(">", "").replace("-", "_")))
#         self.header.bind("<Button-3>", self.show_context_menu)

#         tk.Label(self.frame, text="Port:", bg="lightgreen").grid(row=1, column=0, sticky="e")
#         self.port_entry = tk.Entry(self.frame, width=10)
#         self.port_entry.grid(row=1, column=1, padx=(2,4), pady=2)
#         self.port_entry.insert(0, port)

#         tk.Label(self.frame, text="Name:", bg="lightgreen").grid(row=2, column=0, sticky="e")
#         self.name_entry = tk.Entry(self.frame, width=10)
#         self.name_entry.grid(row=2, column=1, padx=(2,4), pady=2)
#         self.name_entry.insert(0, name)

#         tk.Label(self.frame, text="Value:", bg="lightgreen").grid(row=3, column=0, sticky="e")
#         self.value_var = tk.DoubleVar(value=value)
#         self.value_label = tk.Label(self.frame, textvariable=self.value_var, bg="white", width=8)
#         self.value_label.grid(row=3, column=1, padx=(2,4), pady=2)

#         tk.Label(self.frame, text="Min Reading:", bg="lightgreen").grid(row=4, column=0, sticky="e")
#         self.min_entry = tk.Entry(self.frame, width=10)
#         self.min_entry.grid(row=4, column=1, padx=(2,4), pady=2)
#         self.min_entry.insert(0, str(min_val))

#         tk.Label(self.frame, text="Max Reading:", bg="lightgreen").grid(row=5, column=0, sticky="e")
#         self.max_entry = tk.Entry(self.frame, width=10)
#         self.max_entry.grid(row=5, column=1, padx=(2,4), pady=2)
#         self.max_entry.insert(0, str(max_val))

#         tk.Label(self.frame, text="Min Voltage:", bg="lightgreen").grid(row=6, column=0, sticky="e")
#         self.min_v_entry = tk.Entry(self.frame, width=10)
#         self.min_v_entry.grid(row=6, column=1, padx=(2,4), pady=2)
#         self.min_v_entry.insert(0, str(min_voltage))

#         tk.Label(self.frame, text="Max Voltage:", bg="lightgreen").grid(row=7, column=0, sticky="e")
#         self.max_v_entry = tk.Entry(self.frame, width=10)
#         self.max_v_entry.grid(row=7, column=1, padx=(2,4), pady=2)
#         self.max_v_entry.insert(0, str(max_voltage))

#     def get_data(self):
#         pos = self.get_position()
#         return {"type": self.type,
#                 "x": pos[0],
#                 "y": pos[1],
#                 "port": self.port_entry.get(),
#                 "name": self.name_entry.get(),
#                 "value": self.value_var.get(),
#                 "min": float(self.min_entry.get() or 0.0),
#                 "max": float(self.max_entry.get() or 0.0),
#                 "min_voltage": float(self.min_v_entry.get() or 0.0),
#                 "max_voltage": float(self.max_v_entry.get() or 0.0)}

#     def get_command(self):
#         """
#         Build the sensor configuration command.
#         Format: s{port}{min_voltage}{max_voltage}{min_reading}{max_reading}
#         where each numeric field is formatted to exactly BUFFERSENSOR characters.
#         """
#         port = self.port_entry.get().strip()
#         try:
#             min_voltage = float(self.min_v_entry.get() or 0.0)
#             max_voltage = float(self.max_v_entry.get() or 0.0)
#             min_reading = float(self.min_entry.get() or 0.0)
#             max_reading = float(self.max_entry.get() or 0.0)
#         except ValueError:
#             min_voltage = max_voltage = min_reading = max_reading = 0.0
#         min_voltage_str = format_value(min_voltage, BUFFERSENSOR)
#         max_voltage_str = format_value(max_voltage, BUFFERSENSOR)
#         min_reading_str = format_value(min_reading, BUFFERSENSOR)
#         max_reading_str = format_value(max_reading, BUFFERSENSOR)
#         return f"s{port}{min_voltage_str}{max_voltage_str}{min_reading_str}{max_reading_str}"
    
#     def get_query_command(self):
#         # For polling or refresh, we want to query sensors with just their port.
#         port = self.port_entry.get().strip()
#         return f"s{port}"
    
#     def update_from_response(self, response):
#         """
#         Update sensor data from a response.
#         Two response formats are expected:
#           1. Full configuration (starting with "rs"):
#              Format: rs{port}{value}{min_voltage}{max_voltage}{min_reading}{max_reading}
#              Here each numeric field is BUFFERSENSOR characters long.
#           2. Short read response (starting with "s"):
#              Format: s{port}{value} where value is BUFFERSENSOR characters long.
#         """
#         try:
#             if response.startswith("rs") and len(response) >= (2 + 4 + 5 * BUFFERSENSOR):
#                 resp_port = response[2:6]       # 4 characters for port.
#                 new_value = response[6:6 + BUFFERSENSOR]
#                 new_min_voltage = response[6 + BUFFERSENSOR:6 + 2 * BUFFERSENSOR]
#                 new_max_voltage = response[6 + 2 * BUFFERSENSOR:6 + 3 * BUFFERSENSOR]
#                 new_min_reading = response[6 + 3 * BUFFERSENSOR:6 + 4 * BUFFERSENSOR]
#                 new_max_reading = response[6 + 4 * BUFFERSENSOR:6 + 5 * BUFFERSENSOR]
#                 if resp_port == self.port_entry.get().strip():
#                     self.value_var.set(float(new_value))
#                     self.min_v_entry.delete(0, tk.END)
#                     self.min_v_entry.insert(0, new_min_voltage)
#                     self.max_v_entry.delete(0, tk.END)
#                     self.max_v_entry.insert(0, new_max_voltage)
#                     self.min_entry.delete(0, tk.END)
#                     self.min_entry.insert(0, new_min_reading)
#                     self.max_entry.delete(0, tk.END)
#                     self.max_entry.insert(0, new_max_reading)
#             elif response.startswith("s") and not response.startswith("rs") and len(response) >= (1 + 4 + BUFFERSENSOR):
#                 resp_port = response[1:5]  # 4 characters for port.
#                 new_value = response[5:5 + BUFFERSENSOR]
#                 if resp_port == self.port_entry.get().strip():
#                     self.value_var.set(float(new_value))
#         except Exception as e:
#             print("Error updating SensorBlock:", e)

# # Main application.
# class App:
#     def __init__(self, root):
#         self.root = root
#         root.title("GUI Demo")
#         self.blocks = []
#         # Control panel.
#         ctrl = tk.Frame(root)
#         ctrl.pack(side="top", fill="x", padx=5, pady=5)
#         tk.Button(ctrl, text="Add Valve", command=self.add_valve).pack(side="left", padx=2)
#         tk.Button(ctrl, text="Add Sensor", command=self.add_sensor).pack(side="left", padx=2)
#         tk.Button(ctrl, text="Save", command=self.save_state).pack(side="left", padx=2)
#         tk.Button(ctrl, text="Reset", command=self.reset_state).pack(side="left", padx=2)
#         tk.Button(ctrl, text="Send Commands", command=self.send_all_commands).pack(side="left", padx=2)
#         tk.Button(ctrl, text="Read", command=self.read_sensors).pack(side="left", padx=2)
#         # The refresh button toggles a continuous refresh loop.
#         self.refresh_button = tk.Button(ctrl, text="Refresh", command=self.toggle_refresh)
#         self.refresh_button.pack(side="left", padx=2)
        
#         self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
#         self.canvas.pack(fill="both", expand=True)
#         if os.path.exists(SAVE_FILE):
#             self.load_state()
#         self.refresh_running = False  # Flag to control refresh loop

#     def add_valve(self, port="", name="", state=False, input_voltage=0.0, x=50, y=50):
#         block = ValveBlock(self.canvas, x, y, port, name, state, input_voltage, delete_callback=self.delete_block)
#         self.blocks.append(block)
    
#     def add_sensor(self, port="", name="", value=0.0, min_val=0.0, max_val=100.0,
#                    min_voltage=0.0, max_voltage=5.0, x=200, y=50):
#         block = SensorBlock(self.canvas, x, y, port, name, value,
#                             min_val, max_val, min_voltage, max_voltage, delete_callback=self.delete_block)
#         self.blocks.append(block)
    
#     def delete_block(self, block):
#         if tk.messagebox.askyesno("Delete", "Delete this block?"):
#             block.destroy()
#             try:
#                 self.blocks.remove(block)
#             except ValueError:
#                 pass
    
#     def save_state(self):
#         data = [block.get_data() for block in self.blocks]
#         try:
#             with open(SAVE_FILE, "w") as f:
#                 json.dump(data, f, indent=4)
#             tk.messagebox.showinfo("Save", "State saved!")
#         except Exception as e:
#             tk.messagebox.showerror("Error", f"Error saving state: {e}")
    
#     def load_state(self):
#         try:
#             with open(SAVE_FILE, "r") as f:
#                 data = json.load(f)
#             for block in self.blocks:
#                 block.destroy()
#             self.blocks.clear()
#             for item in data:
#                 x = item.get("x", 50)
#                 y = item.get("y", 50)
#                 if item.get("type") == "valve":
#                     self.add_valve(item.get("port", ""), item.get("name", ""),
#                                    item.get("state", False),
#                                    item.get("input_voltage", 0.0), x, y)
#                 elif item.get("type") == "sensor":
#                     self.add_sensor(item.get("port", ""), item.get("name", ""),
#                                     item.get("value", 0.0),
#                                     item.get("min", 0.0), item.get("max", 100.0),
#                                     item.get("min_voltage", 0.0), item.get("max_voltage", 5.0),
#                                     x, y)
#             tk.messagebox.showinfo("Load", "State loaded!")
#         except Exception as e:
#             tk.messagebox.showerror("Error", f"Error loading state: {e}")
    
#     def reset_state(self):
#         if tk.messagebox.askyesno("Reset", "Reset?"):
#             if os.path.exists(SAVE_FILE):
#                 os.remove(SAVE_FILE)
#             for block in self.blocks:
#                 block.destroy()
#             self.blocks.clear()
    
#     def send_all_commands(self):
#         responses = []
#         for block in self.blocks:
#             if hasattr(block, "get_command"):
#                 command = block.get_command()
#                 if not command.startswith("w"):
#                     command = "m" + command
#                 response = send_command(command)
#                 print(f"Send Commands - Block type: {block.type}, Command: {command}")
#                 print(f"Response: {response}\n")
#                 responses.append(f"Sent: {command}\nResponse: {response}")
#                 if hasattr(block, "update_from_response"):
#                     block.update_from_response(response)
#         if responses:
#             tk.messagebox.showinfo("Command Responses", "\n\n".join(responses))
#         else:
#             tk.messagebox.showinfo("Info", "No commands to send.")
    
#     def read_sensors(self):
#         """Send the full configuration read command (rs...) for all sensor blocks once."""
#         responses = []
#         for block in self.blocks:
#             if block.type == "sensor":
#                 # get_command() returns a string starting with "s", so prefixing with "r" gives "rs..."
#                 command = "r" + block.get_command()
#                 response = send_command(command)
#                 print(f"Read - Sensor Block, Command: {command}")
#                 print(f"Response: {response}\n")
#                 responses.append(f"Sent: {command}\nResponse: {response}")
#                 if hasattr(block, "update_from_response"):
#                     block.update_from_response(response)
#         if responses:
#             tk.messagebox.showinfo("Read Responses", "\n\n".join(responses))
#         else:
#             tk.messagebox.showinfo("Info", "No sensor commands sent.")
    
#     def toggle_refresh(self):
#         """Toggle a continuous loop that sends the full configuration read command (rs...) every second."""
#         if not self.refresh_running:
#             self.refresh_running = True
#             self.refresh_button.config(text="Stop Refresh")
#             self.refresh_loop()  # Start the loop
#         else:
#             self.refresh_running = False
#             self.refresh_button.config(text="Refresh")
    
#     def refresh_loop(self):
#         """Continuously send the read command (rs...) to sensors every second."""
#         if not self.refresh_running:
#             return
#         for block in self.blocks:
#             if block.type == "sensor":
#                 command = "r" + block.get_command()
#                 response = send_command(command)
#                 print(f"Refresh - Sensor Block, Command: {command}")
#                 print(f"Response: {response}\n")
#                 if hasattr(block, "update_from_response"):
#                     block.update_from_response(response)
#         self.root.after(1000, self.refresh_loop)

# if __name__ == "__main__":
#     root = tk.Tk()
#     App(root)
#     root.mainloop()











import tkinter as tk
from tkinter import messagebox
import json, os, grpc, concurrent.futures
import relay_pb2
import relay_pb2_grpc
import time

SAVE_FILE = "gui_state.json"    
BUFFERSENSOR = 7  # For sensors, numeric fields will be formatted to BUFFERSENSOR characters.
BUFFERVALVE = 7 - 1   # For valves, the numeric field will be formatted to BUFFERVALVE+1 characters.

def format_value(value, buf):
    """
    Format a float value into a string with total length 'buf' (including the decimal point).
    The number of decimal places is calculated as: buf - (length of integer part) - 1.
    If the value is negative, the sign is taken into account.
    """
    try:
        abs_val = abs(value)
        int_part = str(int(abs_val))
        int_length = len(int_part)
        if value < 0:
            int_length += 1  # account for negative sign
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
    Returns the response body if successful.
    If an error occurs, returns a string describing the error.
    """
    print(f"Sending command: {command}")  # Log the command
    channel = grpc.insecure_channel(target)
    try:
        client = relay_pb2_grpc.RelayServiceStub(channel)
        message = relay_pb2.Message(body=command)
        response = client.RelayData(message, timeout=15)
        print(f"Response received: {response.body}")  # Log the response
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

# Base draggable block for use on the canvas.
class DraggableBlock:
    def __init__(self, canvas, x, y, delete_callback=None):
        self.canvas = canvas
        self.delete_callback = delete_callback
        self.frame = tk.Frame(canvas, bd=2, relief="raised", bg="lightgray")
        self.win = canvas.create_window(x, y, window=self.frame, anchor="nw")
        for event_type in ("<ButtonPress-1>", "<B1-Motion>"):
            handler = getattr(self, "on" + event_type.replace("<", "").replace(">", "").replace("-", "_"))
            canvas.tag_bind(self.win, event_type, handler)
            self.frame.bind(event_type, handler)
        self.frame.bind("<Button-3>", self.show_context_menu)
        canvas.tag_bind(self.win, "<Button-3>", self.show_context_menu)
    
    def onButtonPress_1(self, event):
        self.canvas.tag_raise(self.win)
        self.start_x, self.start_y = self.canvas.coords(self.win)
        self.mouse_x, self.mouse_y = event.x_root, event.y_root
    on_click = onButtonPress_1

    def onB1_Motion(self, event):
        dx = event.x_root - self.mouse_x
        dy = event.y_root - self.mouse_y
        self.canvas.coords(self.win, self.start_x + dx, self.start_y + dy)
    on_drag = onB1_Motion

    def show_context_menu(self, event):
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="Delete", command=self.delete_block)
        menu.tk_popup(event.x_root, event.y_root)

    def delete_block(self):
        if self.delete_callback:
            self.delete_callback(self)
        else:
            self.destroy()

    def get_position(self):
        return self.canvas.coords(self.win)

    def destroy(self):
        self.canvas.delete(self.win)
        self.frame.destroy()

# Valve block
class ValveBlock(DraggableBlock):
    def __init__(self, canvas, x, y, port="", name="", state=False, input_voltage=0.0, delete_callback=None):
        super().__init__(canvas, x, y, delete_callback)
        self.type = "valve"
        self.state = state
        self.frame.config(bg="lightblue")
        self.header = tk.Label(self.frame, text="Valve", bg="lightblue", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        for et in ("<ButtonPress-1>", "<B1-Motion>"):
            self.header.bind(et, getattr(self, "on" + et.replace("<", "").replace(">", "").replace("-", "_")))
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
        # When toggled, send a "w" command to update valve state.
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
        return {"type": self.type,
                "x": pos[0],
                "y": pos[1],
                "port": self.port_entry.get(),
                "name": self.name_entry.get(),
                "state": self.state,
                "input_voltage": float(self.input_voltage_entry.get() or 0.0)}

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
        # Expect valve response in the format: v{port}{state}{voltage}
        try:
            if not response.startswith("v"):
                return
            resp_port = response[1:5]  # assume port is 4 characters
            new_state = response[5]    # 1 character for state
            new_voltage = response[6:6 + (BUFFERVALVE + 1)]
            if resp_port == self.port_entry.get().strip():
                self.state = (new_state == "1")
                self.toggle_button.config(text="On" if self.state else "Off",
                                            bg="green" if self.state else "red")
                self.input_voltage_entry.delete(0, tk.END)
                self.input_voltage_entry.insert(0, new_voltage)
        except Exception as e:
            print("Error updating ValveBlock:", e)

# Sensor block
class SensorBlock(DraggableBlock):
    def __init__(self, canvas, x, y, port="", name="", value=0.0,
                 min_val=0.0, max_val=100.0, min_voltage=0.0, max_voltage=5.0,
                 delete_callback=None):
        super().__init__(canvas, x, y, delete_callback)
        self.type = "sensor"
        self.frame.config(bg="lightgreen")
        self.header = tk.Label(self.frame, text="Sensor", bg="lightgreen", font=("Arial", 10, "bold"))
        self.header.grid(row=0, column=0, columnspan=2, pady=(2,4))
        for et in ("<ButtonPress-1>", "<B1-Motion>"):
            self.header.bind(et, getattr(self, "on" + et.replace("<", "").replace(">", "").replace("-", "_")))
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
        return {"type": self.type,
                "x": pos[0],
                "y": pos[1],
                "port": self.port_entry.get(),
                "name": self.name_entry.get(),
                "value": self.value_var.get(),
                "min": float(self.min_entry.get() or 0.0),
                "max": float(self.max_entry.get() or 0.0),
                "min_voltage": float(self.min_v_entry.get() or 0.0),
                "max_voltage": float(self.max_v_entry.get() or 0.0)}

    def get_command(self):
        """
        Build the sensor configuration command.
        Format: s{port}{min_voltage}{max_voltage}{min_reading}{max_reading}
        where each numeric field is formatted to exactly BUFFERSENSOR characters.
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
        # return f"s{port}"
        
    
    def get_query_command(self):
        # For polling or refresh, we want to query sensors with just their port.
        port = self.port_entry.get().strip()
        return f"s{port}"
    
    def update_from_response(self, response):
        """
        Update sensor data from a response.
        Two response formats are expected:
          1. Full configuration (starting with "rs"):
             Format: rs{port}{value}{min_voltage}{max_voltage}{min_reading}{max_reading}
             Here each numeric field is BUFFERSENSOR characters long.
          2. Short read response (starting with "s"):
             Format: s{port}{value} where value is BUFFERSENSOR characters long.
        """
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

# Main application.
class App:
    def __init__(self, root):
        self.root = root
        root.title("GUI Demo")
        self.blocks = []
        # Control panel.
        ctrl = tk.Frame(root)
        ctrl.pack(side="top", fill="x", padx=5, pady=5)
        tk.Button(ctrl, text="Add Valve", command=self.add_valve).pack(side="left", padx=2)
        tk.Button(ctrl, text="Add Sensor", command=self.add_sensor).pack(side="left", padx=2)
        tk.Button(ctrl, text="Save", command=self.save_state).pack(side="left", padx=2)
        tk.Button(ctrl, text="Reset", command=self.reset_state).pack(side="left", padx=2)
        tk.Button(ctrl, text="Send Commands", command=self.send_all_commands).pack(side="left", padx=2)
        tk.Button(ctrl, text="Read", command=self.read_sensors).pack(side="left", padx=2)
        # The refresh button toggles a continuous refresh loop.
        self.refresh_button = tk.Button(ctrl, text="Refresh", command=self.toggle_refresh)
        self.refresh_button.pack(side="left", padx=2)
        
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(fill="both", expand=True)
        if os.path.exists(SAVE_FILE):
            self.load_state()
        self.refresh_running = False  # Flag to control refresh loop

    def add_valve(self, port="", name="", state=False, input_voltage=0.0, x=50, y=50):
        block = ValveBlock(self.canvas, x, y, port, name, state, input_voltage, delete_callback=self.delete_block)
        self.blocks.append(block)
    
    def add_sensor(self, port="", name="", value=0.0, min_val=0.0, max_val=100.0,
                   min_voltage=0.0, max_voltage=5.0, x=200, y=50):
        block = SensorBlock(self.canvas, x, y, port, name, value,
                            min_val, max_val, min_voltage, max_voltage, delete_callback=self.delete_block)
        self.blocks.append(block)
    
    def delete_block(self, block):
        if tk.messagebox.askyesno("Delete", "Delete this block?"):
            block.destroy()
            try:
                self.blocks.remove(block)
            except ValueError:
                pass
    
    def save_state(self):
        data = [block.get_data() for block in self.blocks]
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=4)
            tk.messagebox.showinfo("Save", "State saved!")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error saving state: {e}")
    
    def load_state(self):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            for block in self.blocks:
                block.destroy()
            self.blocks.clear()
            for item in data:
                x = item.get("x", 50)
                y = item.get("y", 50)
                if item.get("type") == "valve":
                    self.add_valve(item.get("port", ""), item.get("name", ""),
                                   item.get("state", False),
                                   item.get("input_voltage", 0.0), x, y)
                elif item.get("type") == "sensor":
                    self.add_sensor(item.get("port", ""), item.get("name", ""),
                                    item.get("value", 0.0),
                                    item.get("min", 0.0), item.get("max", 100.0),
                                    item.get("min_voltage", 0.0), item.get("max_voltage", 5.0),
                                    x, y)
            tk.messagebox.showinfo("Load", "State loaded!")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error loading state: {e}")
    
    def reset_state(self):
        if tk.messagebox.askyesno("Reset", "Reset?"):
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            for block in self.blocks:
                block.destroy()
            self.blocks.clear()
    
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
            tk.messagebox.showinfo("Command Responses", "\n\n".join(responses))
        else:
            tk.messagebox.showinfo("Info", "No commands to send.")
    
    def read_sensors(self):
        """Send the full configuration read command (rs...) for all sensor blocks once."""
        responses = []
        for block in self.blocks:
            if block.type == "sensor":
                # get_command() returns a string starting with "s", so prefixing with "r" gives "rs..."
                command = "r" + block.get_command()
                response = send_command(command)
                print(f"Read - Sensor Block, Command: {command}")
                print(f"Response: {response}\n")
                responses.append(f"Sent: {command}\nResponse: {response}")
                if hasattr(block, "update_from_response"):
                    block.update_from_response(response)
        if responses:
            tk.messagebox.showinfo("Read Responses", "\n\n".join(responses))
        else:
            tk.messagebox.showinfo("Info", "No sensor commands sent.")
    
    def toggle_refresh(self):
        """Toggle a continuous refresh loop that sends the full configuration read command (rs...) every second."""
        if not self.refresh_running:
            self.refresh_running = True
            self.refresh_button.config(text="Stop Refresh")
            self.refresh_loop()  # Start the loop
        else:
            self.refresh_running = False
            self.refresh_button.config(text="Refresh")
    
    def refresh_loop(self):
        """Continuously send the read command (rs...) to sensors every second using a thread pool."""
        if not self.refresh_running:
            return
        sensor_blocks   = [block for block in self.blocks if block.type == "sensor"]
        if sensor_blocks:
            # Use a thread pool to refresh all sensor blocks concurrently.
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(sensor_blocks)) as executor:
                future_to_block = {
                    executor.submit(send_command, "r" + block.get_command()): block
                    for block in sensor_blocks
                }
                for future in concurrent.futures.as_completed(future_to_block):
                    block = future_to_block[future]
                    try:
                        response = future.result(timeout=5)
                        # Schedule UI update in main thread.
                        self.root.after(0, block.update_from_response, response)
                    except Exception as e:
                        print(f"Error refreshing sensor for block {block.port_entry.get()}: {e}")
        self.root.after(100, self.refresh_loop)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

















