# GUION DE PRESENTACION MAESTRO Y EXHAUSTIVO (VERSION EXTENSA Y DEFENSA TECNICA)
## Llave de Acceso Biometrica con TinyML y USB-HID sobre ESP32-S3

**Autor:** Omar Perez (Omar Payan) | Matricula: A01742658  
**Materia:** TE2046.101  
**Duracion estimada:** 15 a 20 minutos (Ideal para defensa de proyecto, evaluacion tecnica y sesion de preguntas)  
**Objetivo:** Demostrar dominio absoluto de arquitectura de microcontroladores, teoria DSP, matematicas de señales, diseño tensorial CNN, cuantizacion INT8 y criptografia fisica en silicio.

---

### Slide 1: Portada
**Contenido en pantalla:** Embedded ESP-32 CNN Voice Auth | TE2046.101 | Omar Payan - A01742658.

**Guion de Explicacion:**
> "Muy buenas tardes, profesor y compañeros. Hoy les presento el diseño, implementacion y validacion experimental de una **Llave de Acceso Biometrica con Reconocimiento de Voz Embebido basada en TinyML y emulacion USB-HID**, ejecutada de manera 100% autonoma sobre un microcontrolador ESP32-S3.
> 
> El nucleo de esta investigacion es demostrar que hoy en dia no es necesario depender de servidores en la nube ni de costosas placas Linux para ejecutar modelos avanzados de Aprendizaje Profundo. Hemos logrado comprimir una cadena completa de Procesamiento Digital de Señales y una Red Neuronal Convolucional cuantizada a 8 bits dentro de la memoria estatica de un chip de bajo consumo, garantizando seguridad criptografica ligada a la fisica del silicio y una latencia imperceptible inferior a 30 milisegundos."

---

### Slide 2: Contexto y Vulnerabilidades del Modelo Tradicional
**Contenido en pantalla:** Vulnerabilidades de contraseñas, tokens fisicos y biometria en nube vs. Solucion Edge-AI.

**Guion de Explicacion:**
> "Para entender el valor de este desarrollo, analicemos las tres fallas estructurales de los esquemas de autenticacion contemporaneos:
> 
> Primero, **las contraseñas alfanumericas**: el ser humano es incapaz de memorizar claves criptograficas de 64 caracteres de alta entropia. El usuario tiende a reutilizar claves cortas, exponiendose a ataques de fuerza bruta, diccionarios y phishing.
> 
> Segundo, **los tokens fisicos tradicionales**, como llaves USB convencionales o tarjetas RFID: autentican unicamente posesion, no identidad. Si alguien me roba mi credencial o mi memoria USB en la oficina, el atacante adquiere mis privilegios de acceso de forma inmediata.
> 
> Tercero, **la biometria centralizada en la nube**: servicios como Alexa o APIs de autenticacion remota obligan a digitalizar la voz, paquetizarla y transmitirla por TCP/IP a traves de internet. Esto no solo introduce una latencia dependiente de la red, sino que abre vectores criticos de ataque: intercepcion Man-in-the-Middle y almacenamiento de huellas biometricas en bases de datos vulnerables a filtraciones.
> 
> **Nuestra solucion:** Edge-AI estricto (Zero-Cloud). El 100% de la computacion ocurre dentro del microcontrolador. Ni una sola muestra de audio abandona el circuito integrado. Fusionamos la posesion fisica del hardware con la biometria conductual y anatomica del usuario en un autentico factor de doble autenticacion integrado."

---

### Slide 3: Hardware y Potencia de Computo de Borde
**Contenido en pantalla:** ESP32-S3 Dual-Core LX7 240 MHz, SIMD PIE, USB OTG nativo, DMA I2S, comparativa con SBCs.

**Guion de Explicacion:**
> "En cuanto a la seleccion de hardware, elegimos el **ESP32-S3** montado en el factor de forma Arduino Nano ESP32. ¿Por que este microcontrolador especifico?
> 
> El ESP32-S3 incorpora un procesador de doble nucleo **Xtensa 32-bit LX7 corriendo a 240 MHz**, equipado con instrucciones vectoriales SIMD (*Processor Instruction Extensions* o PIE). Estas instrucciones permiten ejecutar operaciones de producto punto y acumulacion en paralelo en un solo ciclo de reloj, acelerando de forma masiva los tensores de convolucion.
> 
> Ademas, el chip cuenta con **320 KB de memoria SRAM interna** y un controlador nativo **USB Full-Speed OTG**. Esto ultimo es crucial: a diferencia de placas como el ESP32 clasico que requerian un conversor UART externo (como el CP2102), el ESP32-S3 expone directamente las lineas diferenciales D+ y D-, permitiendonos compilar la pila de software **TinyUSB** y emular un teclado fisico estandar (*Human Interface Device*).
> 
> Frente a Single Board Computers (SBC) como una Raspberry Pi —que cuesta entre 50 y 80 dolares, tarda 30 segundos en arrancar un kernel Linux y consume entre 3 y 5 Watts—, nuestra solucion corre en un microcontrolador de menos de **5 dolares**, con un arranque en milisegundos y un consumo energetico inferior a 150 mA."

