# GUIA DE ESTUDIO MAESTRA: PROCESAMIENTO DIGITAL DE SEÑALES Y SISTEMAS LINEALES
## Enfoque Conceptual, Aplicado e Intuitivo orientado al Proyecto de Llave Biometrica con ESP32-S3

**Autor:** Omar Perez (Omar Payan) | Matricula: A01742658  
**Materia:** TE2046.101 - Procesamiento de Señales y Sistemas  
**Fuentes Integradas:** Sesiones de Clase S1 a S4, Actividades de Laboratorio W1 a W4 y Proyecto de Hardware Embebido TinyML  
**Objetivo de la Guia:** Dominar los conceptos fundamentales, la intuicion fisica y la interpretacion practica de las señales, transformadas y sistemas lineales **sin atascarse en la derivacion de integrales complejas**, conectando cada concepto teorico visto en clase directamente con lo que ocurre dentro del silicio del ESP32-S3 y el microfono INMP441.

---

## 1. Fundamentos de Señales y Clasificacion en el Mundo Real (Semana 1 / S1 & W1)

### 1.1. Que es realmente una señal y que informacion transporta?
En terminos fisicos, una señal es la representacion matematica de una variable que evoluciona en funcion del tiempo, del espacio o de otra variable independiente, y que transporta **informacion o energia**.
* En el mundo continuo, cuando hablas, tus cuerdas vocales perturban el aire comprimiendo y descomprimiendo moleculas: eso es una señal acustica continua $x(t)$ (presion sonora en pascales).
* Cuando esa onda choca contra la membrana del microfono MEMS **INMP441**, la capacitancia microscopica varia y se genera un voltaje analogico continuo.
* Para poder procesarla en un microprocesador digital como el **ESP32-S3**, esa onda continua debe convertirse en una secuencia numerica discreta $x[n]$ mediante dos pasos basicos: **muestreo temporal** (tomar fotos a intervalos regulares $T_s$) y **cuantizacion** (asignar a cada foto un numero entero de bits).

### 1.2. Señales Continuas vs. Discretas y Analogicas vs. Digitales
* **Continua en el tiempo $x(t)$:** Existe para absolutamente cualquier instante de tiempo real $t$.
* **Discreta en el tiempo $x[n]$:** Solo existe en instantes especificos enteros $n \cdot T_s$.
* **Analogica:** Su amplitud puede tomar infinitos valores continuos dentro de un rango de voltaje.
* **Digital:** Su amplitud esta forzada a un conjunto discreto de niveles representables en binario.
> **Aplicacion en tu proyecto ESP32:**  
> Tu microfono INMP441 toma la presion continua del aire, la convierte en voltaje analogico internamente, y su convertidor Sigma-Delta integrado la digitaliza a $16,000\text{ Hz}$ (16 kHz) con palabras de 16 bits. Cada segundo, tu ESP32 recibe un arreglo plano de 16,000 numeros enteros con signo entre $-32,768$ y $+32,767$.

### 1.3. Clasificacion Esencial de Señales (Para que sirve saberla?)

#### A. Señales Periodicas vs. Aperiódicas
* **Periodica:** Se repite exactamente a si misma cada periodo fijo $T_0$ de manera infinita: $x(t) = x(t + T_0)$. Ejemplos: senoidales puras, ondas cuadradas de reloj de hardware (el BCLK de I2S).
* **Aperiódica:** No se repite de forma identica nunca. Ejemplo: el habla humana o la palabra clave *"FORWARD"*.
> **Por que importa para tu examen y tu proyecto?**  
> Porque la herramienta matematica cambia radicalmente: para señales periodicas se usa la **Serie de Fourier** (espectro de lineas discretas), mientras que para señales aperiodicas como la voz humana se usa la **Transformada de Fourier** (espectro continuo).

#### B. Señales de Energia vs. Señales de Potencia
* **Señal de Energia ($0 < E < \infty$):** Son señales finitas en el tiempo o que decaen a cero cuando $t \to \infty$. Su potencia promedio es cero.
* **Señal de Potencia ($0 < P < \infty$):** Son señales infinitas que continuan oscilando eternamente (como una senoidal continua o el ruido de fondo estacionario). Tienen energia infinita pero una potencia media finita.
> **En tu proyecto:** Un comando de voz como *"FORWARD"* que dura 1 segundo es una **señal de energia finita**. El zumbido constante de un ventilador de oficina o el ruido termico ambiental es un proceso que se modela como una **señal de potencia**.

