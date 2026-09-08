"""
Codificación de fuente (compresión sin pérdida) con selector de algoritmo.

Métodos disponibles: "huffman", "shannon_fano".
"""

import heapq
from collections import Counter
import numpy as np


def build_huffman(symbols):
    freq = Counter(symbols)
    if len(freq) == 1:
        sym = next(iter(freq))
        return {sym: "0"}

    heap = [[wt, [sym, ""]] for sym, wt in freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = "0" + pair[1]
        for pair in hi[1:]:
            pair[1] = "1" + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    return {sym: code for sym, code in heap[0][1:]}


def build_shannon_fano(symbols):
    freq = Counter(symbols)
    items = sorted(freq.items(), key=lambda kv: -kv[1])
    codes = {sym: "" for sym, _ in items}

    def recurse(items):
        if len(items) <= 1:
            return
        total = sum(c for _, c in items)
        acc = 0
        best_diff, split = None, 1
        for i in range(len(items)):
            acc += items[i][1]
            diff = abs((total - acc) - acc)
            if best_diff is None or diff < best_diff:
                best_diff, split = diff, i + 1
        left, right = items[:split], items[split:]
        for sym, _ in left:
            codes[sym] += "0"
        for sym, _ in right:
            codes[sym] += "1"
        recurse(left)
        recurse(right)

    recurse(items)
    return codes


def build_codes(symbols, metodo="huffman"):
    if metodo == "huffman":
        return build_huffman(symbols)
    elif metodo == "shannon_fano":
        return build_shannon_fano(symbols)
    raise ValueError(f"método desconocido: {metodo}")


def encode(symbols, codes):
    return "".join(codes[s] for s in symbols)


def decode(bitstring, codes):
    inv = {v: k for k, v in codes.items()}
    out, buf = [], ""
    for b in bitstring:
        buf += b
        if buf in inv:
            out.append(inv[buf])
            buf = ""
    return out


def metrics(symbols, codes):
    freq = Counter(symbols)
    total = sum(freq.values())
    probs = {s: c / total for s, c in freq.items()}
    H = -sum(p * np.log2(p) for p in probs.values() if p > 0)
    L = sum(probs[s] * len(codes[s]) for s in probs)
    eficiencia = (H / L) if L > 0 else 0.0
    return {"entropia": H, "longitud_promedio": L, "eficiencia": eficiencia}