---

### Slide 4: Arquitectura General del Sistema
**Contenido en pantalla:** Diagrama de 5 bloques: Captura Acustica, Deteccion Inteligente (VAD), Cadena DSP Embebida, Inferencia Neuronal INT8 y Seguridad/USB-HID.

**Guion de Explicacion:**
> "El sistema opera mediante una arquitectura modular de cinco capas sincronizadas:
> 
> 1. **Captura Acustica:** Microfono digital MEMS INMP441 muestreado a 16 kHz y 16 bits mediante el periferico I2S configurado con buffers DMA en segundo plano.
> 2. **VAD y Pre-Roll Buffer:** Un detector de actividad por umbral de energia acústica asistido por un buffer circular de 150 milisegundos que evita el recorte del fonema inicial.
> 3. **Cadena DSP Embebida:** Una secuencia matematica determinista que normaliza, pre-enfatiza, enmarca en ventanas Hamming, ejecuta una FFT Radix-2, aplica un banco de 40 filtros Mel y normaliza mediante CMVN.
> 4. **Inferencia Neuronal INT8:** Una red convolucional personalizada desplegada bajo TensorFlow Lite Micro que evalua la huella en ~15 milisegundos.
> 5. **Seguridad y USB-HID:** Una logica de decision probabilistica de tres compuertas y una derivacion criptografica SHA-256 ligada a los fusibles de silicio (eFuses), inyectando la credencial directamente al sistema operativo."

---

### Slide 5: Maquina de Estados Finitos (FSM) del Firmware
**Contenido en pantalla:** Diagrama de flujo de 6 estados: LISTENING (Azul), RECORDING (Rojo), INFERENCE (Blanco), AUTH_SUCCESS (Verde), AUTH_FAILED (Rojo Flash), COOLDOWN (Apagado).

**Guion de Explicacion:**
> "En sistemas embebidos de tiempo real, el uso de funciones bloqueantes como `delay()` o bucles `while(1)` infinitos destruye la sincronia y puede colgar la pila USB. Por ello, diseñamos una **Maquina de Estados Finitos (FSM)** robusta y asincrona con señalizacion por LED RGB:
> 
> * **Estado 1: ESCUCHANDO (LED Azul):** El microcontrolador muestrea pasivamente el ambiente y alimenta continuamente el buffer circular de pre-roll.
> * **Estado 2: GRABANDO (LED Rojo):** Al detectar una energia acustica sostenida superior a 32 ms, el sistema copia el pre-roll y acumula las 16,000 muestras del segundo completo con un temporizador de salvaguarda de 1.5 s para evitar bloqueos.
> * **Estado 3: INFERENCIA (LED Blanco):** Se ejecuta la cadena DSP y la red neuronal en ~15 ms.
> * **Estado 4: ACCESO CONCEDIDO (LED Verde):** Si se superan los criterios, se deriva la clave de hardware y se inyecta por USB con un espaciado inter-caracter de 12 ms para evitar saturar los buffers del sistema anfitrion.
> * **Estado 5: ACCESO DENEGADO (LED Rojo Parpadeante):** Si la voz no coincide, se emite una alerta visual de dos pulsos y se incrementa el contador de fallos.
> * **Estado 6: ENFRIAMIENTO (LED Apagado):** Un estado critico de 400 ms donde ejecutamos `i2s_zero_dma_buffer()` y purgamos los residuos del canal I2S, forzando a la vez `Keyboard.releaseAll()` para asegurar que ninguna tecla quede pegada en el sistema operativo."

---

### Slide 6: Forma de Onda Temporal y Zona de Pre-Roll
**Contenido en pantalla:** Grafica de amplitud PCM 16-bit vs tiempo (1.0 s) de 'FORWARD', zona sombreada de 150 ms, fonemas /f/, /or/, /w-r/, /d/.