#### C. Señales Deterministas vs. Aleatorias (Estocasticas)
* **Determinista:** Se puede predecir su valor exacto en cualquier instante mediante una formula matematica cerrada ($x(t) = A \cos(\omega t + \phi)$).
* **Aleatoria / Estocastica:** Su valor futuro es incierto; solo se puede describir mediante estadistica y probabilidades (media, varianza, distribucion Gaussiana).
> **En tu proyecto:** Tu voz es un fenomeno cuasi-estocastico. Aunque al pronunciar *"FORWARD"* las cuerdas vocales producen pulsos periodicos, el aire turbulento y las variaciones vocales hacen que cada grabacion sea ligeramente distinta. Por eso no comparas punto a punto la onda en el tiempo, sino que usas una red neuronal entrenada probabilisticamente.

### 1.4. Señales Elementales de Prueba (El lenguaje del ingeniero)
1. **Escalon Unitario $u(t)$:** Vale 0 para $t < 0$ y 1 para $t \ge 0$. Modela el encendido brusco de un circuito o la activacion repentina de un microfono.
2. **Impulso Unitario de Dirac $\delta(t)$:** Un pulso infinitamente estrecho, infinitamente alto, pero con area igual a 1 en $t=0$. Es la herramienta teorica mas poderosa del analisis de sistemas: representa un golpe energetico instantaneo que excita todas las frecuencias imaginables al mismo tiempo.
3. **Senoidales y Exponenciales Complejas ($e^{j\omega_0 t} = \cos(\omega_0 t) + j\sin(\omega_0 t)$):** Son las "funciones propias" de los sistemas lineales. Si metes una senoidal a un sistema lineal, la salida siempre sera otra senoidal de la misma frecuencia, solo alterada en amplitud y fase.

---

## 2. Analisis en Frecuencia de Señales Periodicas: Serie de Fourier (Semana 2 / S2 & W2)

### 2.1. La gran intuicion: Que significa descomponer una señal en frecuencias?
Imagina una orquesta tocando un acorde: tu oido recibe una unica onda de presion en el aire, pero tu cerebro es capaz de distinguir la nota grave del contrabajo, la nota media del piano y el agudo del violin. 

Jean-Baptiste Joseph Fourier demostro que **cualquier señal periodica puede reconstruirse exactamente sumando ondas senoidales puras (armonicos)** a frecuencias que son multiplos enteros de una frecuencia fundamental comun $\omega_0 = 2\pi / T_0$.

### 2.2. Las tres formas de la Serie de Fourier (Sin enredarse)
1. **Forma Trigonometrica:** Expresa la señal usando senos y cosenos:
   $$x(t) = a_0 + \sum [a_n \cos(n\omega_0 t) + b_n \sin(n\omega_0 t)]$$
   * $a_0$: Es el promedio o nivel DC de la señal.
   * $a_n$: Que tanto se parece la señal a un coseno a la frecuencia $n\omega_0$.
   * $b_n$: Que tanto se parece a un seno a esa misma frecuencia.
2. **Forma Compacta (Magnitud y Fase):**
   $$x(t) = C_0 + \sum C_n \cos(n\omega_0 t + \theta_n)$$
   En lugar de dos terminos seno y coseno separados, combina ambos en una sola onda con su **amplitud maxima $C_n$** y su **retraso o desfase angular $\theta_n$**.
3. **Forma Exponencial Compleja:**
   $$x(t) = \sum_{n=-\infty}^{\infty} D_n e^{j n \omega_0 t}$$
   Es la mas usada en ingenieria moderna y software porque agrupa la magnitud y la fase en un solo numero complejo $D_n$.

### 2.3. Efecto de la Simetria: Ahorro de calculos en la practica
Cuando una señal tiene simetria, ciertos coeficientes se anulan automaticamente:
* **Simetria Par ($x(-t) = x(t)$):** Como un coseno. Los componentes seno no existen ($b_n = 0$). Solo hay cosenos.
* **Simetria Impar ($x(-t) = -x(t)$):** Como un seno. Pasa por el origen. El promedio es cero ($a_0 = 0$) y no hay cosenos ($a_n = 0$). Solo hay senos.
* **Simetria de Media Onda ($x(t \pm T/2) = -x(t)$):** Solo contiene **armonicos impares** ($n = 1, 3, 5, \dots$). Los armonicos pares se cancelan.

