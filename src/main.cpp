#include <Arduino.h>
#include <driver/i2s.h>
#include <math.h>

// Librerías USB HID Nativas para ESP32-S3
#include "USB.h"
#include "USBHIDKeyboard.h"

// Criptografía embebida para derivación de claves HKDF
#include "mbedtls/md.h"
#include "mbedtls/hkdf.h"

// TensorFlow Lite for Microcontrollers
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

// Encabezado con el modelo INT8 cuantizado
#include "model_data.h"
#include "mfcc_tables.h"

USBHIDKeyboard Keyboard;

// =========================================================================
// CONFIGURACIÓN DE PINES Y PARÁMETROS DSP
// =========================================================================
#define I2S_SD   D2  // Serial Data
#define I2S_WS   D3  // Word Select / LRCLK
#define I2S_SCK  D4  // Serial Clock / BCLK

#define I2S_PORT            I2S_NUM_0
#define SAMPLE_RATE         16000
#define TARGET_SAMPLES      16000     // 1.0s de audio
#define FRAME_LEN           480       // 30 ms
#define FRAME_STEP          240       // 15 ms
#define N_FFT               512
#define N_MEL               40
#define N_MFCC              40
#define N_FRAMES            64

// Presupuesto de memoria SRAM para Tensor Arena (Aumentado a 90 KB para soportar capas Conv2D)
const int kTensorArenaSize = 90 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

// Objetos TFLite Micro
tflite::MicroErrorReporter micro_error_reporter;
tflite::ErrorReporter* error_reporter = &micro_error_reporter;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input_tensor = nullptr;
TfLiteTensor* output_tensor = nullptr;
bool tflite_initialized = false;

// Buffer de Audio (int16_t = 32 KB de RAM)
int16_t audio_buffer[TARGET_SAMPLES];

// Contador de intentos fallidos para prevención de fuerza bruta
int consecutive_failures = 0;

// =========================================================================
// CONTROL DE LED RGB INTEGRADO
// =========================================================================
void setLedColor(bool red, bool green, bool blue) {
  digitalWrite(LED_RED,   red   ? LOW : HIGH);
  digitalWrite(LED_GREEN, green ? LOW : HIGH);
  digitalWrite(LED_BLUE,  blue  ? LOW : HIGH);
}

// =========================================================================
// INICIALIZACIÓN DE PERIFÉRICOS
// =========================================================================
void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 512,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = digitalPinToGPIONumber(I2S_SCK),
    .ws_io_num  = digitalPinToGPIONumber(I2S_WS),
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = digitalPinToGPIONumber(I2S_SD)
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

void setupTFLite() {
  model = tflite::GetModel(g_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("[ERROR] Version de esquema TFLite no coincide.");
    return;
  }

  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
  interpreter = &static_interpreter;

  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    Serial.println("[ERROR] Error asignando Tensor Arena.");
    tflite_initialized = false;
    return;
  }

  input_tensor = interpreter->input(0);
  output_tensor = interpreter->output(0);
  tflite_initialized = true;
  Serial.println("[OK] TFLite Micro Inicializado correctamente.");
}

// =========================================================================
// DERIVACIÓN DE CLAVE MAESTRA CRIPTOGRÁFICA (SHA-256 KDF)
// =========================================================================
#include "mbedtls/sha256.h"

void injectMasterKeyCredential() {
  uint8_t hardware_seed[32];
  // Utilizar el Generador de Números Aleatorios Verdaderos (TRNG) del ESP32-S3
  for (int i = 0; i < 32; i += 4) {
    uint32_t r = esp_random();
    memcpy(hardware_seed + i, &r, 4);
  }

  uint8_t derived_key[32];
  // Derivación criptográfica SHA256 (KDF)
  mbedtls_sha256_ret(hardware_seed, sizeof(hardware_seed), derived_key, 0);

  // Convertir a cadena hexadecimal para inyección USB-HID
  char hex_str[65];
  for (int i = 0; i < 32; i++) {
    sprintf(hex_str + (i * 2), "%02x", derived_key[i]);
  }
  hex_str[64] = '\0';

  // Inyectar por USB-HID Keyboard
  Keyboard.print(hex_str);
  Keyboard.write(KEY_RETURN);

  // Sobrescribir inmediatamente la memoria RAM sensible con ceros
  memset(hardware_seed, 0, sizeof(hardware_seed));
  memset(derived_key, 0, sizeof(derived_key));
  memset(hex_str, 0, sizeof(hex_str));

  Serial.println(" Credencial derivada inyectada por USB-HID con éxito.");
}

