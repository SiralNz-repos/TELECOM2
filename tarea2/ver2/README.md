[README (1).md](https://github.com/user-attachments/files/31960162/README.1.md)
# Sistema de comunicaciones: cuantización, codificación y control de errores

Estudio comparativo de cuantificadores lineales/no lineales, codificación de
fuente y codificación de canal, aplicado a voz (micrófono USB) y video
(webcam USB) en tiempo real sobre Raspberry Pi.

## Pipeline

```
Señal analógica → Cuantización (lineal | no lineal) → Codificación de fuente
(huffman | shannon_fano) → Codificación de canal (ninguno | vrc | lrc_vrc |
hamming) → Canal ruidoso BSC (prob. p) → Decodificación de canal (detecta /
corrige) → Decodificación de fuente → señal reconstruida
                                        ↓
                          BER de canal (bruto) y BER post-corrección
```

## Instalación

```bash
pip install sounddevice opencv-python numpy matplotlib
```

## Uso

Desde la carpeta `sistema_comunicaciones/`:

```bash
python3 voz_sistema_completo.py     # ventana emergente para voz
python3 video_sistema_completo.py   # ventana emergente para video
```

## Layout de la ventana

Cada ventana se organiza en una grilla de 4 filas × 2 columnas, con cada
elemento en su propia celda (nada se dibuja superpuesto, sin importar el
tamaño real de la ventana o de la pantalla donde se ejecute, ej. por VNC):

| Fila | Columna izquierda (gráficos)              | Columna derecha (selectores) |
|------|--------------------------------------------|-------------------------------|
| 1    | Señal/imágenes: entrada vs. recepción       | Cuantización                  |
| 2    | Entramado de bits (una franja por etapa)    | Fuente                        |
| 3    | Leyenda del entramado de bits               | Canal (FEC)                   |
| 4    | Texto de métricas (entropía, BER, etc.)     | Slider de ruido (p)           |

Cada ventana trae:
- **Selector de cuantización**: lineal vs. no lineal (ley A para voz, gamma para video)
- **Selector de codificación de fuente**: Huffman vs. Shannon-Fano
- **Selector de codificación de canal**: ninguno, VRC, LRC+VRC, Hamming(7,4)
- **Slider de probabilidad de error del canal (p)**
- **Panel de onda/imágenes**: señal (o frame) original vs. cuantizada sin canal
  vs. reconstruida tras pasar por todo el pipeline
- **Panel de entramado de bits**: una franja por etapa (cuantización, fuente,
  canal TX, canal RX, decodificación de canal, símbolos recuperados), con los
  bits que difieren de la etapa de referencia resaltados en rojo
- **Panel de métricas**: entropía, longitud promedio y eficiencia de la
  codificación de fuente, BER de canal (bruto) y BER post-corrección,
  clasificados contra rangos de referencia orientativos

## Estructura de archivos

- `quantization.py` — cuantización lineal, ley A (voz), gamma (video)
- `source_coding.py` — Huffman y Shannon-Fano + métricas de entropía/eficiencia
- `channel_coding.py` — VRC, LRC+VRC, Hamming(7,4)
- `channel.py` — canal binario simétrico (BSC) y cálculo de BER
- `voz_sistema_completo.py` — aplicación de voz (usa todos los módulos anteriores)
- `video_sistema_completo.py` — aplicación de video (usa todos los módulos anteriores)

## Notas importantes para tu análisis

- **Propagación de error en Huffman/Shannon-Fano**: son códigos de longitud
  variable sin protección. Un solo bit invertido en el flujo puede desincronizar
  el decodificador y corromper todos los símbolos siguientes. Por eso el "BER
  canal (bruto)" y el "BER post-corrección" pueden diferir mucho: la codificación
  de canal (FEC) es la que evita que ese único error se propague.
- **VRC** solo detecta (nunca corrige) errores de 1 bit por carácter.
- **LRC+VRC** puede corregir un único bit por bloque si exactamente una fila y
  una columna fallan; con más errores en el mismo bloque, solo detecta.
- **Hamming(7,4)** corrige 1 bit por palabra de 7 bits automáticamente (FEC);
  por eso deberías ver el BER post-corrección caer notablemente frente a VRC/LRC
  para el mismo p, hasta que p sea tan alto que se acumulen 2+ errores por palabra.
- Los rangos de BER en `channel.py` (`RANGOS_BER`) son orientativos — reemplázalos
  por los que use tu bibliografía de curso (ej. Sklar o Proakis) para respaldar
  la propuesta.
- El video se reduce a una resolución pequeña (`RESOLUCION` en
  `video_sistema_completo.py`) porque el pipeline completo en Python puro es
  pesado para tiempo real en una Pi; puedes subirla si tu Pi rinde bien, o
  bajarla más si se traba.
- El panel de bits solo muestra los primeros `VIS_BITS` (300 por defecto) de
  cada etapa, porque los bloques reales tienen miles de bits. El texto de
  métricas indica el tamaño real de cada etapa (cuantización/fuente/canal).

## Historial de cambios

- **v3** — Se reorganizó todo el layout como grilla de 4×2 (antes usaba texto
  flotante y ejes con posiciones absolutas superpuestas), para eliminar el
  encimado de la leyenda, el texto de métricas y la etiqueta del eje X que
  ocurría en pantallas/ventanas más chicas (ej. sobre VNC). Cada elemento
  (onda/imágenes, entramado de bits, leyenda, métricas, cada selector) ahora
  vive en su propia celda de grilla.
- **v2** — Se añadió el panel de "entramado de bits": una franja por etapa del
  pipeline con los errores resaltados en rojo, en ambos scripts (voz y video).
- **v1** — Sistema base: cuantización (lineal/ley A/gamma), codificación de
  fuente (Huffman/Shannon-Fano), codificación de canal (VRC/LRC+VRC/Hamming),
  canal BSC con cálculo de BER, para voz y video, con selectores en ventana
  emergente.