### 2.4. El Fenomeno de Gibbs (Por que las esquinas hacen olas?)
Cuando intentas aproximar una onda con saltos verticales abruptos (como una onda cuadrada) sumando un numero finito de senoides, ocurre algo fascinante: en los puntos de discontinuidad siempre aparece un sobreimpulso o "pico" del **9%** que nunca desaparece, sin importar cuantos millones de armonicos sumes. Solo se comprime en el tiempo.
> **Como aplica a tu proyecto ESP32?**  
> Cuando tomas 30 milisegundos de voz en tu ESP32 para procesarlos, si cortas la trama como un rectangulo con bordes abruptos, ese salto vertical actua exactamente como una discontinuidad de Gibbs, inyectando ruido de alta frecuencia que falsea la biometria. Para evitarlo, en tu codigo multiplicas la trama por una **Ventana Hamming**, que lleva suavemente los bordes a cero y mata de raiz el efecto Gibbs (antifuga espectral).

### 2.5. Teorema de Parseval para Señales Periodicas
Dice que **la potencia total de una señal es la misma si la mides en el tiempo o si sumas las potencias de cada uno de sus armonicos en la frecuencia**:
$$P_{total} = \frac{1}{T}\int |x(t)|^2 dt = \sum |D_n|^2$$
La energia no se crea ni se destruye; el dominio de la frecuencia solo te muestra como esta repartida la potencia entre las diferentes notas musicales o armonicos.

---

## 3. Analisis en Frecuencia de Señales Aperiódicas: Transformada de Fourier (Semana 3 / S3 & W3)

### 3.1. Como pasamos de la Serie a la Transformada de Fourier?
Piensa en una señal que no se repite nunca, como el fonema 'F' al decir *"FORWARD"*.
Matematicamente, puedes imaginar que es una señal periodica cuyo periodo de repeticion es **infinitamente largo** ($T_0 \to \infty$).
Al hacer que el periodo tienda a infinito:
* La separacion entre armonicos ($\Delta\omega = \omega_0 = 2\pi/T_0$) se hace infinitesimalmente pequeña ($d\omega \to 0$).
* Las lineas discretas del espectro se van juntando tanto que se fusionan en una **curva continua**: la **Transformada de Fourier $X(\omega)$**.

### 3.2. Que nos dice fisicamente la Transformada de Fourier $X(\omega)$?
Nos dice la densidad de amplitud y la fase con la que cada frecuencia infinitesimal $\omega$ contribuye a construir la señal $x(t)$.
* Como $X(\omega)$ es un numero complejo para cada frecuencia:
  * **Espectro de Magnitud $|X(\omega)|$:** Nos dice **cuanta energia o presencia** tiene cada tono (graves, medios, agudos).
  * **Espectro de Fase $\angle X(\omega)$:** Nos dice **a que hora llega o como esta desfasada** cada frecuencia respecto al tiempo cero.

### 3.3. Propiedades Fundamentales de la Transformada y su Utilidad Practica

