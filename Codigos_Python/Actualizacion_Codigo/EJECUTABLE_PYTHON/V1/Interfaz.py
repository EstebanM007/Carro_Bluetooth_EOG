import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import serial
import serial.tools.list_ports
from pylsl import StreamInlet, resolve_streams
import json
import traceback

class FakeSerial:
    """Simula un puerto serial para pruebas sin hardware."""
    def write(self, data):
        pass
    def close(self):
        pass

class StreamConfigRow:
    """Fila de configuración para un stream LSL en la interfaz."""
    def __init__(self, parent, available_streams, row_index):
        self.parent = parent
        self.row = row_index

        tk.Label(parent, text="Stream:").grid(row=self.row, column=0, padx=5, pady=5, sticky="w")
        self.stream_var = tk.StringVar()
        # Agregar opción de stream manual
        stream_options = ["Stream Manual"] + available_streams
        self.stream_menu = ttk.Combobox(parent, textvariable=self.stream_var,
                                        values=stream_options, state="readonly", width=30)
        self.stream_menu.grid(row=self.row, column=1, padx=5, pady=5)
        self.stream_menu.bind("<<ComboboxSelected>>", self.on_stream_selection)

        # Campo para stream manual
        self.manual_stream_label = tk.Label(parent, text="Nombre:")
        self.manual_stream_label.grid(row=self.row, column=2, padx=2, pady=5, sticky="w")
        self.manual_stream_name = tk.Entry(parent, width=15)
        self.manual_stream_name.grid(row=self.row, column=3, padx=2, pady=5)
        
        # Inicialmente ocultos
        self.manual_stream_label.grid_remove()
        self.manual_stream_name.grid_remove()

        # Ajustar posiciones de los demás campos
        tk.Label(parent, text="Lim Inf (+):").grid(row=self.row, column=4, padx=2, pady=5, sticky="w")
        self.pos_lower = tk.Entry(parent, width=7)
        self.pos_lower.grid(row=self.row, column=5, padx=2, pady=5)

        tk.Label(parent, text="Lim Sup (+):").grid(row=self.row, column=6, padx=2, pady=5, sticky="w")
        self.pos_upper = tk.Entry(parent, width=7)
        self.pos_upper.grid(row=self.row, column=7, padx=2, pady=5)

        tk.Label(parent, text="Letra (+):").grid(row=self.row, column=8, padx=2, pady=5, sticky="w")
        self.pos_letter = tk.Entry(parent, width=5)
        self.pos_letter.grid(row=self.row, column=9, padx=2, pady=5)

        tk.Label(parent, text="Lim Inf (-):").grid(row=self.row, column=10, padx=2, pady=5, sticky="w")
        self.neg_lower = tk.Entry(parent, width=7)
        self.neg_lower.grid(row=self.row, column=11, padx=2, pady=5)

        tk.Label(parent, text="Lim Sup (-):").grid(row=self.row, column=12, padx=2, pady=5, sticky="w")
        self.neg_upper = tk.Entry(parent, width=7)
        self.neg_upper.grid(row=self.row, column=13, padx=2, pady=5)

        tk.Label(parent, text="Letra (-):").grid(row=self.row, column=14, padx=2, pady=5, sticky="w")
        self.neg_letter = tk.Entry(parent, width=5)
        self.neg_letter.grid(row=self.row, column=15, padx=2, pady=5)

    def on_stream_selection(self, event=None):
        """Maneja la selección del stream para mostrar/ocultar campos manuales."""
        if self.stream_var.get() == "Stream Manual":
            self.manual_stream_label.grid()
            self.manual_stream_name.grid()
        else:
            self.manual_stream_label.grid_remove()
            self.manual_stream_name.grid_remove()

    def get_data(self):
        """Obtiene y valida los datos de la fila de configuración."""
        def parse_float(entry):
            val = entry.get().strip()
            return float(val) if val else None

        stream_selection = self.stream_var.get()
        if stream_selection == "Stream Manual":
            manual_name = self.manual_stream_name.get().strip()
            if not manual_name:
                messagebox.showerror("Error", "Debe especificar el nombre del stream manual.")
                return None
            stream_id = f"Manual: {manual_name}"
        else:
            stream_id = stream_selection

        data = {
            "stream": stream_id,
            "stream_type": "manual" if stream_selection == "Stream Manual" else "auto",
            "manual_name": self.manual_stream_name.get().strip() if stream_selection == "Stream Manual" else "",
            "pos_lower": parse_float(self.pos_lower),
            "pos_upper": parse_float(self.pos_upper),
            "pos_letter": self.pos_letter.get().strip(),
            "neg_lower": parse_float(self.neg_lower),
            "neg_upper": parse_float(self.neg_upper),
            "neg_letter": self.neg_letter.get().strip(),
        }
        
        if not data["stream"]:
            messagebox.showerror("Error", "Seleccione un stream para cada fila.")
            return None
        if not (data["pos_upper"] is not None or data["neg_upper"] is not None):
            messagebox.showerror("Error", "Debe definir al menos un límite superior para cada fila.")
            return None
        if data["pos_upper"] is not None and (not data["pos_letter"] or len(data["pos_letter"]) != 1):
            messagebox.showerror("Error", "Debe definir una sola letra (+) si usa límites positivos.")
            return None
        if data["neg_upper"] is not None and (not data["neg_letter"] or len(data["neg_letter"]) != 1):
            messagebox.showerror("Error", "Debe definir una sola letra (-) si usa límites negativos.")
            return None
        return data

    def set_data(self, data):
        """Carga datos en la fila de configuración."""
        if data.get("stream_type") == "manual":
            self.stream_var.set("Stream Manual")
            self.manual_stream_name.delete(0, tk.END)
            self.manual_stream_name.insert(0, data.get("manual_name", ""))
            self.on_stream_selection()
        else:
            self.stream_var.set(data.get("stream", ""))
            
        self.pos_lower.delete(0, tk.END)
        self.pos_lower.insert(0, "" if data.get("pos_lower") is None else str(data.get("pos_lower")))
        self.pos_upper.delete(0, tk.END)
        self.pos_upper.insert(0, "" if data.get("pos_upper") is None else str(data.get("pos_upper")))
        self.pos_letter.delete(0, tk.END)
        self.pos_letter.insert(0, data.get("pos_letter", ""))
        self.neg_lower.delete(0, tk.END)
        self.neg_lower.insert(0, "" if data.get("neg_lower") is None else str(data.get("neg_lower")))
        self.neg_upper.delete(0, tk.END)
        self.neg_upper.insert(0, "" if data.get("neg_upper") is None else str(data.get("neg_upper")))
        self.neg_letter.delete(0, tk.END)
        self.neg_letter.insert(0, data.get("neg_letter", ""))

    def update_stream_options(self, available_streams):
        """Actualiza las opciones de streams disponibles."""
        current_selection = self.stream_var.get()
        stream_options = ["Stream Manual"] + available_streams
        self.stream_menu['values'] = stream_options
        
        # Mantener selección si todavía está disponible
        if current_selection in stream_options:
            self.stream_var.set(current_selection)

