# Presentacion Ejecutiva del Proyecto: Llave Biometrica con TinyML y USB-HID sobre ESP32-S3

---

## Slide 1: Portada y Titulo

### Llave de Acceso Biometrica con Reconocimiento de Voz Embebido (TinyML) e Inyeccion de Credenciales por USB-HID
**Subtitulo:** Seguridad fisica de nueva generacion impulsada por Inteligencia Artificial en el borde (Edge AI)  
**Autor:** Omar Perez  
**Plataforma:** ESP32-S3 (Xtensa Dual-Core LX7) + Microfono MEMS I2S INMP441  
**Repositorio Oficial:** `https://github.com/opyntorr/esp32-voice-recognizer.git`  

---

## Slide 2: El Problema y la Oportunidad

### Limitaciones de la Autenticacion Tradicional
* **Tokens Fisicos (USB / Tarjetas):** Vulnerables a extravio, robo o suplantacion fisica; cualquier persona que los posea obtiene acceso.
* **Contraseñas Complejas:** Dificiles de memorizar para los usuarios y susceptibles a ataques de phishing o fuerza bruta.
* **Biometria Centralizada en la Nube:** Transmite muestras de voz a servidores externos, introduciendo latencia, dependencia de conexion y riesgos criticos de privacidad.

### La Solucion: Edge AI / Zero-Cloud
* **Autonomia Total:** El microcontrolador analiza la voz directamente en su silicio local.
* **Privacidad Absoluta:** Ningun paquete de audio o dato biometrico sale jamas del dispositivo.
* **Factor Doble Integrado:** Posesion fisica del hardware + Biometria conductual de voz.

---

## Slide 3: Propuesta de Valor y Caracteristicas Clave

### Lo que hace unico a este sistema
1. **Deteccion Automatica de Voz (VAD Inteligente):** Monitorea continuamente el entorno con un filtro de persistencia temporal (32 ms) que descarta ruidos aislados.
2. **Buffer Circular de Pre-Roll (150 ms):** Preserva el inicio y fonema de ataque de la palabra clave ("FORWARD") para evitar truncamientos.
3. **Inferencia Ultrarrapida (<15 ms):** Red Convolucional (CNN) cuantizada a INT8 ejecutada en memoria estatica con TensorFlow Lite Micro.
4. **Criptografia Ligada al Silicio:** Contraseña maestra ligada a los eFuses de hardware del chip.
5. **Emulacion USB-HID Universal:** Funciona como un teclado fisico estandar sin requerir software ni controladores especiales en la PC anfitriona.

---

## Slide 4: Arquitectura del Sistema (Pipeline de Extremo a Extremo)

### Flujo Operativo en 5 Etapas
```
[1. Sensor Acustico I2S] -> Captura a 16 kHz / 16-bit mono desde microfono INMP441
           |
           v
[2. Disparo VAD + Pre-Roll] -> Deteccion continua + Inyeccion de los 150 ms previos
           |
           v
[3. Procesador DSP Embebido] -> Pre-enfasis -> Framing -> FFT Radix-2 -> 40 Mel -> DCT-II -> CMVN
           |
           v
[4. Red Neuronal INT8 TinyML] -> Evaluacion convolucional en TFLite Micro (~15 ms)
           |
           v
[5. Inyeccion Criptografica HID] -> Validacion de umbrales -> Escritura automatica por USB
```

---

## Slide 5: Hardware Utilizado y Conectividad

### Componentes de Grado Industrial y Bajo Costo
* **Microcontrolador ESP32-S3 (Arduino Nano ESP32):**
  * Procesador Dual-Core Xtensa 32-bit LX7 a 240 MHz con aceleracion SIMD.
  * 320 KB SRAM interna + 16 MB Flash.
  * Interfaz nativa USB Full-Speed OTG para emular teclados sin chips intermedios.