| Propiedad | Que hace en el tiempo? | Que le pasa al espectro en frecuencia? | Aplicacion en tu ESP32 / Audio |
| :--- | :--- | :--- | :--- |
| **Linealidad** | Si sumas dos señales $a x_1(t) + b x_2(t)$ | Sus espectros simplemente se suman $a X_1(\omega) + b X_2(\omega)$ | Permite separar la voz del usuario del ruido aditivo del ventilador sumando/restando espectros. |
| **Escalamiento Temporal** | Comprimir la señal en el tiempo $x(at)$ con $a > 1$ (hablar rapido) | El espectro se ensancha en frecuencia $\frac{1}{\|a\|}X(\frac{\omega}{a})$ | Si hablas mas rapido, tus formantes abarcan un espectro mas ancho. Hay una relacion inversa: mas estrecho en tiempo = mas ancho en frecuencia. |
| **Desplazamiento Temporal** | Retrasar la señal un tiempo $t_0$: $x(t - t_0)$ | La magnitud **NO cambia**: $\|X(\omega)\| e^{-j\omega t_0}$ | Si dices *"FORWARD"* 100 ms mas tarde, la huella biometrica de magnitud es identica; solo cambia la fase lineal. |
| **Modulacion (Desplazamiento en Frecuencia)** | Multiplicar por un coseno $\cos(\omega_c t)$ en el tiempo | El espectro se traslada a la frecuencia portadora $\pm \omega_c$ | Es la base de la radio AM/FM y de las actividades que hiciste en MATLAB al modular con portadora de 2500 Hz. |
| **Diferenciacion en el Tiempo** | Derivar la señal $\frac{d}{dt}x(t)$ | Multiplica el espectro por $j\omega$ (realce de agudos) | Derivar en el tiempo equivale a un filtro pasa-altas. Es el fundamento teorico exacto del **filtro de pre-enfasis** de tu proyecto. |
| **Convolucion en el Tiempo** | Pasar una señal por un filtro $x(t) * h(t)$ | **Se multiplican directamente sus espectros:** $X(\omega) \cdot H(\omega)$ | Es el descubrimiento mas importante de la ingenieria de señales: en lugar de resolver integrales de convolucion imposibles, multiplicas en frecuencia y listo. |

### 3.4. Relacion de Parseval para Señales de Energia
$$\int_{-\infty}^{\infty} |x(t)|^2 dt = \frac{1}{2\pi}\int_{-\infty}^{\infty} |X(\omega)|^2 d\omega$$
Nos dice que la energia total calculada integrando el voltaje al cuadrado en el tiempo es exactamente igual al area bajo la curva de la **Densidad Espectral de Energia** $|X(\omega)|^2$.

---

## 4. Analisis en el Dominio del Tiempo y Convolucion de Sistemas LTI (Semana 4 / S4 & W4)

### 4.1. Que es un Sistema Lineal e Invariante en el Tiempo (LTI)?
Un sistema es cualquier proceso fisico que toma una señal de entrada $x(t)$ y produce una señal de salida $y(t)$:
* **Linealidad (Superposicion):** Si la entrada $x_1$ produce $y_1$ y la entrada $x_2$ produce $y_2$, entonces meter $a x_1 + b x_2$ produce exactamente $a y_1 + b y_2$. No hay distorsion no lineal.
* **Invarianza en el tiempo:** Las propiedades fisicas del sistema no cambian con el reloj. Si le metes la misma entrada hoy o mañana, la respuesta sera exactamente la misma, solo retrasada.
> **En tu proyecto:** La habitacion donde grabas, el canal acustico del microfono y los filtros digitales del ESP32 se comportan como sistemas LTI durante la ventana de analisis de 1 segundo.

### 4.2. La Respuesta al Impulso $h(t)$: El ADN de un Sistema
Si a una habitacion o a un circuito le aplicas un impulso perfecto $\delta(t)$ (como disparar una pistola de salva o dar un aplauso seco en un cuarto vacio), el eco o la respuesta que emite el sistema es $h(t)$ (**la respuesta al impulso**).
* **El secreto de los sistemas lineales:** Si conoces $h(t)$, **conoces absolutamente todo sobre el sistema**. Puedes predecir como reaccionara ante cualquier señal arbitraria del universo mediante la operacion de **Convolucion**.

### 4.3. Que significa fisicamente la Convolucion? ($x(t) * h(t)$)
Cualquier señal continua $x(t)$ puede verse como una fila infinita de pequeños impulsos pegados uno tras otro. 
Cada uno de esos impulsos excita al sistema produciendo una pequeña respuesta al impulso escalada y retrasada. 
La salida final $y(t)$ es simplemente la suma (integral) de todas esas respuestas superpuestas:
$$y(t) = \int_{-\infty}^{\infty} x(\tau) h(t - \tau) d\tau$$

#### Los 4 pasos mecanicos de la convolucion grafica:
1. **Cambio de variable:** Escribes las señales en funcion de $\tau$: $x(\tau)$ y $h(\tau)$.
2. **Reflexion (Inversion temporal):** Reflejas la respuesta al impulso para obtener $h(-\tau)$.
3. **Desplazamiento:** Mueves la señal reflejada en el tiempo segun el parametro $t$: $h(t - \tau)$.
4. **Multiplicacion e Integracion:** Multiplicas las dos curvas donde se traslapan y calculas el area bajo la curva para cada instante $t$.

