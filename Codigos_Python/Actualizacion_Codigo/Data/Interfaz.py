import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os

class EOGAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador EOG - Interfaz Interactiva")
        self.root.geometry("1200x800")
        
        # Configurar el cierre de la aplicación
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables para almacenar datos
        self.df = None
        self.csv_path = ""
        
        # Crear la interfaz
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar el grid para que se expanda
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # ============================================================================
        # 1. SELECCIÓN DE ARCHIVO
        # ============================================================================
        ttk.Label(main_frame, text="Archivo CSV:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        self.file_var = tk.StringVar()
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        file_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(file_frame, text="Seleccionar", command=self.select_file).grid(row=0, column=1)
        
        # ============================================================================
        # 2. PARÁMETROS K Y K_MAX
        # ============================================================================
        params_frame = ttk.LabelFrame(main_frame, text="Parámetros de Análisis", padding="10")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Parámetro K
        ttk.Label(params_frame, text="Factor K (umbrales mínimos):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.k_var = tk.DoubleVar(value=2.2)
        k_spinbox = tk.Spinbox(params_frame, from_=1.0, to=5.0, increment=0.1, 
                              textvariable=self.k_var, width=10, format="%.1f")
        k_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        # Parámetro K_MAX
        ttk.Label(params_frame, text="Factor K_max (límites máximos):").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.k_max_var = tk.DoubleVar(value=3.0)
        k_max_spinbox = tk.Spinbox(params_frame, from_=1.5, to=6.0, increment=0.1, 
                                  textvariable=self.k_max_var, width=10, format="%.1f")
        k_max_spinbox.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # Información de parámetros
        info_text = "K: Factor para umbrales mínimos (1.5-3.0 típico) | K_max: Factor para límites máximos"
        ttk.Label(params_frame, text=info_text, font=('Arial', 8), foreground='gray').grid(
            row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # ============================================================================
        # 3. BOTONES DE CONTROL
        # ============================================================================
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.analyze_button = ttk.Button(button_frame, text="Analizar EOG", 
                                        command=self.analyze_eog, style="Accent.TButton")
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Limpiar", command=self.clear_analysis).pack(side=tk.LEFT)
        
        # ============================================================================
        # 4. ÁREA DE RESULTADOS
        # ============================================================================
        results_frame = ttk.LabelFrame(main_frame, text="Resultados del Análisis", padding="10")
        results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        results_frame.columnconfigure(0, weight=1)
        
        # Text widget para mostrar estadísticas
        self.results_text = tk.Text(results_frame, height=8, width=80, font=('Consolas', 9))
        scrollbar_results = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar_results.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_results.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # ============================================================================
        # 5. ÁREA DEL GRÁFICO
        # ============================================================================
        graph_frame = ttk.LabelFrame(main_frame, text="Visualización EOG", padding="5")
        graph_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
        
        # Crear figura de matplotlib
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Inicializar con gráfico vacío
        self.ax.text(0.5, 0.5, 'Seleccione un archivo CSV y presione "Analizar EOG"', 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=self.ax.transAxes, fontsize=14, color='gray')
        self.ax.set_title('Análisis EOG: Umbrales Mínimos y Límites Máximos')
        self.canvas.draw()
        
    def select_file(self):
        """Seleccionar archivo CSV"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            self.csv_path = file_path
            self.file_var.set(file_path)
            # Limpiar análisis anterior
            self.clear_analysis()
            
    def analyze_eog(self):
        """Realizar análisis EOG con los parámetros actuales"""
        if not self.csv_path:
            messagebox.showerror("Error", "Por favor seleccione un archivo CSV primero")
            return
        
        try:
            # Cargar datos
            self.df = pd.read_csv(self.csv_path, sep=';')
            
            # Verificar que existan las columnas necesarias
            if 'Time (s)' not in self.df.columns or 'EOG1' not in self.df.columns:
                messagebox.showerror("Error", 
                    "El archivo CSV debe contener las columnas 'Time (s)' y 'EOG1'")
                return
            
            # Extraer datos
            time = self.df['Time (s)']
            signal = self.df['EOG1']
            
            # Obtener parámetros de la interfaz
            k = self.k_var.get()
            k_max = self.k_max_var.get()
            
            # Cálculos estadísticos
            mu = signal.mean()
            sigma = signal.std()
            
            # Umbrales y límites
            threshold_high = mu + k * sigma
            threshold_low = mu - k * sigma
            max_limit_high = mu + k_max * sigma
            max_limit_low = mu - k_max * sigma
            
            # Detección de activaciones
            activation_pos = signal > threshold_high
            activation_neg = signal < threshold_low
            
            # Actualizar gráfico
            self.update_plot(time, signal, mu, sigma, k, k_max, 
                           threshold_high, threshold_low, 
                           max_limit_high, max_limit_low,
                           activation_pos, activation_neg)
            
            # Actualizar resultados
            self.update_results(mu, sigma, k, k_max, threshold_high, threshold_low,
                              max_limit_high, max_limit_low, activation_pos, activation_neg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el archivo:\n{str(e)}")
    
    def update_plot(self, time, signal, mu, sigma, k, k_max, 
                   threshold_high, threshold_low, max_limit_high, max_limit_low,
                   activation_pos, activation_neg):
        """Actualizar el gráfico con los nuevos datos"""
        self.ax.clear()
        
        # Señal principal
        self.ax.plot(time, signal, label='Señal EOG', linewidth=1.5, color='blue')
        
        # Umbrales mínimos
        self.ax.axhline(threshold_high, color='orange', linestyle='--', linewidth=2, 
                       label=f'Umbral mínimo alto = μ + {k}·σ')
        self.ax.axhline(threshold_low, color='orange', linestyle='--', linewidth=2, 
                       label=f'Umbral mínimo bajo = μ − {k}·σ')
        
        # Límites máximos
        self.ax.axhline(max_limit_high, color='green', linestyle=':', linewidth=2, 
                       label=f'Límite máximo alto = μ + {k_max}·σ')
        self.ax.axhline(max_limit_low, color='green', linestyle=':', linewidth=2, 
                       label=f'Límite máximo bajo = μ − {k_max}·σ')
        
        # Puntos de activación
        self.ax.scatter(time[activation_pos], signal[activation_pos],
                       color='red', marker='o', s=30, alpha=0.7, label='Activación Derecha')
        self.ax.scatter(time[activation_neg], signal[activation_neg],
                       color='purple', marker='o', s=30, alpha=0.7, label='Activación Izquierda')
        
        # Anotaciones numéricas
        x_loc = time.iloc[-1] + (time.iloc[-1] - time.iloc[0]) * 0.01
        offset_vertical = (signal.max() - signal.min()) * 0.02
        
        # Etiquetas de valores
        self.ax.text(x_loc, threshold_high + offset_vertical, f'{threshold_high:.1f}', 
                    va='bottom', ha='left', color='orange', fontweight='bold', 
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        self.ax.text(x_loc, threshold_low + offset_vertical, f'{threshold_low:.1f}', 
                    va='bottom', ha='left', color='orange', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        self.ax.text(x_loc, max_limit_high + offset_vertical, f'{max_limit_high:.1f}', 
                    va='bottom', ha='left', color='green', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        self.ax.text(x_loc, max_limit_low + offset_vertical, f'{max_limit_low:.1f}', 
                    va='bottom', ha='left', color='green', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Configuración del gráfico
        self.ax.set_xlabel('Tiempo (s)', fontsize=12)
        self.ax.set_ylabel('Amplitud EOG (μV)', fontsize=12)
        self.ax.set_title('Análisis EOG: Umbrales Mínimos y Límites Máximos', fontsize=14, fontweight='bold')
        self.ax.legend(loc='upper left', fontsize=9)
        self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def update_results(self, mu, sigma, k, k_max, threshold_high, threshold_low,
                      max_limit_high, max_limit_low, activation_pos, activation_neg):
        """Actualizar el área de resultados con las estadísticas"""
        self.results_text.delete(1.0, tk.END)
        
        results = f"""{'='*60}
ANÁLISIS ESTADÍSTICO DE LA SEÑAL EOG
{'='*60}
Media (μ): {mu:.2f} mV
Desviación estándar (σ): {sigma:.2f} mV
Factor k (umbrales): {k}
Factor k_max (límites): {k_max}
{'-'*60}
UMBRALES MÍNIMOS:
  Alto: {threshold_high:.2f} mV
  Bajo: {threshold_low:.2f} mV
{'-'*60}
LÍMITES MÁXIMOS:
  Alto: {max_limit_high:.2f} mV
  Bajo: {max_limit_low:.2f} mV
{'-'*60}
ACTIVACIONES DETECTADAS:
  Derecha (por encima del umbral alto): {activation_pos.sum()}
  Izquierda (por debajo del umbral bajo): {activation_neg.sum()}
  Total de activaciones: {activation_pos.sum() + activation_neg.sum()}
{'='*60}
"""
        
        self.results_text.insert(tk.END, results)
    
    def clear_analysis(self):
        """Limpiar el análisis actual"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'Seleccione un archivo CSV y presione "Analizar EOG"', 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=self.ax.transAxes, fontsize=14, color='gray')
        self.ax.set_title('Análisis EOG: Umbrales Mínimos y Límites Máximos')
        self.canvas.draw()
        
        self.results_text.delete(1.0, tk.END)
        self.df = None
    
    def on_closing(self):
        """Manejar el cierre de la aplicación"""
        try:
            # Cerrar la figura de matplotlib si existe
            plt.close(self.fig)
        except:
            pass
        
        # Destruir la ventana y cerrar la aplicación
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = EOGAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()