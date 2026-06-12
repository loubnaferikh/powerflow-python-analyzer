\
\
\
\
\


from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .ybus import build_ybus
from .zbus import build_zbus_from_ybus

SQRT3 = np.sqrt(3.0)
A = np.exp(1j * 2.0 * np.pi / 3.0)
T = np.array(
    [
        [1.0, 1.0, 1.0],
        [1.0, A**2, A],
        [1.0, A, A**2],
    ],
    dtype=complex,
)


@dataclass(frozen=True)
class SequenceNetworks:


    z0: np.ndarray
    z1: np.ndarray
    z2: np.ndarray
    note: str


def _safe_inverse_ybus(data, allow_pinv: bool = True) -> np.ndarray:

    if data.Ybus is None:
        data.Ybus = build_ybus(data.linedata, nbus=data.nbus)
    try:
        return build_zbus_from_ybus(data.Ybus, allow_pinv=False)
    except Exception:
        if allow_pinv:
            return build_zbus_from_ybus(data.Ybus, allow_pinv=True)
        raise


def build_sequence_networks(data, k0: float = 1.0, k2: float = 1.0) -> SequenceNetworks:
\
\
\

    z1 = _safe_inverse_ybus(data, allow_pinv=True)
    z2 = complex(k2) * z1
    z0 = complex(k0) * z1
    note = (
        "Approximation utilisée : Z1 = inv(Ybus), Z2 = k2·Z1, Z0 = k0·Z1. "
        "Utiliser k0/k2 pour ajuster si les données de séquence réelles sont connues."
    )
    return SequenceNetworks(z0=z0, z1=z1, z2=z2, note=note)


def prefault_voltage(data) -> np.ndarray:
\
\
\
\

    if getattr(data, "V", None) is not None:
        return np.asarray(data.V, dtype=complex).reshape(-1)
    vm = np.asarray(data.busdata[:, 2], dtype=float)
    va = np.deg2rad(np.asarray(data.busdata[:, 3], dtype=float))
    return vm * np.exp(1j * va)


def seq_to_phase(i0: complex, i1: complex, i2: complex) -> np.ndarray:

    return T @ np.array([i0, i1, i2], dtype=complex)


def phase_to_seq(ia: complex, ib: complex, ic: complex) -> np.ndarray:

    return np.linalg.inv(T) @ np.array([ia, ib, ic], dtype=complex)


