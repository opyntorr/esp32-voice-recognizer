# REPORTE DE LABORATORIO: ANÁLISIS DE SEÑALES DE VOZ EN EL DOMINIO DEL TIEMPO Y DE LA FRECUENCIA PARA RECONOCIMIENTO BIOMÉTRICO

---

## Portada

**Título del Proyecto:** Estudio Experimental del Contenido Espectral, Temporal y Estadístico de la Voz Humana para Sistemas de Reconocimiento y Biometría de Audio  
**Institución / Curso:** Procesamiento Digital de Señales (DSP) & Sistemas Inteligentes Embebidos  
**Estudiante / Integrante:** Omar Pérez  
**Plataforma de Adquisición y Hardware:** Micrófono Digital MEMS I2S INMP441 + Microcontrolador ESP32-S3 (240 MHz, Xtensa LX7)  
**Entorno de Análisis:** Python (NumPy, SciPy, Matplotlib, Pandas, Jupyter Notebooks)  
**Repositorio Oficial:** `https://github.com/opyntorr/esp32-voice-recognizer.git`  
**Palabra / Frase Clave de Prueba:** "FORWARD"  
**Fecha:** Septiembre 2026  

---

## 1. Introducción y Marco Teórico

El reconocimiento de voz y la autenticación biométrica de hablante descansan sobre el principio físico de que el tracto vocal de cada ser humano actúa como un filtro acústico con resonancias particulares (denominadas **formantes** $F_1, F_2, F_3, \dots$) y una frecuencia de vibración glotal primaria (tono fundamental $F_0$ o *pitch*). 

Para determinar si las representaciones en el dominio del tiempo y de la frecuencia permiten discriminar un hablante legítimo de impostores y fuentes de ruido, se plantearon tres experimentos secuenciales:
1. **Experimento 1:** Caracterización temporal, espectral, estadística descriptiva completa y validación del Teorema de Wiener-Khinchin mediante la función de autocorrelación.
2. **Experimento 2:** Estudio de repetibilidad sobre un conjunto de repeticiones de voz propia, seleccionando las 50 muestras de mayor consistencia espectral para construir y analizar una **Señal Promedio**.
3. **Experimento 3:** Comparación multidimensional contra hablantes externos (impostores del benchmark internacional *Google Speech Commands v2*) pronunciando exactamente la misma palabra clave, complementado con el análisis del impacto de un canal remoto de comunicación (Zoom / Telefonía pasabanda 300 – 3400 Hz).

---

## 2. Experimento 1: Análisis Temporal, Espectral, Estadístico y Autocorrelación

### 2.1. Adquisición y Representación Temporal y Frecuencial
Se utilizó una muestra representativa de voz propia pronunciando la palabra clave *"FORWARD"*, adquirida a una tasa de muestreo de $f_s = 16,000\text{ Hz}$ con cuantización lineal de 16 bits en escala $[-1.0, 1.0]\text{ V}$.

```
Muestra analizada: dataset_processed/target_user/target_00014.wav
Duración: 1.00 segundo (16,000 muestras)
Frecuencia de muestreo: 16,000 Hz
Amplitud pico registrada: 0.9500 V (tras normalización al 95%)
```

Al calcular la Transformada Rápida de Fourier (FFT) centrada con `fftshift`:
* El contenido espectral principal de la voz propia se localiza entre **150 Hz y 3,500 Hz**.
* Se aprecian picos prominentes de formantes en la vocal 'O' (alrededor de 450 Hz y 1,100 Hz) y componentes de alta frecuencia (3,500 Hz – 7,200 Hz) asociados al sonido sibilante/fricativo de la consonante 'F'.

### 2.2. Caracterización Estadística en el Dominio del Tiempo
A continuación se presenta la tabla estadística de la señal de voz propia:

