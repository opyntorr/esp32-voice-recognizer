import os
import sys
import wave
import urllib.request
import tarfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DATASET_DIR = "dataset"
WAV_DIR = os.path.join(DATASET_DIR, "wavs")
PROCESSED_DIR = "dataset_processed"

# Carpetas de destino para las 3 clases
TARGET_DIR = os.path.join(PROCESSED_DIR, "target_user")
IMPOSTOR_DIR = os.path.join(PROCESSED_DIR, "impostors_control")
NOISE_DIR = os.path.join(PROCESSED_DIR, "background_noise")

os.makedirs(TARGET_DIR, exist_ok=True)
os.makedirs(IMPOSTOR_DIR, exist_ok=True)
os.makedirs(NOISE_DIR, exist_ok=True)

SAMPLE_RATE = 16000
TARGET_SAMPLES = 16000  # 1.0 segundo exacto

print("=======================================================================")
print(" 🛠️ PREPARACIÓN Y NORMALIZACIÓN DE DATASET (1.0s / 16 kHz)")
print("=======================================================================")

def process_audio_file(filepath, target_samples=16000, norm_peak=0.95, alpha=0.97):
    """
    1. Lee el archivo WAV.
    2. Realiza VAD/Centrado a 1.0 segundo (16,000 muestras).
    3. Aplica normalización pico al 95%.
    4. Aplica filtro de pre-énfasis: y[n] = x[n] - 0.97 * x[n-1].
    """
    with wave.open(filepath, "rb") as wf:
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

    # 1. Alineación Temporal / Trimming
    if len(audio) > target_samples:
        # Detectar el centro de energía de la voz
        energy = audio ** 2
        window_size = 480
        energy_smooth = np.convolve(energy, np.ones(window_size)/window_size, mode='same')
        max_idx = np.argmax(energy_smooth)
        
        start = max(0, max_idx - target_samples // 2)
        end = start + target_samples
        if end > len(audio):
            end = len(audio)
            start = max(0, end - target_samples)
        audio = audio[start:end]

    # Padding si dura menos de 1 segundo
    if len(audio) < target_samples:
        pad_len = target_samples - len(audio)
        pad_left = pad_len // 2
        pad_right = pad_len - pad_left
        audio = np.pad(audio, (pad_left, pad_right), mode='constant')

    # 2. Normalización de Amplitud Pico (95%)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        target_max = 32767.0 * norm_peak
        audio = (audio / max_val) * target_max

    # 3. Filtro de Pre-énfasis FIR: y[n] = x[n] - 0.97 * x[n-1]
    audio_preemphasized = np.append(audio[0], audio[1:] - alpha * audio[:-1])

    return audio_preemphasized.astype(np.int16)

# -------------------------------------------------------------------------
# 1. Procesar Muestras del Usuario (target_user: IDs 14 a 161)
# -------------------------------------------------------------------------
print("\n1️⃣ Procesando muestras personales ('target_user')...")
user_count = 0
for f in sorted(os.listdir(WAV_DIR)):
    if f.endswith(".wav"):
        try:
            num = int(f.split("_")[-1].replace(".wav", ""))
            if 14 <= num <= 161:
                # Excluir la muestra saturada mi_voz_038.wav si es necesario
                src_path = os.path.join(WAV_DIR, f)
                cleaned_pcm = process_audio_file(src_path)
                
                out_path = os.path.join(TARGET_DIR, f"user_{num:03d}.wav")
                with wave.open(out_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(cleaned_pcm.tobytes())
                user_count += 1
        except Exception:
            pass

print(f"   ✅ {user_count} muestras de 'target_user' recortadas a 1.0s, normalizadas y pre-enfatizadas.")

# -------------------------------------------------------------------------
# 2. Procesar Ruido de Fondo (background_noise: IDs 162 en adelante)
# -------------------------------------------------------------------------
print("\n2️⃣ Procesando muestras de ruido de fondo ('background_noise')...")
noise_count = 0
for f in sorted(os.listdir(WAV_DIR)):
    if f.endswith(".wav"):
        try:
            num = int(f.split("_")[-1].replace(".wav", ""))
            if num >= 162:
                src_path = os.path.join(WAV_DIR, f)
                cleaned_pcm = process_audio_file(src_path)
                
                out_path = os.path.join(NOISE_DIR, f"noise_{num:03d}.wav")
                with wave.open(out_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(cleaned_pcm.tobytes())
                noise_count += 1
        except Exception:
            pass

print(f"   ✅ {noise_count} muestras de 'background_noise' procesadas.")

# -------------------------------------------------------------------------
# 3. Descargar/Extraer Muestras "forward" de Google Speech Commands v2
# -------------------------------------------------------------------------
print("\n3️⃣ Obteniendo muestras impostoras de Google Speech Commands v2 ('forward')...")

GSC_TAR_URL = "http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz"
GSC_TAR_PATH = os.path.join(DATASET_DIR, "speech_commands_v0.02.tar.gz")

if not os.path.exists(GSC_TAR_PATH):
    print("   ⬇️ Descargando Google Speech Commands v2 dataset (~2.4 GB, puede tomar un par de minutos)...")
    try:
        urllib.request.urlretrieve(GSC_TAR_URL, GSC_TAR_PATH)
        print("   ✅ Descarga completada.")
    except Exception as e:
        print(f"   ⚠️ Error descargando dataset completo: {e}")

impostor_count = 0
if os.path.exists(GSC_TAR_PATH):
    print("   📦 Extrayendo muestras de la carpeta 'forward' de Google Speech Commands...")
    with tarfile.open(GSC_TAR_PATH, "r:gz") as tar:
        for member in tar:
            if ("./forward/" in member.name or "forward/" in member.name) and member.name.endswith(".wav"):
                f_obj = tar.extractfile(member)
                if f_obj:
                    content = f_obj.read()
                    temp_temp_path = os.path.join(PROCESSED_DIR, "temp.wav")
                    with open(temp_temp_path, "wb") as tf:
                        tf.write(content)
                    
                    cleaned_pcm = process_audio_file(temp_temp_path)
                    out_path = os.path.join(IMPOSTOR_DIR, f"impostor_{impostor_count:04d}.wav")
                    with wave.open(out_path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(cleaned_pcm.tobytes())
                    
                    if os.path.exists(temp_temp_path):
                        os.remove(temp_temp_path)
                    impostor_count += 1
                    
                    if impostor_count >= 400:
                        break

print(f"   ✅ {impostor_count} muestras de impostores 'forward' procesadas a 1.0s.")

print("\n=======================================================================")
print(" 🚀 DATASET PROCESADO Y ALINEADO CON ÉXITO")
print("=======================================================================")
print(f"  • target_user (Tus muestras)       : {user_count} archivos en {TARGET_DIR}")
print(f"  • impostors_control (Otras voces)  : {impostor_count} archivos en {IMPOSTOR_DIR}")
print(f"  • background_noise (Ruido)          : {noise_count} archivos en {NOISE_DIR}")
print("=======================================================================\n")