**Guion de Explicacion:**
> "Esta grafica ilustra la forma de onda de 1 segundo de la palabra clave 'FORWARD'. Quiero llamar su atencion a la zona sombreada en los primeros 150 milisegundos: es nuestro **Buffer Circular de Pre-Roll**.
> 
> En cualquier sistema disparado por volumen, la consonante inicial 'F' —siendo una fricativa labiodental no sonora— tiene una energia muy baja comparada con la vocal 'O'. Si empezaramos a grabar en el momento exacto en que la señal cruza el umbral de 8,500 cuentas, la 'F' se truncaria y la red recibiria una muestra incompleta. Al mantener en memoria las 2,400 muestras anteriores al disparo y ensamblarlas con el audio entrante, capturamos con fidelidad matematica la secuencia fonetica completa: el ataque fricativo, el nucleo vocalico periodico de maxima amplitud y la caida final."

---

### Slide 7: Transformaciones Matematicas DSP en Tiempo Real
**Contenido en pantalla:** Descripcion de las 6 transformaciones: Normalizacion 95%, Pre-enfasis, Enmarcado Hamming, FFT Radix-2, 40 Filtros Mel + DCT-II, CMVN Temporal.

**Guion de Explicacion:**
> "Para que una red convolucional pueda clasificar voz, debemos convertir la señal unidimensional de voltaje en una representacion tiempo-frecuencia invariance. Esto se logra mediante una cadena DSP de 6 etapas:
> 
> 1. **Normalizacion de pico:** Escalamos la onda de forma que su maximo alcance 31,128 cuentas (el 95% de 32,767). Esto compensa si el usuario habla mas fuerte o a distinta distancia.
> 2. **Pre-enfasis:** Un filtro FIR que eleva los formantes de alta frecuencia.
> 3. **Enmarcado Hamming:** Segmentacion en 64 tramas de 30 ms con solapamiento de 15 ms.
> 4. **FFT Radix-2:** Descomposicion ortogonal en el dominio de la frecuencia.
> 5. **Banco Mel y DCT-II:** Compresion perceptual y descorrelacion cepstral.
> 6. **CMVN:** Estandarizacion temporal que neutraliza la acustica del entorno."

---

### Slide 8: Efecto del Filtro de Pre-énfasis
**Contenido en pantalla:** Graficas comparativas: detalle temporal de 60 ms y respuesta espectral (caida natural de 6 dB/octava vs espectro pre-enfatizado en 2 - 7.6 kHz).

**Guion de Explicacion:**
> "El habla humana tiene una caracteristica fisiologica universal: la vibracion de las cuerdas vocales y la radiacion labial introducen una **caida natural de energia de aproximadamente 6 dB por octava** hacia las altas frecuencias.
> 
> Como vemos en la curva azul inferior, los graves (<1 kHz) acaparan casi toda la potencia, mientras que las frecuencias de 2 a 7.6 kHz quedan atenuadas. Sin embargo, en esas frecuencias altas residen las cavidades de resonancia mas sensibles que diferencian una voz humana de otra. Aplicando la ecuacion de diferencias $y[n] = x[n] - 0.97 \cdot x[n-1]$, implementamos un filtro pasa-altas que 'aplana' el espectro (curva naranja), permitiendo que la red convolucional extraiga caracteristicas con igual resolucion dinamica en todo el espectro."

---

### Slide 9: Espectro de Fase FFT y Razon de su Descarte
**Contenido en pantalla:** Grafica del angulo de fase phi(f) entre -pi y +pi en 16,000 puntos. Explicacion de invarianza espacial.

**Guion de Explicacion:**
> "Al calcular la Transformada de Fourier obtenemos una señal compleja con magnitud y fase. En esta diapositiva graficamos el espectro de fase completo de la palabra 'FORWARD'.
> 
> Noten como la distribucion angular oscila caoticamente entre $-\pi$ y $+\pi$. Esto se debe a que la fase representa la alineacion temporal milimetrica de cada onda senoidal. Una variacion de apenas 2 centimetros en la distancia de la boca al microfono introduce un retardo temporal que destruye completamente la coherencia de fase. Por esta razon de estricta invarianza espacial y acustica, el estandar de la industria y nuestro pipeline descartan la fase y operan exclusivamente con la **densidad espectral de potencia** ($|X(f)|^2$)."

---

### Slide 10: Huella Acustica Promedio y Formantes
**Contenido en pantalla:** FFT promedio de 148 muestras del usuario con banda de desviacion estandar (+/- 1 std). Picos de formantes: F1 = 136 Hz, F2 = 402 Hz, F3 = 1065 Hz.

