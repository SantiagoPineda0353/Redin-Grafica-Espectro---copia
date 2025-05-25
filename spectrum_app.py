from flask import Flask, render_template, request, redirect
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
#pip install matplotlib
#pip install colorama

app = Flask(__name__)

Bw = 0 # en KHz
temperatura = 0 #en K

# transitores
signals = [
    {"fc": 0, "bw": 0, "pot": 0},
    {"fc": 0, "bw": 4, "pot": 0},
    {"fc": 0, "bw": 0, "pot": 0}
]

def recoger_datos():
    global Bw, temperatura,signals
    Bw = float(request.args.get('Bw'))
    temperatura = float(request.args.get('temperatura'))

    signals = []
    for i in range(3):
        fc = float(request.args.get(f'fc{i}'))
        bw = float(request.args.get(f'bw{i}'))
        pot = float(request.args.get(f'power{i}'))
        signals.append({"fc": fc, "bw": bw, "power": pot})

def longitud_signal(f, fc, bw, pot):
    y = (bw/2)
    x = (f - fc) / y
    x2 = x**2
    power = pot - (3*x2)
    return power


@app.route('/generar_grafica', methods=['GET', 'POST'])
def generar_grafica():
    
    global Bw, temperatura, signals
    #Calcular ruido termico
    recoger_datos()
    Bw*= 1000 #Pasar de KHz a Hz
    k = 1.38*10**-23 #onstante de Boltzmann
    #noise_floor = 10 * math.log10(k*temperatura*Bw) + 30 # en dBm
    noise_floor = 10 * np.log10(k * temperatura * Bw) + 30

    colors = ['red', 'green', 'blue']

    # rango de frecuencia
    min_left = float('inf')
    max_right = float('-inf')
    for s in signals:
        left = s["fc"] - (s["bw"] / 2)
        right = s["fc"] + (s["bw"] / 2)
        min_left = min(min_left, left)
        max_right = max(max_right, right)

    frequencies = np.linspace(min_left - 10, max_right + 10, 3000)

    np.random.seed(42)
    noise = noise_floor + np.random.normal(0, 0.5, size=frequencies.shape)

    # grafico
    plt.figure(figsize=(12, 6))

    max_p_max = 0
    for idx, s in enumerate(signals):
        max_p_max = max(max_p_max,s["power"])
        power = longitud_signal(frequencies, s["fc"], s["bw"], s["power"])
        plt.plot(frequencies, power, color=colors[idx], linewidth=2.5, label=f"Tx {idx+1}: Fc={s['fc']} MHz")
        
        plt.axvline(x=s["fc"], color=colors[idx], linestyle='-', linewidth=1)
        
        # media potencia
        level = 1
        left = s["fc"] - (s["bw"]/2) * level
        right = s["fc"] + (s["bw"]/2) * level
        plt.axvline(x=left, color=colors[idx], linestyle=':', linewidth=1)
        plt.axvline(x=right, color=colors[idx], linestyle=':', linewidth=1)

    # configuracion
    plt.title("Graficao de Espectro")
    plt.xlabel("Frecuencia (MHz)")
    plt.ylabel("Potencia (dBm)")

    plt.ylim(noise_floor - 5, max_p_max+5)
    plt.xlim(min_left - 5, max_right + 5)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/img/grafico.png")   
    plt.close() 

    return render_template('index.html',image_url=('static/img/grafico.png'))
    

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)





#####







def thermal_noise(temp_k, bw_hz):
    k = 1.38e-23  # Constante de Boltzmann
    noise_power_watts = k * temp_k * bw_hz
    noise_power_dbm = 10 * np.log10(noise_power_watts / 1e-3)
    return noise_power_dbm

def generate_spectrum_plot(temp_k, system_bw, noise_dbm_override, signals):
    freqs = np.linspace(0, 10000, 1000)  # Frecuencia de 0 a 10 kHz
    noise_dbm = thermal_noise(temp_k, system_bw) if noise_dbm_override is None else noise_dbm_override
    noise = np.random.normal(noise_dbm, 1, len(freqs))

    # ✅ Reemplaza plt.figure() por plt.subplots() para poder cerrar la figura correctamente
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freqs, noise, label='Nivel de ruido', color='gray')

    for idx, signal in enumerate(signals):
        fc = signal['fc']
        bw = signal['bw']
        power = signal['power']
        start = fc - bw / 2
        end = fc + bw / 2
        shape = np.logical_and(freqs >= start, freqs <= end)
        signal_line = np.zeros_like(freqs)
        signal_line[shape] = power
        ax.plot(freqs, signal_line, label=f'Señal {idx + 1}')

    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('Potencia (dBm)')
    ax.set_title('Gráfico de Espectro')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close(fig)  # ✅ Cerrar explícitamente la figura

    return image_base64


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("formulario recibido")
        temp_k = float(request.form['temperature'])
        system_bw = float(request.form['system_bw'])
        noise_dbm = request.form['noise_dbm']
        noise_dbm = float(noise_dbm) if noise_dbm else None

        print(f"Temperatura: {temp_k}")
        print(f"Ancho de banda del sistema: {system_bw}")
        print(f"Ruido sobrescrito: {noise_dbm}")


        signals = []
        for i in range(1, 4):
            power = float(request.form[f'power{i}'])
            fc = float(request.form[f'fc{i}'])
            bw = float(request.form[f'bw{i}'])
            signals.append({"power": power, "fc": fc, "bw": bw})

        spectrum_image = generate_spectrum_plot(temp_k, system_bw, noise_dbm, signals)
        return render_template('index.html', spectrum_image=spectrum_image)

    return render_template('index.html', spectrum_image=None)

if __name__ == '__main__':
    app.run(debug=True)
