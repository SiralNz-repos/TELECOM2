"""
Sistema completo de comunicaciones para voz, en una ventana emergente:

  mic USB -> cuantización (lineal | ley A)
          -> codificación de fuente (huffman | shannon_fano)
          -> codificación de canal (ninguno | vrc | lrc_vrc | hamming)
          -> canal BSC (ruido ajustable con slider)
          -> decodificación de canal -> decodificación de fuente -> reconstrucción
          -> BER de canal y BER post-corrección

Paneles:
  1. Onda: señal original vs. cuantizada (sin canal) vs. reconstruida (tras canal)
  2. Entramado de bits: una fila por etapa del pipeline (cuantización, fuente,
     canal TX, canal RX, decodificación de canal, símbolos recuperados),
     con los bits que cambiaron respecto a la etapa de referencia resaltados
     en rojo. Solo se muestran los primeros VIS_BITS bits de cada bloque.

Dependencias:
    pip install sounddevice numpy matplotlib

Uso:
    python3 voz_sistema_completo.py
    (ejecutar desde la carpeta sistema_comunicaciones/, o con ésta en PYTHONPATH)
"""

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import RadioButtons, Slider
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

import quantization as q
import source_coding as sc
import channel_coding as cc
import channel as ch

# ---- Parámetros ---------------------------------------------------------
SAMPLE_RATE = 8000       # Hz (estándar de telefonía / ley A)
BLOCK_SIZE = 256         # muestras por bloque procesado
BITS = 8                 # resolución de cuantización
DEVICE = None            # índice del micrófono USB; None = default del sistema
REFRESH_MS = 200         # cada cuánto se reprocesa y redibuja
VIS_BITS = 300           # cuántos bits de cada etapa se muestran en el panel de bits
# --------------------------------------------------------------------------

estado = {
    "cuantizacion": "a_law",       # "lineal" | "a_law"
    "fuente": "huffman",           # "huffman" | "shannon_fano"
    "canal_cod": "hamming",        # "ninguno" | "vrc" | "lrc_vrc" | "hamming"
    "p": 0.01,                     # probabilidad de error del BSC
}

buffer_audio = np.zeros(BLOCK_SIZE, dtype=np.float32)
resultados = {}

# 0 = bit 0, 1 = bit 1, 2 = bit erróneo (respecto a la etapa de referencia), 3 = relleno
BIT_CMAP = ListedColormap(["white", "black", "#e03030", "#dddddd"])
ETIQUETAS_FILAS = [
    "1. Símbolos cuantizados",
    "2. Tras codificación de fuente",
    "3. Tras codificación de canal (TX)",
    "4. Recibido (canal ruidoso)",
    "5. Tras decodificación de canal",
    "6. Símbolos recuperados",
]


def audio_callback(indata, frames, time_info, status):
    global buffer_audio
    if status:
        print(status)
    buffer_audio = indata[:, 0].copy()


def idx_to_bits(idx, bits=BITS):
    out = []
    for v in idx:
        out.extend(int(b) for b in format(int(v), f"0{bits}b"))
    return out


def fila_bits(bits, ref=None, n=VIS_BITS):
    """Recorta/rellena `bits` a longitud n. Si se da `ref`, marca en rojo (valor 2)
    las posiciones donde `bits` difiere de `ref` (comparando solo bits reales, no relleno)."""
    bits = list(bits[:n])
    if len(bits) < n:
        bits = bits + [3] * (n - len(bits))

    if ref is not None:
        ref = list(ref[:n])
        if len(ref) < n:
            ref = ref + [3] * (n - len(ref))
        bits = [
            2 if (b in (0, 1) and r in (0, 1) and b != r) else b
            for b, r in zip(bits, ref)
        ]

    return np.array(bits, dtype=float)