**Guion de Explicacion:**
> "En esta diapositiva podemos apreciar la **firma biometrica real** del usuario. Promediamos el espectro de Fourier de 148 grabaciones individuales de mi voz diciendo 'FORWARD'.
> 
> Se observan con total nitidez las resonancias caracteristicas de mi tracto vocal:
> * **F1 en 136 Hz:** Asociado al tono fundamental glotal ($F_0$).
> * **F2 en 402 Hz:** Asociado a la primera cavidad faringea.
> * **F3 en 1,065 Hz:** Formante clave de la vocalizacion posterior.
> La banda verde sombreada indica la variabilidad natural ($\pm 1\sigma$), demostrando que la emision vocal es altamente reproducible cuando el hablante se encuentra en condiciones confortables."

---

### Slide 11: Separabilidad Biometrica: Usuario vs 400 Impostores
**Contenido en pantalla:** Curva de densidad espectral del usuario (verde) vs promedio de 400 impostores (rojo discontinuo). Zona de maxima separabilidad entre 400 y 1,500 Hz.

**Guion de Explicacion:**
> "Aqui reside la justificacion matematica de por que este sistema funciona. Superpusimos la firma media del usuario frente a 400 muestras de personas distintas diciendo la misma palabra 'FORWARD' del dataset de Google Speech Commands.
> 
> Observen la region entre **400 Hz y 1,500 Hz**: mientras que el espectro promedio de los impostores decae monotonamente a partir de los 500 Hz, mi voz exhibe picos de resonancia pronunciados en 402 Hz y 1,065 Hz debido a la geometria unica de mi cavidad oral y nasal. Es esta disparidad espectral lo que la red convolucional aprende a detectar como una frontera de decision de alta dimension."

---

### Slide 12: Enmarcado Temporal y Ventana Hamming (Anti-Leakage)
**Contenido en pantalla:** Trama de 30 ms (480 pts), Ponderacion de la Ventana Hamming, Trama suavizada final con extremos atenuados.

**Guion de Explicacion:**
> "La Transformada de Fourier asume que la señal analizada es periodica e infinita. Si simplemente cortaramos bloques rectangulares de 30 ms de audio, los puntos de inicio y fin de la trama tendrian discontinuidades abruptas de voltaje. Al calcular la FFT, esas discontinuidades generarian armonicos espurios artificiales, un fenomeno conocido como **fuga espectral** (*spectral leakage*).
> 
> Para neutralizarlo, multiplicamos cada trama de 480 muestras por una **ventana Hamming precalculada**: $w[n] = 0.54 - 0.46 \cos(2\pi n / (N-1))$. Como muestra la tercera grafica, la ventana forza suavemente los extremos a cero, preservando intacta la periodicidad central y garantizando picos espectrales limpios."

---

### Slide 13: Espectrograma Log-Mel en el Tiempo
**Contenido en pantalla:** Mapa de calor de 40 canales Mel x 64 tramas temporales (1.0 s) con escala de energia ln(E).

**Guion de Explicacion:**
> "Al concatenar las tramas en el tiempo, obtenemos este **Espectrograma Log-Mel de 40 canales verticales por 64 tramas horizontales**.
> 
> En este mapa de calor, el eje vertical representa las frecuencias perceptuales (desde 80 Hz en la base hasta 7,600 Hz en la cuspide) y el color representa la energia logaritmica. Vemos con claridad la cronologia fonetica: el arranque de alta energia en canales bajos (tonos amarillos intensos) durante los primeros 250 ms que corresponden al fonema vocalico, seguido de una dispersion de menor energia en frecuencias medias hasta extinguirse en el silencio de la sala."

---

### Slide 14: De Filtros Mel a la Matriz MFCC Normalizada con CMVN
**Contenido en pantalla:** 4 graficas: Banco de 40 filtros triangulares Mel, Matriz MFCC (DCT-II), Espectrograma Log-Mel y Matriz Normalizada CMVN (Tensor INT8).