### 4.4. Respuesta Total de un Sistema: Entrada Cero vs. Estado Cero
Cualquier sistema dinamico (como un circuito RLC o un filtro analogico) tiene dos fuentes de energia:
1. **Respuesta a Entrada Cero (Zero-Input Response, $y_{zi}(t)$):** Es lo que hace el sistema impulsado unicamente por la energia que ya tenia almacenada en sus capacitores o inductores antes de que empiece el experimento ($x(t) = 0$).
2. **Respuesta a Estado Cero (Zero-State Response, $y_{zs}(t)$):** Es lo que hace el sistema asumiendo que arranco completamente descargado (condiciones iniciales cero) impulsado unicamente por la señal externa $x(t)$.
$$\text{Respuesta Total } y(t) = y_{zi}(t) + y_{zs}(t)$$
La integral de convolucion $x(t) * h(t)$ calcula exclusivamente la **Respuesta a Estado Cero ($y_{zs}(t)$)**.

---

## 5. Como se Conecta Toda Esta Teoria con tu Proyecto de Llave Biometrica en ESP32

En la siguiente matriz veras exactamente como cada tema visto en las diapositivas de clase corresponde a una linea de codigo o decision de hardware en tu proyecto:

| Concepto de Clase (S1 - S4) | Pregunta Teorica del Examen | Implementacion Real en tu ESP32-S3 | Funcion Practica / Beneficio |
| :--- | :--- | :--- | :--- |
| **Muestreo y Cuantizacion (S1)** | Teorema de Nyquist: $f_s \ge 2 f_{max}$ | Lectura I2S por DMA a $16,000\text{ Hz}$ y 16 bits en `audio_buffer[16000]`. | Captura hasta 8,000 Hz, cubriendo los formantes de voz humana sin saturar los 320 KB de SRAM. |
| **Diferenciacion en Tiempo (S3)** | Derivar una señal multiplica su espectro por $j\omega$ (filtro pasa-altas). | Filtro FIR de pre-enfasis: $y[n] = x[n] - 0.97 x[n-1]$. | Compensa la caida natural glotal de 6 dB/octava, amplificando las altas frecuencias (2 a 7.6 kHz) donde reside la identidad de la voz. |
| **Ventaneo y Fenomeno de Gibbs (S2)** | Discontinuidades abruptas causan fugas espectrales (*spectral leakage*). | Enmarcado temporal en tramas de 30 ms con **Ventana Hamming** de 480 puntos. | Suaviza los extremos a cero, eliminando armonicos falsos antes de calcular la FFT. |
| **De Serie a Transformada de Fourier (S2 & S3)** | Descomposicion de señales no periodicas en densidades de frecuencia. | Algoritmo **FFT Radix-2 Cooley-Tukey** de 512 puntos en $O(N \log N)$. | Calcula el espectro de cada trama en **0.15 ms** en lugar de los 8 ms que tardaria la DFT directa, evitando que salte el Watchdog. |
| **Espectro de Magnitud vs. Fase (S3)** | La fase depende del retardo temporal; la magnitud es la energia intrinseca. | Descarte de la fase espectral $\angle X(\omega)$ y conservacion exclusiva de la magnitud de potencia $\|X(\omega)\|^2$. | Otorga **invarianza espacial**: el sistema te reconoce hables a 15 cm o a 25 cm del microfono. |
| **Convolucion y Teorema de Parseval (S3 & S4)** | Un filtro convoluciona en el tiempo y multiplica en frecuencia. La energia se conserva. | Banco de 40 Filtros Mel triangulares y Normalizacion CMVN temporal. | Integra la energia acustica imitando la coclea humana y cancela la funcion de transferencia acustica de la habitacion (eco/reverberacion). |
| **Teorema de Wiener-Khinchin (Lab W1-W4)** | $\mathcal{F}\{R_{xx}(\tau)\} = \|X(f)\|^2$. La autocorrelacion mide periodicidad. | Extraccion del tono fundamental ($F_0$) y diseño del clasificador convolucional. | Permite diferenciar la frecuencia de vibracion glotal modal ($F_0 \approx 123\text{ Hz}$ tuya vs $98\text{ Hz}$ o $210\text{ Hz}$ de impostores). |

