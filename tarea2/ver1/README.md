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

Cada ventana trae:
- **Selector de cuantización**: lineal vs. no lineal (ley A para voz, gamma para video)
- **Selector de codificación de fuente**: Huffman vs. Shannon-Fano
- **Selector de codificación de canal**: ninguno, VRC, LRC+VRC, Hamming(7,4)
- **Slider de probabilidad de error del canal (p)**
- Panel de texto con entropía, longitud promedio, eficiencia de la codificación de
  fuente, BER de canal (bruto) y BER post-corrección, clasificado contra rangos
  de referencia orientativos.

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
