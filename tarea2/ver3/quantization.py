"""
Cuantizadores lineales y no lineales.

- Voz: cuantización lineal uniforme vs. companding ley A (ITU-T G.711).
- Video/imagen: cuantización lineal uniforme vs. gamma (perceptual).

Todas las funciones trabajan con señales normalizadas:
  - Voz: rango [-1, 1]
  - Imagen: rango [0, 1]
"""

import numpy as np

# ---------------- Voz: lineal y ley A -----------------------------------

def linear_quantize(x, bits=8):
    """Cuantiza x en [-1,1] a 2**bits niveles uniformes.
    Retorna (x_reconstruida, indices_enteros)."""
    x = np.clip(x, -1.0, 1.0)
    levels = 2 ** bits
    step = 2.0 / levels
    idx = np.clip(np.round((x + 1.0) / step), 0, levels - 1)
    xq = idx * step - 1.0
    return xq, idx.astype(np.int64)


def a_law_encode(x, A=87.6):
    x = np.clip(x, -1.0, 1.0)
    absx = np.abs(x)
    thresh = 1.0 / A
    y = np.where(
        absx < thresh,
        A * absx / (1 + np.log(A)),
        (1 + np.log(A * np.maximum(absx, 1e-12))) / (1 + np.log(A)),
    )
    return np.sign(x) * y


def a_law_decode(y, A=87.6):
    absy = np.abs(y)
    thresh = 1.0 / (1 + np.log(A))
    x = np.where(
        absy < thresh,
        absy * (1 + np.log(A)) / A,
        np.exp(absy * (1 + np.log(A)) - 1) / A,
    )
    return np.sign(y) * x


def a_law_quantize(x, bits=8, A=87.6):
    """Cuantización no lineal completa: compresión ley A -> cuantiza -> expansión."""
    y = a_law_encode(x, A)
    yq, idx = linear_quantize(y, bits)
    xq = a_law_decode(yq, A)
    return xq, idx


# ---------------- Video/imagen: lineal y gamma ---------------------------

def linear_quantize_img(img01, bits=8):
    """img01 en [0,1]. Retorna (imagen_reconstruida, indices_enteros)."""
    img01 = np.clip(img01, 0.0, 1.0)
    levels = 2 ** bits
    idx = np.clip(np.round(img01 * (levels - 1)), 0, levels - 1)
    xq = idx / (levels - 1)
    return xq, idx.astype(np.int64)


def gamma_quantize_img(img01, bits=8, gamma=2.2):
    """Cuantización no lineal perceptual: codifica con gamma antes de cuantizar."""
    img01 = np.clip(img01, 0.0, 1.0)
    y = np.power(img01, 1.0 / gamma)
    levels = 2 ** bits
    idx = np.clip(np.round(y * (levels - 1)), 0, levels - 1)
    yq = idx / (levels - 1)
    xq = np.power(yq, gamma)
    return xq, idx.astype(np.int64)