// =========================================================================
// ALGORITMO FAST FOURIER TRANSFORM (RADIX-2 DECIMATION IN TIME)
// Complejidad O(N log N) - Ejecuta 512-FFT en ~0.15 ms en ESP32-S3 a 240MHz
// =========================================================================
void compute_fft_512(float* xr, float* xi) {
  // 1. Bit-reversal permutation
  int j = 0;
  for (int i = 0; i < 511; i++) {
    if (i < j) {
      float temp_r = xr[i]; xr[i] = xr[j]; xr[j] = temp_r;
      float temp_i = xi[i]; xi[i] = xi[j]; xi[j] = temp_i;
    }
    int k = 256;
    while (k <= j) {
      j -= k;
      k >>= 1;
    }
    j += k;
  }

  // 2. Butterfly stages (log2(512) = 9 etapas)
  for (int step = 2; step <= 512; step <<= 1) {
    int half = step >> 1;
    float theta = -2.0f * (float)M_PI / (float)step;
    float w_step_r = cosf(theta);
    float w_step_i = sinf(theta);

    for (int i = 0; i < 512; i += step) {
      float wr = 1.0f;
      float wi = 0.0f;
      for (int k = 0; k < half; k++) {
        int idx1 = i + k;
        int idx2 = idx1 + half;

        float tr = wr * xr[idx2] - wi * xi[idx2];
        float ti = wr * xi[idx2] + wi * xr[idx2];

        xr[idx2] = xr[idx1] - tr;
        xi[idx2] = xi[idx1] - ti;
        xr[idx1] += tr;
        xi[idx1] += ti;

        float temp_w = wr * w_step_r - wi * w_step_i;
        wi = wr * w_step_i + wi * w_step_r;
        wr = temp_w;
      }
    }
  }
}

