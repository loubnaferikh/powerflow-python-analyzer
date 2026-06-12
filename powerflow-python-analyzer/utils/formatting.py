

from __future__ import annotations
import numpy as np


def complex_to_str(z: complex, digits: int = 3) -> str:
    z = complex(z)
    sign = "+" if z.imag >= 0 else "-"
    return f"{z.real:.{digits}f} {sign} j{abs(z.imag):.{digits}f}"


def matrix_to_strings(matrix: np.ndarray, digits: int = 3) -> list[list[str]]:
    arr = np.asarray(matrix)
    out: list[list[str]] = []
    for row in arr:
        formatted = []
        for value in row:
            if np.iscomplexobj(arr):
                formatted.append(complex_to_str(value, digits))
            else:
                formatted.append(f"{float(value):.{digits}f}")
        out.append(formatted)
    return out


def safe_float(text: str, default: float) -> float:
    try:
        return float(str(text).replace(",", "."))
    except Exception:
        return default


def bus_type_label(code: int) -> str:
    mapping = {1: "Slack", 2: "PV", 0: "PQ", 3: "Slack"}
    return mapping.get(int(code), str(code))
