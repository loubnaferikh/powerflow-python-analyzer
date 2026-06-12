\
\
\
\
\
\
\
\
\
\


from __future__ import annotations

import numpy as np


def _as_2d_float_array(array: np.ndarray, name: str) -> np.ndarray:

    arr = np.asarray(array, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"{name} doit être un tableau 2D.")
    return arr


def _infer_nbus(linedata: np.ndarray, nbus: int | None = None) -> int:

    if nbus is not None:
        if int(nbus) <= 0:
            raise ValueError("nbus doit être strictement positif.")
        return int(nbus)

    if linedata.size == 0:
        raise ValueError("Impossible de déduire nbus : linedata est vide.")

    max_bus = int(np.max(linedata[:, :2]))
    if max_bus <= 0:
        raise ValueError("Les numéros de bus doivent commencer à 1.")
    return max_bus


def build_ybus(linedata: np.ndarray, nbus: int | None = None) -> np.ndarray:
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\

    linedata = _as_2d_float_array(linedata, "linedata")
    if linedata.shape[1] < 4:
        raise ValueError(
            "linedata doit contenir au moins 4 colonnes : from, to, R, X."
        )

    nbus = _infer_nbus(linedata, nbus)
    ybus = np.zeros((nbus, nbus), dtype=complex)

    for k, row in enumerate(linedata):
        from_bus = int(row[0]) - 1
        to_bus = int(row[1]) - 1

        if from_bus < 0 or to_bus < 0 or from_bus >= nbus or to_bus >= nbus:
            raise ValueError(
                f"Ligne {k}: bus invalide ({int(row[0])}, {int(row[1])}) pour nbus={nbus}."
            )

        r = float(row[2])
        x = float(row[3])
        b_half = float(row[4]) if linedata.shape[1] >= 5 else 0.0
        tap = float(row[5]) if linedata.shape[1] >= 6 else 1.0

        if abs(tap) < 1e-15:
            tap = 1.0

        z = complex(r, x)
        if abs(z) < 1e-15:
            raise ZeroDivisionError(
                f"Ligne {k}: impédance nulle R+jX = 0 entre bus {from_bus+1} et {to_bus+1}."
            )

        y_series = 1.0 / z
        y_shunt = 1j * b_half


        ybus[from_bus, to_bus] -= y_series / tap
        ybus[to_bus, from_bus] -= y_series / tap


        ybus[from_bus, from_bus] += y_series / (tap**2) + y_shunt
        ybus[to_bus, to_bus] += y_series + y_shunt

    return ybus


if __name__ == "__main__":

    linedata_test = np.array(
        [
            [1, 2, 0.02, 0.06, 0.03, 1.0],
            [1, 3, 0.08, 0.24, 0.025, 1.0],
            [2, 3, 0.06, 0.18, 0.02, 1.0],
        ],
        dtype=float,
    )
    print(build_ybus(linedata_test))
