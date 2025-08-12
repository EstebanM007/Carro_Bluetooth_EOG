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
    def __init__(self, baudrate=9600):
        self.baudrate = baudrate
        self.is_open = True
    
    def write(self, data):
        """Simula escritura de datos."""
        return len(data)
    
    def close(self):
        """Simula cierre de puerto."""
        self.is_open = False
    
    def __str__(self):
        return f"FakeSerial(baudrate={self.baudrate})"

class StreamConfigRow:
    """Fila de configuración para un stream LSL en la interfaz."""
    def __init__(self, parent, available_streams, row_index):
        self.parent = parent
        self.row = row_index
        self.widgets = []

        # Stream selection
        lbl_stream = tk.Label(parent, text="Stream:", font=("Arial", 9))
        lbl_stream.grid(row=self.row, column=0, padx=(5, 2), pady=3, sticky="w")
        self.widgets.append(lbl_stream)
        
        self.stream_var = tk.StringVar()
        self.stream_menu = ttk.Combobox(parent, textvariable=self.stream_var,
                                        values=available_streams, state="readonly", width=25, font=("Arial", 8))
        self.stream_menu.grid(row=self.row, column=1, padx=2, pady=3)
        self.widgets.append(self.stream_menu)

        # Positive condition
        lbl_pos = tk.Label(parent, text="Condición (+):", font=("Arial", 9, "bold"), fg="green")
        lbl_pos.grid(row=self.row, column=2, padx=(10, 2), pady=3, sticky="w")
        self.widgets.append(lbl_pos)
        
        lbl_pos_inf = tk.Label(parent, text="Min:", font=("Arial", 8))
        lbl_pos_inf.grid(row=self.row, column=3, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_pos_inf)
        
        self.pos_lower = tk.Entry(parent, width=8, font=("Arial", 8))
        self.pos_lower.grid(row=self.row, column=4, padx=2, pady=3)
        self.widgets.append(self.pos_lower)

        lbl_pos_sup = tk.Label(parent, text="Max:", font=("Arial", 8))
        lbl_pos_sup.grid(row=self.row, column=5, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_pos_sup)
        
        self.pos_upper = tk.Entry(parent, width=8, font=("Arial", 8))
        self.pos_upper.grid(row=self.row, column=6, padx=2, pady=3)
        self.widgets.append(self.pos_upper)

        lbl_pos_char = tk.Label(parent, text="Char:", font=("Arial", 8))
        lbl_pos_char.grid(row=self.row, column=7, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_pos_char)
        
        self.pos_letter = tk.Entry(parent, width=4, font=("Arial", 8))
        self.pos_letter.grid(row=self.row, column=8, padx=2, pady=3)
        self.widgets.append(self.pos_letter)

        # Negative condition
        lbl_neg = tk.Label(parent, text="Condición (-):", font=("Arial", 9, "bold"), fg="red")
        lbl_neg.grid(row=self.row, column=9, padx=(10, 2), pady=3, sticky="w")
        self.widgets.append(lbl_neg)
        
        lbl_neg_inf = tk.Label(parent, text="Min:", font=("Arial", 8))
        lbl_neg_inf.grid(row=self.row, column=10, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_neg_inf)
        
        self.neg_lower = tk.Entry(parent, width=8, font=("Arial", 8))
        self.neg_lower.grid(row=self.row, column=11, padx=2, pady=3)
        self.widgets.append(self.neg_lower)

        lbl_neg_sup = tk.Label(parent, text="Max:", font=("Arial", 8))
        lbl_neg_sup.grid(row=self.row, column=12, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_neg_sup)
        
        self.neg_upper = tk.Entry(parent, width=8, font=("Arial", 8))
        self.neg_upper.grid(row=self.row, column=13, padx=2, pady=3)
        self.widgets.append(self.neg_upper)

        lbl_neg_char = tk.Label(parent, text="Char:", font=("Arial", 8))
        lbl_neg_char.grid(row=self.row, column=14, padx=2, pady=3, sticky="w")
        self.widgets.append(lbl_neg_char)
        
        self.neg_letter = tk.Entry(parent, width=4, font=("Arial", 8))
        self.neg_letter.grid(row=self.row, column=15, padx=2, pady=3)
        self.widgets.append(self.neg_letter)

    def get_data(self):
        """Obtiene y valida los datos de la fila de configuración."""
        def parse_float(entry):
            val = entry.get().strip()
            if not val:
                return None
            try:
                return float(val)
            except ValueError:
                raise ValueError(f"Valor numérico inválido: '{val}'")

        try:
            data = {
                "stream": self.stream_var.get(),
                "pos_lower": parse_float(self.pos_lower),
                "pos_upper": parse_float(self.pos_upper),
                "pos_letter": self.pos_letter.get().strip(),
                "neg_lower": parse_float(self.neg_lower),
                "neg_upper": parse_float(self.neg_upper),
                "neg_letter": self.neg_letter.get().strip(),
            }
            
            # Validaciones
            if not data["stream"]:
                raise ValueError("Debe seleccionar un stream")
            
            # Validar condición positiva
            pos_has_values = any(x is not None for x in [data["pos_lower"], data["pos_upper"]])
            if pos_has_values:
                if data["pos_upper"] is None:
                    raise ValueError("Debe definir un valor máximo para la condición positiva")
                if not data["pos_letter"] or len(data["pos_letter"]) != 1:
                    raise ValueError("Debe definir exactamente un carácter para la condición positiva")
                if data["pos_lower"] is not None and data["pos_lower"] >= data["pos_upper"]:
                    raise ValueError("El valor mínimo debe ser menor que el máximo en la condición positiva")
            
            # Validar condición negativa
            neg_has_values = any(x is not None for x in [data["neg_lower"], data["neg_upper"]])
            if neg_has_values:
                if data["neg_upper"] is None:
                    raise ValueError("Debe definir un valor máximo para la condición negativa")
                if not data["neg_letter"] or len(data["neg_letter"]) != 1:
                    raise ValueError("Debe definir exactamente un carácter para la condición negativa")
                if data["neg_lower"] is not None and data["neg_lower"] >= data["neg_upper"]:
                    raise ValueError("El valor mínimo debe ser menor que el máximo en la condición negativa")
            
            # Al menos una condición debe estar definida
            if not pos_has_values and not neg_has_values:
                raise ValueError("Debe definir al menos una condición (positiva o negativa)")
            
            return data
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            return None

    def set_data(self, data):
        """Carga datos en la fila de configuración."""
        self.stream_var.set(data.get("stream", ""))
        
        entries_data = [
            (self.pos_lower, data.get("pos_lower")),
            (self.pos_upper, data.get("pos_upper")),
            (self.pos_letter, data.get("pos_letter", "")),
            (self.neg_lower, data.get("neg_lower")),
            (self.neg_upper, data.get("neg_upper")),
            (self.neg_letter, data.get("neg_letter", ""))
        ]
        
        for entry, value in entries_data:
            entry.delete(0, tk.END)
            if isinstance(value, str):
                entry.insert(0, value)
            elif value is not None:
                entry.insert(0, str(value))

    def destroy(self):
        """Elimina todos los widgets de la fila."""
        for widget in self.widgets:
            widget.destroy()

