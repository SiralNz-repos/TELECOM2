"""
Codificación de canal (control de errores) con selector de esquema.

Métodos disponibles: "ninguno", "vrc", "lrc_vrc", "hamming".
Todas las funciones trabajan sobre listas de bits (enteros 0/1).
"""

import numpy as np

# ---------------- VRC: 1 bit de paridad por cada 7 bits de dato ----------

def vrc_encode(databits):
    out = []
    for i in range(0, len(databits), 7):
        chunk = databits[i:i + 7]
        if len(chunk) < 7:
            chunk = chunk + [0] * (7 - len(chunk))
        parity = sum(chunk) % 2
        out.extend(chunk + [parity])
    return out


def vrc_decode(codebits):
    out, detectados = [], 0
    for i in range(0, len(codebits), 8):
        chunk = codebits[i:i + 8]
        if len(chunk) < 8:
            chunk = chunk + [0] * (8 - len(chunk))
        data, parity = chunk[:7], chunk[7]
        if sum(data) % 2 != parity:
            detectados += 1
        out.extend(data)
    return out, detectados, 0  # VRC solo detecta, nunca corrige


# ---------------- LRC + VRC: matriz de paridad 2D ------------------------

def lrc_vrc_encode(databits, chars_por_bloque=8):
    chars = []
    for i in range(0, len(databits), 7):
        c = databits[i:i + 7]
        if len(c) < 7:
            c = c + [0] * (7 - len(c))
        chars.append(c)
    while len(chars) % chars_por_bloque != 0:
        chars.append([0] * 7)

    out = []
    for b in range(0, len(chars), chars_por_bloque):
        block = np.array(chars[b:b + chars_por_bloque])           # filas x 7
        vrc = (block.sum(axis=1) % 2).reshape(-1, 1)
        block_vrc = np.hstack([block, vrc])                       # filas x 8
        lrc = (block_vrc.sum(axis=0) % 2).reshape(1, -1)           # 1 x 8
        full = np.vstack([block_vrc, lrc])                        # (filas+1) x 8
        out.extend(full.flatten().tolist())
    return out


def lrc_vrc_decode(codebits, chars_por_bloque=8):
    rows, cols = chars_por_bloque + 1, 8
    block_bits = rows * cols
    data_out, detectados, corregidos = [], 0, 0

    for b in range(0, len(codebits), block_bits):
        chunk = codebits[b:b + block_bits]
        if len(chunk) < block_bits:
            chunk = chunk + [0] * (block_bits - len(chunk))
        mat = np.array(chunk).reshape(rows, cols)
        data_rows, lrc_row = mat[:-1, :], mat[-1, :]

        row_err = (data_rows.sum(axis=1) % 2) != 0
        col_err = ((np.vstack([data_rows, lrc_row]).sum(axis=0)) % 2) != 0

        if row_err.any() or col_err.any():
            detectados += 1
            if row_err.sum() == 1 and col_err.sum() == 1:
                r, c = np.where(row_err)[0][0], np.where(col_err)[0][0]
                mat[r, c] ^= 1
                corregidos += 1

        data_out.extend(mat[:-1, :7].flatten().tolist())
    return data_out, detectados, corregidos


# ---------------- Hamming(7,4): corrige 1 bit por palabra código ---------

_G = np.array([
    [1, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 1, 0, 1],
    [0, 0, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1],
])
_H = np.array([
    [1, 1, 0, 1, 1, 0, 0],
    [1, 0, 1, 1, 0, 1, 0],
    [0, 1, 1, 1, 0, 0, 1],
])


def hamming74_encode(databits):
    out = []
    for i in range(0, len(databits), 4):
        chunk = databits[i:i + 4]
        if len(chunk) < 4:
            chunk = chunk + [0] * (4 - len(chunk))
        c = (np.array(chunk) @ _G) % 2
        out.extend(c.tolist())
    return out


def hamming74_decode(codebits):
    out, detectados, corregidos = [], 0, 0
    for i in range(0, len(codebits), 7):
        chunk = codebits[i:i + 7]
        if len(chunk) < 7:
            chunk = chunk + [0] * (7 - len(chunk))
        c = np.array(chunk)
        s = (_H @ c) % 2
        if s.any():
            detectados += 1
            pos = None
            for j in range(7):
                if np.array_equal(_H[:, j], s):
                    pos = j
                    break
            if pos is not None:
                c[pos] ^= 1
                corregidos += 1
        out.extend(c[[0, 1, 2, 3]].tolist())
    return out, detectados, corregidos


# ---------------- Selector unificado --------------------------------------

def encode_canal(databits, metodo="hamming"):
    if metodo == "ninguno":
        return databits
    if metodo == "vrc":
        return vrc_encode(databits)
    if metodo == "lrc_vrc":
        return lrc_vrc_encode(databits)
    if metodo == "hamming":
        return hamming74_encode(databits)
    raise ValueError(f"método desconocido: {metodo}")


def decode_canal(codebits, metodo="hamming"):
    if metodo == "ninguno":
        return codebits, 0, 0
    if metodo == "vrc":
        return vrc_decode(codebits)
    if metodo == "lrc_vrc":
        return lrc_vrc_decode(codebits)
    if metodo == "hamming":
        return hamming74_decode(codebits)
    raise ValueError(f"método desconocido: {metodo}")
