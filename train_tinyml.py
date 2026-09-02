import os
import sys
import wave
import numpy as np
import scipy.signal
import scipy.fftpack

sys.stdout.reconfigure(encoding='utf-8')

import tensorflow as tf
from tensorflow.keras import layers, models

# =========================================================================
# PARÁMETROS DEL PIPELINE DSP (ESP32-S3 COMPATIBLE)
# =========================================================================
SAMPLE_RATE = 16000
TARGET_SAMPLES = 16000   # 1.0s exacto
FRAME_LEN = 480          # 30 ms
FRAME_STEP = 240         # 15 ms
N_FFT = 512              # FFT 512 puntos
N_MEL = 40               # 40 Filtros Mel
N_MFCC = 40              # 40 Coeficientes Cepstrales
LOW_FREQ = 80            # 80 Hz
HIGH_FREQ = 7600         # 7600 Hz

PROCESSED_DIR = "dataset_processed"
TARGET_DIR = os.path.join(PROCESSED_DIR, "target_user")
IMPOSTOR_DIR = os.path.join(PROCESSED_DIR, "impostors_control")
NOISE_DIR = os.path.join(PROCESSED_DIR, "background_noise")

print("=======================================================================")
print("  ENTRENADOR TINYML CNN & CONVERTIDOR INT8 PARA ESP32-S3")
print("=======================================================================")

def hz_to_mel(hz):
    return 2595.0 * np.log10(1.0 + hz / 700.0)

def mel_to_hz(mel):
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

def get_mel_filterbank(n_filters=40, n_fft=512, sr=16000, low_f=80, high_f=7600):
    low_mel = hz_to_mel(low_f)
    high_mel = hz_to_mel(high_f)
    mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    fbank = np.zeros((n_filters, int(np.floor(n_fft / 2 + 1))))
    for m in range(1, n_filters + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin_points[m - 1]) / (bin_points[m] - bin_points[m - 1] + 1e-6)
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin_points[m + 1] - k) / (bin_points[m + 1] - bin_points[m] + 1e-6)
    return fbank

MEL_FBANK = get_mel_filterbank(N_MEL, N_FFT, SAMPLE_RATE, LOW_FREQ, HIGH_FREQ)
HAMMING_WIN = np.hamming(FRAME_LEN)

def extract_mfcc_cmvn(audio):
    """
    Cadena DSP idéntica a la ejecutada en el ESP32:
    Pre-énfasis -> Framing -> Hamming -> FFT -> Mel Filterbank -> Log -> DCT -> CMVN
    """
    if len(audio) != TARGET_SAMPLES:
        if len(audio) < TARGET_SAMPLES:
            audio = np.pad(audio, (0, TARGET_SAMPLES - len(audio)))
        else:
            audio = audio[:TARGET_SAMPLES]

    # Pre-énfasis
    pre_emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

    # Framing (Enmarcado)
    num_frames = 1 + int(np.floor((TARGET_SAMPLES - FRAME_LEN) / FRAME_STEP)) # ~64 tramas
    frames = np.zeros((num_frames, FRAME_LEN))
    for t in range(num_frames):
        start = t * FRAME_STEP
        frames[t] = pre_emphasized[start:start + FRAME_LEN] * HAMMING_WIN

    # STFT & Espectro de Potencia
    mag_frames = np.abs(np.fft.rfft(frames, n=N_FFT))
    pow_frames = ((1.0 / N_FFT) * (mag_frames ** 2))

    # Banco de Filtros Mel & Compresión Logarítmica
    mel_energies = np.dot(pow_frames, MEL_FBANK.T)
    mel_energies = np.where(mel_energies == 0, np.finfo(float).eps, mel_energies)
    log_mel = np.log(mel_energies)

    # DCT-II para extraer MFCCs
    mfcc = scipy.fftpack.dct(log_mel, type=2, axis=1, norm='ortho')[:, :N_MFCC]

    # Normalización Cepstral CMVN (Canal)
    mean = np.mean(mfcc, axis=0)
    std = np.std(mfcc, axis=0) + 1e-6
    mfcc_cmvn = (mfcc - mean) / std

    # Garantizar exactamente 64 tramas temporales (40, 64)
    mfcc_cmvn = mfcc_cmvn[:64, :]
    if mfcc_cmvn.shape[0] < 64:
        mfcc_cmvn = np.pad(mfcc_cmvn, ((0, 64 - mfcc_cmvn.shape[0]), (0, 0)))

    # Transponer a dimensión (N_MFCC, 64) -> (40, 64)
    return mfcc_cmvn.T

