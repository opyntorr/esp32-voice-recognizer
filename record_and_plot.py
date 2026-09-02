import serial
import time
import os
import wave
import csv
import numpy as np
import matplotlib.pyplot as plt

PORT = 'COM4'
BAUD = 921600
SAMPLE_RATE = 16000
RECORD_TIME_SEC = 2
TOTAL_SAMPLES = SAMPLE_RATE * RECORD_TIME_SEC  # 32,000 muestras
EXPECTED_BYTES = TOTAL_SAMPLES * 2             # 64,000 bytes PCM 16-bit

DATASET_DIR = "dataset"
WAV_DIR = os.path.join(DATASET_DIR, "wavs")
PLOT_DIR = os.path.join(DATASET_DIR, "plots")
LOG_CSV = os.path.join(DATASET_DIR, "log_muestras.csv")

os.makedirs(WAV_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

if not os.path.exists(LOG_CSV):
    with open(LOG_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Fecha_Hora", "Etiqueta", "Archivo_WAV", "Archivo_PNG", "Duracion_s", "Amplitud_Pico", "Promedio_RMS", "Diagnostico"])

print("\n=======================================================")
print(" 🎙️ TINYML DATASET RECORDER & ACOUSTIC PLOTTER")
print("=======================================================")

try:
    ser = serial.Serial(PORT, BAUD, timeout=3)
    time.sleep(1.5)
    ser.reset_input_buffer()
    print(f"🟢 Conectado exitosamente al ESP32 en {PORT}\n")
except Exception as e:
    print(f"❌ Error conectando a {PORT}: {e}")
    print("Asegúrate de cerrar cualquier Monitor Serie abierto.")
    exit(1)

current_label = "mi_voz"
sample_count = 1

existing_files = [f for f in os.listdir(WAV_DIR) if f.endswith('.wav')]
if existing_files:
    indices = []
    for f in existing_files:
        try:
            num = int(f.split('_')[-1].replace('.wav', ''))
            indices.append(num)
        except ValueError:
            pass
    if indices:
        sample_count = max(indices) + 1

def record_single_sample(label_name, index_num):
    print(f"\n🔴 [GRABANDO] Muestra #{index_num:03d} - Etiqueta: [{label_name}]")
    print(" 🎙️ Habla AHORA durante 2 segundos...")
    
    ser.reset_input_buffer()
    ser.write(b'b')  # Enviar comando 'b' para solicitar PCM binario
    
    pcm_bytes = bytearray()
    start_time = time.time()
    
    while len(pcm_bytes) < EXPECTED_BYTES and (time.time() - start_time < 3.5):
        chunk = ser.read(min(4096, EXPECTED_BYTES - len(pcm_bytes)))
        if chunk:
            pcm_bytes.extend(chunk)

    if len(pcm_bytes) < EXPECTED_BYTES:
        print(f"⚠️ Atención: Se leyeron {len(pcm_bytes)} bytes de {EXPECTED_BYTES} esperados.")
        pcm_bytes.extend(b'\x00' * (EXPECTED_BYTES - len(pcm_bytes)))

    audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)

    base_name = f"{label_name}_{index_num:03d}"
    wav_path = os.path.join(WAV_DIR, f"{base_name}.wav")
    png_path = os.path.join(PLOT_DIR, f"{base_name}.png")

    # 1. Guardar archivo WAV
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)

    # 2. Generar Gráfico en Imagen PNG (Forma de Onda + Espectrograma)
    peak_val = int(np.max(np.abs(audio_data)))
    rms_val = int(np.sqrt(np.mean(audio_data.astype(np.float64)**2)))
    time_axis = np.linspace(0, RECORD_TIME_SEC, len(audio_data))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [1, 1]})
    fig.patch.set_facecolor('#111827')

    # Dominio del Tiempo
    ax1.set_facecolor('#1F2937')
    ax1.plot(time_axis, audio_data, color='#00FFCC', lw=1.2)
    ax1.set_title(f"Muestra: {base_name} | Amplitud Pico: {peak_val} | RMS: {rms_val}", color='#F9FAFB', fontsize=12)
    ax1.set_ylabel("Amplitud PCM 16-bit", color='#9CA3AF')
    ax1.set_ylim(-16000, 16000)
    ax1.grid(True, color='#374151', linestyle='--', alpha=0.5)
    ax1.tick_params(colors='#9CA3AF')

    # Espectrograma de Frecuencia
    ax2.set_facecolor('#1F2937')
    Pxx, freqs, bins, im = ax2.specgram(audio_data, NFFT=512, Fs=SAMPLE_RATE, noverlap=256, cmap='magma')
    ax2.set_title("Espectrograma de Frecuencia (Hz vs Tiempo)", color='#F9FAFB', fontsize=11)
    ax2.set_xlabel("Tiempo (segundos)", color='#9CA3AF')
    ax2.set_ylabel("Frecuencia (Hz)", color='#9CA3AF')
    ax2.set_ylim(0, 8000)
    ax2.tick_params(colors='#9CA3AF')

    plt.tight_layout()
    plt.savefig(png_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 3. Registrar en CSV
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    diag_str = "OK" if peak_val > 1000 else "Débil"
    
    with open(LOG_CSV, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([index_num, timestamp_str, label_name, wav_path, png_path, RECORD_TIME_SEC, peak_val, rms_val, diag_str])

    print(f"🟢 [GUARDADO EXITOSO]")
    print(f"   🔊 Audio WAV : {wav_path}")
    print(f"   🖼️ Gráfica   : {png_path}")
    print(f"   📊 Métricas  : Pico = {peak_val} | RMS = {rms_val} [{diag_str}]\n")

while True:
    print("-------------------------------------------------------")
    print(f"Etiqueta actual: [{current_label}] | Próxima Muestra: #{sample_count:03d}")
    print("Opciones:")
    print("  [ENTER]  -> Grabar 1 muestra manualmente (2 segundos)")
    print("  [c]      -> MODO AUTOMÁTICO CONTINUO (Graba cada 2 segundos sin parar)")
    print("  [1]      -> Etiqueta: 'mi_voz'")
    print("  [2]      -> Etiqueta: 'otra_voz'")
    print("  [3]      -> Etiqueta: 'ruido_fondo'")
    print("  [q]      -> Salir")
    
    cmd = input("\n👉 Elige opción: ").strip().lower()

    if cmd == 'q':
        break
    elif cmd == '1':
        current_label = "mi_voz"
        print("✅ Etiqueta activa: mi_voz")
        continue
    elif cmd == '2':
        current_label = "otra_voz"
        print("✅ Etiqueta activa: otra_voz")
        continue
    elif cmd == '3':
        current_label = "ruido_fondo"
        print("✅ Etiqueta activa: ruido_fondo")
        continue
    elif cmd == 'c':
        print("\n🚀 INICIANDO MODO AUTOMÁTICO CONTINUO...")
        print("El sistema grabará cada 2 segundos. Presiona Ctrl+C para detener.\n")
        try:
            while True:
                for i in range(2, 0, -1):
                    print(f"⏱️ Preparado en {i}...", end="\r", flush=True)
                    time.sleep(0.8)
                record_single_sample(current_label, sample_count)
                sample_count += 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n⏸️ Modo automático detenido por el usuario.")
            continue
    else:
        record_single_sample(current_label, sample_count)
        sample_count += 1

ser.close()
print("Grabador finalizado.")