def procesar_bloque(x):
    """Corre el pipeline completo sobre un bloque de audio y llena `resultados`."""
    # 1. Cuantización
    if estado["cuantizacion"] == "lineal":
        xq_ref, idx = q.linear_quantize(x, bits=BITS)
    else:
        xq_ref, idx = q.a_law_quantize(x, bits=BITS)

    simbolos = idx.tolist()
    databits = idx_to_bits(simbolos)

    # 2. Codificación de fuente
    codes = sc.build_codes(simbolos, metodo=estado["fuente"])
    bitstring = sc.encode(simbolos, codes)
    metr = sc.metrics(simbolos, codes)
    fuente_bits = [int(b) for b in bitstring]

    # 3. Codificación de canal
    codebits = cc.encode_canal(fuente_bits, metodo=estado["canal_cod"])

    # 4. Canal ruidoso (BSC)
    rxbits, _ = ch.canal_bsc(codebits, estado["p"])
    ber_canal, _, _ = ch.calcular_ber(codebits, rxbits)

    # 5. Decodificación de canal
    decoded_fuente_bits, detectados, corregidos = cc.decode_canal(rxbits, metodo=estado["canal_cod"])
    ber_post, _, _ = ch.calcular_ber(fuente_bits, decoded_fuente_bits)

    # 6. Decodificación de fuente y reconstrucción
    bitstring_rx = "".join(str(b) for b in decoded_fuente_bits)
    simbolos_rx = sc.decode(bitstring_rx, codes)
    if len(simbolos_rx) < len(simbolos):
        simbolos_rx = simbolos_rx + simbolos[len(simbolos_rx):]  # relleno si el flujo se desincronizó
    simbolos_rx = np.array(simbolos_rx[:len(simbolos)])
    simbolos_rx_bits = idx_to_bits(simbolos_rx.tolist())

    if estado["cuantizacion"] == "lineal":
        step = 2.0 / (2 ** BITS)
        xq_rx = simbolos_rx * step - 1.0
    else:
        step = 2.0 / (2 ** BITS)
        y_rx = simbolos_rx * step - 1.0
        xq_rx = q.a_law_decode(y_rx)

    matriz_bits = np.vstack([
        fila_bits(databits),
        fila_bits(fuente_bits),
        fila_bits(codebits),
        fila_bits(rxbits, ref=codebits),
        fila_bits(decoded_fuente_bits, ref=fuente_bits),
        fila_bits(simbolos_rx_bits, ref=databits),
    ])

    resultados.update({
        "x": x, "xq_ref": xq_ref, "xq_rx": xq_rx,
        "ber_canal": ber_canal, "ber_post": ber_post,
        "metricas_fuente": metr,
        "detectados": detectados, "corregidos": corregidos,
        "matriz_bits": matriz_bits,
        "n_databits": len(databits), "n_fuente": len(fuente_bits),
        "n_canal": len(codebits),
    })


