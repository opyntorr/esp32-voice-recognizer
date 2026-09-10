# GUION DE PRESENTACION EJECUTIVA (VERSION CORTA Y CONCISA)
## Llave de Acceso Biometrica con TinyML y USB-HID sobre ESP32-S3

**Autor:** Omar Perez (Omar Payan) | Matricula: A01742658  
**Materia:** TE2046.101  
**Duracion estimada:** 5 a 7 minutos  
**Objetivo:** Transmitir con contundencia el problema, la solucion tecnica de borde (Edge-AI), el pipeline DSP-TinyML y las metricas reales alcanzadas en el silicio.

---

### Slide 1: Portada
> "Buenas tardes. Mi nombre es Omar Perez y hoy les presento el desarrollo de una Llave de Acceso Biometrica con Reconocimiento de Voz Embebido basada en TinyML y emulacion USB-HID, implementada completamente sobre un microcontrolador ESP32-S3."

---

### Slide 2: Contexto y Vulnerabilidades
> "Actualmente enfrentamos un dilema critico en ciberseguridad: las contraseñas complejas se olvidan o son victimas de phishing; los tokens fisicos convencionales solo autentican posesion, no identidad; y la biometria en la nube compromete la privacidad al enviar muestras de audio por internet. Nuestra solucion es Zero-Cloud: un dispositivo de borde que fusiona posesion fisica y biometria conductual en el silicio local, garantizando privacidad absoluta y cero latencia de red."

---

### Slide 3: Hardware y Arquitectura de Cómputo
> "El nucleo del sistema es un ESP32-S3 con doble procesador Xtensa LX7 a 240 MHz con aceleracion vectorial SIMD. Por menos de 5 dolares, integra controlador USB OTG nativo para emular un teclado fisico y canales DMA para el microfono MEMS digital INMP441 via I2S. Supera a placas Linux como Raspberry Pi en consumo energetico, tiempo de arranque instantaneo y costo."

---

### Slide 4: Arquitectura General del Sistema
> "El pipeline opera en 5 etapas continuas: 
> 1. Captura digital I2S a 16 kHz y 16 bits.
> 2. Deteccion de actividad de voz (VAD) con buffer circular de pre-roll de 150 ms para no recortar el inicio de la palabra.
> 3. Cadena de procesamiento digital de señales (DSP) en tiempo real.
> 4. Inferencia con una red neuronal convolucional INT8 en TensorFlow Lite Micro.
> 5. Evaluacion criptografica e inyeccion directa de la credencial por teclado USB."

---

### Slide 5: Maquina de Estados Finitos (FSM)
> "Para garantizar estabilidad industrial, el firmware corre una maquina de estados no bloqueante con retroalimentacion visual en LED RGB: 
> * Azul para escucha continua.
> * Rojo durante la grabacion de 1 segundo.
> * Blanco mientras se ejecuta la inferencia.
> * Verde al conceder acceso con inyeccion de contraseña.
> * Rojo parpadeante si se deniega el acceso.
> * Y un estado de enfriamiento con purga de buffers DMA y liberacion forzada de teclas HID para evitar bloqueos."

---

### Slide 6: Forma de Onda Temporal y Pre-Roll Buffer
> "Aqui observamos la captura de 1 segundo de la palabra clave 'FORWARD'. Noten la zona sombreada de 150 milisegundos: corresponde al buffer circular de pre-roll. Si empezaramos a grabar en el cruce del umbral, perderiamos el fonema fricativo 'F'. Gracias a este buffer, la palabra entra completa con su envolvente natural: ataque fricativo, nucleo vocalico de maxima energia y transicion oclusiva final."

---

### Slide 7: Transformaciones Matematicas DSP en Tiempo Real
> "Para transformar audio temporal en patrones espectro-temporales, implementamos una cadena matematica rigurosa:
> * Normalizacion pico al 95% para independizar la distancia al microfono.
> * Filtro FIR de pre-enfasis para compensar la atenuacion glotal de 6 dB por octava.
> * Enmarcado Hamming de 30 ms con 50% de solapamiento.
> * FFT Radix-2 en O(N log N) que procesa 512 puntos en apenas 0.15 ms.
> * Banco de 40 filtros Mel y DCT-II para extraer coeficientes MFCC.
> * Y normalizacion CMVN para anular la funcion de transferencia acustica de la sala."

---

### Slide 8: Efecto del Filtro de Pre-énfasis
> "En esta grafica vemos el impacto del pre-enfasis: en el dominio del tiempo, aplanamos la onda restando el 97% de la muestra previa; en el espectro en frecuencia, realzamos notablemente la banda de 2 a 7.6 kHz. Es justamente en esas altas frecuencias donde residen los formantes criticos que diferencian una voz de otra."

---

### Slide 9: Espectro de Fase FFT y su Descarte
> "Analizamos el espectro de fase de 16,000 puntos. Como se observa, la distribucion angular oscila aleatoriamente entre menos pi y mas pi debido a minimas diferencias milimetricas en la distancia de la boca al sensor. Por esta razon, en la extraccion MFCC se descarta la fase y se conserva unicamente la magnitud de potencia, otorgando invarianza espacial."

---

