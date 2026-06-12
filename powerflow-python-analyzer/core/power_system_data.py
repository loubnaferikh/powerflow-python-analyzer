

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class PowerSystemData:


    busdata: np.ndarray
    linedata: np.ndarray
    basemva: float = 100.0
    gendata: np.ndarray | None = None
    Ybus: np.ndarray | None = None
    Zbus: np.ndarray | None = None
    V: np.ndarray | None = None
    Pg: np.ndarray | None = None
    Qg: np.ndarray | None = None
    Pc: np.ndarray | None = None
    Qc: np.ndarray | None = None
    results: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.busdata = np.asarray(self.busdata, dtype=float)
        self.linedata = np.asarray(self.linedata, dtype=float)
        if self.gendata is not None:
            self.gendata = np.asarray(self.gendata, dtype=float)
        if self.busdata.ndim != 2:
            raise ValueError("busdata doit être un tableau 2D.")
        if self.linedata.ndim != 2:
            raise ValueError("linedata doit être un tableau 2D.")
        if self.busdata.shape[1] < 8:
            raise ValueError("busdata doit contenir au minimum 8 colonnes.")

    @property
    def nbus(self) -> int:
        return int(self.busdata.shape[0])

    def ensure_ybus(self) -> np.ndarray:

        if self.Ybus is None:
            from .ybus import build_ybus
            self.Ybus = build_ybus(self.linedata, nbus=self.nbus)
        return self.Ybus
