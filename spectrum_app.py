import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin interfaz gráfica
import numpy as np
import io
from kivy.core.image import Image as CoreImage

kivy.require('2.0.0')

class SpectrumSimulator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Título
        title = Label(
            text='Simulador de Espectro',
            size_hint_y=None,
            height=40,
            font_size=20,
            bold=True
        )
        self.add_widget(title)
        
        # ScrollView para los controles
        scroll = ScrollView(size_hint_y=0.6)
        controls_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        controls_layout.bind(minimum_height=controls_layout.setter('height'))
        
        # Parámetros globales
        global_params = GridLayout(cols=2, size_hint_y=None, height=80, spacing=5)
        
        global_params.add_widget(Label(text='Temperatura (K):', size_hint_y=None, height=30))
        self.temp_input = TextInput(text='300', size_hint_y=None, height=30, multiline=False)
        global_params.add_widget(self.temp_input)
        
        global_params.add_widget(Label(text='Ancho de banda del ruido (KHz):', size_hint_y=None, height=30))
        self.noise_bw_input = TextInput(text='1000', size_hint_y=None, height=30, multiline=False)
        global_params.add_widget(self.noise_bw_input)
        
        controls_layout.add_widget(global_params)
        
        # Señales
        self.signals = []
        for i in range(3):
            signal_group = self.create_signal_group(i + 1)
            controls_layout.add_widget(signal_group)
            
        scroll.add_widget(controls_layout)
        self.add_widget(scroll)
        
        # Botón para generar gráfico
        generate_btn = Button(
            text='Generar gráfico',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        generate_btn.bind(on_press=self.generate_plot)
        self.add_widget(generate_btn)
        
        # Área del gráfico
        self.plot_widget = None
        
    def create_signal_group(self, signal_num):
        # Crear grupo de controles para una señal
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=5)
        
        # Título de la señal
        title = Label(
            text=f'Señal {signal_num}',
            size_hint_y=None,
            height=30,
            font_size=16,
            bold=True
        )
        main_layout.add_widget(title)
        
        # Grid para los parámetros
        params_grid = GridLayout(cols=2, size_hint_y=None, height=150, spacing=5)
        
        signal_inputs = {}
        
        # Frecuencia central
        params_grid.add_widget(Label(text='Frecuencia central (MHz):', size_hint_y=None, height=30))
        signal_inputs['freq'] = TextInput(
            text=str(95 + signal_num * 5), 
            size_hint_y=None, 
            height=30, 
            multiline=False
        )
        params_grid.add_widget(signal_inputs['freq'])
        
        # Potencia
        params_grid.add_widget(Label(text='Potencia (dBm):', size_hint_y=None, height=30))
        signal_inputs['power'] = TextInput(
            text=str(30 - signal_num * 10), 
            size_hint_y=None, 
            height=30, 
            multiline=False
        )
        params_grid.add_widget(signal_inputs['power'])
        
        # Ancho de banda
        params_grid.add_widget(Label(text='Ancho de banda (MHz):', size_hint_y=None, height=30))
        signal_inputs['bandwidth'] = TextInput(
            text=str(2 + signal_num), 
            size_hint_y=None, 
            height=30, 
            multiline=False
        )
        params_grid.add_widget(signal_inputs['bandwidth'])
        
        main_layout.add_widget(params_grid)
        self.signals.append(signal_inputs)
        
        return main_layout
    
    def gaussian_signal(self, freq_range, center_freq, power, bandwidth):
        """Genera una señal gaussiana"""
        sigma = bandwidth / 4  # Ancho de la campana
        amplitude = 10**(power/20)  # Convertir dBm a amplitud
        gaussian = amplitude * np.exp(-0.5 * ((freq_range - center_freq) / sigma) ** 2)
        return 20 * np.log10(gaussian + 1e-10)  # Convertir a dB
    
    def generate_plot(self, instance):
        # Limpiar gráfico anterior
        if self.plot_widget:
            self.remove_widget(self.plot_widget)
        
        # Crear figura con fondo blanco
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8), facecolor='white')
        ax.set_facecolor('white')
        
        # Rango de frecuencias
        freq_range = np.linspace(90, 120, 1000)
        
        # Colores para las señales
        colors = ['red', 'green', 'blue']
        
        # Graficar cada señal
        for i, (signal_inputs, color) in enumerate(zip(self.signals, colors)):
            try:
                center_freq = float(signal_inputs['freq'].text)
                power = float(signal_inputs['power'].text)
                bandwidth = float(signal_inputs['bandwidth'].text)
                
                # Generar señal gaussiana
                signal_db = self.gaussian_signal(freq_range, center_freq, power, bandwidth)
                
                ax.plot(freq_range, signal_db, color=color, linewidth=3, 
                       label=f'Señal {i+1}')
                
            except ValueError:
                continue
        
        # Configurar el gráfico
        ax.set_xlabel('Frecuencia (MHz)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Potencia (dBm)', fontsize=12, fontweight='bold')
        ax.set_title('Gráfica de Espectro', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3, color='gray', linestyle='-', linewidth=0.5)
        ax.set_xlim(90, 120)
        ax.set_ylim(-120, 40)
        
        # Añadir líneas verticales para las frecuencias centrales
        for i, signal_inputs in enumerate(self.signals):
            try:
                center_freq = float(signal_inputs['freq'].text)
                ax.axvline(x=center_freq, color=colors[i], linestyle='--', alpha=0.7, linewidth=2)
            except ValueError:
                continue
        
        # Mejorar apariencia
        ax.tick_params(axis='both', which='major', labelsize=10)
        plt.tight_layout()
        
        # Convertir matplotlib figure a imagen para Kivy
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Crear imagen de Kivy
        core_image = CoreImage(buf, ext='png')
        self.plot_widget = Image(texture=core_image.texture, size_hint_y=0.8)
        self.add_widget(self.plot_widget)
        
        # Cerrar figura para liberar memoria
        plt.close(fig)
        buf.close()

class SpectrumApp(App):
    def build(self):
        return SpectrumSimulator()

if __name__ == '__main__':
    SpectrumApp().run()