def _phase_voltages_from_sequences(v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:

    vals = np.vstack([v0, v1, v2])
    return T @ vals


def _voltage_after_fault_all_buses(vpre: np.ndarray, seq: SequenceNetworks, k: int, i0: complex, i1: complex, i2: complex) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:

    n = len(vpre)
    v0_pre = np.zeros(n, dtype=complex)
    v1_pre = vpre.astype(complex)
    v2_pre = np.zeros(n, dtype=complex)
    v0 = v0_pre - seq.z0[:, k] * i0
    v1 = v1_pre - seq.z1[:, k] * i1
    v2 = v2_pre - seq.z2[:, k] * i2
    vabc = _phase_voltages_from_sequences(v0, v1, v2)
    return v0, v1, v2, vabc


def fault_matrices(fault_type: str, zf: complex = 0.0j, zg: complex = 0.0j) -> dict[str, np.ndarray | None]:
\
\
\
\

    f = fault_type.upper().replace(" ", "")
    yf = 1 / zf if abs(zf) > 1e-15 else np.inf

    if f in {"3PH", "LLL", "LLLG", "3LG"}:
        z012 = np.diag([zf + 3 * zg, zf, zf]).astype(complex)
        y012 = None
        return {"Zf_012": z012, "Yf_012": y012}

    if f == "LG":

        y012 = (yf / 3.0) * np.ones((3, 3), dtype=complex) if np.isfinite(yf) else None
        return {"Zf_012": None, "Yf_012": y012}

    if f == "LL":
        y012 = (yf / 2.0) * np.array(
            [[0, 0, 0], [0, 1, -1], [0, -1, 1]], dtype=complex
        ) if np.isfinite(yf) else None
        return {"Zf_012": None, "Yf_012": y012}

    if f == "LLG":

        den = 3.0 * (zf**2 + 2.0 * zf * zg)
        if abs(den) < 1e-15:
            y012 = None
        else:
            y012 = (1.0 / den) * np.array(
                [
                    [2*zf, -zf, -zf],
                    [-zf, 2*zf + 3*zg, -zf - 3*zg],
                    [-zf, -zf - 3*zg, 2*zf + 3*zg],
                ],
                dtype=complex,
            )
        return {"Zf_012": None, "Yf_012": y012}

    raise ValueError(f"Type de défaut inconnu: {fault_type}")


def analyze_fault(
    data,
    fault_bus: int,
    fault_type: str = "3PH",
    zf: complex = 0.0j,
    zg: complex = 0.0j,
    k0: float = 1.0,
    k2: float = 1.0,
) -> dict:
\
\
\
\
\
\
\

    if fault_bus < 1 or fault_bus > data.nbus:
        raise ValueError(f"fault_bus doit être compris entre 1 et {data.nbus}.")

    f = fault_type.upper().replace(" ", "")
    k = int(fault_bus) - 1
    seq = build_sequence_networks(data, k0=k0, k2=k2)
    vpre = prefault_voltage(data)
    vk = complex(vpre[k])

    z0kk = complex(seq.z0[k, k])
    z1kk = complex(seq.z1[k, k])
    z2kk = complex(seq.z2[k, k])

    if f in {"3PH", "LLL", "LLLG", "3LG"}:
        i0 = 0.0j
        i1 = vk / (z1kk + zf)
        i2 = 0.0j
        iphase = np.array([i1, i1 * A**2, i1 * A], dtype=complex)

        v1 = vpre - seq.z1[:, k] * i1
        v0 = np.zeros_like(v1)
        v2 = np.zeros_like(v1)
        vabc = _phase_voltages_from_sequences(v0, v1, v2)
        formula = "If = Vk(0) / (Z1kk + Zf)"
    elif f == "LG":
        i1 = vk / (z0kk + z1kk + z2kk + 3.0 * zf)
        i0 = i1
        i2 = i1
        iphase = seq_to_phase(i0, i1, i2)
        v0, v1, v2, vabc = _voltage_after_fault_all_buses(vpre, seq, k, i0, i1, i2)
        formula = "I0 = I1 = I2 = Vk(0) / (Z0kk + Z1kk + Z2kk + 3Zf)"
    elif f == "LL":
        i0 = 0.0j
        i1 = vk / (z1kk + z2kk + zf)
        i2 = -i1
        iphase = seq_to_phase(i0, i1, i2)
        v0, v1, v2, vabc = _voltage_after_fault_all_buses(vpre, seq, k, i0, i1, i2)
        formula = "I1 = Vk(0) / (Z1kk + Z2kk + Zf), I2 = -I1, I0 = 0"
    elif f == "LLG":
        den_parallel = z2kk + z0kk + 2.0 * zf + 3.0 * zg
        if abs(den_parallel) < 1e-15:
            raise ZeroDivisionError("Dénominateur nul pour le défaut L-L-G.")
        z_parallel = ((z2kk + zf) * (z0kk + zf + 3.0 * zg)) / den_parallel
        i1 = vk / (z1kk + z_parallel)
        i2 = -i1 * (z0kk + zf + 3.0 * zg) / den_parallel
        i0 = -i1 * (z2kk + zf) / den_parallel
        iphase = seq_to_phase(i0, i1, i2)
        v0, v1, v2, vabc = _voltage_after_fault_all_buses(vpre, seq, k, i0, i1, i2)
        formula = "I1 = Vk(0)/(Z1 + (Z2+Zf)//(Z0+Zf+3Zg)); I2/I0 par division de courant"
    else:
        raise ValueError(f"Type de défaut non supporté : {fault_type}")

    ifault_pu = abs(iphase[0]) if f in {"3PH", "LLL", "LLLG", "3LG", "LG"} else max(abs(iphase))

    scc_mva = abs(vk) * ifault_pu * float(data.basemva)

    result = {
        "fault_type": "3PH" if f in {"3PH", "LLL", "LLLG", "3LG"} else f,
        "fault_bus": int(fault_bus),
        "zf": complex(zf),
        "zg": complex(zg),
        "k0": float(k0),
        "k2": float(k2),
        "Vk_prefault": vk,
        "Zkk": {"Z0": z0kk, "Z1": z1kk, "Z2": z2kk},
        "I_seq": np.array([i0, i1, i2], dtype=complex),
        "I_phase": iphase,
        "V_seq_all": np.vstack([v0, v1, v2]),
        "V_phase_all": vabc,
        "V_phase_fault_bus": vabc[:, k],
        "ifault_pu": float(ifault_pu),
        "scc_mva": float(scc_mva),
        "formula": formula,
        "sequence_note": seq.note,
        "fault_matrices": fault_matrices(f, zf=zf, zg=zg),
    }
    data.results["fault"] = result
    return result


def format_complex(z: complex, digits: int = 4) -> str:

    z = complex(z)
    return f"{z.real:.{digits}f}{z.imag:+.{digits}f}j"
