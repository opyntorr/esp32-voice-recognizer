# 🔑 ESP32-S3 Biometric Voice Key with TinyML & USB-HID

Sistema embebido de autenticación biométrica por reconocimiento de voz basado en **Edge AI / TinyML** ejecutándose sobre un microcontrolador **ESP32-S3** con micrófono digital I2S **INMP441** y emulación nativa de teclado **USB-HID**.

---

## 🌟 Características Principales

- **Detección Automática de Voz (VAD):** Monitoreo acústico continuo en tiempo real con umbral de amplitud y filtro de persistencia temporal para evitar falsos positivos.
- **Pre-Roll Ring Buffer (150 ms):** Búfer circular en memoria RAM para capturar el fonema inicial completo de la palabra clave sin recortes.
- **Cadena DSP Embebida de Alta Eficiencia:**
  - Normalización por valor pico al 95%.
  - Filtro FIR de Pre-énfasis ($y[n] = x[n] - 0.97 \cdot x[n-1]$).
  - Enmarcado con Ventana Hamming (tramas de 30 ms, 15 ms de salto).
  - **FFT Radix-2** optimizada en $O(N \log N)$ (512 puntos en ~0.15 ms).
  - Banco de 40 Filtros Mel triangulares (80 Hz – 7600 Hz).
  - Transformada Discreta del Coseno (DCT-II ortogonal) para 40 coeficientes MFCC.
  - Normalización de Media y Varianza Cepstral (CMVN).
- **Red Neuronal Convolucional (CNN) INT8:**
  - Arquitectura profunda compacta (< 11k parámetros).
  - Cuantización Post-Entrenamiento (PTQ) completa a INT8 en **TensorFlow Lite Micro**.
  - Precisión de validación > 97%.
- **Seguridad Criptográfica & USB-HID:**
  - Derivación criptográfica SHA-256 (KDF) a partir del TRNG por hardware del silicio.
  - Inyección de token de acceso como teclado USB nativo al superar criterios biométricos.
  - Higiene de memoria con sanitización instantánea (`memset(..., 0, ...)`) de buffers sensibles.
- **Retroalimentación Visual con LED RGB Integrado:**
  - 🔵 **Azul:** Modo de escucha continuo (Listo).
  - 🔴 **Rojo:** Grabando palabra clave ("FORWARD").
  - ⚪ **Blanco:** Procesando inferencia TinyML en tiempo real.
  - 🟢 **Verde:** ✅ Autenticación exitosa (Token inyectado).
  - 🚨 **Rojo Parpadeante:** ❌ Acceso denegado (No coincide la voz).

---

## 🛠️ Hardware Utilizado

- **Microcontrolador:** Arduino Nano ESP32 / ESP32-S3 (240 MHz Xtensa LX7, 320 KB SRAM).
- **Micrófono MEMS Digital:** INMP441 (I2S, 16-bit mono, 16 kHz).
- **Conexión de Pines:**
  - `SCK / BCLK` $\rightarrow$ GPIO D4
  - `WS / LRCK` $\rightarrow$ GPIO D5
  - `SD / DOUT` $\rightarrow$ GPIO D6
  - `L/R` $\rightarrow$ GND (Canal Izquierdo)
  - `VDD` $\rightarrow$ 3.3V
  - `GND` $\rightarrow$ GND

---

## 📂 Estructura del Repositorio

```text
├── src/
│   ├── main.cpp            # Firmware completo ESP32-S3 (I2S, VAD, DSP, TFLite, HID)
│   ├── model_data.h        # Modelo TinyML INT8 cuantizado exportado a C array
│   └── mfcc_tables.h       # Tablas precalculadas de Hamming, Mel Filterbank y DCT
├── prepare_dataset.py      # Preprocesamiento, normalización y balanceo de datos
├── train_tinyml.py         # Extracción MFCC, entrenamiento CNN y cuantización INT8
├── generate_tables.py      # Generador de coeficientes DSP para C++
├── audit_dataset.py        # Auditoría de calidad de señales de audio grabadas
├── platformio.ini          # Configuración del proyecto PlatformIO
└── README.md
```

---

## 🚀 Compilación y Despliegue

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/opyntorr/esp32-voice-recognizer.git
   cd esp32-voice-recognizer
   ```
2. Abrir en **PlatformIO** (VS Code).
3. Poner el ESP32 en modo DFU (**doble clic en el botón RESET**).
4. Compilar y subir el firmware (`PlatformIO: Upload`).
5. Abrir el Monitor Serie a **921,600 baudios** o simplemente decir **"FORWARD"** frente al micrófono.
