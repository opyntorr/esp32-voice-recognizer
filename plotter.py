import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Configuración de puerto serie y buffer
PORT = 'COM4'
BAUD = 115200
BUFFER_SIZE = 1000  # Número de muestras visibles en pantalla (~0.06 segundos de audio)

data_deque = collections.deque([0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)

print(f"Conectando a {PORT} a {BAUD} baudios...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    time.sleep(1.5)  # Esperar estabilización del puerto serie
    
    # Enviar comando 'p' para activar el flujo de datos
    ser.write(b'p\n')
    print("  Modo Graficador (Plotter) Activado en el ESP32!")
except Exception as e:
    print(f" Error al abrir puerto {PORT}: {e}")
    print("Asegúrate de cerrar el Serial Monitor de PlatformIO antes de ejecutar este script.")
    exit(1)

# Configuración del gráfico de Matplotlib
fig, ax = plt.subplots(figsize=(10, 5))
fig.canvas.manager.set_window_title("Osciloscopio en Tiempo Real - INMP441 + ESP32")
line, = ax.plot(np.zeros(BUFFER_SIZE), color='#00FFCC', lw=1.5)

ax.set_facecolor('#111827')
fig.patch.set_facecolor('#1F2937')
ax.set_ylim(-8000, 8000)
ax.set_title("Onda de Voz en Tiempo Real (INMP441 MEMS)", color='#F9FAFB', fontsize=14, pad=12)
ax.set_xlabel("Muestras (Solapamiento continuo)", color='#9CA3AF')
ax.set_ylabel("Amplitud PCM (16-bit)", color='#9CA3AF')
ax.tick_params(colors='#9CA3AF')
ax.grid(True, color='#374151', linestyle='--', alpha=0.6)

def update(frame):
    # Leer todas las líneas disponibles en el buffer serie
    while ser.in_waiting > 0:
        try:
            line_str = ser.readline().decode('utf-8', errors='ignore').strip()
            if line_str and not line_str.startswith("---") and not line_str.startswith(""):
                val = int(line_str)
                data_deque.append(val)
        except ValueError:
            pass

    arr = np.array(data_deque)
    line.set_ydata(arr)

    # Calcular estadísticas en vivo
    peak = np.max(np.abs(arr)) if len(arr) > 0 else 0
    ax.set_title(f"Osciloscopio INMP441 - Amplitud Pico en Vivo: {peak} | Frecuencia: 16 kHz", color='#00FFCC', fontsize=12)
    return line,

def on_close(event):
    print("\nDesactivando flujo de datos en el ESP32...")
    try:
        ser.write(b'p\n')  # Desactivar modo plotter al cerrar la ventana
        ser.close()
        print(" Puerto Serie Cerrado.")
    except Exception:
        pass

fig.canvas.mpl_connect('close_event', on_close)

ani = animation.FuncAnimation(fig, update, interval=20, blit=True, cache_frame_data=False)

print("\n Abriendo osciloscopio gráfico... Habla frente al micrófono para ver tu onda de voz!")
plt.show()