class App:
    """Ventana principal de la aplicación de configuración LSL y COM."""
    
    # Velocidades de baudios estándar
    BAUD_RATES = [300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200, 128000, 256000]
    
    def __init__(self, master):
        """Inicializa la interfaz y los componentes principales."""
        self.master = master
        master.title("🔧 Interfaz de Configuración LSL y COM - v2.0")
        master.geometry("1200x800")
        master.minsize(1000, 600)
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables de estado
        self.running = False
        self.log_viewers = {}
        self.lsl_thread = None
        self.last_samples = {}
        self.serial_connection = None
        self.start_time = None
        
        # Crear interfaz
        self.create_widgets()
        
        # Inicializar datos
        self.available_serial_ports = []
        self.available_lsl_streams = []
        self.condition_rows = []
        
        # Cargar datos iniciales
        self.refresh_all()
        
        # Configurar cierre de ventana
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # Frame principal con scroll
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Frame de configuración del Puerto Serial ---
        self.create_serial_frame(main_frame)
        
        # --- Frame de control ---
        self.create_control_frame(main_frame)
        
        # --- Frame de configuración de condiciones ---
        self.create_conditions_frame(main_frame)
        
        # --- Frame de estadísticas ---
        self.create_stats_frame(main_frame)

    def create_serial_frame(self, parent):
        """Crea el frame de configuración serial."""
        self.frame_serial = tk.LabelFrame(parent, text="🔌 Configuración Puerto Serial", 
                                         font=("Arial", 10, "bold"), fg="blue")
        self.frame_serial.pack(fill="x", pady=(0, 10))

        # Primera fila: Puerto y Baudios
        row1_frame = tk.Frame(self.frame_serial)
        row1_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row1_frame, text="Puerto:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        self.serial_var = tk.StringVar()
        self.serial_menu = ttk.Combobox(row1_frame, textvariable=self.serial_var, 
                                       state="readonly", width=15, font=("Arial", 8))
        self.serial_menu.pack(side="left", padx=(0, 10))

        tk.Label(row1_frame, text="Baudios:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        self.baud_var = tk.StringVar(value="9600")
        self.baud_menu = ttk.Combobox(row1_frame, textvariable=self.baud_var,
                                     values=[str(b) for b in self.BAUD_RATES],
                                     state="readonly", width=10, font=("Arial", 8))
        self.baud_menu.pack(side="left", padx=(0, 10))

        self.btn_refresh_all = tk.Button(row1_frame, text="🔄 Actualizar", 
                                        command=self.refresh_all, font=("Arial", 8))
        self.btn_refresh_all.pack(side="left", padx=(0, 10))

        # Segunda fila: Opciones
        row2_frame = tk.Frame(self.frame_serial)
        row2_frame.pack(fill="x", padx=10, pady=5)
        
        self.simulate_serial = tk.BooleanVar(value=True)
        self.chk_simulate = tk.Checkbutton(row2_frame, text="🔧 Modo simulación (mostrar en GUI)",
                                          variable=self.simulate_serial, font=("Arial", 9))
        self.chk_simulate.pack(side="left", padx=(0, 20))

        self.show_serial_console = tk.BooleanVar(value=True)
        self.chk_show_console = tk.Checkbutton(row2_frame, text="📺 Mostrar consola serial",
                                              variable=self.show_serial_console,
                                              command=self.toggle_serial_console, font=("Arial", 9))
        self.chk_show_console.pack(side="left")

        # Consola serial
        self.serial_console_frame = tk.LabelFrame(self.frame_serial, text="📟 Consola Serial", 
                                                 font=("Arial", 9))
        self.serial_console_frame.pack(fill="x", padx=10, pady=5)
        
        console_frame = tk.Frame(self.serial_console_frame)
        console_frame.pack(fill="x", padx=5, pady=5)
        
        self.serial_console = scrolledtext.ScrolledText(console_frame, height=4, state="disabled",
                                                       font=("Consolas", 8), bg="black", fg="green")
        self.serial_console.pack(side="left", fill="both", expand=True)

        self.btn_clear_console = tk.Button(console_frame, text="🗑️ Limpiar", 
                                          command=self.clear_console, font=("Arial", 8))
        self.btn_clear_console.pack(side="right", padx=(5, 0))

    def create_control_frame(self, parent):
        """Crea el frame de control."""
        self.frame_control = tk.LabelFrame(parent, text="🎛️ Control de Conexión", 
                                          font=("Arial", 10, "bold"), fg="purple")
        self.frame_control.pack(fill="x", pady=(0, 10))
        
        control_inner = tk.Frame(self.frame_control)
        control_inner.pack(fill="x", padx=10, pady=10)

        # Botones de conexión
        btn_frame = tk.Frame(control_inner)
        btn_frame.pack(side="left")
        
        self.btn_connect = tk.Button(btn_frame, text="🟢 Conectar", command=self.start_connection,
                                    bg="lightgreen", font=("Arial", 9, "bold"))
        self.btn_connect.pack(side="left", padx=(0, 5))
        
        self.btn_disconnect = tk.Button(btn_frame, text="🔴 Desconectar", command=self.stop_connection,
                                       state="disabled", bg="lightcoral", font=("Arial", 9, "bold"))
        self.btn_disconnect.pack(side="left", padx=(0, 20))
        
        # Estado
        self.lbl_status = tk.Label(btn_frame, text="⚫ Estado: Desconectado", 
                                  font=("Arial", 9, "bold"), fg="red")
        self.lbl_status.pack(side="left", padx=(0, 20))

        # Botones de configuración
        config_frame = tk.Frame(control_inner)
        config_frame.pack(side="right")
        
        self.btn_save = tk.Button(config_frame, text="💾 Guardar Config", command=self.save_config,
                                 font=("Arial", 8))
        self.btn_save.pack(side="left", padx=(0, 5))
        
        self.btn_load = tk.Button(config_frame, text="📂 Cargar Config", command=self.load_config,
                                 font=("Arial", 8))
        self.btn_load.pack(side="left")

    def create_conditions_frame(self, parent):
        """Crea el frame de configuración de condiciones."""
        self.frame_conditions = tk.LabelFrame(parent, text="⚙️ Configuración de Condiciones", 
                                             font=("Arial", 10, "bold"), fg="darkgreen")
        self.frame_conditions.pack(fill="both", expand=True, pady=(0, 10))

        # Botones de control de streams
        btn_frame = tk.Frame(self.frame_conditions)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_add_stream = tk.Button(btn_frame, text="➕ Agregar Stream", command=self.add_stream_row,
                                       bg="lightblue", font=("Arial", 8, "bold"))
        self.btn_add_stream.pack(side="left", padx=(0, 5))
        
        self.btn_remove_stream = tk.Button(btn_frame, text="➖ Quitar Stream", command=self.remove_stream_row,
                                          bg="lightyellow", font=("Arial", 8, "bold"))
        self.btn_remove_stream.pack(side="left", padx=(0, 20))
        
        tk.Label(btn_frame, text="Streams disponibles:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        self.global_streams_var = tk.StringVar()
        self.global_streams_menu = ttk.Combobox(btn_frame, textvariable=self.global_streams_var, 
                                               state="readonly", width=30, font=("Arial", 8))
        self.global_streams_menu.pack(side="left")

        # Frame scrollable para condiciones
        canvas_frame = tk.Frame(self.frame_conditions)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def create_stats_frame(self, parent):
        """Crea el frame de estadísticas."""
        self.frame_stats = tk.LabelFrame(parent, text="📊 Estadísticas de Conexión", 
                                        font=("Arial", 10, "bold"), fg="orange")
        self.frame_stats.pack(fill="x")
        
        stats_inner = tk.Frame(self.frame_stats)
        stats_inner.pack(fill="x", padx=10, pady=5)
        
        self.lbl_uptime = tk.Label(stats_inner, text="⏱️ Tiempo activo: --", font=("Arial", 9))
        self.lbl_uptime.pack(side="left", padx=(0, 20))
        
        self.lbl_samples = tk.Label(stats_inner, text="📈 Muestras procesadas: 0", font=("Arial", 9))
        self.lbl_samples.pack(side="left", padx=(0, 20))
        
        self.lbl_commands = tk.Label(stats_inner, text="📤 Comandos enviados: 0", font=("Arial", 9))
        self.lbl_commands.pack(side="left")

    def _on_mousewheel(self, event):
        """Maneja el scroll del mouse en el canvas."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def refresh_all(self):
        """Actualiza la lista de puertos seriales y streams LSL."""
        self.update_serial_ports()
        self.update_streams()

    def update_serial_ports(self):
        """Actualiza la lista de puertos seriales disponibles."""
        try:
            ports = serial.tools.list_ports.comports()
            self.available_serial_ports = [f"{port.device} - {port.description}" for port in ports]
            self.serial_menu['values'] = self.available_serial_ports
            
            if self.available_serial_ports:
                self.serial_var.set(self.available_serial_ports[0])
            else:
                self.serial_var.set("")
                
        except Exception as e:
            messagebox.showwarning("Advertencia", f"Error al actualizar puertos: {e}")

    def update_streams(self):
        """Actualiza la lista de streams LSL disponibles."""
        try:
            streams = resolve_streams(wait_time=2.0)
            self.available_lsl_streams = [f"{s.name()} ({s.type()}) - {s.channel_count()}ch" for s in streams]
            
            self.global_streams_menu['values'] = self.available_lsl_streams
            if self.available_lsl_streams:
                self.global_streams_var.set(self.available_lsl_streams[0])
            else:
                self.global_streams_var.set("No hay streams disponibles")
                
            # Actualizar streams en filas existentes
            for row in self.condition_rows:
                row.stream_menu['values'] = self.available_lsl_streams
                
        except Exception as e:
            messagebox.showwarning("Advertencia", f"Error al resolver streams LSL: {e}")
            self.available_lsl_streams = []

    def add_stream_row(self):
        """Agrega una nueva fila de configuración de stream."""
        row_index = len(self.condition_rows)
        new_row = StreamConfigRow(self.scrollable_frame, self.available_lsl_streams, row_index)
        self.condition_rows.append(new_row)
        
        # Actualizar scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def remove_stream_row(self):
        """Elimina la última fila de configuración de stream."""
        if self.condition_rows:
            row = self.condition_rows.pop()
            row.destroy()
            
            # Actualizar scroll region
            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def setup_log_viewers(self):
        """Crea los cuadros de log para cada stream en modo simulación."""
        # Limpiar logs anteriores
        if hasattr(self, 'frame_logs') and self.frame_logs:
            self.frame_logs.destroy()
            
        self.frame_logs = tk.LabelFrame(self.master, text="🖥️ Visualización en Tiempo Real (Simulación)", 
                                       font=("Arial", 10, "bold"), fg="teal")
        self.frame_logs.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_viewers = {}
        
        for i, stream_id in enumerate(self.conditions_by_stream.keys()):
            frame = tk.LabelFrame(self.frame_logs, text=f"📡 {stream_id}", font=("Arial", 9))
            frame.pack(fill="both", expand=True, padx=5, pady=2)
            
            txt = scrolledtext.ScrolledText(frame, height=4, font=("Consolas", 8), 
                                          bg="navy", fg="white", state="disabled")
            txt.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.log_viewers[stream_id] = txt

    def update_log(self, stream_id, message):
        """Agrega un mensaje al log del stream correspondiente."""
        if stream_id in self.log_viewers:
            viewer = self.log_viewers[stream_id]
            viewer.config(state="normal")
            
            timestamp = time.strftime("%H:%M:%S")
            viewer.insert(tk.END, f"[{timestamp}] {message}\n")
            viewer.see(tk.END)
            
            # Limitar líneas del log
            lines = viewer.get("1.0", tk.END).count('\n')
            if lines > 100:
                viewer.delete("1.0", "11.0")
                
            viewer.config(state="disabled")

    def clear_console(self):
        """Limpia la consola serial."""
        self.serial_console.config(state="normal")
        self.serial_console.delete(1.0, tk.END)
        self.serial_console.config(state="disabled")

    def save_config(self):
        """Guarda la configuración actual en un archivo JSON."""
        if not self.condition_rows:
            messagebox.showinfo("Información", "No hay configuración para guardar.")
            return
            
        config = {
            "serial_port": self.serial_var.get(),
            "baud_rate": self.baud_var.get(),
            "simulate_serial": self.simulate_serial.get(),
            "conditions": []
        }
        
        for row in self.condition_rows:
            data = row.get_data()
            if data is not None:
                config["conditions"].append(data)
        
        if not config["conditions"]:
            messagebox.showinfo("Información", "No hay condiciones válidas para guardar.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Guardar Configuración"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")

    def load_config(self):
        """Carga una configuración desde un archivo JSON."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Cargar Configuración"
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Cargar configuración serial
                if "serial_port" in config:
                    self.serial_var.set(config["serial_port"])
                if "baud_rate" in config:
                    self.baud_var.set(str(config["baud_rate"]))
                if "simulate_serial" in config:
                    self.simulate_serial.set(config["simulate_serial"])
                
                # Limpiar filas actuales
                while self.condition_rows:
                    self.remove_stream_row()
                
                # Cargar condiciones
                for cond in config.get("conditions", []):
                    self.add_stream_row()
                    if self.condition_rows:
                        self.condition_rows[-1].set_data(cond)
                
                messagebox.showinfo("Éxito", "Configuración cargada correctamente.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar: {e}")

    def start_connection(self):
        """Inicia la conexión con los streams LSL y el puerto serial."""
        if not self.condition_rows:
            messagebox.showwarning("Advertencia", "Debe agregar al menos una condición antes de conectar.")
            return
        
        # Validar condiciones
        self.stream_conditions = []
        for row in self.condition_rows:
            data = row.get_data()
            if data is None:
                return  # Error ya mostrado en get_data()
            self.stream_conditions.append(data)

        # Configurar puerto serial
        if self.simulate_serial.get():
            baud_rate = int(self.baud_var.get())
            self.serial_connection = FakeSerial(baud_rate)
        else:
            port = self.serial_var.get()
            if not port:
                messagebox.showerror("Error", "Debe seleccionar un puerto serial.")
                return
            
            try:
                port_device = port.split(" - ")[0]  # Extraer solo el nombre del puerto
                baud_rate = int(self.baud_var.get())
                self.serial_connection = serial.Serial(port_device, baud_rate, timeout=1)
                time.sleep(2)  # Esperar estabilización
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo conectar al puerto {port}: {e}")
                return

        # Agrupar condiciones por stream
        self.conditions_by_stream = {}
        for cond in self.stream_conditions:
            stream_id = cond["stream"]
            self.conditions_by_stream.setdefault(stream_id, []).append(cond)

        # Conectar a streams LSL
        self.inlets = {}
        for stream_id in self.conditions_by_stream.keys():
            try:
                all_streams = resolve_streams(wait_time=2.0)
                stream_name = stream_id.split(" (")[0]  # Extraer nombre sin tipo
                match_streams = [s for s in all_streams if s.name() == stream_name]
                
                if not match_streams:
                    messagebox.showerror("Error", f"No se encontró el stream: {stream_id}")
                    self.cleanup_connection()
                    return
                    
                self.inlets[stream_id] = StreamInlet(match_streams[0])
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al conectar al stream {stream_id}: {e}")
                self.cleanup_connection()
                return

        # Actualizar interfaz
        self.disable_config_controls()
        self.running = True
        self.start_time = time.time()
        self.samples_processed = 0
        self.commands_sent = 0
        
        self.lbl_status.config(text="🟢 Estado: Conectado", fg="green")
        
        # Configurar logs si está en simulación
        if self.simulate_serial.get():
            self.setup_log_viewers()
        else:
            if hasattr(self, 'frame_logs') and self.frame_logs:
                self.frame_logs.destroy()
                self.frame_logs = None

        # Inicializar estadísticas
        self.last_samples = {stream_id: [] for stream_id in self.inlets.keys()}
        
        # Iniciar hilo de procesamiento
        self.lsl_thread = threading.Thread(target=self.lsl_connection_loop, daemon=True)
        self.lsl_thread.start()
        
        # Iniciar actualización de estadísticas
        self.update_stats()
        
        self.append_serial_console(f"🟢 Conexión establecida - Baudios: {baud_rate}\n")

    def cleanup_connection(self):
        """Limpia recursos de conexión en caso de error."""
        if hasattr(self, 'serial_connection') and self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
        
        for inlet in getattr(self, 'inlets', {}).values():
            try:
                inlet.close_stream()
            except:
                pass

    def stop_connection(self):
        """Detiene la conexión y libera recursos."""
        self.running = False
        
        # Actualizar interfaz
        self.lbl_status.config(text="🔴 Estado: Desconectado", fg="red")
        self.enable_config_controls()
        
        # Cerrar conexiones
        self.cleanup_connection()
        
        # Limpiar logs de simulación
        if hasattr(self, 'frame_logs') and self.frame_logs:
            self.frame_logs.destroy()
            self.frame_logs = None
        
        # Esperar a que termine el hilo
        if self.lsl_thread and self.lsl_thread.is_alive():
            self.lsl_thread.join(timeout=2)
        self.lsl_thread = None
        
        self.append_serial_console("🔴 Conexión terminada\n")

    def disable_config_controls(self):
        """Deshabilita controles de configuración durante la conexión."""
        self.btn_connect.config(state="disabled")
        self.btn_disconnect.config(state="normal")
        self.btn_add_stream.config(state="disabled")
        self.btn_remove_stream.config(state="disabled")
        self.btn_refresh_all.config(state="disabled")
        self.serial_menu.config(state="disabled")
        self.baud_menu.config(state="disabled")
        self.global_streams_menu.config(state="disabled")
        
        for row in self.condition_rows:
            row.stream_menu.config(state="disabled")
            row.pos_lower.config(state="disabled")
            row.pos_upper.config(state="disabled")
            row.pos_letter.config(state="disabled")
            row.neg_lower.config(state="disabled")
            row.neg_upper.config(state="disabled")
            row.neg_letter.config(state="disabled")

    def enable_config_controls(self):
        """Habilita controles de configuración tras desconexión."""
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.btn_add_stream.config(state="normal")
        self.btn_remove_stream.config(state="normal")
        self.btn_refresh_all.config(state="normal")
        self.serial_menu.config(state="readonly")
        self.baud_menu.config(state="readonly")
        self.global_streams_menu.config(state="readonly")
        
        for row in self.condition_rows:
            row.stream_menu.config(state="readonly")
            row.pos_lower.config(state="normal")
            row.pos_upper.config(state="normal")
            row.pos_letter.config(state="normal")
            row.neg_lower.config(state="normal")
            row.neg_upper.config(state="normal")
            row.neg_letter.config(state="normal")

    def append_serial_console(self, text):
        """Agrega texto a la consola serial."""
        if self.show_serial_console.get():
            self.serial_console.config(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            self.serial_console.insert(tk.END, f"[{timestamp}] {text}")
            self.serial_console.see(tk.END)
            
            # Limitar líneas
            lines = self.serial_console.get("1.0", tk.END).count('\n')
            if lines > 200:
                self.serial_console.delete("1.0", "21.0")
            
            self.serial_console.config(state="disabled")

    def update_stats(self):
        """Actualiza las estadísticas en tiempo real."""
        if self.running and self.start_time:
            # Tiempo activo
            uptime = int(time.time() - self.start_time)
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.lbl_uptime.config(text=f"⏱️ Tiempo activo: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Muestras y comandos
            self.lbl_samples.config(text=f"📈 Muestras procesadas: {self.samples_processed}")
            self.lbl_commands.config(text=f"📤 Comandos enviados: {self.commands_sent}")
            
            # Programar siguiente actualización
            self.master.after(1000, self.update_stats)

    def lsl_connection_loop(self):
        """Hilo principal para la lectura de streams LSL y envío por serial."""
        try:
            while self.running:
                for stream_id, inlet in self.inlets.items():
                    try:
                        sample, timestamp = inlet.pull_sample(timeout=0.01)
                        if sample:
                            self.samples_processed += 1
                            value = sample[0]  # Usar primer canal
                            
                            # Guardar muestra para estadísticas
                            self.last_samples[stream_id].append(value)
                            if len(self.last_samples[stream_id]) > 1000:
                                self.last_samples[stream_id] = self.last_samples[stream_id][-1000:]
                            
                            # Evaluar condiciones
                            for cond in self.conditions_by_stream.get(stream_id, []):
                                self.evaluate_condition(stream_id, value, cond, timestamp)
                                
                    except Exception as e:
                        if self.running:  # Solo mostrar error si aún está corriendo
                            self.master.after(0, self.append_serial_console, f"⚠️ Error en stream {stream_id}: {e}\n")
                
                time.sleep(0.001)  # Pequeña pausa para no saturar CPU
                
        except Exception as e:
            if self.running:
                traceback_str = traceback.format_exc()
                self.master.after(0, messagebox.showerror, "Error Crítico", 
                                f"Error en hilo de procesamiento:\n{e}\n\nDetalles:\n{traceback_str}")
                self.master.after(0, self.stop_connection)

    def evaluate_condition(self, stream_id, value, cond, timestamp):
        """Evalúa una condición específica y envía comando si corresponde."""
        command_sent = False
        
        # Evaluar condición positiva
        if cond["pos_upper"] is not None:
            pos_lower = cond["pos_lower"] if cond["pos_lower"] is not None else float('-inf')
            if pos_lower <= value <= cond["pos_upper"]:
                self.send_command(cond["pos_letter"])
                self.commands_sent += 1
                command_sent = True
                
                message = f"✅ Valor {value:.3f} en rango positivo [{pos_lower:.3f}, {cond['pos_upper']:.3f}] → '{cond['pos_letter']}'"
                
                if self.simulate_serial.get():
                    self.master.after(0, self.update_log, stream_id, message)
                
                self.master.after(0, self.append_serial_console, f"📤 {cond['pos_letter']}\n")
        
        # Evaluar condición negativa
        if cond["neg_upper"] is not None and not command_sent:  # Evitar comandos duplicados
            neg_lower = cond["neg_lower"] if cond["neg_lower"] is not None else float('-inf')
            if neg_lower <= value <= cond["neg_upper"]:
                self.send_command(cond["neg_letter"])
                self.commands_sent += 1
                command_sent = True
                
                message = f"❌ Valor {value:.3f} en rango negativo [{neg_lower:.3f}, {cond['neg_upper']:.3f}] → '{cond['neg_letter']}'"
                
                if self.simulate_serial.get():
                    self.master.after(0, self.update_log, stream_id, message)
                
                self.master.after(0, self.append_serial_console, f"📤 {cond['neg_letter']}\n")
        
        # Log de valores fuera de rango (solo en simulación)
        if self.simulate_serial.get() and not command_sent:
            message = f"📊 Valor {value:.3f} - Sin acción"
            self.master.after(0, self.update_log, stream_id, message)

    def send_command(self, command):
        """Envía un comando por el puerto serial."""
        try:
            if self.serial_connection:
                self.serial_connection.write(command.encode('utf-8'))
        except Exception as e:
            self.master.after(0, self.append_serial_console, f"❌ Error enviando '{command}': {e}\n")

    def toggle_serial_console(self):
        """Muestra u oculta la consola serial."""
        if self.show_serial_console.get():
            self.serial_console_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.serial_console_frame.pack_forget()

    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.running:
            if messagebox.askokcancel("Cerrar", "¿Desea desconectar y cerrar la aplicación?"):
                self.stop_connection()
                time.sleep(0.5)  # Dar tiempo para limpieza
                self.master.destroy()
        else:
            self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()