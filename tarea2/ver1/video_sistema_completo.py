"""
Sistema completo de comunicaciones para video, en una ventana emergente:

  webcam USB -> escala de grises -> cuantización (lineal | gamma)
             -> codificación de fuente (huffman | shannon_fano)
             -> codificación de canal (ninguno | vrc | lrc_vrc | hamming)
             -> canal BSC (ruido ajustable con slider)
             -> decodificación de canal -> decodificación de fuente -> reconstrucción
             -> BER de canal y BER post-corrección

Paneles:
  1. Imágenes: original / cuantizada (sin canal) / reconstruida (tras canal)
  2. Entramado de bits: una fila por etapa del pipeline, con los bits que
     cambiaron respecto a la etapa de referencia resaltados en rojo. Solo se
     muestran los primeros VIS_BITS bits de cada frame (aplanado).

Dependencias:
    pip install opencv-python numpy matplotlib

Uso:
    python3 video_sistema_completo.py
    (ejecutar desde la carpeta sistema_comunicaciones/, o con ésta en PYTHONPATH)

Nota de rendimiento: se reduce el frame a RESOLUCION x RESOLUCION antes de
procesar, porque el pipeline (fuente + canal + BER, en Python puro) es
demasiado pesado para correr en tiempo real sobre un frame completo en una Pi.
"""

import numpy as np
import cv2
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
CAM_INDEX = 0
RESOLUCION = 48
BITS = 8
REFRESH_MS = 300
VIS_BITS = 300
# --------------------------------------------------------------------------

estado = {
    "cuantizacion": "gamma",
    "fuente": "huffman",
    "canal_cod": "hamming",
    "p": 0.01,
}

resultados = {}

BIT_CMAP = ListedColormap(["white", "black", "#e03030", "#dddddd"])
ETIQUETAS_FILAS = [
    "1. Símbolos cuantizados",
    "2. Tras codificación de fuente",
    "3. Tras codificación de canal (TX)",
    "4. Recibido (canal ruidoso)",
    "5. Tras decodificación de canal",
    "6. Símbolos recuperados",
]


def idx_to_bits(idx, bits=BITS):
    out = []
    for v in idx:
        out.extend(int(b) for b in format(int(v), f"0{bits}b"))
    return out


def fila_bits(bits, ref=None, n=VIS_BITS):
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


def procesar_frame(gris01):
    h, w = gris01.shape

    if estado["cuantizacion"] == "lineal":
        xq_ref, idx = q.linear_quantize_img(gris01, bits=BITS)
    else:
        xq_ref, idx = q.gamma_quantize_img(gris01, bits=BITS)

    simbolos = idx.flatten().tolist()
    databits = idx_to_bits(simbolos)

    codes = sc.build_codes(simbolos, metodo=estado["fuente"])
    bitstring = sc.encode(simbolos, codes)
    metr = sc.metrics(simbolos, codes)
    fuente_bits = [int(b) for b in bitstring]

    codebits = cc.encode_canal(fuente_bits, metodo=estado["canal_cod"])
    rxbits, _ = ch.canal_bsc(codebits, estado["p"])
    ber_canal, _, _ = ch.calcular_ber(codebits, rxbits)

    decoded_fuente_bits, detectados, corregidos = cc.decode_canal(rxbits, metodo=estado["canal_cod"])
    ber_post, _, _ = ch.calcular_ber(fuente_bits, decoded_fuente_bits)

    bitstring_rx = "".join(str(b) for b in decoded_fuente_bits)
    simbolos_rx = sc.decode(bitstring_rx, codes)
    if len(simbolos_rx) < len(simbolos):
        simbolos_rx = simbolos_rx + simbolos[len(simbolos_rx):]
    simbolos_rx = np.array(simbolos_rx[:len(simbolos)])
    simbolos_rx_bits = idx_to_bits(simbolos_rx.tolist())
    simbolos_rx_img = simbolos_rx.reshape(h, w)

    levels = 2 ** BITS
    if estado["cuantizacion"] == "lineal":
        xq_rx = simbolos_rx_img / (levels - 1)
    else:
        yq_rx = simbolos_rx_img / (levels - 1)
        xq_rx = np.power(yq_rx, 2.2)

    matriz_bits = np.vstack([
        fila_bits(databits),
        fila_bits(fuente_bits),
        fila_bits(codebits),
        fila_bits(rxbits, ref=codebits),
        fila_bits(decoded_fuente_bits, ref=fuente_bits),
        fila_bits(simbolos_rx_bits, ref=databits),
    ])

    resultados.update({
        "original": gris01, "xq_ref": xq_ref, "xq_rx": xq_rx,
        "ber_canal": ber_canal, "ber_post": ber_post,
        "metricas_fuente": metr, "detectados": detectados, "corregidos": corregidos,
        "matriz_bits": matriz_bits,
        "n_databits": len(databits), "n_fuente": len(fuente_bits), "n_canal": len(codebits),
    })