class App:
    """Ventana principal de la aplicación de configuración LSL y COM."""
    def __init__(self, master):
        """
        Inicializa la interfaz y los componentes principales.
        """
        self.master = master
        master.title("Interfaz de Configuración LSL y COM - Versión Mejorada")
        self.running = False
        self.log_viewers = {}
        self.lsl_thread = None
        self.last_samples = {}  # Para autoajuste de umbrales
        self.stream_reconnection_attempts = {}
        self.max_reconnection_attempts = 5

        # --- Frame de configuración del Puerto Serial ---
        self.frame_serial = tk.LabelFrame(master, text="Puerto Serial")
        self.frame_serial.pack(padx=10, pady=10, fill="x")

        # Primera fila: Puerto y baudios
        serial_row1 = tk.Frame(self.frame_serial)
        serial_row1.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        tk.Label(serial_row1, text="Puerto:").pack(side="left", padx=5)
        self.serial_var = tk.StringVar()
        self.serial_menu = ttk.Combobox(serial_row1, textvariable=self.serial_var, state="readonly", width=15)
        self.serial_menu.pack(side="left", padx=5)

        tk.Label(serial_row1, text="Baudios:").pack(side="left", padx=5)
        self.baudrate_var = tk.StringVar(value="9600")
        self.baudrate_menu = ttk.Combobox(serial_row1, textvariable=self.baudrate_var, 
                                         values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"],
                                         state="readonly", width=10)
        self.baudrate_menu.pack(side="left", padx=5)

        self.btn_refresh_all = tk.Button(serial_row1, text="Actualizar", command=self.refresh_all)
        self.btn_refresh_all.pack(side="left", padx=5)

        # Segunda fila: Checkboxes
        self.simulate_serial = tk.BooleanVar(value=True)
        self.chk_simulate = tk.Checkbutton(
            self.frame_serial,
            text="Simular COM (mostrar en GUI)",
            variable=self.simulate_serial
        )
        self.chk_simulate.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        self.show_serial_console = tk.BooleanVar(value=True)
        self.chk_show_console = tk.Checkbutton(
            self.frame_serial,
            text="Mostrar consola serial",
            variable=self.show_serial_console,
            command=self.toggle_serial_console
        )
        self.chk_show_console.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # Checkbox para reconexión automática
        self.auto_reconnect = tk.BooleanVar(value=True)
        self.chk_auto_reconnect = tk.Checkbutton(
            self.frame_serial,
            text="Reconexión automática de streams",
            variable=self.auto_reconnect
        )
        self.chk_auto_reconnect.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # Consola serial
        self.serial_console_frame = tk.LabelFrame(self.frame_serial, text="Consola Serial")
        self.serial_console_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=0, sticky="we")
        self.serial_console = scrolledtext.ScrolledText(self.serial_console_frame, height=6, state="disabled")
        self.serial_console.pack(fill="x", padx=5, pady=5)

        self.btn_clear_console = tk.Button(self.frame_serial, text="Limpiar consola", command=self.clear_console)
        self.btn_clear_console.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        # --- Frame de control de conexión y configuración ---
        self.frame_control = tk.Frame(master)
        self.frame_control.pack(padx=10, pady=10, fill="x")

        self.btn_connect = tk.Button(self.frame_control, text="Conectar", command=self.start_connection)
        self.btn_connect.pack(side="left", padx=5)
        self.btn_disconnect = tk.Button(self.frame_control, text="Desconectar", command=self.stop_connection, state="disabled")
        self.btn_disconnect.pack(side="left", padx=5)
        self.lbl_status = tk.Label(self.frame_control, text="Estado: Desconectado")
        self.lbl_status.pack(side="left", padx=10)

        self.btn_save = tk.Button(self.frame_control, text="Guardar configuración", command=self.save_config)
        self.btn_save.pack(side="left", padx=5)
        self.btn_load = tk.Button(self.frame_control, text="Cargar configuración", command=self.load_config)
        self.btn_load.pack(side="left", padx=5)

        # --- Frame de Configuración de Condiciones ---
        self.frame_conditions = tk.LabelFrame(master, text="Configuración de Condiciones")
        self.frame_conditions.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(self.frame_conditions)
        btn_frame.grid(row=0, column=0, columnspan=16, sticky="w", padx=5, pady=5)
        self.btn_add_stream = tk.Button(btn_frame, text="Agregar Stream", command=self.add_stream_row)
        self.btn_add_stream.pack(side="left", padx=5)
        self.btn_remove_stream = tk.Button(btn_frame, text="Quitar Stream", command=self.remove_stream_row)
        self.btn_remove_stream.pack(side="left", padx=5)
        tk.Label(btn_frame, text="Streams disponibles:").pack(side="left", padx=5)
        self.global_streams_var = tk.StringVar()
        self.global_streams_menu = ttk.Combobox(btn_frame, textvariable=self.global_streams_var, state="readonly", width=30)
        self.global_streams_menu.pack(side="left", padx=5)

        # Frame con scroll para las condiciones
        self.conditions_canvas = tk.Canvas(self.frame_conditions)
        self.conditions_scrollbar = ttk.Scrollbar(self.frame_conditions, orient="vertical", command=self.conditions_canvas.yview)
        self.conditions_container = tk.Frame(self.conditions_canvas)
        
        self.conditions_container.bind(
            "<Configure>",
            lambda e: self.conditions_canvas.configure(scrollregion=self.conditions_canvas.bbox("all"))
        )
        
        self.conditions_canvas.create_window((0, 0), window=self.conditions_container, anchor="nw")
        self.conditions_canvas.configure(yscrollcommand=self.conditions_scrollbar.set)
        
        self.conditions_canvas.grid(row=1, column=0, columnspan=15, sticky="nsew", padx=5, pady=5)
        self.conditions_scrollbar.grid(row=1, column=15, sticky="ns", padx=5, pady=5)
        
        self.frame_conditions.grid_rowconfigure(1, weight=1)
        self.frame_conditions.grid_columnconfigure(0, weight=1)

        self.frame_logs = None
        self.available_serial_ports = []
        self.available_lsl_streams = []
        self.condition_rows = []
        self.refresh_all()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_all(self):
        """Actualiza la lista de puertos seriales y streams LSL."""
        self.update_serial_ports()
        self.update_streams()

    def update_serial_ports(self):
        """Actualiza la lista de puertos seriales disponibles."""
        ports = serial.tools.list_ports.comports()
        self.available_serial_ports = [port.device for port in ports]
        self.serial_menu['values'] = self.available_serial_ports
        if self.available_serial_ports and not self.serial_var.get():
            self.serial_var.set(self.available_serial_ports[0])

    def update_streams(self):
        """Actualiza la lista de streams LSL disponibles."""
        try:
            streams = resolve_streams(wait_time=1.0)  # Esperar hasta 1 segundo
            self.available_lsl_streams = [f"{s.name()} ({s.type()})" for s in streams]
            self.global_streams_menu['values'] = self.available_lsl_streams
            if self.available_lsl_streams and not self.global_streams_var.get():
                self.global_streams_var.set(self.available_lsl_streams[0])
        except Exception as e:
            # No mostrar error si no hay streams disponibles
            pass
            
        # Actualizar todas las filas de configuración
        for row in self.condition_rows:
            row.update_stream_options(self.available_lsl_streams)

    def add_stream_row(self):
        """Agrega una nueva fila de configuración de stream."""
        row_index = len(self.condition_rows) + 2
        new_row = StreamConfigRow(self.conditions_container, self.available_lsl_streams, row_index)
        self.condition_rows.append(new_row)

    def remove_stream_row(self):
        """Elimina la última fila de configuración de stream."""
        if self.condition_rows:
            row = self.condition_rows.pop()
            for widget in self.conditions_container.grid_slaves(row=row.row):
                widget.destroy()

    def setup_log_viewers(self):
        """Crea los cuadros de log para cada stream en modo simulación."""
        if self.frame_logs:
            self.frame_logs.destroy()
        self.frame_logs = tk.LabelFrame(self.master, text="Visualización de Condiciones (Simulación)")
        self.frame_logs.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_viewers = {}
        for stream_id in self.conditions_by_stream.keys():
            frame = tk.LabelFrame(self.frame_logs, text=f"Stream: {stream_id}")
            frame.pack(padx=5, pady=5, fill="both", expand=True)
            txt = scrolledtext.ScrolledText(frame, height=4)
            txt.pack(padx=5, pady=5, fill="both", expand=True)
            self.log_viewers[stream_id] = txt

    def update_log(self, stream_id, message):
        """Agrega un mensaje al log del stream correspondiente."""
        if stream_id in self.log_viewers:
            viewer = self.log_viewers[stream_id]
            timestamp = time.strftime("%H:%M:%S")
            viewer.insert(tk.END, f"[{timestamp}] {message}\n")
            viewer.see(tk.END)
            # Limitar líneas para evitar uso excesivo de memoria
            lines = viewer.get("1.0", tk.END).split('\n')
            if len(lines) > 200:
                viewer.delete("1.0", f"{len(lines)-100}.0")

    def clear_console(self):
        """Limpia la consola serial."""
        self.serial_console.config(state="normal")
        self.serial_console.delete(1.0, tk.END)
        self.serial_console.config(state="disabled")

    def save_config(self):
        """Guarda la configuración actual en un archivo JSON."""
        config = {
            "serial_settings": {
                "port": self.serial_var.get(),
                "baudrate": self.baudrate_var.get(),
                "simulate": self.simulate_serial.get(),
                "show_console": self.show_serial_console.get(),
                "auto_reconnect": self.auto_reconnect.get()
            },
            "stream_conditions": []
        }
        
        for row in self.condition_rows:
            data = row.get_data()
            if data is not None:
                config["stream_conditions"].append(data)
                
        if not config["stream_conditions"]:
            messagebox.showinfo("Guardar configuración", "No hay configuración válida para guardar.")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Guardar configuración", "Configuración guardada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar configuración: {e}")

    def load_config(self):
        """Carga una configuración desde un archivo JSON."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    config = json.load(f)
                
                # Cargar configuración serial si existe
                if "serial_settings" in config:
                    serial_settings = config["serial_settings"]
                    self.serial_var.set(serial_settings.get("port", ""))
                    self.baudrate_var.set(serial_settings.get("baudrate", "9600"))
                    self.simulate_serial.set(serial_settings.get("simulate", True))
                    self.show_serial_console.set(serial_settings.get("show_console", True))
                    self.auto_reconnect.set(serial_settings.get("auto_reconnect", True))
                    self.toggle_serial_console()
                
                # Limpiar filas actuales
                for row in self.condition_rows:
                    for widget in self.conditions_container.grid_slaves(row=row.row):
                        widget.destroy()
                self.condition_rows.clear()
                
                # Cargar condiciones de streams
                stream_conditions = config.get("stream_conditions", config if isinstance(config, list) else [])
                for i, cond in enumerate(stream_conditions):
                    new_row = StreamConfigRow(self.conditions_container, self.available_lsl_streams, i+2)
                    new_row.set_data(cond)
                    self.condition_rows.append(new_row)
                    
                messagebox.showinfo("Cargar configuración", "Configuración cargada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar configuración: {e}")

    def start_connection(self):
        """Inicia la conexión con los streams LSL y el puerto serial."""
        self.btn_connect.config(state="disabled")
        self.disable_config_fields()

        # Configurar conexión serial
        if self.simulate_serial.get():
            self.serial_connection = FakeSerial()
        else:
            port = self.serial_var.get()
            baudrate = int(self.baudrate_var.get())
            if not port:
                messagebox.showerror("Error", "Seleccione un puerto serial.")
                self.enable_config_fields()
                return
            try:
                self.serial_connection = serial.Serial(port, baudrate, timeout=1)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo conectar al puerto: {e}")
                self.enable_config_fields()
                return

        self.running = True
        self.lbl_status.config(text="Estado: Conectado")
        self.btn_disconnect.config(state="normal")

        # Procesar configuración de streams
        self.stream_conditions = []
        for row in self.condition_rows:
            data = row.get_data()
            if data is None:
                self.enable_config_fields()
                return
            self.stream_conditions.append(data)

        self.conditions_by_stream = {}
        for cond in self.stream_conditions:
            stream_id = cond["stream"]
            self.conditions_by_stream.setdefault(stream_id, []).append(cond)

        # Inicializar inlets y reconexión
        self.inlets = {}
        self.stream_reconnection_attempts = {}
        self.last_samples = {stream_id: [] for stream_id in self.conditions_by_stream.keys()}

        # Conectar a streams disponibles
        self.connect_to_streams()

        if self.simulate_serial.get():
            self.setup_log_viewers()
        else:
            if self.frame_logs:
                self.frame_logs.destroy()
                self.frame_logs = None

        self.lsl_thread = threading.Thread(target=self.lsl_connection_loop, daemon=True)
        self.lsl_thread.start()

    def connect_to_streams(self):
        """Conecta a los streams LSL disponibles."""
        for stream_id in self.conditions_by_stream.keys():
            if stream_id not in self.inlets:
                self.connect_single_stream(stream_id)

    def connect_single_stream(self, stream_id):
        """Conecta a un stream específico."""
        try:
            # Obtener configuración del stream
            stream_config = None
            for cond in self.stream_conditions:
                if cond["stream"] == stream_id:
                    stream_config = cond
                    break
            
            if not stream_config:
                return False
            
            if stream_config["stream_type"] == "manual":
                # Stream manual: buscar por nombre
                manual_name = stream_config["manual_name"]
                all_streams = resolve_streams(wait_time=1.0)
                match_streams = [s for s in all_streams if s.name() == manual_name]
                if not match_streams:
                    if self.simulate_serial.get():
                        self.master.after(0, self.update_log, stream_id, f"Esperando stream manual: {manual_name}")
                    return False
                self.inlets[stream_id] = StreamInlet(match_streams[0])
            else:
                # Stream automático
                all_streams = resolve_streams(wait_time=1.0)
                match_streams = [s for s in all_streams if f"{s.name()} ({s.type()})" == stream_id]
                if not match_streams:
                    if self.simulate_serial.get():
                        self.master.after(0, self.update_log, stream_id, f"Stream no disponible: {stream_id}")
                    return False
                self.inlets[stream_id] = StreamInlet(match_streams[0])
            
            self.stream_reconnection_attempts[stream_id] = 0
            if self.simulate_serial.get():
                self.master.after(0, self.update_log, stream_id, "Conectado exitosamente")
            return True
            
        except Exception as e:
            if self.simulate_serial.get():
                self.master.after(0, self.update_log, stream_id, f"Error de conexión: {e}")
            return False

    def disable_config_fields(self):
        """Deshabilita los campos de configuración durante la conexión."""
        self.btn_add_stream.config(state="disabled")
        self.btn_remove_stream.config(state="disabled")
        self.btn_refresh_all.config(state="disabled")
        self.serial_menu.config(state="disabled")
        self.baudrate_menu.config(state="disabled")
        self.global_streams_menu.config(state="disabled")
        for row in self.condition_rows:
            row.stream_menu.config(state="disabled")
            row.manual_stream_name.config(state="disabled")
            row.pos_lower.config(state="disabled")
            row.pos_upper.config(state="disabled")
            row.pos_letter.config(state="disabled")
            row.neg_lower.config(state="disabled")
            row.neg_upper.config(state="disabled")
            row.neg_letter.config(state="disabled")

    def stop_connection(self):
        """Detiene la conexión y libera recursos."""
        self.running = False
        self.lbl_status.config(text="Estado: Desconectado")
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.enable_config_fields()
        
        if hasattr(self, "serial_connection") and not self.simulate_serial.get():
            try:
                self.serial_connection.close()
            except Exception:
                pass
            
        if self.frame_logs:
            self.frame_logs.destroy()
            self.frame_logs = None
            
        # Esperar a que el hilo termine
        if self.lsl_thread and self.lsl_thread.is_alive():
            self.lsl_thread.join(timeout=2)
        self.lsl_thread = None
        
        # Limpiar inlets y reconexiones solo si existen
        if hasattr(self, "inlets"):
            self.inlets.clear()
        if hasattr(self, "stream_reconnection_attempts"):
            self.stream_reconnection_attempts.clear()

    def enable_config_fields(self):
        """Habilita los campos de configuración tras desconexión o error."""
        self.btn_add_stream.config(state="normal")
        self.btn_remove_stream.config(state="normal")
        self.btn_refresh_all.config(state="normal")
        self.serial_menu.config(state="readonly")
        self.baudrate_menu.config(state="readonly")
        self.global_streams_menu.config(state="readonly")
        for row in self.condition_rows:
            row.stream_menu.config(state="readonly")
            row.manual_stream_name.config(state="normal")
            row.pos_lower.config(state="normal")
            row.pos_upper.config(state="normal")
            row.pos_letter.config(state="normal")
            row.neg_lower.config(state="normal")
            row.neg_upper.config(state="normal")
            row.neg_letter.config(state="normal")

    def append_serial_console(self, text):
        """Agrega texto a la consola serial."""
        self.serial_console.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.serial_console.insert(tk.END, f"[{timestamp}] {text}")
        self.serial_console.see(tk.END)
        self.serial_console.config(state="disabled")
        # Limitar líneas para evitar uso excesivo de memoria
        lines = self.serial_console.get("1.0", tk.END).split('\n')
        if len(lines) > 500:
            self.serial_console.config(state="normal")
            self.serial_console.delete("1.0", f"{len(lines)-300}.0")
            self.serial_console.config(state="disabled")

    def lsl_connection_loop(self):
        """Hilo principal para la lectura de streams LSL y envío por serial."""
        reconnection_check_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Verificar reconexiones cada 5 segundos
                if self.auto_reconnect.get() and current_time - reconnection_check_time > 5.0:
                    self.check_and_reconnect_streams()
                    reconnection_check_time = current_time
                
                # Procesar datos de cada stream
                for stream_id, inlet in list(self.inlets.items()):
                    if not self.running:
                        break
                        
                    try:
                        sample, timestamp = inlet.pull_sample(timeout=0.01)
                        if sample:
                            value = sample[0] if isinstance(sample, (list, tuple)) else sample
                            
                            # Guardar historial para análisis
                            self.last_samples[stream_id].append(value)
                            if len(self.last_samples[stream_id]) > 500:
                                self.last_samples[stream_id] = self.last_samples[stream_id][-500:]
                            
                            # Procesar condiciones para este stream
                            self.process_stream_conditions(stream_id, value)
                            
                    except Exception as e:
                        # Error en stream específico
                        if self.simulate_serial.get():
                            self.master.after(0, self.update_log, stream_id, f"Error en stream: {e}")
                        
                        # Remover inlet problemático si reconexión está habilitada
                        if self.auto_reconnect.get():
                            if stream_id in self.inlets:
                                del self.inlets[stream_id]
                                self.stream_reconnection_attempts[stream_id] = 0
                
                time.sleep(0.001)  # Pequeña pausa para evitar uso excesivo de CPU
                
        except Exception as e:
            # Error general en el hilo
            traceback_str = traceback.format_exc()
            self.master.after(0, messagebox.showerror, "Error en hilo LSL", f"{e}\n\n{traceback_str}")
            self.master.after(0, self.stop_connection)

    def check_and_reconnect_streams(self):
        """Verifica y reconecta streams desconectados."""
        for stream_id in self.conditions_by_stream.keys():
            if stream_id not in self.inlets:
                attempts = self.stream_reconnection_attempts.get(stream_id, 0)
                if attempts < self.max_reconnection_attempts:
                    if self.connect_single_stream(stream_id):
                        self.stream_reconnection_attempts[stream_id] = 0
                        if self.simulate_serial.get():
                            self.master.after(0, self.update_log, stream_id, "Reconectado exitosamente")
                    else:
                        self.stream_reconnection_attempts[stream_id] = attempts + 1
                        if self.simulate_serial.get():
                            self.master.after(0, self.update_log, stream_id, 
                                            f"Intento de reconexión {attempts + 1}/{self.max_reconnection_attempts}")

    def process_stream_conditions(self, stream_id, value):
        """Procesa las condiciones para un stream y valor específico."""
        for cond in self.conditions_by_stream.get(stream_id, []):
            # Condición positiva
            if (cond["pos_lower"] is not None and cond["pos_upper"] is not None and 
                cond["pos_lower"] <= value <= cond["pos_upper"]):
                
                try:
                    self.serial_connection.write(cond["pos_letter"].encode())
                    if self.simulate_serial.get():
                        msg = f"Valor {value:.3f} en [{cond['pos_lower']},{cond['pos_upper']}]: enviando '{cond['pos_letter']}' (Positivo)"
                        self.master.after(0, self.update_log, stream_id, msg)
                    if self.show_serial_console.get():
                        self.master.after(0, self.append_serial_console, f"Enviado: {cond['pos_letter']}\n")
                except Exception as e:
                    if self.simulate_serial.get():
                        self.master.after(0, self.update_log, stream_id, f"Error enviando '{cond['pos_letter']}': {e}")
            
            # Condición negativa
            if (cond["neg_lower"] is not None and cond["neg_upper"] is not None and 
                cond["neg_lower"] <= value <= cond["neg_upper"]):
                
                try:
                    self.serial_connection.write(cond["neg_letter"].encode())
                    if self.simulate_serial.get():
                        msg = f"Valor {value:.3f} en [{cond['neg_lower']},{cond['neg_upper']}]: enviando '{cond['neg_letter']}' (Negativo)"
                        self.master.after(0, self.update_log, stream_id, msg)
                    if self.show_serial_console.get():
                        self.master.after(0, self.append_serial_console, f"Enviado: {cond['neg_letter']}\n")
                except Exception as e:
                    if self.simulate_serial.get():
                        self.master.after(0, self.update_log, stream_id, f"Error enviando '{cond['neg_letter']}': {e}")

    def toggle_serial_console(self):
        """Muestra u oculta la consola serial."""
        if self.show_serial_console.get():
            self.serial_console_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=0, sticky="we")
        else:
            self.serial_console_frame.grid_remove()

    def get_stream_statistics(self, stream_id):
        """Obtiene estadísticas básicas de un stream para ayuda en configuración."""
        if stream_id in self.last_samples and self.last_samples[stream_id]:
            samples = self.last_samples[stream_id]
            return {
                "min": min(samples),
                "max": max(samples),
                "avg": sum(samples) / len(samples),
                "count": len(samples)
            }
        return None

    def show_stream_stats(self):
        """Muestra ventana con estadísticas de streams para ayudar en configuración."""
        if not self.running or not self.last_samples:
            messagebox.showinfo("Estadísticas", "No hay datos disponibles. Inicie la conexión primero.")
            return
        
        stats_window = tk.Toplevel(self.master)
        stats_window.title("Estadísticas de Streams")
        stats_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        for stream_id in self.last_samples.keys():
            stats = self.get_stream_statistics(stream_id)
            if stats:
                text_widget.insert(tk.END, f"Stream: {stream_id}\n")
                text_widget.insert(tk.END, f"  Mínimo: {stats['min']:.3f}\n")
                text_widget.insert(tk.END, f"  Máximo: {stats['max']:.3f}\n")
                text_widget.insert(tk.END, f"  Promedio: {stats['avg']:.3f}\n")
                text_widget.insert(tk.END, f"  Muestras: {stats['count']}\n")
                text_widget.insert(tk.END, f"  Sugerencia umbral (+): [{stats['avg']:.3f}, {stats['max']:.3f}]\n")
                text_widget.insert(tk.END, f"  Sugerencia umbral (-): [{stats['min']:.3f}, {stats['avg']:.3f}]\n")
                text_widget.insert(tk.END, "\n" + "-"*50 + "\n\n")
        
        text_widget.config(state="disabled")

    def on_closing(self):
        """Cierra la aplicación y libera recursos."""
        self.stop_connection()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")  # Ventana más grande para acomodar nuevas funciones
    app = App(root)
    
    # Agregar menú con funciones adicionales
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # Menú Herramientas
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Herramientas", menu=tools_menu)
    tools_menu.add_command(label="Estadísticas de Streams", command=app.show_stream_stats)
    tools_menu.add_separator()
    tools_menu.add_command(label="Actualizar Streams", command=app.refresh_all)
    
    # Menú Ayuda
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Ayuda", menu=help_menu)
    help_menu.add_command(label="Acerca de", 
                         command=lambda: messagebox.showinfo("Acerca de", 
                         "Interfaz LSL-Serial Mejorada v2.0\n\n"
                         "Funciones principales:\n"
                         "• Configuración de baudios personalizables\n"
                         "• Streams manuales por nombre\n"
                         "• Reconexión automática\n"
                         "• Estadísticas en tiempo real\n"
                         "• Mejor manejo de errores"))
    
    root.mainloop()