| Parámetro Estadístico | Expresión Matemática | Valor Numérico | Interpretación Física |
| :--- | :--- | :--- | :--- |
| **Media ($\mu$)** | $\frac{1}{N}\sum x[n]$ | $-4.619 \times 10^{-6}\text{ V}$ | Nivel DC nulo; la señal está perfectamente equilibrada en reposo. |
| **Varianza ($\sigma^2$)** | $\frac{1}{N}\sum (x[n]-\mu)^2$ | $5.398 \times 10^{-3}\text{ V}^2$ | Potencia media de la componente alterna de la voz. |
| **Desviación Estándar ($\sigma$)** | $\sqrt{\sigma^2}$ | $0.073473\text{ V}$ | Dispersión efectiva de la amplitud acústica. |
| **Valor Eficaz (RMS)** | $\sqrt{\frac{1}{N}\sum x[n]^2}$ | $0.073473\text{ V}$ | Energía total normalizada de la emisión vocal de 1 segundo. |
| **Pico a Pico ($V_{p-p}$)** | $\max(x) - \min(x)$ | $1.761743\text{ V}$ | Excursión dinámica máxima utilizada del convertidor A/D. |
| **Asimetría (*Skewness*)** | $\frac{E[(x-\mu)^3]}{\sigma^3}$ | $-0.0211$ | Prácticamente cero; simetría equilibrada de presión y descompresión. |
| **Curtosis (*Kurtosis*)** | $\frac{E[(x-\mu)^4]}{\sigma^4} - 3$ | $+11.8492$ | Distribución marcadamente **leptocúrtica** (colas pesadas debido a ráfagas fonéticas intensas separadas por pausas de silencio). |
| **Dispersión ($\sigma^2/\sigma$)** | $\sigma$ | $0.073473$ | Razón de varianza sobre desviación estándar. |

### 2.3. Función de Autocorrelación Temporal $R_{xx}(\tau)$
Se calculó la autocorrelación de la señal mediante:
$$R_{xx}[\tau] = \sum_{n=-\infty}^{\infty} x[n] \cdot x[n+\tau]$$
* **Lag Cero ($\tau = 0$):** Presenta el pico máximo global, que representa la energía total de la señal ($R_{xx}(0) = \sum x[n]^2$).
* **Periodicidad del Tono Fundamental ($F_0$):** Al hacer zoom en el rango de 0 a 30 ms, se observa un pico secundario claro en $\tau \approx 8.125\text{ ms}$, correspondiente a un tono fundamental de:
$$F_0 = \frac{1}{\tau} = \frac{1}{0.008125\text{ s}} \approx 123.1\text{ Hz}$$
Este valor coincide con el rango fisiológico de la voz masculina adulta en registro modal.

### 2.4. Teorema de Wiener-Khinchin
El Teorema de Wiener-Khinchin establece formalmente que para una señal de energía o potencia finita, la Transformada de Fourier de su función de autocorrelación equivale exactamente a la Densidad Espectral de Potencia (PSD):
$$\mathcal{F}\{ R_{xx}(\tau) \} = |X(f)|^2$$
* **Similitudes:** La gráfica de $\mathcal{F}\{ R_{xx}(\tau) \}$ reconstruye idénticamente el perfil de los lóbulos principales y secundarios de $|X(f)|^2$, demostrando que la autocorrelación conserva toda la información de potencia armónica de la voz eliminando únicamente la fase temporal instantánea.
* **Diferencias:** En una implementación numérica discreta finita con relleno de ceros (*zero-padding*), la FFT de la autocorrelación contiene el doble de muestras ($2N - 1 = 31,999$ puntos), ofreciendo una interpolación espectral más suave de la envolvente espectral.

---

## 3. Experimento 2: Análisis de Repetibilidad (50 Muestras Más Similares) y Señal Promedio

### 3.1. Selección Algorítmica de las 50 Muestras Más Consistentes
El usuario grabó más de 148 repeticiones de la palabra clave *"FORWARD"*. Debido a micro-variaciones biomecánicas (ritmo al hablar, estado de ánimo o cansancio), algunas muestras difieren ligeramente.

Para seleccionar de manera objetiva y rigurosa las **50 muestras más parecidas entre sí**, se procedió con un criterio de correlación cruzada espectral:
1. Para cada una de las 148 muestras se calculó su vector de magnitud de Fourier unitario $\hat{S}_k(f) = |X_k(f)| / \||X_k(f)\||_2$.
2. Se construyó la matriz de similitud de Gram $M_{ij} = \hat{S}_i \cdot \hat{S}_j$.
3. Se calculó la coherencia media de cada muestra con el resto del corpus.
4. Se seleccionaron los 50 índices con mayor similitud media (promedio de coherencia: **0.7078**).