def main():
    fig = plt.figure(figsize=(14, 9))
    fig.canvas.manager.set_window_title("Sistema de comunicaciones de voz")

    # Columna izquierda (gráficos) vs. columna derecha (selectores), como filas
    # independientes de grilla -- así nada se dibuja encima de otra cosa sin
    # importar el tamaño real de la ventana.
    gs = fig.add_gridspec(
        4, 2,
        width_ratios=[3.0, 1.0],
        height_ratios=[2.2, 3.0, 0.5, 0.9],
        left=0.10, right=0.97, top=0.95, bottom=0.05,
        hspace=0.55, wspace=0.10,
    )

    # ---- Panel 1: onda -------------------------------------------------
    ax_wave = fig.add_subplot(gs[0, 0])
    t = np.arange(BLOCK_SIZE) / SAMPLE_RATE
    line_x, = ax_wave.plot(t, np.zeros(BLOCK_SIZE), color="#4da6ff", lw=1.3, label="Original")
    line_ref, = ax_wave.plot(t, np.zeros(BLOCK_SIZE), color="#888", lw=1.0, ls="--", label="Cuantizada (sin canal)")
    line_rx, = ax_wave.plot(t, np.zeros(BLOCK_SIZE), color="#ff9d4d", lw=1.3, label="Reconstruida (tras canal)")
    ax_wave.set_ylim(-1.05, 1.05)
    ax_wave.set_xlabel("tiempo (s)")
    ax_wave.set_ylabel("amplitud")
    ax_wave.set_title("Señal: entrada vs. recepción")
    ax_wave.legend(loc="upper right", fontsize=8)
    ax_wave.grid(alpha=0.2)

    # ---- Panel 2: entramado de bits ------------------------------------
    ax_bits = fig.add_subplot(gs[1, 0])
    matriz_inicial = np.full((6, VIS_BITS), 3.0)
    im_bits = ax_bits.imshow(matriz_inicial, aspect="auto", cmap=BIT_CMAP, vmin=0, vmax=3, interpolation="nearest")
    ax_bits.set_yticks(range(6))
    ax_bits.set_yticklabels(ETIQUETAS_FILAS, fontsize=7.5)
    ax_bits.set_xlabel(f"posición de bit (primeros {VIS_BITS} de cada bloque)", fontsize=8)
    ax_bits.set_title("Entramado de bits: cómo cambia el flujo en cada etapa", fontsize=10)

    # ---- Fila dedicada solo para la leyenda del entramado ----------------
    ax_leyenda = fig.add_subplot(gs[2, 0])
    ax_leyenda.axis("off")
    leyenda = [
        Patch(facecolor="white", edgecolor="gray", label="bit 0"),
        Patch(facecolor="black", label="bit 1"),
        Patch(facecolor="#e03030", label="bit erróneo"),
        Patch(facecolor="#dddddd", label="relleno (bloque más corto)"),
    ]
    ax_leyenda.legend(handles=leyenda, loc="center", ncol=4, fontsize=8, frameon=False)

    # ---- Fila dedicada solo para el texto de métricas ---------------------
    ax_info = fig.add_subplot(gs[3, 0])
    ax_info.axis("off")
    info = ax_info.text(0.0, 1.0, "", fontsize=8.5, va="top", ha="left", transform=ax_info.transAxes)

    # ---- Columna derecha: selectores, una fila de grilla cada uno --------
    ax_q = fig.add_subplot(gs[0, 1])
    r_q = RadioButtons(ax_q, ["a_law", "lineal"])
    ax_q.set_title("Cuantización", fontsize=9)

    ax_f = fig.add_subplot(gs[1, 1])
    r_f = RadioButtons(ax_f, ["huffman", "shannon_fano"])
    ax_f.set_title("Fuente", fontsize=9)

    ax_c = fig.add_subplot(gs[2, 1])
    r_c = RadioButtons(ax_c, ["hamming", "lrc_vrc", "vrc", "ninguno"])
    ax_c.set_title("Canal (FEC)", fontsize=9)

    ax_p = fig.add_subplot(gs[3, 1])
    s_p = Slider(ax_p, "p", 0.0, 0.2, valinit=estado["p"])
    ax_p.set_title("Ruido (p)", fontsize=9)

    r_q.on_clicked(lambda label: estado.update(cuantizacion=label))
    r_f.on_clicked(lambda label: estado.update(fuente=label))
    r_c.on_clicked(lambda label: estado.update(canal_cod=label))
    s_p.on_changed(lambda val: estado.update(p=val))

    def update(_frame):
        x = buffer_audio.copy()
        procesar_bloque(x)

        line_x.set_ydata(resultados["x"])
        line_ref.set_ydata(resultados["xq_ref"])
        line_rx.set_ydata(resultados["xq_rx"])

        im_bits.set_data(resultados["matriz_bits"])

        m = resultados["metricas_fuente"]
        info.set_text(
            f"Fuente:  H = {m.get('entropia',0):.2f} bits/símbolo   "
            f"L = {m.get('longitud_promedio',0):.2f} bits/símbolo   "
            f"eficiencia = {m.get('eficiencia',0)*100:.1f}%   "
            f"(tamaños: cuant. {resultados['n_databits']} b, fuente {resultados['n_fuente']} b, canal {resultados['n_canal']} b)\n"
            f"BER canal (bruto):  {resultados['ber_canal']:.2e}  →  {ch.clasificar_ber(resultados['ber_canal'])}\n"
            f"BER post-corrección:  {resultados['ber_post']:.2e}  →  {ch.clasificar_ber(resultados['ber_post'])}   "
            f"(detectados: {resultados['detectados']}, corregidos: {resultados['corregidos']})"
        )
        return line_x, line_ref, line_rx, im_bits

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE,
        dtype="float32", device=DEVICE, callback=audio_callback,
    )
    with stream:
        print(f"Capturando desde: {sd.query_devices(DEVICE, 'input')['name']}")
        ani = animation.FuncAnimation(fig, update, interval=REFRESH_MS, blit=False, cache_frame_data=False)
        plt.show()


if __name__ == "__main__":
    main()
