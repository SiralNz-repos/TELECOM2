"""
Modulación digital con selector de esquema.

Métodos disponibles: "ask", "fsk", "bpsk", "qpsk", "qam16".
Cada símbolo se representa como un número complejo (I + jQ).

Referencia de uso real (para la propuesta):
- ASK: enlaces ópticos simples de bajo costo, RFID.
- FSK: Bluetooth clásico, radios de bajo costo, muy robusta a ruido de amplitud.
- BPSK/QPSK: base de enlaces satelitales, 3G, y el modo más robusto de LTE/Wi-Fi
  cuando el SNR es bajo.
- QAM (16/64/256/1024...): usado por Wi-Fi 802.11ac (hasta 256-QAM) y 802.11ax
  (hasta 1024-QAM) y por LTE/5G, para maximizar bits/símbolo cuando el SNR es
  bueno. A mayor orden de QAM, más throughput pero más sensible al ruido —
  por eso estos estándares cambian de esquema de modulación dinámicamente
  según la calidad del enlace (adaptive modulation and coding, MCS).
"""

import numpy as np

BITS_POR_SIMBOLO = {
    "ask": 1,
    "fsk": 1,
    "bpsk": 1,
    "qpsk": 2,
    "qam16": 4,
}

_NIVELES_QAM16 = [-3, -1, 1, 3]


def bits_a_simbolos(bits, metodo):
    """Agrupa bits y los mapea a símbolos complejos I/Q. Retorna (simbolos, bits_por_simbolo)."""
    bps = BITS_POR_SIMBOLO[metodo]
    bits = list(bits)
    if len(bits) % bps != 0:
        bits = bits + [0] * (bps - len(bits) % bps)
    grupos = [bits[i:i + bps] for i in range(0, len(bits), bps)]

    if metodo == "ask":
        simbolos = [complex(1.0 if g[0] else 0.15, 0.0) for g in grupos]
    elif metodo == "fsk":
        # Dos frecuencias representadas como dos ejes ortogonales en el plano IQ
        simbolos = [complex(1, 0) if g[0] == 0 else complex(0, 1) for g in grupos]
    elif metodo == "bpsk":
        simbolos = [complex(1, 0) if g[0] == 0 else complex(-1, 0) for g in grupos]
    elif metodo == "qpsk":
        mapa = {
            (0, 0): complex(1, 1), (0, 1): complex(-1, 1),
            (1, 1): complex(-1, -1), (1, 0): complex(1, -1),
        }
        simbolos = [mapa[(g[0], g[1])] / np.sqrt(2) for g in grupos]
    elif metodo == "qam16":
        simbolos = []
        for g in grupos:
            i = _NIVELES_QAM16[g[0] * 2 + g[1]]
            qd = _NIVELES_QAM16[g[2] * 2 + g[3]]
            simbolos.append(complex(i, qd) / np.sqrt(10))
    else:
        raise ValueError(f"esquema desconocido: {metodo}")

    return np.array(simbolos), bps


def agregar_ruido_awgn(simbolos, sigma):
    """Ruido gaussiano complejo aditivo, simulando el canal físico."""
    if len(simbolos) == 0:
        return simbolos
    ruido = (np.random.randn(len(simbolos)) + 1j * np.random.randn(len(simbolos))) * sigma
    return simbolos + ruido


def constelacion_ideal(metodo):
    """Puntos ideales de la constelación (sin ruido), para dibujar como referencia."""
    if metodo == "ask":
        return np.array([0.15 + 0j, 1 + 0j])
    if metodo == "fsk":
        return np.array([1 + 0j, 1j])
    if metodo == "bpsk":
        return np.array([1 + 0j, -1 + 0j])
    if metodo == "qpsk":
        return np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    if metodo == "qam16":
        return np.array([complex(i, q) for i in _NIVELES_QAM16 for q in _NIVELES_QAM16]) / np.sqrt(10)
    raise ValueError(f"esquema desconocido: {metodo}")


def calcular_baudios(n_bits, duracion_s, metodo):
    """Tasa de símbolo (baudios) a partir de la tasa de bits y bits/símbolo del esquema."""
    bps = BITS_POR_SIMBOLO[metodo]
    tasa_bits = n_bits / duracion_s if duracion_s > 0 else 0.0
    return tasa_bits / bps, bps
