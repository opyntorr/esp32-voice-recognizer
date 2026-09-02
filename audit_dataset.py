import os
import wave
import sys
import numpy as np

# Forzar salida utf-8 en consola de Windows
sys.stdout.reconfigure(encoding='utf-8')

WAV_DIR = r"dataset/wavs"

print("=======================================================================")
print(" AUDITORIA Y CONTROL DE CALIDAD DEL DATASET DE AUDIO")
print("=======================================================================")

files = sorted([f for f in os.listdir(WAV_DIR) if f.endswith(".wav")])

target_user_files = []
background_noise_files = []
corrupted_or_empty_files = []
low_amplitude_files = []
clipped_files = []

for f in files:
    try:
        num = int(f.split("_")[-1].replace(".wav", ""))
    except ValueError:
        continue

    path = os.path.join(WAV_DIR, f)

    try:
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)

        duration = n_frames / framerate
        audio_data = np.frombuffer(frames, dtype=np.int16)

        if len(audio_data) == 0:
            corrupted_or_empty_files.append((f, "Archivo vacio"))
            continue

        peak = int(np.max(np.abs(audio_data)))
        rms = int(np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)))

        if 14 <= num <= 161:
            category = "target_user"
            if peak < 800:
                low_amplitude_files.append((f, num, peak, rms, "Senal de voz muy debil"))
            elif peak > 32000:
                clipped_files.append((f, num, peak, rms, "Posible saturacion/clipping"))
            else:
                target_user_files.append((f, num, peak, rms, duration))

        elif num >= 162:
            category = "background_noise"
            background_noise_files.append((f, num, peak, rms, duration))
        else:
            category = "pruebas_iniciales"

    except Exception as e:
        corrupted_or_empty_files.append((f, str(e)))

print(f"\n--- RESUMEN DE LA AUDITORIA DE ARCHIVOS ---")
print(f"  * Total de archivos analizados          : {len(files)}")
print(f"  * Muestras VALIDAS de 'target_user' (14-161): {len(target_user_files)}")
print(f"  * Muestras de 'background_noise' (162+)  : {len(background_noise_files)}")
print(f"  * Muestras debiles/descartables (<800 pico): {len(low_amplitude_files)}")
print(f"  * Muestras saturadas (>32000 pico)      : {len(clipped_files)}")
print(f"  * Archivos corruptos o vacios           : {len(corrupted_or_empty_files)}")

if low_amplitude_files:
    print(f"\n[!] ARCHIVOS DEBILES / SIN VOZ CLARA (Recomendado revisar o excluir):")
    for fname, num, peak, rms, reason in low_amplitude_files:
        print(f"   - {fname} (ID #{num:03d}): Pico={peak}, RMS={rms} -> {reason}")

if clipped_files:
    print(f"\n[!] ARCHIVOS SATURADOS (Recomendado revisar):")
    for fname, num, peak, rms, reason in clipped_files:
        print(f"   - {fname} (ID #{num:03d}): Pico={peak}, RMS={rms} -> {reason}")

if target_user_files:
    peaks = [p for _, _, p, _, _ in target_user_files]
    rmss = [r for _, _, _, r, _ in target_user_files]
    print(f"\n[+] ESTADISTICAS DE 'target_user' VALIDOS:")
    print(f"   - Amplitud Pico Promedio : {int(np.mean(peaks))}")
    print(f"   - Amplitud Pico Minima   : {np.min(peaks)}")
    print(f"   - Amplitud Pico Maxima   : {np.max(peaks)}")
    print(f"   - RMS Promedio           : {int(np.mean(rmss))}")