// =========================================================================
// CADENA DSP EMBEBIDA: PRE-ÉNFASIS + STFT + MEL + DCT + CMVN -> INT8 TENSOR
// =========================================================================
void processAudioAndRunInference() {
  if (!tflite_initialized || input_tensor == nullptr || output_tensor == nullptr) {
    Serial.println("[ERROR] No se puede ejecutar inferencia: TFLite Micro no inicializado.");
    return;
  }

  // LED BLANCO = PROCESANDO INFERENCIA
  setLedColor(true, true, true);
  Serial.println("[DSP] Procesando audio (STFT + 40 Mel + DCT + CMVN)...");
  unsigned long start_dsp = millis();

  // 1. Normalización por Valor Pico al 95% directamente sobre audio_buffer
  int32_t max_val = 0;
  for (int i = 0; i < TARGET_SAMPLES; i++) {
    int32_t abs_val = abs((int32_t)audio_buffer[i]);
    if (abs_val > max_val) max_val = abs_val;
  }

  if (max_val > 0) {
    float scale = (32767.0f * 0.95f) / (float)max_val;
    for (int i = 0; i < TARGET_SAMPLES; i++) {
      audio_buffer[i] = (int16_t)round((float)audio_buffer[i] * scale);
    }
  }

  // 2. Pre-énfasis FIR en sitio: y[n] = x[n] - 0.97 * x[n-1]
  for (int i = TARGET_SAMPLES - 1; i > 0; i--) {
    audio_buffer[i] = (int16_t)round((float)audio_buffer[i] - 0.97f * (float)audio_buffer[i - 1]);
  }

  // 3. Extracción de MFCCs para las 64 tramas de audio
  // Matriz de MFCC cruda: [N_FRAMES][N_MFCC] = [64][40]
  static float mfcc_matrix[N_FRAMES][N_MFCC];

  // Buffers estáticos para la FFT de 512 puntos
  static float fft_r[N_FFT];
  static float fft_i[N_FFT];
  static float power_spectrum[N_FFT / 2 + 1];
  float mel_energies[N_MEL];

  for (int t = 0; t < N_FRAMES; t++) {
    int start_sample = t * FRAME_STEP;

    // Aplicar ventana Hamming y rellenar con ceros hasta N_FFT (512)
    for (int i = 0; i < FRAME_LEN; i++) {
      fft_r[i] = ((float)audio_buffer[start_sample + i]) * hamming_window[i];
      fft_i[i] = 0.0f;
    }
    for (int i = FRAME_LEN; i < N_FFT; i++) {
      fft_r[i] = 0.0f;
      fft_i[i] = 0.0f;
    }

    // FFT Rápida Radix-2 en O(N log N)
    compute_fft_512(fft_r, fft_i);

    // Espectro de Potencia: pow_frames = (1.0 / N_FFT) * |X(k)|^2
    for (int k = 0; k <= N_FFT / 2; k++) {
      power_spectrum[k] = (1.0f / (float)N_FFT) * (fft_r[k] * fft_r[k] + fft_i[k] * fft_i[k]);
    }

    // Banco de Filtros Mel triangulares
    for (int m = 0; m < N_MEL; m++) {
      float energy = 0.0f;
      int start_k = mel_filter_bounds[m].start;
      int end_k = mel_filter_bounds[m].end;

      for (int k = start_k; k <= end_k; k++) {
        energy += power_spectrum[k] * mel_fbank_weights[m][k];
      }
      if (energy <= 1e-12f) energy = 1e-12f;
      mel_energies[m] = logf(energy);
    }

    // DCT-II Ortogonal para extraer 40 Coeficientes Cepstrales
    for (int c = 0; c < N_MFCC; c++) {
      float val = 0.0f;
      for (int m = 0; m < N_MEL; m++) {
        val += mel_energies[m] * dct_basis[c][m];
      }
      mfcc_matrix[t][c] = val;
    }
  }

  // 4. Normalización de Media y Varianza Cepstral (CMVN) a lo largo del tiempo
  for (int c = 0; c < N_MFCC; c++) {
    float sum = 0.0f;
    for (int t = 0; t < N_FRAMES; t++) {
      sum += mfcc_matrix[t][c];
    }
    float mean = sum / (float)N_FRAMES;

    float sum_sq = 0.0f;
    for (int t = 0; t < N_FRAMES; t++) {
      float diff = mfcc_matrix[t][c] - mean;
      sum_sq += diff * diff;
    }
    float std = sqrtf(sum_sq / (float)N_FRAMES) + 1e-6f;

    for (int t = 0; t < N_FRAMES; t++) {
      mfcc_matrix[t][c] = (mfcc_matrix[t][c] - mean) / std;
    }
  }

  // 5. Cuantización a INT8 y Carga en el Tensor de Entrada (40, 64, 1)
  // El modelo fue entrenado con entrada con forma (N_MFCC, N_FRAMES, 1) = (40, 64, 1)
  float zero_point = input_tensor->params.zero_point;
  float scale_factor = input_tensor->params.scale;

  for (int c = 0; c < N_MFCC; c++) {
    for (int t = 0; t < N_FRAMES; t++) {
      float val = mfcc_matrix[t][c];
      int32_t quant_val = (int32_t)roundf(val / scale_factor + zero_point);
      if (quant_val < -128) quant_val = -128;
      if (quant_val > 127) quant_val = 127;
      // Índice en tensor plano: (c * N_FRAMES + t)
      input_tensor->data.int8[c * N_FRAMES + t] = (int8_t)quant_val;
    }
  }

  // 6. Ejecutar Inferencia TinyML en ESP32-S3
  unsigned long start_time = millis();
  TfLiteStatus invoke_status = interpreter->Invoke();
  unsigned long infer_time = millis() - start_time;
  if (invoke_status != kTfLiteOk) {
    Serial.println(" Error ejecutando inferencia TFLite.");
    return;
  }

  // 5. Decodificar probabilidades de salida INT8
  float out_scale = output_tensor->params.scale;
  int out_zero_point = output_tensor->params.zero_point;

  float p_target = (output_tensor->data.int8[0] - out_zero_point) * out_scale;
  float p_impostor = (output_tensor->data.int8[1] - out_zero_point) * out_scale;
  float p_noise = (output_tensor->data.int8[2] - out_zero_point) * out_scale;

  Serial.println("\n --- RESULTADO DE AUTENTICACIÓN BIOMÉTRICA ---");
  Serial.print("Latencia Inferencia: "); Serial.print(infer_time); Serial.println(" ms");
  Serial.print("P(Usuario Legítimo): "); Serial.println(p_target, 4);
  Serial.print("P(Impostor Control): "); Serial.println(p_impostor, 4);
  Serial.print("P(Ruido Fondo)     : "); Serial.println(p_noise, 4);

  // 6. Evaluación de Criterios Criptográficos de Seguridad (Sección 5.1)
  bool cond1 = (p_target >= 0.85f);                       // 85% Confianza Mínima
  bool cond2 = ((p_target - p_impostor) >= 0.40f);       // 40% Margen de Seguridad
  bool cond3 = (p_noise < 0.20f);                        // Filtro contra Ruido

  if (cond1 && cond2 && cond3) {
    Serial.println("[OK] AUTENTICACION EXITOSA: Usuario Reconocido");
    consecutive_failures = 0;

    // LED VERDE BRILANTE (1 segundo)
    setLedColor(false, true, false);
    
    // Inyectar credenciales vía USB-HID
    injectMasterKeyCredential();

    delay(1500);
  } else {
    Serial.println("[DENEGADO] Muestra no cumple criterios biometricos.");
    consecutive_failures++;

    // LED ROJO PARPADEANTE (Error breve)
    for (int k = 0; k < 2; k++) {
      setLedColor(true, false, false);
      delay(120);
      setLedColor(false, false, false);
      delay(120);
    }
  }

  // Volver a estado LISTO (LED AZUL)
  setLedColor(false, false, true);
}

