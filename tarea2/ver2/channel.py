"""
Canal binario simétrico (BSC) y cálculo de BER.
"""

import numpy as np

# Rangos de referencia orientativos (ajusta según la bibliografía de tu curso,
# ej. Sklar "Digital Communications" o Proakis)
RANGOS_BER = [
    (1e-2, float("inf"), "Inaceptable, degradación severa"),
    (1e-3, 1e-2, "Marginal (voz con degradación audible)"),
    (1e-6, 1e-3, "Buena calidad para voz digital"),
    (0.0, 1e-6, "Buena calidad para datos/video"),
]


def canal_bsc(bits, p):
    """Invierte cada bit con probabilidad p (canal binario simétrico)."""
    bits = np.array(bits)
    flips = np.random.rand(len(bits)) < p
    return np.bitwise_xor(bits, flips.astype(int)).tolist(), int(flips.sum())


def calcular_ber(bits_tx, bits_rx):
    n = min(len(bits_tx), len(bits_rx))
    if n == 0:
        return 0.0, 0, 0
    tx = np.array(bits_tx[:n])
    rx = np.array(bits_rx[:n])
    errores = int(np.sum(tx != rx))
    return errores / n, errores, n


def clasificar_ber(ber):
    for lo, hi, etiqueta in RANGOS_BER:
        if lo <= ber < hi:
            return etiqueta
    return "fuera de rango"