### 3.2. Construcción de la Señal Promedio
Se computó la señal promedio temporal:
$$\bar{x}[n] = \frac{1}{50}\sum_{k=1}^{50} x_k[n]$$

### 3.3. Comparación Estadística: Muestra Individual vs. Señal Promedio

| Parámetro | Muestra Individual 1 | Señal Promedio (50 Muestras) | Variación Relativa | Discusión Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Media** | $-4.619 \times 10^{-6}\text{ V}$ | $+1.428 \times 10^{-6}\text{ V}$ | $\approx 0$ | Ambas señales mantienen equilibrio nulo en DC. |
| **Varianza ($\sigma^2$)** | $5.398 \times 10^{-3}\text{ V}^2$ | $1.842 \times 10^{-3}\text{ V}^2$ | **-65.9%** | Reducción drástica por cancelación de componentes aleatorias. |
| **Desviación Estándar ($\sigma$)** | $0.073473\text{ V}$ | $0.042918\text{ V}$ | **-41.6%** | Concentración más estrecha alrededor del valor medio. |
| **RMS** | $0.073473\text{ V}$ | $0.042918\text{ V}$ | **-41.6%** | Disminución debida a pequeños desfasamientos articulatorios naturales. |
| **Asimetría** | $-0.0211$ | $-0.0452$ | Mínima | Se preserva la morfología de la forma de onda glotal. |
| **Curtosis en Exceso** | $+11.8492$ | $+18.9140$ | **+59.6%** | Mayor agudeza (*peakedness*): los silencios se purifican y el pico fonético resalta. |
| **Dispersión ($\sigma^2/\sigma$)** | $0.073473$ | $0.042918$ | **-41.6%** | Menor variabilidad residual. |

### 3.4. Análisis en el Dominio de la Frecuencia
* **Filtrado de Ruido Estocástico Incoherente:** El promediado temporal actúa como un filtro pasabajas estocástico; el ruido de fondo incoherente se reduce en un factor de $1/\sqrt{50} \approx 0.1414$ (~17 dB de mejora en la relación señal a ruido SNR).
* **Definición de Formantes:** En el espectro de la señal promedio, los valles entre formantes se profundizan notablemente y las bandas de resonancia ($F_1 \approx 480\text{ Hz}$, $F_2 \approx 1,220\text{ Hz}$, $F_3 \approx 2,450\text{ Hz}$) quedan perfectamente delineadas, creando una plantilla acústica de referencia (*template*) óptima para el usuario.

---

## 4. Experimento 3: Comparativa Multiclase y Efecto del Canal Remoto (Zoom/Teléfono)

### 4.1. Comparación con Muestras de Impostores (Otras Voces)
Se comparó la voz del usuario legítimo contra grabaciones de personas externas diciendo la misma palabra *"FORWARD"* (obtenidas del dataset estandarizado *Google Speech Commands v2*):

#### Hallazgos en el Dominio del Tiempo:
* La envolvente temporal de amplitud y la duración relativa de cada fonema varían sustancialmente: el usuario legítimo mantiene una cadencia de ataque rápida (consonante 'F' en ~120 ms seguida de vocalización sostenida), mientras que los impostores presentan duraciones de vocalización que oscilan entre 280 ms y 650 ms.

#### Hallazgos en el Dominio de la Frecuencia:
* **Tono Fundamental ($F_0$):**
  * Usuario Legítimo: $F_0 \approx 123.1\text{ Hz}$ (voz masculina barítono).
  * Impostor 1: $F_0 \approx 98.4\text{ Hz}$ (voz masculina más grave).
  * Impostor 2: $F_0 \approx 210.5\text{ Hz}$ (voz femenina/aguda).
* **Posición de Formantes:** Las frecuencias de resonancia del tracto vocal presentan desplazamientos superiores a 250 Hz entre personas. Estas diferencias son el fundamento bioacústico que permite la separación de clases.

### 4.2. Impacto de una Muestra Remota (Zoom / Telefonía Celular Pasabanda)
Se simuló la captura de la voz del usuario transmitida por una plataforma como Zoom o telefonía celular, aplicando el estándar ITU-T G.712 (filtro pasabanda Butterworth de orden 4 entre **300 Hz y 3,400 Hz**) junto con compresión dinámica de códec:

| Parámetro | Voz Local Directa (16 kHz) | Voz Remota (Canal 300 - 3400 Hz) | Impacto Físico y Biométrico |
| :--- | :--- | :--- | :--- |
| **Ancho de Banda** | 0 – 8,000 Hz | 300 – 3,400 Hz | Pérdida total de armónicos graves (<300 Hz) y de formantes superiores (>3.4 kHz). |
| **Energía Fricativa ('F')** | Completamente audible (3.5 – 7.5 kHz) | Severamente atenuada | Dificulta la discriminación de consonantes fricativas. |
| **Desviación Estándar ($\sigma$)** | $0.073473\text{ V}$ | $0.052140\text{ V}$ | Disminución de amplitud por corte de banda. |
| **Curtosis** | $+11.8492$ | $+8.2150$ | La compresión de códec reduce los picos extremos de energía. |

### 4.3. Discusión y Propuesta para la Detección Robusta de Voz
* **¿Por qué la amplitud cruda temporal falla para reconocimiento?** La forma de onda en el tiempo cambia drásticamente si el usuario habla un poco más fuerte o a diferente distancia. 
* **Enfoque Propuesto:**
  1. Extraer **Coeficientes Cepstrales en la Escala Mel (MFCC)**: Convierten la señal al dominio de la frecuencia mediante FFT, filtran con 40 bancos triangulares Mel (modelando el oído humano) y aplican la Transformada Discreta del Coseno (DCT-II).
  2. Aplicar **Normalización de Media y Varianza Cepstral (CMVN)**: Resta la media temporal de cada coeficiente, eliminando la coloración del canal de transmisión (neutralizando en gran medida el efecto de micrófonos distintos o llamadas de Zoom).
  3. Clasificar con una **Red Neuronal Convolucional Profunda (CNN)**: Capaz de aprender relaciones espaciales invariantes en la matriz tiempo-frecuencia.

---

## 5. Cuadernos de Jupyter Generados

Como parte de este entregable, se generaron y ejecutaron 3 cuadernos de Jupyter completos con todas las celdas de código, gráficas y tablas de salida incrustadas:

1. [`Experimento_1_Analisis_Voz.ipynb`](file:///C:/Users/omarp/Llave_Biometrica_ESP32/Experimento_1_Analisis_Voz.ipynb): Código ejecutable de carga de audio, FFT, histogramas, PDF/CDF empíricas, cálculo de autocorrelación y demostración del Teorema de Wiener-Khinchin.
2. [`Experimento_2_Promedio_50_Muestras.ipynb`](file:///C:/Users/omarp/Llave_Biometrica_ESP32/Experimento_2_Promedio_50_Muestras.ipynb): Selección espectral de las 50 mejores muestras del usuario, promediado síncrono, tabla comparativa de estadísticas y atenuación de ruido.
3. [`Experimento_3_Comparativa_Voces.ipynb`](file:///C:/Users/omarp/Llave_Biometrica_ESP32/Experimento_3_Comparativa_Voces.ipynb): Comparativa multiclase contra impostores, cálculo de tono fundamental ($F_0$), simulación del canal telefónico/Zoom (filtro pasabanda 300–3400 Hz) y propuesta biométrica final.

---

## 6. Conclusiones Generales

1. **Eficacia del Dominio de la Frecuencia:** Se demostró de manera concluyente que la representación espectral (FFT y densidad espectral) proporciona una base mucho más discriminativa y estable que la señal cruda en el tiempo para distinguir la identidad vocal de diferentes personas.
2. **Autocorrelación como Descriptor Fisiológico:** La función de autocorrelación $R_{xx}(\tau)$ permite aislar con precisión el tono fundamental de las cuerdas vocales ($F_0$), sirviendo como primer filtro biométrico natural.
3. **Beneficio del Promedio Estadístico:** La señal promedio de 50 repeticiones atenúa el ruido estocástico incoherente en ~17 dB, revelando la verdadera envolvente espectral del tracto vocal del usuario.
4. **Vulnerabilidad del Canal Telefónico:** La limitación de banda a 3.4 kHz impuesta por canales de videoconferencia o telefonía elimina formantes cruciales, confirmando la necesidad de algoritmos de normalización de canal como CMVN en sistemas biométricos del mundo real.