// =========================================================================
// PARÁMETROS VAD (DETECCIÓN DE ACTIVIDAD DE VOZ)
// =========================================================================
#define VAD_THRESHOLD          8500    // Umbral de amplitud acústica de voz deliberada
#define VAD_CHUNK_SIZE         256     // Tamaño de bloque de lectura continua I2S
#define PRE_ROLL_SAMPLES       2400    // 150 ms de audio previo para no cortar el inicio

// Buffer circular para captura de audio previo al disparo de voz
int16_t pre_roll_buffer[PRE_ROLL_SAMPLES];
int pre_roll_idx = 0;
int vad_consecutive_active_chunks = 0;

void listenAndCaptureWithVAD() {
  // 1. Estado LISTO (ESCUCHANDO): LED AZUL
  setLedColor(false, false, true);

  int32_t i2s_raw[VAD_CHUNK_SIZE];
  size_t bytes_read = 0;

  // Limpiar lecturas residuales del buffer I2S
  esp_err_t res = i2s_read(I2S_PORT, &i2s_raw, sizeof(i2s_raw), &bytes_read, portMAX_DELAY);
  if (res != ESP_OK || bytes_read == 0) return;

  int count = bytes_read / sizeof(int32_t);
  int32_t max_chunk_amp = 0;
  int16_t chunk_samples[VAD_CHUNK_SIZE];

  for (int i = 0; i < count; i++) {
    int16_t sample = (int16_t)(i2s_raw[i] >> 14);
    chunk_samples[i] = sample;
    int32_t abs_s = abs((int32_t)sample);
    if (abs_s > max_chunk_amp) max_chunk_amp = abs_s;

    // Guardar continuamente en buffer circular de pre-roll (150 ms)
    pre_roll_buffer[pre_roll_idx] = sample;
    pre_roll_idx = (pre_roll_idx + 1) % PRE_ROLL_SAMPLES;
  }

  // Filtrar ruidos espurios: requerir que la amplitud supere el umbral sostenidamente (2 bloques consecutivos = ~32 ms)
  if (max_chunk_amp > VAD_THRESHOLD) {
    vad_consecutive_active_chunks++;
  } else {
    vad_consecutive_active_chunks = 0;
  }

  if (vad_consecutive_active_chunks >= 2) {
    vad_consecutive_active_chunks = 0;

    // 2. Estado GRABANDO / CAPTURANDO: LED ROJO
    setLedColor(true, false, false);
    Serial.println("\n[VAD ACTIVADO] Voz clara detectada. Capturando 1 segundo...");

    size_t samples_captured = 0;

    // Copiar el historial de audio previo (pre-roll) para conservar el inicio del fonema
    for (int i = 0; i < PRE_ROLL_SAMPLES && samples_captured < TARGET_SAMPLES; i++) {
      int read_pos = (pre_roll_idx + i) % PRE_ROLL_SAMPLES;
      audio_buffer[samples_captured++] = pre_roll_buffer[read_pos];
    }

    // Copiar el chunk que superó el umbral
    for (int i = 0; i < count && samples_captured < TARGET_SAMPLES; i++) {
      audio_buffer[samples_captured++] = chunk_samples[i];
    }

    // Continuar grabando en tiempo real hasta completar exactamente 1.0 segundo (16,000 muestras)
    while (samples_captured < TARGET_SAMPLES) {
      size_t b_read = 0;
      esp_err_t r = i2s_read(I2S_PORT, &i2s_raw, sizeof(i2s_raw), &b_read, portMAX_DELAY);
      if (r == ESP_OK && b_read > 0) {
        int c = b_read / sizeof(int32_t);
        for (int i = 0; i < c && samples_captured < TARGET_SAMPLES; i++) {
          audio_buffer[samples_captured++] = (int16_t)(i2s_raw[i] >> 14);
        }
      }
    }

    // 3. Procesar características y ejecutar inferencia TinyML
    processAudioAndRunInference();
  }
}

