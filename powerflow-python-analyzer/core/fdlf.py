

from __future__ import annotations
import numpy as np

from .power_results import (
    convert_bus_types,
    specified_power_pu,
    format_power_flow_results,
)


def fast_decoupled_load_flow(data, tol=1e-5, maxiter=100):
\
\
\
\
\
\

    Ybus = data.ensure_ybus()
    busdata = data.busdata
    n = data.nbus

    B_full = -np.imag(Ybus)

    bus_type = convert_bus_types(busdata)
    idx_slack = np.where(bus_type == 1)[0]
    idx_noslack = np.array([i for i in range(n) if i not in idx_slack], dtype=int)
    idx_pq = np.where(bus_type == 0)[0]

    Vm = busdata[:, 2].astype(float).copy()
    Va = np.deg2rad(busdata[:, 3].astype(float)).copy()

    P_spec, Q_spec = specified_power_pu(busdata, data.basemva)


    Bp_full = B_full.copy()
    for i in range(n):
        Bp_full[i, i] = 0.0
        Bp_full[i, i] = -np.sum(Bp_full[i, :])

    Bp = Bp_full[np.ix_(idx_noslack, idx_noslack)]
    Bpp = B_full[np.ix_(idx_pq, idx_pq)]

    history = []
    converged = False
    err = np.inf

    if len(idx_noslack) == 0:
        raise ValueError("Aucun bus non-slack : FDLF impossible.")

    for iteration in range(1, maxiter + 1):
        V = Vm * np.exp(1j * Va)
        S_cal = V * np.conj(Ybus @ V)
        P_cal = S_cal.real

        dP = P_spec[idx_noslack] - P_cal[idx_noslack]
        bP = dP / Vm[idx_noslack]
        dTheta = np.linalg.solve(Bp, bP)
        Va[idx_noslack] += dTheta

        V = Vm * np.exp(1j * Va)
        S_cal = V * np.conj(Ybus @ V)
        Q_cal = S_cal.imag

        dQ = Q_spec[idx_pq] - Q_cal[idx_pq]

        if len(idx_pq) > 0:
            bQ = dQ / Vm[idx_pq]
            dV = np.linalg.solve(Bpp, bQ)
            Vm[idx_pq] += dV
            max_dQ = float(np.max(np.abs(dQ)))
        else:
            max_dQ = 0.0

        max_dP = float(np.max(np.abs(dP))) if dP.size else 0.0
        err = max(max_dP, max_dQ)
        history.append(err)

        if err < tol:
            converged = True
            break

        if err > 1e10:
            raise RuntimeError(
                f"Divergence FDLF détectée à l'itération {iteration}. "
                "Vérifie le ratio R/X des lignes."
            )

    V = Vm * np.exp(1j * Va)
    return format_power_flow_results(
        data=data,
        V=V,
        method="Fast Decoupled Load Flow",
        iterations=iteration,
        converged=converged,
        history=history,
        max_error=err,
    )