def load_dataset():
    X = []
    y = []

    def load_from_folder(folder_path, label):
        if not os.path.exists(folder_path):
            return
        for f in os.listdir(folder_path):
            if f.endswith(".wav"):
                p = os.path.join(folder_path, f)
                with wave.open(p, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                feat = extract_mfcc_cmvn(audio)
                X.append(feat)
                y.append(label)

    print(" Extrayendo MFCCs + CMVN de las 3 clases...")
    load_from_folder(TARGET_DIR, 0)     # Clase 0: target_user
    load_from_folder(IMPOSTOR_DIR, 1)   # Clase 1: impostors_control
    load_from_folder(NOISE_DIR, 2)      # Clase 2: background_noise

    X = np.array(X)[..., np.newaxis]   # Dimensión: (N, 40, 64, 1)
    y = np.array(y)
    return X, y

# Cargar dataset
X, y = load_dataset()
print(f" Dataset listo. Forma de tensores de entrada X: {X.shape}, Etiquetas y: {y.shape}")

# Mezclar y dividir en Entrenamiento (80%) y Validación (20%)
indices = np.arange(len(X))
np.random.shuffle(indices)
X = X[indices]
y = y[indices]

split_idx = int(0.8 * len(X))
X_train, X_val = X[:split_idx], X[split_idx:]
y_train, y_val = y[:split_idx], y[split_idx:]

# =========================================================================
# DISEÑO DE LA RED NEURONAL CONVOLUCIONAL (CNN - RESTRICCIÓN < 35,000 PARÁMETROS)
# =========================================================================
def build_tinyml_cnn():
    model = models.Sequential([
        layers.Input(shape=(N_MFCC, 64, 1)),

        # Capa Convolucional 1
        layers.Conv2D(16, (3, 3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.2),

        # Capa Convolucional 2 (Depthwise Separable para eficiencia)
        layers.DepthwiseConv2D((3, 3), padding='same', activation='relu'),
        layers.Conv2D(32, (1, 1), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        # Capa Convolucional 3
        layers.Conv2D(32, (3, 3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),

        # Capa Clasificadora de Salida (3 Clases)
        layers.Dense(3, activation='softmax')
    ])
    return model

model = build_tinyml_cnn()
model.summary()

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

print("\n Entrenando Modelo CNN TinyML...")
history = model.fit(
    X_train, y_train,
    epochs=40,
    batch_size=16,
    validation_data=(X_val, y_val),
    verbose=1
)

# =========================================================================
# CUANTIZACIÓN INT8 COMPLETA (POST-TRAINING QUANTIZATION)
# =========================================================================
print("\n Aplicando Cuantización INT8 estricta para TFLite Micro...")

def representative_dataset_gen():
    for i in range(min(100, len(X_train))):
        yield [X_train[i:i+1].astype(np.float32)]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_quant_model = converter.convert()

# Guardar archivo .tflite
tflite_path = "model_quantized.tflite"
with open(tflite_path, "wb") as f:
    f.write(tflite_quant_model)

print(f" Modelo INT8 Cuantizado guardado en: {tflite_path} ({len(tflite_quant_model) / 1024:.2f} KB)")

# =========================================================================
# EXPORTACIÓN A ARREGLO DE DATOS C++ (model_data.h)
# =========================================================================
header_path = os.path.join("src", "model_data.h")
print(f" Generando encabezado C++ para ESP32 en: {header_path}...")

with open(header_path, "w") as f:
    f.write("// ARCHIVO GENERADO AUTOMÁTICAMENTE - MODELO TINYML INT8 PARA ESP32-S3\n")
    f.write("#ifndef MODEL_DATA_H_\n")
    f.write("#ifndef MODEL_DATA_H_\n#define MODEL_DATA_H_\n\n")
    f.write("#include <cstdint>\n\n")
    f.write(f"alignas(8) const unsigned char g_model[] = {{\n  ")
    
    for i, byte in enumerate(tflite_quant_model):
        f.write(f"0x{byte:02x}")
        if i < len(tflite_quant_model) - 1:
            f.write(", ")
        if (i + 1) % 12 == 0:
            f.write("\n  ")
            
    f.write("\n};\n")
    f.write(f"const unsigned int g_model_len = {len(tflite_quant_model)};\n\n")
    f.write("#endif // MODEL_DATA_H_\n")

print(f" ¡ÉXITO! Modelo exportado a C++ en '{header_path}'. ¡Listo para compilar en ESP32-S3!")
