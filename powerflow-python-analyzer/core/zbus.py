

from __future__ import annotations

import numpy as np

from .ybus import build_ybus


def _as_square_complex_matrix(matrix: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(matrix, dtype=complex)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"{name} doit être une matrice carrée.")
    return arr


def build_zbus_from_ybus(
    Ybus: np.ndarray,
    *,
    cond_limit: float = 1e14,
    allow_pinv: bool = False,
) -> np.ndarray:


    ybus = _as_square_complex_matrix(Ybus, "Ybus")

    try:
        cond = np.linalg.cond(ybus)
    except Exception as exc:
        raise np.linalg.LinAlgError(
            f"Impossible d'évaluer le conditionnement de Ybus: {exc}"
        ) from exc

    if not np.isfinite(cond) or cond > cond_limit:
        if allow_pinv:
            return np.linalg.pinv(ybus)
        raise np.linalg.LinAlgError(
            "Ybus est singulière ou très mal conditionnée. "
            f"Conditionnement = {cond:.3e}."
        )

    return np.linalg.inv(ybus)


def build_zbus_direct(
    linedata: np.ndarray,
    nbus: int | None = None,
    *,
    allow_pinv: bool = False,
) -> np.ndarray:


    ybus = build_ybus(linedata, nbus=nbus)
    return build_zbus_from_ybus(ybus, allow_pinv=allow_pinv)