**Guion de Explicacion:**
> "Esta diapositiva resume la transformacion final hacia el tensor de entrada de la red:
> 
> 1. **Banco Mel:** 40 filtros triangulares que se van ensanchando conforme sube la frecuencia, imitando la escala perceptual de la coclea humana.
> 2. **DCT-II Ortogonal:** Al aplicar la Transformada Discreta del Coseno sobre las energias Mel, descorrelacionamos los canales. El coeficiente $c=1$ almacena la energia total, mientras que los coeficientes $c=2$ a $c=13$ capturan la envolvente del tracto vocal.
> 3. **Normalizacion CMVN Temporal:** Restamos la media de cada fila y dividimos entre su desviacion estandar. Esto convierte la matriz en un mapa estandarizado con media cero y varianza unitaria (grafica inferior derecha). Gracias a CMVN, si el microfono capta reverberacion de la sala o variaciones en la respuesta en frecuencia del sensor, dicho sesgo estacionario queda completamente cancelado."

---

### Slide 15: Arquitectura CNN INT8 de Ultrabajo Consumo
**Contenido en pantalla:** Metricas: 10,883 parametros, 20.5 KB Flash, 90 KB SRAM Tensor Arena, latencia ~15 ms, DepthwiseConv2D y GAP.

**Guion de Explicacion:**
> "Diseñamos una arquitectura profunda altamente optimizada para microcontroladores. Tuvimos tres restricciones fundamentales:
> 
> * **Memoria:** Usamos `DepthwiseSeparableConv2D`, una tecnica donde primero se filtra espacialmente cada canal y luego se combinan mediante una convolucion $1 \times 1$. Esto reduce en **mas de un 80%** las operaciones matematicas comparado con una convolucion 2D estandar.
> * **Sin capas densas masivas:** En lugar de aplanar tensores con `Flatten()` y meter capas densas de miles de neuronas que dispararian la memoria RAM a cientos de kilobytes, colocamos una capa `GlobalAveragePooling2D`. Esto colapsa el mapa espacial a un vector compacto de 32 elementos.
> * **Cuantizacion Post-Entrenamiento (PTQ) a INT8:** Convertimos todos los pesos, activaciones y entradas de punto flotante de 32 bits a enteros de 8 bits con signo. Esto reduce el modelo en un **75%**, dejandolo en apenas **20.5 KB en Flash** y permitiendo que se ejecute en un bloque de memoria estatica de **90 KB (Tensor Arena)** sin fugas de memoria."

---

### Slide 16: Recorrido Tensorial de la Red Convolucional
**Contenido en pantalla:** Diagrama 3D de bloques: Entrada (40x64x1) -> Conv1 (20x32x16) -> Separable (10x16x32) -> Conv3 (10x16x32) -> GAP Vector (32x1) -> Dense Softmax (Y1, Y2, Y3).

**Guion de Explicacion:**
> "Aqui podemos seguir con precision el recorrido tensorial dentro del chip:
> 
> El tensor de entrada $(40, 64, 1)$ ingresa al **Bloque Conv 1** con 16 filtros $3 \times 3$, seguido de ReLU, Batch Normalization y MaxPool $2 \times 2$, reduciendo la dimensionalidad a $(20, 32, 16)$.
> El **Bloque 2 (Separable)** aplica convolucion en profundidad y proyeccion $1 \times 1$ con 32 filtros, seguido de otro MaxPool $2 \times 2$, resultando en un tensor de $(10, 16, 32)$.
> El **Bloque 3** profundiza las caracteristicas de alto nivel sin reducir resolucion.
> La capa **GAP** promedia espacialmente las matrices, produciendo un vector unidimensional de $32 \times 1$.
> Finalmente, una capa **Dense Softmax** calcula las probabilidades de las tres clases: $Y_1$ (Usuario Legitimo), $Y_2$ (Impostor de Control) e $Y_3$ (Ruido Ambiental)."

---

### Slide 17: Seguridad Criptografica Ligada al Silicio
**Contenido en pantalla:** Triple compuerta (>=85%, >=40%, <20%), derivacion SHA-256 ligada a eFuses (esp_read_mac) y anti-clonacion.

**Guion de Explicacion:**
> "La mejor inteligencia artificial no sirve de nada si la capa de ciberseguridad es debil. Implementamos dos mecanismos de seguridad fundamentales:
> 
> Primero, **la Triple Compuerta Biometrica:** No basta con que la probabilidad del usuario sea mayor al 50%. Exigimos concurrentemente que:
> 1. $P(\text{Usuario}) \ge 85\%$.
> 2. El margen de victoria sobre el impostor sea al menos del 40% ($P(\text{Usuario}) - P(\text{Impostor}) \ge 0.40$).
> 3. La probabilidad de ruido sea inferior al 20%.
> 
> Segundo, **la Raiz de Confianza Ligada al Silicio:** ¿Como generamos la contraseña? En lugar de guardar una clave fija en texto plano en la memoria Flash (vulnerable a extraccion fisica), usamos una **KDF determinista**. Leemos la direccion MAC unica que viene grabada de fabrica en los fusibles electronicos irreversibles (**eFuses**) del ESP32-S3 y calculamos:
> $$\text{Clave Maestra} = \text{SHA256}(\text{eFuse\_MAC} \parallel \text{Domain\_Salt})$$
> Esto produce una cadena hexadecimal fija de 64 caracteres exclusiva de esta placa. Si un atacante roba el firmware binario y lo clona en otro ESP32, la MAC de los eFuses del nuevo microcontrolador sera distinta y la clave generada sera completamente diferente. Ademas, aplicamos `memset` a ceros inmediatamente despues de la inyeccion USB."