* **Microfono Digital MEMS INMP441:**
  * Comunicacion síncrona I2S con acceso directo a memoria (DMA).
  * Relacion Señal/Ruido (SNR) de 61 dBA.

### Tabla de Conexionado
| Linea I2S | Pin Microfono | Pin ESP32-S3 | Funcion |
| :--- | :--- | :--- | :--- |
| **Alimentacion** | VDD / GND | 3.3V / GND | Energia regulada de bajo ruido |
| **Serial Data (SD)** | SD | D2 (GPIO 5) | Flujo PCM directo a memoria DMA |
| **Word Select (WS)** | WS | D3 (GPIO 6) | Sincronizacion de tramas (16 kHz) |
| **Serial Clock (SCK)** | SCK | D4 (GPIO 7) | Reloj maestro de muestreo BCLK |
| **Canal (L/R)** | L/R | GND | Configuracion de canal izquierdo |

---

## Slide 6: Procesamiento Digital de Señales (DSP)

### De Ondas Acusticas a Espectrogramas MFCC en Milisegundos
* **Normalizacion de Pico al 95%:** Ajusta la amplitud independientemente de la distancia de la boca al sensor.
* **Filtro FIR de Pre-enfasis:** $y[n] = x[n] - 0.97 \cdot x[n-1]$ (realza frecuencias formantes entre 2 y 7.6 kHz).
* **Enmarcado Hamming:** 64 tramas temporales de 30 ms con 50% de solapamiento (15 ms de salto).
* **FFT Radix-2 en O(N log N):** Algoritmo Cooley-Tukey optimizado; calcula una FFT de 512 puntos en **0.15 ms**.
* **40 Filtros Triangulares Mel + DCT-II:** Modela la percepcion psicoacustica del oido humano y descorrelaciona la energia.
* **Normalizacion CMVN:** Resta la media y divide entre la desviacion estandar en el tiempo, cancelando el eco de la sala.

---

## Slide 7: Inteligencia Artificial: Red Neuronal Convolucional INT8

### Arquitectura Optimizada para Microcontroladores
* **Entrada:** Matriz espectro-temporal de 40 MFCCs x 64 tramas x 1 canal.
* **Convoluciones 2D y Depthwise Separables:** Maximizan la capacidad de extraccion de patrones de formantes minimizando operaciones matematicas.
* **Global Average Pooling:** Elimina capas densas voluminosas, reduciendo el riesgo de sobreajuste.
* **Salida:** 3 neuronas con activacion Softmax:
  * Clase 0: Usuario Legitimo ("FORWARD").
  * Clase 1: Impostores de Control (Hablantes externos diciendo "FORWARD").
  * Clase 2: Ruido Ambiental y Silencio.

### Eficiencia y Cuantizacion
* **Parametros Totales:** 10,883 parametros.
* **Cuantizacion Completa INT8:** Reduce el modelo original de float32 a **solo 20.5 KB**.
* **Presupuesto Tensor Arena:** 90 KB de SRAM fija (cero fugas de memoria, cero asignaciones dinamicas).

---

## Slide 8: Seguridad y Criptografia Ligada al Silicio

### Triple Filtro Biometrico de Seguridad
Para conceder acceso, la inferencia debe cumplir simultaneamente:
1. **Confianza Minima:** $P(\text{Usuario Legitimo}) \ge 85\%$.
2. **Margen contra Impostores:** $P(\text{Usuario}) - P(\text{Impostor}) \ge 40\%$.
3. **Filtro Anti-Ruido:** $P(\text{Ruido Ambiental}) < 20\%$.

### Clave Maestra Inmutable Ligada a eFuses
* **Identidad Fisica Unica:** Utiliza la direccion MAC grabada de fabrica en los fusibles electronicos irreversibles del silicio (`esp_read_mac`).
* **Derivacion Determinista SHA-256:**
  $$\text{Clave Maestra (64 caracteres)} = \text{SHA256}(\text{eFuse\_MAC} \parallel \text{Domain\_Salt})$$