### Slide 10: Huella Acustica Promedio (Firma Biometrica)
> "A partir de 148 muestras de mi voz, calculamos la huella espectral media. Se aprecian claramente los tres formantes del tracto vocal: F1 en 136 Hz, F2 en 402 Hz y F3 en 1065 Hz. La franja sombreada verde representa una desviacion estandar, evidenciando una notable consistencia y repetibilidad articulatoria."

---

### Slide 11: Diferenciacion Biometrica: Usuario vs 400 Impostores
> "Esta es la prueba de fuego: comparamos la firma de mi voz frente a 400 muestras de impostores diciendo exactamente 'FORWARD'. Entre 400 Hz y 1,500 Hz existe una zona de maxima separabilidad biometrica: los formantes de los impostores colapsan prematuramente, mientras que mi resonancia orofaringea mantiene energia en bandas especificas. Esto fundamenta la separacion de clases."

---

### Slide 12: Enmarcado Temporal y Ventana Hamming (Anti-Leakage)
> "Para procesar la señal de forma cuasi-estacionaria, dividimos el audio en tramas de 30 milisegundos (480 muestras). Al multiplicar cada trama por una ventana Hamming precalculada, forzamos los extremos suavemente a cero, eliminando discontinuidades de borde y cancelando la fuga espectral (spectral leakage) antes de la FFT."

---

### Slide 13: Espectrograma Mel en el Tiempo
> "El resultado del banco de 40 filtros triangulares es esta representacion tiempo-frecuencia de 40 canales por 64 tramas. Vemos claramente la evolucion de la energia acustica: alta concentracion en filtros graves y medios durante los primeros 250 ms que corresponden al cuerpo de la vocal, transicionando hacia el reposo."

---

### Slide 14: De Filtros Mel a la Matriz MFCC Normalizada por CMVN
> "El pipeline se completa en cuatro pasos:
> 1. Aplicamos el banco de 40 filtros Mel triangulares espaciados perceptualmente.
> 2. Comprimimos logaritmicamente la energia.
> 3. Aplicamos la DCT-II ortogonal para descorrelacionar canales en 40 coeficientes cepstrales.
> 4. Normalizamos por CMVN restando media y dividiendo entre desviacion estandar, entregando una matriz de 40x64 estandarizada lista para la red neuronal."

---

### Slide 15: Arquitectura CNN INT8 de Ultrabajo Consumo
> "Diseñamos una red neuronal convolucional personalizada con tres decisiones de ingenieria clave:
> 1. Entrada de 40x64x1 en tensores INT8.
> 2. Convoluciones separables en profundidad (DepthwiseSeparableConv2D), que reducen mas del 80% de los calculos matematicos.
> 3. Global Average Pooling para eliminar capas densas masivas.
> El modelo completo pesa apenas 20.5 KB en Flash, tiene 10,883 parametros y corre en un Tensor Arena estatico de 90 KB en SRAM."

---

### Slide 16: Diagrama del Flujo Tensorial de la CNN
> "Aqui vemos el recorrido tensorial: el bloque Conv 1 extrae 16 mapas espaciales; el bloque separable colapsa y refina a 32 filtros; el bloque 3 profundiza las caracteristicas; GAP reduce el mapa a un vector de solo 32 valores; y finalmente una capa Softmax de 3 neuronas clasifica entre Usuario Legitimo, Impostor y Ruido Ambiental."

---

### Slide 17: Seguridad Criptografica Ligada al Silicio
> "Para autorizar el acceso, exigimos una triple compuerta: confianza del usuario superior al 85%, margen sobre impostores mayor al 40% y ruido menor al 20%. Ademas, la contraseña no se almacena en memoria: se deriva deterministamente mediante SHA-256 a partir de la direccion MAC grabada en los fusibles electronicos (eFuses) de silicio del chip. Si alguien clona el firmware en otra placa, la clave generada sera completamente inutil."

---

### Slide 18: Evaluacion y Metricas en Hardware Real
> "Medido en el microcontrolador real a 240 MHz:
> * Extraccion DSP: 11.2 ms.
> * Inferencia CNN: 14.8 ms.
> * Tiempo total de decision: menos de 30 milisegundos tras hablar.
> * Consumo de SRAM: 55.3% y Flash al 19.7%.
> * Desempeño: 95.2% de acierto con usuario legitimo y 0.0% de falsas aceptaciones frente a 400 impostores."

---

### Slide 19: Áreas de Mejora Identificadas
> "Hemos identificado mejoras tecnicas concretas:
> 1. Deteccion anti-spoofing con reto interactivo para evitar ataques por grabacion en altavoz.
> 2. Blindaje ante voces similares incorporando 'hard negatives' con tonos y formantes parecidos.
> 3. Uso del periferico criptografico HMAC ligado a eFuse para proteger la clave de derivacion.
> 4. Y enrolamiento local en memoria no volatil (NVS) basado en embeddings vectoriales sin necesidad de reentrenar la red."

---

### Slide 20: Cierre y Preguntas
> "En conclusion, hemos demostrado que es perfectamente viable construir un sistema biometrico de grado industrial, seguro, privado y de tiempo real sobre un microcontrolador de 5 dolares sin depender de internet. Muchas gracias. Quedo a su disposicion para preguntas."
