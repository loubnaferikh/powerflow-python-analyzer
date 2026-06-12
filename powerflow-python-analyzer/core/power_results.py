

from __future__ import annotations
import numpy as np


def convert_bus_types(busdata: np.ndarray) -> np.ndarray:

    raw_type = np.asarray(busdata[:, 1], dtype=int)
    bus_type = raw_type.copy()
    if np.max(raw_type) == 3:
        bus_type[raw_type == 3] = 1
        bus_type[raw_type == 2] = 2
        bus_type[raw_type == 1] = 0
    return bus_type


def get_power_columns(busdata: np.ndarray):

    pc_mw = busdata[:, 4]
    qc_mvar = busdata[:, 5]
    pg_mw = busdata[:, 6]
    qg_mvar = busdata[:, 7]
    qsh_mvar = busdata[:, 10] if busdata.shape[1] > 10 else np.zeros(busdata.shape[0])
    return pc_mw, qc_mvar, pg_mw, qg_mvar, qsh_mvar


def initial_voltage(busdata: np.ndarray) -> np.ndarray:
    vm = busdata[:, 2].astype(float)
    va = np.deg2rad(busdata[:, 3].astype(float))
    return vm * np.exp(1j * va)


def specified_power_pu(busdata: np.ndarray, basemva: float):
    pc, qc, pg, qg, qsh = get_power_columns(busdata)
    p_spec = (pg - pc) / basemva
    q_spec = (qg - qc + qsh) / basemva
    return p_spec, q_spec


def calculate_power_injections(Ybus: np.ndarray, V: np.ndarray):

    S = V * np.conj(Ybus @ V)
    return S.real, S.imag


def calculate_loads_generations(data, V: np.ndarray):
    P_inj, Q_inj = calculate_power_injections(data.Ybus, V)
    pc_mw, qc_mvar, _, _, qsh_mvar = get_power_columns(data.busdata)
    Pg = (P_inj + pc_mw / data.basemva) * data.basemva
    Qg = (Q_inj + qc_mvar / data.basemva - qsh_mvar / data.basemva) * data.basemva
    return Pg, Qg, pc_mw.copy(), qc_mvar.copy()


def calculate_losses(data, V: np.ndarray):
    Pg, Qg, Pc, Qc = calculate_loads_generations(data, V)
    _, _, _, _, qsh = get_power_columns(data.busdata)
    losses_p = float(np.sum(Pg) - np.sum(Pc))
    losses_q = float(np.sum(Qg) - np.sum(Qc) + np.sum(qsh))
    return losses_p, losses_q


def calculate_line_flows(data, V: np.ndarray) -> list[dict]:
    flows = []
    for k, row in enumerate(data.linedata):
        i = int(row[0]) - 1
        j = int(row[1]) - 1
        r = float(row[2])
        x = float(row[3])
        b_half = float(row[4]) if data.linedata.shape[1] >= 5 else 0.0
        tap = float(row[5]) if data.linedata.shape[1] >= 6 else 1.0
        if abs(tap) < 1e-15:
            tap = 1.0

        z = complex(r, x)
        if abs(z) < 1e-15:
            raise ZeroDivisionError(f"Ligne {k + 1}: impédance nulle.")

        y = 1 / z
        y_sh = 1j * b_half
        Iij = (V[i] / tap - V[j]) * y + (V[i] / (tap**2)) * y_sh
        Iji = (V[j] - V[i] / tap) * y + V[j] * y_sh
        Sij = V[i] * np.conj(Iij) * data.basemva
        Sji = V[j] * np.conj(Iji) * data.basemva

        flows.append({
            "line": k + 1,
            "from_bus": i + 1,
            "to_bus": j + 1,
            "P_from_to": float(Sij.real),
            "Q_from_to": float(Sij.imag),
            "P_to_from": float(Sji.real),
            "Q_to_from": float(Sji.imag),
            "P_loss": float((Sij + Sji).real),
            "Q_loss": float((Sij + Sji).imag),
        })
    return flows


def format_power_flow_results(data, V, method, iterations, converged, history, max_error=None):
    data.Ybus = data.ensure_ybus()
    Pg, Qg, Pc, Qc = calculate_loads_generations(data, V)
    losses_p, losses_q = calculate_losses(data, V)
    history_arr = np.asarray(history, dtype=float)
    if max_error is None:
        max_error = float(history_arr[-1]) if history_arr.size else np.nan

    result = {
        "method": method,
        "V": V,
        "Vm": np.abs(V),
        "Va": np.rad2deg(np.angle(V)),
        "Pg": Pg,
        "Qg": Qg,
        "Pc": Pc,
        "Qc": Qc,
        "iterations": int(iterations),
        "converged": bool(converged),
        "max_error": float(max_error),
        "losses_p": losses_p,
        "losses_q": losses_q,
        "convergence_history": history_arr,
    }
    data.V = V
    data.Pg = Pg
    data.Qg = Qg
    data.Pc = Pc
    data.Qc = Qc
    data.results[method] = result
    return result