* **Garantia Anti-Clonacion:** Aunque un atacante copie exactamente el firmware a otro ESP32, la MAC de los eFuses sera diferente y la clave generada sera inutil.
* **Sanitizacion Inmediata:** Los buffers en memoria RAM se borran a ceros (`memset`) inmediatamente despues de la inyeccion.

---

## Slide 9: Arquitectura de Software: Maquina de Estados Finitos (FSM)

### Operacion Continua y Resiliente
* **STATE_LISTENING (LED Azul):** Escucha continua con pre-roll buffer activo.
* **STATE_RECORDING (LED Rojo):** Grabacion exacta de 1.0 segundo con timeout de proteccion.
* **STATE_INFERENCE (LED Blanco):** Extraccion DSP y evaluacion neuronal en ~15 ms.
* **STATE_AUTH_SUCCESS (LED Verde):** Autenticacion lograda e inyeccion segura USB-HID.
* **STATE_AUTH_FAILED (LED Rojo Flash):** Muestra rechazada y aviso visual.
* **STATE_COOLDOWN (LED Apagado):** Enfriamiento de 400 ms, liberacion forzada de teclas (`Keyboard.releaseAll()`) y purga activa de buffers DMA I2S (`i2s_zero_dma_buffer`).

---

## Slide 10: Resultados Experimentales y Metricas

### Rendimiento Medido en Hardware Real
| Parametro de Evaluacion | Resultado Experimental | Estado / Evaluacion |
| :--- | :--- | :--- |
| **Tiempo de Extraccion DSP** | 11.2 milisegundos | En tiempo real sin demoras perceptibles |
| **Latencia de Inferencia CNN** | 14.8 milisegundos | Ultrarrapido en ESP32-S3 |
| **Tiempo de Respuesta Total** | < 30 ms (post-grabacion) | Acceso instantaneo |
| **Uso de Memoria SRAM** | 55.3% (181 KB de 320 KB) | Libre de desbordamientos |
| **Uso de Memoria Flash** | 19.7% (620 KB de 3.1 MB) | Ample espacio para expansion |
| **Tasa de Acierto Usuario** | 95.2% de confianza promedio | Alta confiabilidad biometrica |
| **Falsas Aceptaciones (FAR)** | 0% en pruebas de laboratorio | Rechazo absoluto de impostores |

---

## Slide 11: Casos de Uso y Aplicaciones Practicas

### Donde se aplica esta tecnologia?
1. **Acceso a Estaciones de Trabajo y Laptops:** Inyeccion de contraseñas complejas o tokens de inicio de sesion corporativos sin necesidad de escribir en el teclado.
2. **Bovedas de Contraseñas y Gestores (KeePass, Bitwarden):** Desbloqueo rapido de la base de datos de contraseñas mediante comando biometrico.
3. **Control de Acceso Fisico Seguro:** Cerraduras electronicas y puertas de alta seguridad que exijan confirmacion de presencia fisica y de voz.
4. **Entornos Industriales o de Salud:** Autenticacion manos libres en ambientes donde el teclado es un foco de contaminacion o se requiere guantes de proteccion.

---

## Slide 12: Conclusiones y Trabajo Futuro

### Conclusiones Principales
* Se logro implementar con exito un sistema biometrico de voz de grado productivo en un microcontrolador economico sin conectividad a internet.
* La combinacion de VAD con buffer pre-roll, FFT Radix-2 en $O(N \log N)$ y cuantizacion INT8 demuestra el inmenso potencial de TinyML en dispositivos restringidos.
* La integracion de criptografia basada en eFuses elimina de raiz la vulnerabilidad de clonacion de dispositivos.

### Siguientes Pasos
* Soporte para multiples palabras clave o frases de paso (*passphrases* personalizables).
* Aprendizaje local (*On-Device Few-Shot Learning*) para registrar usuarios directamente en el microcontrolador sin reentrenamiento en PC.