---

## 6. Banco de Preguntas y Respuestas Conceptuales para Preparar tu Evaluacion

A continuacion tienes las preguntas conceptuales mas comunes que un profesor de procesamiento de señales y sistemas suele hacer en examenes orales o escritos, respondidas con claridad y orientadas a tu aplicacion:

#### P1: Por que en ingenieria de audio se prefiere trabajar en el dominio de la frecuencia en lugar de quedarse en el dominio del tiempo?
**Respuesta:** En el dominio del tiempo la señal es una curva compleja que sube y baja rapidamente; dos personas diciendo la misma palabra tienen formas de onda completamente distintas y desfasadas, haciendo imposible compararlas directamente punto a punto. En el dominio de la frecuencia, la Transformada de Fourier descompone la señal en sus notas constitutivas, revelando las frecuencias de resonancia del tracto vocal (**formantes**), que son caracteristicas fisicas e invariantes de la persona.

#### P2: Cual es la diferencia conceptual entre la Serie de Fourier y la Transformada de Fourier?
**Respuesta:** La Serie de Fourier se aplica exclusivamente a señales **periodicas** (que se repiten infinitamente) y produce un espectro de lineas discretas en frecuencias armonicas ($n\omega_0$). La Transformada de Fourier se aplica a señales **aperiódicas** (como un comando de voz unico de 1 segundo) y produce un espectro continuo en todas las frecuencias.

#### P3: Que relacion fisica existe entre la respuesta al impulso $h(t)$ y la convolucion?
**Respuesta:** La respuesta al impulso $h(t)$ es la firma dinamica completa de un sistema LTI. Dado que cualquier señal de entrada puede descomponerse en una sucesion continua de impulsos de Dirac escalados, la salida del sistema es la superposicion continua de las respuestas a esos impulsos, lo cual se calcula matematicamente mediante la integral de convolucion.

#### P4: Por que es necesario aplicar una ventana como Hamming antes de hacer la FFT en tramas de voz?
**Respuesta:** La FFT asume implicitamente que la trama de 30 milisegundos se repite periodicamente de forma infinita. Si la cortamos como un bloque rectangular, el inicio y el final de la trama tendran voltajes distintos, generando una discontinuidad brusca (efecto Gibbs). Esa discontinuidad genera frecuencias falsas en todo el espectro (*spectral leakage*). La ventana Hamming atenua suavemente los bordes a cero, asegurando que solo aparezcan las frecuencias reales de la voz.

#### P5: Que establece el Teorema de Parseval y que utilidad tiene?
**Respuesta:** Establece el principio de conservacion de la energia: la energia total de una señal medida en el tiempo (integral de la señal al cuadrado) es exactamente igual a la suma de la energia distribuida en todas sus componentes de frecuencia. Es util porque permite medir la potencia de una señal directamente desde su espectro de Fourier o diseñar filtros para atenuar bandas de ruido sin alterar la energia de la banda util.

#### P6: Por que un filtro de pre-enfasis como $y[n] = x[n] - 0.97 x[n-1]$ amplifica las altas frecuencias?
**Respuesta:** Porque en una señal discreta, restar a la muestra actual la muestra previa equivale a una derivada numerica aproximada ($\Delta x / \Delta t$). En la teoria de Fourier, derivar en el tiempo equivale a multiplicar por la frecuencia ($\mathcal{F}\{d/dt\} = j\omega$). Por tanto, a bajas frecuencias ($\omega \approx 0$) la ganancia es casi nula, mientras que a altas frecuencias la ganancia crece linealmente, compensando la caida natural de la voz humana.

#### P7: Que ventaja tiene utilizar la FFT frente a la definicion formal de la DFT?
**Respuesta:** La definicion formal de la DFT requiere $N^2$ multiplicaciones complejas. Para 512 puntos son mas de 262,000 operaciones por trama. El algoritmo FFT Radix-2 de Cooley-Tukey explota la simetria y periodicidad de los factores de giro exponenciales, reduciendo la complejidad a $O(N \log_2 N)$, es decir, apenas 4,608 operaciones (~50 veces menos computo). Esto es lo que permite que el ESP32-S3 procese la señal en 0.15 ms sin bloquear la CPU ni colgar la conexion USB.
