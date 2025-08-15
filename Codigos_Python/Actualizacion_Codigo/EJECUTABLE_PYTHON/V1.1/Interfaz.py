import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import serial
import serial.tools.list_ports
from pylsl import StreamInlet, resolve_streams
import json
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque

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

class RealTimeVisualizer:
    """Visualizador en tiempo real de datos LSL."""
    def __init__(self, parent_frame, stream_id, max_points=500):
        self.stream_id = stream_id
        self.max_points = max_points
        self.data_buffer = deque(maxlen=max_points)
        self.time_buffer = deque(maxlen=max_points)
        
        # Crear frame para este visualizador
        self.frame = tk.LabelFrame(parent_frame, text=f"📊 {stream_id}", font=("Arial", 9))
        self.frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Crear figura matplotlib
        self.fig = Figure(figsize=(8, 3), dpi=80, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Tiempo (s)')
        self.ax.set_ylabel('Amplitud')
        self.ax.grid(True, alpha=0.3)
        
        # Crear canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Línea de datos
        self.line, = self.ax.plot([], [], 'b-', linewidth=1.5, label='Señal')
        
        # Líneas de threshold (se configurarán dinámicamente)
        self.pos_threshold_line = None
        self.neg_threshold_line = None
        
        # Variables de tiempo
        self.start_time = time.time()
        
    def add_data_point(self, value, timestamp=None):
        """Agrega un punto de datos al visualizador."""
        if timestamp is None:
            current_time = time.time() - self.start_time
        else:
            current_time = timestamp - self.start_time if hasattr(self, 'start_time') else timestamp
            
        self.data_buffer.append(value)
        self.time_buffer.append(current_time)
        
    def update_thresholds(self, conditions):
        """Actualiza las líneas de threshold basadas en las condiciones."""
        self.ax.lines = [self.line]  # Mantener solo la línea principal
        
        for cond in conditions:
            # Línea de threshold positivo
            if cond.get("pos_upper") is not None:
                pos_upper = cond["pos_upper"]
                pos_lower = cond.get("pos_lower", float('-inf'))
                
                if pos_lower != float('-inf'):
                    self.ax.axhspan(pos_lower, pos_upper, alpha=0.2, color='green', 
                                   label=f'Positivo: [{pos_lower:.2f}, {pos_upper:.2f}]')
                else:
                    self.ax.axhline(y=pos_upper, color='green', linestyle='--', alpha=0.7,
                                   label=f'Pos Max: {pos_upper:.2f}')
            
            # Línea de threshold negativo
            if cond.get("neg_upper") is not None:
                neg_upper = cond["neg_upper"]
                neg_lower = cond.get("neg_lower", float('-inf'))
                
                if neg_lower != float('-inf'):
                    self.ax.axhspan(neg_lower, neg_upper, alpha=0.2, color='red',
                                   label=f'Negativo: [{neg_lower:.2f}, {neg_upper:.2f}]')
                else:
                    self.ax.axhline(y=neg_upper, color='red', linestyle='--', alpha=0.7,
                                   label=f'Neg Max: {neg_upper:.2f}')
        
        self.ax.legend(loc='upper right', fontsize=8)
        
    def update_plot(self):
        """Actualiza la gráfica con los datos actuales."""
        if len(self.data_buffer) > 1:
            # Actualizar datos de la línea
            self.line.set_data(list(self.time_buffer), list(self.data_buffer))
            
            # Ajustar límites del eje
            if self.time_buffer:
                self.ax.set_xlim(max(0, self.time_buffer[-1] - 30), self.time_buffer[-1] + 1)
                
            if self.data_buffer:
                data_array = np.array(list(self.data_buffer))
                margin = (np.max(data_array) - np.min(data_array)) * 0.1 or 1
                self.ax.set_ylim(np.min(data_array) - margin, np.max(data_array) + margin)
            
            # Redibujar canvas
            try:
                self.canvas.draw_idle()
            except:
                pass  # Ignorar errores de redibujado durante cierre
    
    def destroy(self):
        """Destruye el visualizador y libera recursos."""
        try:
            plt.close(self.fig)
            self.frame.destroy()
        except:
            pass

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

    def get_command_chars(self):
        """Obtiene los caracteres de comando definidos en esta fila."""
        chars = []
        if self.pos_letter.get().strip():
            chars.append(self.pos_letter.get().strip())
        if self.neg_letter.get().strip():
            chars.append(self.neg_letter.get().strip())
        return chars

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
        master.title("🔧 Interfaz de Configuración LSL y COM - v2.2 Enhanced")
        master.geometry("1400x1000")
        master.minsize(1200, 800)
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables de estado
        self.running = False
        self.test_mode_active = False
        self.log_viewers = {}
        self.visualizers = {}
        self.lsl_thread = None
        self.last_samples = {}
        self.serial_connection = None
        self.start_time = None
        self.lsl_reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # segundos
        self.stream_search_timeout = 10  # segundos para buscar streams
        
        # Variables de estadísticas
        self.samples_processed = 0
        self.commands_sent = 0
        self.connection_errors = 0
        self.lsl_reconnections = 0
        
        # Crear interfaz con scroll principal
        self.create_main_scroll()
        
        # Variables de datos
        self.available_serial_ports = []
        self.available_lsl_streams = []
        self.condition_rows = []
        self.inlets = {}
        self.conditions_by_stream = {}
        
        # Cargar datos iniciales
        self.refresh_all()
        
        # Configurar cierre de ventana
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_main_scroll(self):
        """Crea el sistema de scroll principal para toda la interfaz."""
        # Frame contenedor principal
        main_container = tk.Frame(self.master)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame principal con scrollbar
        self.main_canvas = tk.Canvas(main_container, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.main_canvas.yview)
        self.main_scrollable_frame = tk.Frame(self.main_canvas)

        # Configurar scroll
        def configure_scroll(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            # Ajustar ancho del frame scrollable al ancho del canvas
            canvas_width = self.main_canvas.winfo_width()
            if canvas_width > 1:
                self.main_canvas.itemconfig(self.canvas_frame, width=canvas_width)

        self.main_scrollable_frame.bind("<Configure>", configure_scroll)
        
        # Configurar el ancho del canvas cuando cambie de tamaño
        def configure_canvas(event):
            canvas_width = event.width
            self.main_canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
        self.main_canvas.bind("<Configure>", configure_canvas)

        self.canvas_frame = self.main_canvas.create_window((0, 0), window=self.main_scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        # Empaquetar correctamente
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        # Bind mousewheel para scroll
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", self._on_main_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(self.master)

        # Crear widgets en el frame scrollable
        self.create_widgets()

    def _on_main_mousewheel(self, event):
        """Maneja el scroll del mouse en la ventana principal."""
        self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # --- Frame de configuración del Puerto Serial ---
        self.create_serial_frame()
        
        # --- Frame de control ---
        self.create_control_frame()
        
        # --- Frame de prueba de comandos ---
        self.create_test_frame()
        
        # --- Frame de configuración de condiciones ---
        self.create_conditions_frame()
        
        # --- Frame de estadísticas ---
        self.create_stats_frame()
        
        # Actualizar scroll después de crear todos los widgets
        self.main_scrollable_frame.update_idletasks()
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def create_serial_frame(self):
        """Crea el frame de configuración serial."""
        self.frame_serial = tk.LabelFrame(self.main_scrollable_frame, text="🔌 Configuración Puerto Serial", 
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

        # Estado de conexión COM
        self.lbl_com_status = tk.Label(row1_frame, text="📡 COM: Sin conectar", 
                                      font=("Arial", 8), fg="gray")
        self.lbl_com_status.pack(side="left", padx=(10, 0))

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
        self.chk_show_console.pack(side="left", padx=(0, 20))

        self.auto_reconnect_lsl = tk.BooleanVar(value=True)
        self.chk_auto_reconnect = tk.Checkbutton(row2_frame, text="🔄 Reconexión automática LSL",
                                                variable=self.auto_reconnect_lsl, font=("Arial", 9))
        self.chk_auto_reconnect.pack(side="left", padx=(0, 20))

        # Nuevo checkbox para visualización
        self.show_realtime_plot = tk.BooleanVar(value=False)
        self.chk_show_plot = tk.Checkbutton(row2_frame, text="📊 Visualización en tiempo real",
                                           variable=self.show_realtime_plot,
                                           command=self.toggle_realtime_visualization, font=("Arial", 9))
        self.chk_show_plot.pack(side="left")

        # Tercera fila: Timeout de búsqueda
        row3_frame = tk.Frame(self.frame_serial)
        row3_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row3_frame, text="Timeout búsqueda streams (seg):", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        self.search_timeout_var = tk.StringVar(value="10")
        search_timeout_entry = tk.Entry(row3_frame, textvariable=self.search_timeout_var, width=5, font=("Arial", 9))
        search_timeout_entry.pack(side="left", padx=(0, 20))

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

    def create_control_frame(self):
        """Crea el frame de control."""
        self.frame_control = tk.LabelFrame(self.main_scrollable_frame, text="🎛️ Control de Conexión", 
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
        status_frame = tk.Frame(btn_frame)
        status_frame.pack(side="left", padx=(0, 20))
        
        self.lbl_status = tk.Label(status_frame, text="⚫ Estado: Desconectado", 
                                  font=("Arial", 9, "bold"), fg="red")
        self.lbl_status.pack()
        
        self.lbl_lsl_status = tk.Label(status_frame, text="📡 LSL: Sin streams", 
                                      font=("Arial", 8), fg="gray")
        self.lbl_lsl_status.pack()

        # Botones de configuración
        config_frame = tk.Frame(control_inner)
        config_frame.pack(side="right")
        
        self.btn_save = tk.Button(config_frame, text="💾 Guardar Config", command=self.save_config,
                                 font=("Arial", 8))
        self.btn_save.pack(side="left", padx=(0, 5))
        
        self.btn_load = tk.Button(config_frame, text="📂 Cargar Config", command=self.load_config,
                                 font=("Arial", 8))
        self.btn_load.pack(side="left")

    def create_test_frame(self):
        """Crea el frame de prueba de comandos."""
        self.frame_test = tk.LabelFrame(self.main_scrollable_frame, text="🧪 Prueba de Comandos", 
                                       font=("Arial", 10, "bold"), fg="darkorange")
        self.frame_test.pack(fill="x", pady=(0, 10))

        # Control de prueba
        test_control_frame = tk.Frame(self.frame_test)
        test_control_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_start_test = tk.Button(test_control_frame, text="🔬 Iniciar Prueba", 
                                       command=self.start_test_mode, bg="lightyellow", font=("Arial", 9, "bold"))
        self.btn_start_test.pack(side="left", padx=(0, 5))
        
        self.btn_stop_test = tk.Button(test_control_frame, text="⏹️ Detener Prueba", 
                                      command=self.stop_test_mode, state="disabled", 
                                      bg="lightgray", font=("Arial", 9, "bold"))
        self.btn_stop_test.pack(side="left", padx=(0, 20))
        
        self.lbl_test_status = tk.Label(test_control_frame, text="🔴 Prueba: Inactiva", 
                                       font=("Arial", 9, "bold"), fg="red")
        self.lbl_test_status.pack(side="left")

        # Panel de comandos manuales
        manual_frame = tk.Frame(self.frame_test)
        manual_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(manual_frame, text="Comando manual:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        self.manual_command_var = tk.StringVar()
        self.manual_command_entry = tk.Entry(manual_frame, textvariable=self.manual_command_var, 
                                           width=10, font=("Arial", 9))
        self.manual_command_entry.pack(side="left", padx=(0, 5))
        self.manual_command_entry.bind("<Return>", self.send_manual_command)
        
        self.btn_send_manual = tk.Button(manual_frame, text="📤 Enviar", 
                                        command=self.send_manual_command, font=("Arial", 8))
        self.btn_send_manual.pack(side="left", padx=(0, 20))

        # Comandos rápidos
        self.quick_commands_frame = tk.Frame(manual_frame)
        self.quick_commands_frame.pack(side="left")
        
        tk.Label(self.quick_commands_frame, text="Comandos rápidos:", font=("Arial", 9)).pack(side="left", padx=(0, 5))
        
        # Frame para botones de comandos rápidos
        self.quick_buttons_frame = tk.Frame(self.quick_commands_frame)
        self.quick_buttons_frame.pack(side="left")

        # Test log
        test_log_frame = tk.LabelFrame(self.frame_test, text="📝 Log de Pruebas", font=("Arial", 9))
        test_log_frame.pack(fill="x", padx=10, pady=5)
        
        self.test_log = scrolledtext.ScrolledText(test_log_frame, height=3, state="disabled",
                                                 font=("Consolas", 8), bg="navy", fg="white")
        self.test_log.pack(fill="x", padx=5, pady=5)

    def create_conditions_frame(self):
        """Crea el frame de configuración de condiciones."""
        self.frame_conditions = tk.LabelFrame(self.main_scrollable_frame, text="⚙️ Configuración de Condiciones", 
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

    def create_stats_frame(self):
        """Crea el frame de estadísticas."""
        self.frame_stats = tk.LabelFrame(self.main_scrollable_frame, text="📊 Estadísticas de Conexión", 
                                        font=("Arial", 10, "bold"), fg="orange")
        self.frame_stats.pack(fill="x")
        
        # Primera fila de estadísticas
        stats_row1 = tk.Frame(self.frame_stats)
        stats_row1.pack(fill="x", padx=10, pady=5)
        
        self.lbl_uptime = tk.Label(stats_row1, text="⏱️ Tiempo activo: --", font=("Arial", 9))
        self.lbl_uptime.pack(side="left", padx=(0, 20))
        
        self.lbl_samples = tk.Label(stats_row1, text="📈 Muestras procesadas: 0", font=("Arial", 9))
        self.lbl_samples.pack(side="left", padx=(0, 20))
        
        self.lbl_commands = tk.Label(stats_row1, text="📤 Comandos enviados: 0", font=("Arial", 9))
        self.lbl_commands.pack(side="left")

        # Segunda fila de estadísticas
        stats_row2 = tk.Frame(self.frame_stats)
        stats_row2.pack(fill="x", padx=10, pady=(0, 5))
        
        self.lbl_errors = tk.Label(stats_row2, text="⚠️ Errores de conexión: 0", font=("Arial", 9))
        self.lbl_errors.pack(side="left", padx=(0, 20))
        
        self.lbl_reconnections = tk.Label(stats_row2, text="🔄 Reconexiones LSL: 0", font=("Arial", 9))
        self.lbl_reconnections.pack(side="left", padx=(0, 20))

    def _on_mousewheel(self, event):
        """Maneja el scroll del mouse en el canvas de condiciones."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def refresh_all(self):
        """Actualiza la lista de puertos seriales y streams LSL."""
        self.update_serial_ports()
        self.update_streams()
        self.update_quick_commands()

    def update_serial_ports(self):
        """Actualiza la lista de puertos seriales disponibles."""
        try:
            ports = serial.tools.list_ports.comports()
            self.available_serial_ports = [f"{port.device} - {port.description}" for port in ports]
            self.serial_menu['values'] = self.available_serial_ports
            
            if self.available_serial_ports:
                if not self.serial_var.get() or self.serial_var.get() not in self.available_serial_ports:
                    self.serial_var.set(self.available_serial_ports[0])
            else:
                self.serial_var.set("")
                
        except Exception as e:
            self.append_serial_console(f"⚠️ Error al actualizar puertos: {e}\n")
            messagebox.showwarning("Advertencia", f"Error al actualizar puertos: {e}")

    def update_streams(self):
        """Actualiza la lista de streams LSL disponibles."""
        try:
            streams = resolve_streams(wait_time=2.0)
            self.available_lsl_streams = [f"{s.name()} ({s.type()}) - {s.channel_count()}ch" for s in streams]
            
            self.global_streams_menu['values'] = self.available_lsl_streams
            if self.available_lsl_streams:
                self.global_streams_var.set(self.available_lsl_streams[0])
                self.lbl_lsl_status.config(text=f"📡 LSL: {len(self.available_lsl_streams)} streams", fg="green")
            else:
                self.global_streams_var.set("No hay streams disponibles")
                self.lbl_lsl_status.config(text="📡 LSL: Sin streams", fg="gray")
                
            # Actualizar streams en filas existentes
            for row in self.condition_rows:
                row.stream_menu['values'] = self.available_lsl_streams
                
        except Exception as e:
            self.append_serial_console(f"⚠️ Error al resolver streams LSL: {e}\n")
            self.lbl_lsl_status.config(text="📡 LSL: Error", fg="red")
            self.available_lsl_streams = []

    def update_quick_commands(self):
        """Actualiza los botones de comandos rápidos basados en las condiciones configuradas."""
        # Limpiar botones existentes
        for widget in self.quick_buttons_frame.winfo_children():
            widget.destroy()
        
        # Obtener comandos únicos de todas las filas
        commands = set()
        for row in self.condition_rows:
            commands.update(row.get_command_chars())
        
        # Crear botones para cada comando
        for i, cmd in enumerate(sorted(commands)):
            if cmd:  # Solo si el comando no está vacío
                btn = tk.Button(self.quick_buttons_frame, text=cmd, 
                               command=lambda c=cmd: self.send_test_command(c),
                               width=3, height=1, font=("Arial", 8, "bold"),
                               bg="lightcyan", relief="raised")
                btn.pack(side="left", padx=1)

    def add_stream_row(self):
        """Agrega una nueva fila de configuración de stream."""
        row_index = len(self.condition_rows)
        new_row = StreamConfigRow(self.scrollable_frame, self.available_lsl_streams, row_index)
        self.condition_rows.append(new_row)
        
        # Actualizar scroll region y comandos rápidos
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.master.after(100, self.update_quick_commands)

    def remove_stream_row(self):
        """Elimina la última fila de configuración de stream."""
        if self.condition_rows:
            row = self.condition_rows.pop()
            row.destroy()
            
            # Actualizar scroll region y comandos rápidos
            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.update_quick_commands()

    def toggle_realtime_visualization(self):
        """Activa o desactiva la visualización en tiempo real."""
        if self.show_realtime_plot.get():
            self.append_serial_console("📊 Visualización en tiempo real activada\n")
        else:
            self.append_serial_console("📊 Visualización en tiempo real desactivada\n")
            # Destruir visualizadores existentes
            self.cleanup_visualizers()

    def setup_realtime_visualizers(self):
        """Crea los visualizadores en tiempo real para cada stream configurado."""
        if not self.show_realtime_plot.get():
            return
            
        # Limpiar visualizadores anteriores
        self.cleanup_visualizers()
        
        # Crear frame para visualizadores
        self.frame_visualizers = tk.LabelFrame(self.main_scrollable_frame, 
                                              text="📊 Visualización en Tiempo Real", 
                                              font=("Arial", 10, "bold"), fg="teal")
        self.frame_visualizers.pack(fill="both", expand=True, padx=0, pady=5)
        
        # Crear visualizador para cada stream único
        for stream_id in self.conditions_by_stream.keys():
            visualizer = RealTimeVisualizer(self.frame_visualizers, stream_id)
            self.visualizers[stream_id] = visualizer
            
            # Configurar thresholds basados en las condiciones
            conditions = self.conditions_by_stream[stream_id]
            visualizer.update_thresholds(conditions)

    def cleanup_visualizers(self):
        """Limpia todos los visualizadores existentes."""
        for visualizer in self.visualizers.values():
            visualizer.destroy()
        self.visualizers.clear()
        
        if hasattr(self, 'frame_visualizers') and self.frame_visualizers:
            self.frame_visualizers.destroy()
            self.frame_visualizers = None

    def update_visualizers(self):
        """Actualiza todos los visualizadores en tiempo real."""
        if not self.show_realtime_plot.get() or not self.visualizers:
            return
            
        for stream_id, visualizer in self.visualizers.items():
            try:
                visualizer.update_plot()
            except Exception as e:
                # Silenciosamente ignorar errores de actualización durante cierre
                pass
        
        # Programar siguiente actualización
        if self.running:
            self.master.after(100, self.update_visualizers)  # Actualizar cada 100ms

    def wait_for_streams_with_progress(self, required_streams, timeout=10):
        """Espera a que aparezcan los streams requeridos con indicador de progreso."""
        self.append_serial_console(f"🔍 Buscando streams configurados (timeout: {timeout}s)...\n")
        
        start_time = time.time()
        found_streams = []
        
        while time.time() - start_time < timeout:
            try:
                # Resolver streams disponibles
                available_streams = resolve_streams(wait_time=0.5)
                available_names = [f"{s.name()} ({s.type()}) - {s.channel_count()}ch" for s in available_streams]
                
                # Verificar cuáles streams requeridos están disponibles
                current_found = []
                for req_stream in required_streams:
                    if req_stream in available_names:
                        current_found.append(req_stream)
                
                # Actualizar progreso si hay cambios
                if len(current_found) != len(found_streams):
                    found_streams = current_found[:]
                    elapsed = time.time() - start_time
                    progress_msg = f"🔍 Encontrados {len(found_streams)}/{len(required_streams)} streams ({elapsed:.1f}s)"
                    
                    if found_streams:
                        progress_msg += f" - Disponibles: {', '.join([s.split(' (')[0] for s in found_streams])}"
                    
                    self.append_serial_console(f"{progress_msg}\n")
                    
                    # Si encontramos todos los streams, salir
                    if len(found_streams) == len(required_streams):
                        self.append_serial_console("✅ Todos los streams encontrados!\n")
                        return True, found_streams
                
                # Pequeña pausa para no saturar
                time.sleep(0.2)
                
            except Exception as e:
                self.append_serial_console(f"⚠️ Error durante búsqueda: {e}\n")
        
        # Timeout alcanzado
        missing_streams = [s for s in required_streams if s not in found_streams]
        if missing_streams:
            self.append_serial_console(f"⚠️ Timeout: faltan streams: {', '.join([s.split(' (')[0] for s in missing_streams])}\n")
            
            # Mostrar diálogo de confirmación
            response = messagebox.askyesno(
                "Streams Faltantes",
                f"No se encontraron los siguientes streams después de {timeout} segundos:\n\n" +
                "\n".join([f"• {s.split(' (')[0]}" for s in missing_streams]) +
                f"\n\nStreams encontrados: {len(found_streams)}/{len(required_streams)}\n\n" +
                "¿Desea continuar con los streams disponibles?",
                icon="warning"
            )
            
            if response:
                return True, found_streams
            else:
                return False, []
        
        return True, found_streams

    def start_test_mode(self):
        """Inicia el modo de prueba de comandos."""
        if not self.test_mode_active:
            # Configurar conexión serial para pruebas
            try:
                if self.simulate_serial.get():
                    baud_rate = int(self.baud_var.get())
                    self.serial_connection = FakeSerial(baud_rate)
                else:
                    port = self.serial_var.get()
                    if not port:
                        messagebox.showerror("Error", "Debe seleccionar un puerto serial.")
                        return
                    
                    port_device = port.split(" - ")[0]
                    baud_rate = int(self.baud_var.get())
                    self.serial_connection = serial.Serial(port_device, baud_rate, timeout=1)
                    time.sleep(2)
                
                self.test_mode_active = True
                self.btn_start_test.config(state="disabled")
                self.btn_stop_test.config(state="normal")
                self.lbl_test_status.config(text="🟢 Prueba: Activa", fg="green")
                self.lbl_com_status.config(text="📡 COM: Conectado (Prueba)", fg="green")
                
                self.append_test_log("🟢 Modo de prueba iniciado")
                self.append_serial_console("🧪 Modo de prueba activado\n")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al iniciar modo de prueba: {e}")
                self.connection_errors += 1

    def stop_test_mode(self):
        """Detiene el modo de prueba de comandos."""
        if self.test_mode_active:
            self.test_mode_active = False
            
            # Cerrar conexión serial si existe
            if self.serial_connection:
                try:
                    self.serial_connection.close()
                except:
                    pass
                self.serial_connection = None
            
            self.btn_start_test.config(state="normal")
            self.btn_stop_test.config(state="disabled")
            self.lbl_test_status.config(text="🔴 Prueba: Inactiva", fg="red")
            self.lbl_com_status.config(text="📡 COM: Sin conectar", fg="gray")
            
            self.append_test_log("🔴 Modo de prueba detenido")
            self.append_serial_console("🧪 Modo de prueba desactivado\n")

    def send_manual_command(self, event=None):
        """Envía un comando manual durante el modo de prueba."""
        if not self.test_mode_active:
            messagebox.showwarning("Advertencia", "Debe iniciar el modo de prueba primero.")
            return
        
        command = self.manual_command_var.get().strip()
        if command:
            self.send_test_command(command)
            self.manual_command_var.set("")  # Limpiar campo

    def send_test_command(self, command):
        """Envía un comando de prueba por el puerto serial."""
        if not self.test_mode_active:
            messagebox.showwarning("Advertencia", "Debe iniciar el modo de prueba primero.")
            return
        
        try:
            if self.serial_connection:
                self.serial_connection.write(command.encode('utf-8'))
                self.commands_sent += 1
                
                self.append_test_log(f"📤 Comando enviado: '{command}'")
                self.append_serial_console(f"🧪 TEST: {command}\n")
                
        except Exception as e:
            self.append_test_log(f"❌ Error enviando '{command}': {e}")
            self.connection_errors += 1

    def append_test_log(self, message):
        """Agrega un mensaje al log de pruebas."""
        self.test_log.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.test_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.test_log.see(tk.END)
        
        # Limitar líneas del log
        lines = self.test_log.get("1.0", tk.END).count('\n')
        if lines > 50:
            self.test_log.delete("1.0", "11.0")
            
        self.test_log.config(state="disabled")

    def setup_log_viewers(self):
        """Crea los cuadros de log para cada stream en modo simulación."""
        # Limpiar logs anteriores
        if hasattr(self, 'frame_logs') and self.frame_logs:
            self.frame_logs.destroy()
            
        self.frame_logs = tk.LabelFrame(self.main_scrollable_frame, text="🖥️ Visualización en Tiempo Real (Simulación)", 
                                       font=("Arial", 10, "bold"), fg="teal")
        self.frame_logs.pack(fill="both", expand=True, padx=0, pady=5)
        
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
            "auto_reconnect_lsl": self.auto_reconnect_lsl.get(),
            "show_realtime_plot": self.show_realtime_plot.get(),
            "search_timeout": self.search_timeout_var.get(),
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
                if "auto_reconnect_lsl" in config:
                    self.auto_reconnect_lsl.set(config["auto_reconnect_lsl"])
                if "show_realtime_plot" in config:
                    self.show_realtime_plot.set(config["show_realtime_plot"])
                if "search_timeout" in config:
                    self.search_timeout_var.set(str(config["search_timeout"]))
                
                # Limpiar filas actuales
                while self.condition_rows:
                    self.remove_stream_row()
                
                # Cargar condiciones
                for cond in config.get("conditions", []):
                    self.add_stream_row()
                    if self.condition_rows:
                        self.condition_rows[-1].set_data(cond)
                
                self.update_quick_commands()
                messagebox.showinfo("Éxito", "Configuración cargada correctamente.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar: {e}")

    def start_connection(self):
        """Inicia la conexión con los streams LSL y el puerto serial."""
        if self.test_mode_active:
            messagebox.showwarning("Advertencia", "Debe detener el modo de prueba antes de conectar.")
            return
            
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

        # Agrupar condiciones por stream
        self.conditions_by_stream = {}
        required_streams = []
        for cond in self.stream_conditions:
            stream_id = cond["stream"]
            self.conditions_by_stream.setdefault(stream_id, []).append(cond)
            if stream_id not in required_streams:
                required_streams.append(stream_id)

        # Obtener timeout de búsqueda
        try:
            search_timeout = float(self.search_timeout_var.get())
            if search_timeout <= 0:
                search_timeout = 10
        except ValueError:
            search_timeout = 10
            self.search_timeout_var.set("10")

        # Buscar streams configurados con timeout
        success, found_streams = self.wait_for_streams_with_progress(required_streams, search_timeout)
        
        if not success:
            self.append_serial_console("❌ Conexión cancelada por el usuario\n")
            return

        # Actualizar condiciones solo para streams encontrados
        if len(found_streams) < len(required_streams):
            self.conditions_by_stream = {k: v for k, v in self.conditions_by_stream.items() if k in found_streams}
            
        if not self.conditions_by_stream:
            messagebox.showerror("Error", "No se encontraron streams configurados.")
            return

        # Configurar puerto serial
        try:
            if self.simulate_serial.get():
                baud_rate = int(self.baud_var.get())
                self.serial_connection = FakeSerial(baud_rate)
            else:
                port = self.serial_var.get()
                if not port:
                    messagebox.showerror("Error", "Debe seleccionar un puerto serial.")
                    return
                
                port_device = port.split(" - ")[0]  # Extraer solo el nombre del puerto
                baud_rate = int(self.baud_var.get())
                self.serial_connection = serial.Serial(port_device, baud_rate, timeout=1)
                time.sleep(2)  # Esperar estabilización
            
            self.lbl_com_status.config(text="📡 COM: Conectado", fg="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al puerto {self.serial_var.get()}: {e}")
            self.connection_errors += 1

        # Conectar a los streams LSL
        if not self.connect_to_lsl_streams():
            return

        # Iniciar loop de LSL en un thread separado
        self.running = True
        self.lsl_reconnect_attempts = 0
        self.samples_processed = 0
        self.commands_sent = 0
        self.connection_errors = 0
        self.lsl_reconnections = 0
        self.start_time = time.time()
        
        self.lbl_status.config(text="🟢 Estado: Conectado", fg="green")
        self.append_serial_console("✅ Conexión establecida\n")
        
        # Deshabilitar controles de configuración
        self.disable_config_controls()
        
        # Iniciar thread de conexión LSL
        self.lsl_thread = threading.Thread(target=self.lsl_connection_loop, daemon=True)
        self.lsl_thread.start()
        
        # Actualizar estadísticas
        self.update_stats()

    def connect_to_lsl_streams(self):
        """Conecta a los streams LSL configurados."""
        try:
            # Resolver streams disponibles
            streams = resolve_streams(wait_time=1.0)
            streams_dict = {f"{s.name()} ({s.type()}) - {s.channel_count()}ch": s for s in streams}
            
            # Conectar a cada stream configurado
            self.inlets = {}
            for stream_id in self.conditions_by_stream.keys():
                if stream_id in streams_dict:
                    self.inlets[stream_id] = StreamInlet(streams_dict[stream_id])
                    self.append_serial_console(f"✅ Conectado a stream: {stream_id}\n")
                else:
                    self.append_serial_console(f"⚠️ Stream no encontrado: {stream_id}\n")
                    return False
                
            return True
            
        except Exception as e:
            self.append_serial_console(f"❌ Error conectando a streams LSL: {e}\n")
            return False

    def disable_config_controls(self):
        """Deshabilita controles de configuración durante la conexión."""
        self.btn_connect.config(state="disabled")
        self.btn_disconnect.config(state="normal")
        self.btn_add_stream.config(state="disabled")
        self.btn_remove_stream.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.btn_load.config(state="disabled")
        self.btn_start_test.config(state="disabled")
        
        for row in self.condition_rows:
            for widget in row.widgets:
                if isinstance(widget, (ttk.Combobox, tk.Entry)):
                    widget.config(state="disabled")

    def enable_config_controls(self):
        """Habilita controles de configuración después de desconectar."""
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.btn_add_stream.config(state="normal")
        self.btn_remove_stream.config(state="normal")
        self.btn_save.config(state="normal")
        self.btn_load.config(state="normal")
        self.btn_start_test.config(state="normal")
        
        for row in self.condition_rows:
            for widget in row.widgets:
                if isinstance(widget, ttk.Combobox):
                    widget.config(state="readonly")
                elif isinstance(widget, tk.Entry):
                    widget.config(state="normal")

    def stop_connection(self):
        """Detiene la conexión actual."""
        self.running = False
        
        # Cerrar conexiones
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        for inlet in self.inlets.values():
            try:
                inlet.close_stream()
            except:
                pass
        self.inlets.clear()
        
        # Limpiar visualizadores y logs
        self.cleanup_visualizers()
        if hasattr(self, 'frame_logs'):
            self.frame_logs.destroy()
        self.log_viewers.clear()
        
        # Actualizar interfaz
        self.enable_config_controls()
        self.lbl_status.config(text="⚫ Estado: Desconectado", fg="red")
        self.lbl_com_status.config(text="📡 COM: Sin conectar", fg="gray")
        
        self.append_serial_console("🔴 Conexión detenida\n")

    def evaluate_condition(self, stream_id, value, timestamp):
        """Evalúa todas las condiciones para un stream y valor específico."""
        conditions = self.conditions_by_stream.get(stream_id, [])
        
        # Actualizar visualizador si está activado
        if self.show_realtime_plot.get() and stream_id in self.visualizers:
            self.visualizers[stream_id].add_data_point(value, timestamp)
        
        # Evaluar cada condición
        for cond in conditions:
            # Condición positiva
            if (cond.get("pos_upper") is not None and 
                (cond.get("pos_lower") is None or value >= cond["pos_lower"]) and
                value <= cond["pos_upper"] and
                cond.get("pos_letter")):
                
                self.send_command(cond["pos_letter"])
                return
                
            # Condición negativa
            if (cond.get("neg_upper") is not None and 
                (cond.get("neg_lower") is None or value >= cond["neg_lower"]) and
                value <= cond["neg_upper"] and
                cond.get("neg_letter")):
                
                self.send_command(cond["neg_letter"])
                return

    def send_command(self, command):
        """Envía un comando por el puerto serial."""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(command.encode('utf-8'))
                self.commands_sent += 1
                self.append_serial_console(f"📤 {command}\n")
                
        except Exception as e:
            self.append_serial_console(f"⚠️ Error enviando comando: {e}\n")
            self.connection_errors += 1

    def lsl_connection_loop(self):
        """Loop principal de procesamiento de datos LSL."""
        while self.running:
            try:
                # Procesar cada stream
                for stream_id, inlet in self.inlets.items():
                    sample, timestamp = inlet.pull_sample(timeout=0.0)
                    if sample is not None:
                        value = sample[0]  # Tomar primer canal
                        self.samples_processed += 1
                        
                        # Actualizar log en modo simulación
                        if self.simulate_serial.get() and stream_id in self.log_viewers:
                            self.update_log(stream_id, f"Valor: {value:.3f}")
                        
                        # Evaluar condiciones
                        self.evaluate_condition(stream_id, value, timestamp)
                        
                time.sleep(0.001)  # Pequeña pausa
                
            except Exception as e:
                if self.running:
                    self.append_serial_console(f"⚠️ Error en loop LSL: {e}\n")
                    if self.auto_reconnect_lsl.get() and self.lsl_reconnect_attempts < self.max_reconnect_attempts:
                        self.lsl_reconnect_attempts += 1
                        self.lsl_reconnections += 1
                        self.append_serial_console(f"🔄 Intentando reconexión ({self.lsl_reconnect_attempts}/{self.max_reconnect_attempts})...\n")
                        time.sleep(self.reconnect_delay)
                        if self.connect_to_lsl_streams():
                            continue
                    
                    self.stop_connection()
                    messagebox.showerror("Error", f"Error en conexión LSL: {e}")

    def update_stats(self):
        """Actualiza las estadísticas en la interfaz."""
        if self.running:
            # Calcular tiempo activo
            uptime = time.time() - self.start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            
            # Actualizar etiquetas
            self.lbl_uptime.config(text=f"⏱️ Tiempo activo: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.lbl_samples.config(text=f"📈 Muestras procesadas: {self.samples_processed}")
            self.lbl_commands.config(text=f"📤 Comandos enviados: {self.commands_sent}")
            self.lbl_errors.config(text=f"⚠️ Errores de conexión: {self.connection_errors}")
            self.lbl_reconnections.config(text=f"🔄 Reconexiones LSL: {self.lsl_reconnections}")
            
            # Actualizar visualizadores si están activos
            self.update_visualizers()
            
            # Programar siguiente actualización
            self.master.after(1000, self.update_stats)

    def toggle_serial_console(self):
        """Muestra u oculta la consola serial."""
        if self.show_serial_console.get():
            self.serial_console_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.serial_console_frame.pack_forget()

    def append_serial_console(self, message):
        """Agrega un mensaje a la consola serial."""
        self.serial_console.config(state="normal")
        self.serial_console.insert(tk.END, message)
        self.serial_console.see(tk.END)
        
        # Limitar líneas
        lines = self.serial_console.get("1.0", tk.END).count('\n')
        if lines > 1000:
            self.serial_console.delete("1.0", "101.0")
        
        self.serial_console.config(state="disabled")

    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.running:
            if messagebox.askokcancel("Confirmar Salida", 
                                     "Hay una conexión activa. ¿Desea cerrar la aplicación?"):
                self.stop_connection()
            else:
                return
            
        self.master.destroy()

def main():
    """Función principal que inicia la aplicación."""
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()