def main():
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la webcam. Revisa CAM_INDEX.")

    fig = plt.figure(figsize=(13, 8.5))
    fig.canvas.manager.set_window_title("Sistema de comunicaciones de video")
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.3], left=0.05, right=0.78, top=0.93, bottom=0.08, hspace=0.5)

    # ---- Panel 1: imágenes ---------------------------------------------
    gs_img = gs[0].subgridspec(1, 3, wspace=0.15)
    axes_img = [fig.add_subplot(gs_img[i]) for i in range(3)]
    titles = ["Original", "Cuantizada (sin canal)", "Reconstruida (tras canal)"]
    imgs = []
    blank = np.zeros((RESOLUCION, RESOLUCION))
    for a, title in zip(axes_img, titles):
        im = a.imshow(blank, cmap="gray", vmin=0, vmax=1)
        a.set_title(title, fontsize=10)
        a.axis("off")
        imgs.append(im)

    # ---- Panel 2: entramado de bits ------------------------------------
    ax_bits = fig.add_subplot(gs[1])
    matriz_inicial = np.full((6, VIS_BITS), 3.0)
    im_bits = ax_bits.imshow(matriz_inicial, aspect="auto", cmap=BIT_CMAP, vmin=0, vmax=3, interpolation="nearest")
    ax_bits.set_yticks(range(6))
    ax_bits.set_yticklabels(ETIQUETAS_FILAS, fontsize=8)
    ax_bits.set_xlabel(f"posición de bit (primeros {VIS_BITS} del frame aplanado)")
    ax_bits.set_title("Entramado de bits: cómo cambia el flujo en cada etapa")
    leyenda = [
        Patch(facecolor="white", edgecolor="gray", label="bit 0"),
        Patch(facecolor="black", label="bit 1"),
        Patch(facecolor="#e03030", label="bit erróneo"),
        Patch(facecolor="#dddddd", label="relleno"),
    ]
    ax_bits.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, -0.22),
                   ncol=4, fontsize=8, frameon=False)

    info = fig.text(0.05, 0.02, "", fontsize=9, va="bottom")

    ax_q = plt.axes([0.81, 0.76, 0.17, 0.15])
    r_q = RadioButtons(ax_q, ["gamma", "lineal"])
    ax_q.set_title("Cuantización", fontsize=9)

    ax_f = plt.axes([0.81, 0.56, 0.17, 0.15])
    r_f = RadioButtons(ax_f, ["huffman", "shannon_fano"])
    ax_f.set_title("Fuente", fontsize=9)

    ax_c = plt.axes([0.81, 0.31, 0.17, 0.20])
    r_c = RadioButtons(ax_c, ["hamming", "lrc_vrc", "vrc", "ninguno"])
    ax_c.set_title("Canal (FEC)", fontsize=9)

    ax_p = plt.axes([0.81, 0.14, 0.17, 0.03])
    s_p = Slider(ax_p, "p (ruido)", 0.0, 0.2, valinit=estado["p"])

    r_q.on_clicked(lambda label: estado.update(cuantizacion=label))
    r_f.on_clicked(lambda label: estado.update(fuente=label))
    r_c.on_clicked(lambda label: estado.update(canal_cod=label))
    s_p.on_changed(lambda val: estado.update(p=val))

    def update(_frame):
        ok, frame = cap.read()
        if not ok:
            return imgs + [im_bits]
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris = cv2.resize(gris, (RESOLUCION, RESOLUCION), interpolation=cv2.INTER_AREA)
        gris01 = gris.astype(np.float32) / 255.0

        procesar_frame(gris01)

        imgs[0].set_data(resultados["original"])
        imgs[1].set_data(resultados["xq_ref"])
        imgs[2].set_data(resultados["xq_rx"])
        im_bits.set_data(resultados["matriz_bits"])

        m = resultados["metricas_fuente"]
        info.set_text(
            f"Fuente: H={m.get('entropia',0):.2f} bits/símbolo   "
            f"L={m.get('longitud_promedio',0):.2f} bits/símbolo   "
            f"eficiencia={m.get('eficiencia',0)*100:.1f}%   |   "
            f"tamaños -> cuantización: {resultados['n_databits']} bits, "
            f"fuente: {resultados['n_fuente']} bits, canal: {resultados['n_canal']} bits\n"
            f"BER canal: {resultados['ber_canal']:.2e} ({ch.clasificar_ber(resultados['ber_canal'])})   "
            f"BER post-corrección: {resultados['ber_post']:.2e} ({ch.clasificar_ber(resultados['ber_post'])})   "
            f"[det: {resultados['detectados']}, corr: {resultados['corregidos']}]"
        )
        return imgs + [im_bits]

    ani = animation.FuncAnimation(fig, update, interval=REFRESH_MS, blit=False, cache_frame_data=False)
    plt.show()
    cap.release()


if __name__ == "__main__":
    main()