---

### Slide 18: Evaluacion y Metricas en Hardware Real
**Contenido en pantalla:** DSP = 11.2 ms, Inferencia = 14.8 ms, Tiempo total < 30 ms, SRAM = 55.3%, Flash = 19.7%, Acierto = 95.2%, FAR = 0.0%.

**Guion de Explicacion:**
> "Validamos el sistema experimentalmente sobre la placa física corriendo a 240 MHz:
> 
> * **Tiempos de ejecucion:** La extraccion DSP completa (STFT, Mel, DCT y CMVN) toma apenas **11.2 milisegundos**. La inferencia de la CNN toma **14.8 milisegundos**. El tiempo de decision tras terminar de hablar es de **menos de 30 ms**, lo cual resulta en una percepcion de acceso totalmente instantaneo.
> * **Recursos de memoria:** Usamos 181 KB de SRAM (**55.3% de la memoria total**), dejando mas de 140 KB libres para las colas DMA y la pila TinyUSB. La memoria Flash ocupa solo 620 KB de los 3.1 MB de la particion de programa (**19.7%**).
> * **Rendimiento biometrico:** Alcanzamos un **95.2% de precision con el usuario legitimo** y un **0.0% de Falsas Aceptaciones (FAR)** frente al banco de 400 impostores en pruebas de laboratorio."

---

### Slide 19: Áreas de Mejora y Trabajo Futuro
**Contenido en pantalla:** Tabla de 7 areas de mejora: Anti-Spoofing, Hard Negatives, eFuse HMAC, Pre-enfasis en Python, Rate Limiting, Enrolamiento NVS y Dual-Core FreeRTOS.

**Guion de Explicacion:**
> "Como ingenieros responsables, identificamos con rigor cientifico las areas de evolucion para llevar este dispositivo a un producto comercial de grado militar:
> 
> 1. **Deteccion Anti-Spoofing:** Implementar vivacidad mediante un reto interactivo (por ejemplo, pronunciar un numero aleatorio de 3 digitos mostrado en una pantalla OLED) para neutralizar ataques de repeticion grabados con un telefono celular.
> 2. **Blindaje ante Voces Parecidas:** Incorporar 'hard negatives' de familiares o personas con formantes similares durante el entrenamiento para endurecer las fronteras de decision.
> 3. **Blindaje Criptografico con eFuse HMAC:** Utilizar el periferico acelerador SHA/HMAC por hardware del ESP32-S3 quemando una clave en el eFuse `BLOCK_KEY0` con lectura deshabilitada.
> 4. **Rate Limiting:** Aplicar retardos exponenciales ante intentos fallidos consecutivos (1s, 2s, 4s, 8s) para frustrar ataques de diccionario.
> 5. **Enrolamiento Local por Embeddings:** Migrar hacia modelos con perdidas metricas (ArcFace / Triplet Loss) para almacenar vectores caracteristicos en memoria NVS y registrar usuarios sin necesidad de reentrenar la red en PC.
> 6. **Separacion Dual-Core:** Asignar la captura I2S DMA y la pila USB al Nucleo 0 y dedicar exclusivamente el Nucleo 1 a la inferencia convolucional."

---

### Slide 20: Cierre y Preguntas
**Contenido en pantalla:** Agradecimiento y sesion de preguntas.

**Guion de Explicacion:**
> "En conclusion, hemos demostrado que es totalmente factible construir un sistema biometrico de voz de alta seguridad, resistente a clonacion, con proteccion absoluta de la privacidad y con tiempos de respuesta en tiempo real, operando sobre un microcontrolador economico de menos de 5 dolares.
> 
> Muchas gracias por su atencion. Quedo completamente abierto a sus preguntas, observaciones tecnicas o demostracion en vivo."