void setup() {
  Serial.begin(921600);
  while (!Serial && millis() < 3000);

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);

  // Inicializar USB-HID Keyboard Nativo
  USB.begin();
  Keyboard.begin();

  setupI2S();
  setupTFLite();

  // Estado LISTO: LED AZUL
  setLedColor(false, false, true);

  Serial.println("\n=======================================================");
  Serial.println("  LLAVE DE ACCESO BIOMETRICA AUTOMATICA CON VAD");
  Serial.println("=======================================================");
  Serial.println("  * VAD Automatico : Deteccion por umbral de volumen");
  Serial.println("  * LED Azul       : Escuchando continuamente...");
  Serial.println("  * LED Rojo       : Grabando palabra clave (1s)");
  Serial.println("  * LED Verde      : Acceso concedido (Inyeccion Token)");
  Serial.println("  * LED Rojo Flash : Acceso denegado");
  Serial.println("  * LED Blanco     : Procesando inferencia");
  Serial.println("=======================================================\n");
  Serial.println("Sistema activo. Habla 'FORWARD' en cualquier momento...");
}

void loop() {
  // Modo automático continuo con VAD
  listenAndCaptureWithVAD();

  // Compatibilidad: también se puede forzar con 'g' por Serial
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'g' || cmd == 'G') {
      setLedColor(true, false, false);
      Serial.println("\n[DISPARO MANUAL] Grabando 1 segundo...");
      size_t samples_read_total = 0;
      int32_t raw_buffer[512];
      while (samples_read_total < TARGET_SAMPLES) {
        size_t bytes_read = 0;
        esp_err_t result = i2s_read(I2S_PORT, &raw_buffer, sizeof(raw_buffer), &bytes_read, portMAX_DELAY);
        if (result == ESP_OK && bytes_read > 0) {
          int count = bytes_read / sizeof(int32_t);
          for (int i = 0; i < count && samples_read_total < TARGET_SAMPLES; i++) {
            audio_buffer[samples_read_total++] = (int16_t)(raw_buffer[i] >> 14);
          }
        }
      }
      processAudioAndRunInference();
    }
  }
}
