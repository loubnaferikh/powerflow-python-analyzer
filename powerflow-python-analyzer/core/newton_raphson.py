

from __future__ import annotations
import numpy as np

from .power_results import (
    convert_bus_types,
    specified_power_pu,
    initial_voltage,
    format_power_flow_results,
)


def _solve_linear(J: np.ndarray, rhs: np.ndarray, method_name: str) -> np.ndarray:
    try:
        return np.linalg.solve(J, rhs)
    except np.linalg.LinAlgError as exc:
        raise np.linalg.LinAlgError(
            f"Jacobienne singulière ou mal conditionnée dans {method_name}."
        ) from exc


def newton_raphson_rectangular(data, tol=1e-5, maxiter=100):

    Ybus = data.ensure_ybus()
    busdata = data.busdata
    n = data.nbus

    G = np.real(Ybus)
    B = -np.imag(Ybus)

    bus_type = convert_bus_types(busdata)
    idx_slack = np.where(bus_type == 1)[0]
    idx_autres = np.array([i for i in range(n) if i not in idx_slack], dtype=int)
    idx_pq = np.where(bus_type == 0)[0]
    idx_pv = np.where(bus_type == 2)[0]

    V0 = initial_voltage(busdata)
    e = np.real(V0).copy()
    f = np.imag(V0).copy()

    P_spec, Q_spec = specified_power_pu(busdata, data.basemva)
    V2_spec = busdata[:, 2] ** 2

    history = []
    converged = False
    err = np.inf
    P_cal = np.zeros(n)
    Q_cal = np.zeros(n)

    for iteration in range(1, maxiter + 1):
        c = np.zeros(n)
        d = np.zeros(n)

        for i in range(n):
            for j in range(n):
                c[i] += G[i, j] * e[j] + B[i, j] * f[j]
                d[i] += G[i, j] * f[j] - B[i, j] * e[j]

        P_cal = e * c + f * d
        Q_cal = f * c - e * d

        deltaP = P_spec - P_cal
        deltaQ = Q_spec - Q_cal
        deltaV2 = V2_spec - (e**2 + f**2)

        mismatch = np.concatenate([deltaP[idx_autres], deltaQ[idx_pq], deltaV2[idx_pv]])
        err = float(np.max(np.abs(mismatch))) if mismatch.size else 0.0
        history.append(err)

        if err < tol:
            converged = True
            break

        J1 = np.zeros((n, n))
        J2 = np.zeros((n, n))
        J3 = np.zeros((n, n))
        J4 = np.zeros((n, n))

        for i in range(n):
            J1[i, i] = (e[i] * G[i, i] - f[i] * B[i, i]) + c[i]
            J2[i, i] = (e[i] * B[i, i] + f[i] * G[i, i]) + d[i]
            J3[i, i] = (e[i] * B[i, i] + f[i] * G[i, i]) - d[i]
            J4[i, i] = -(e[i] * G[i, i] - f[i] * B[i, i]) + c[i]

            for j in range(n):
                if i != j:
                    J1[i, j] = e[i] * G[i, j] - f[i] * B[i, j]
                    J2[i, j] = e[i] * B[i, j] + f[i] * G[i, j]
                    J3[i, j] = e[i] * B[i, j] + f[i] * G[i, j]
                    J4[i, j] = -(e[i] * G[i, j] - f[i] * B[i, j])

        J5 = np.diag(2 * e)
        J6 = np.diag(2 * f)

        J_red = np.vstack([
            np.hstack([J1[np.ix_(idx_autres, idx_autres)], J2[np.ix_(idx_autres, idx_autres)]]),
            np.hstack([J3[np.ix_(idx_pq, idx_autres)], J4[np.ix_(idx_pq, idx_autres)]]),
            np.hstack([J5[np.ix_(idx_pv, idx_autres)], J6[np.ix_(idx_pv, idx_autres)]]),
        ])

        dX = _solve_linear(J_red, mismatch, "Newton-Raphson rectangulaire")
        n_inc = len(idx_autres)
        e[idx_autres] += dX[:n_inc]
        f[idx_autres] += dX[n_inc:]

    V = e + 1j * f
    return format_power_flow_results(
        data=data,
        V=V,
        method="Newton-Raphson Rectangular",
        iterations=iteration,
        converged=converged,
        history=history,
        max_error=err,
    )


def _calc_pq_polar(Ybus, Vm, Va):
    n = len(Vm)
    G = np.real(Ybus)
    B = np.imag(Ybus)

    P = np.zeros(n)
    Q = np.zeros(n)

    for i in range(n):
        for j in range(n):
            theta_ij = Va[i] - Va[j]
            P[i] += Vm[i] * Vm[j] * (G[i, j] * np.cos(theta_ij) + B[i, j] * np.sin(theta_ij))
            Q[i] += Vm[i] * Vm[j] * (G[i, j] * np.sin(theta_ij) - B[i, j] * np.cos(theta_ij))

    return P, Q


def newton_raphson_polar(data, tol=1e-5, maxiter=100):
\
\
\

    Ybus = data.ensure_ybus()
    busdata = data.busdata
    n = data.nbus

    G = np.real(Ybus)
    B = np.imag(Ybus)

    bus_type = convert_bus_types(busdata)
    idx_slack = np.where(bus_type == 1)[0]
    idx_autres = np.array([i for i in range(n) if i not in idx_slack], dtype=int)
    idx_pq = np.where(bus_type == 0)[0]

    Vm = busdata[:, 2].astype(float).copy()
    Va = np.deg2rad(busdata[:, 3].astype(float)).copy()

    P_spec, Q_spec = specified_power_pu(busdata, data.basemva)

    history = []
    converged = False
    err = np.inf

    for iteration in range(1, maxiter + 1):
        P_cal, Q_cal = _calc_pq_polar(Ybus, Vm, Va)

        deltaP = P_spec[idx_autres] - P_cal[idx_autres]
        deltaQ = Q_spec[idx_pq] - Q_cal[idx_pq]
        mismatch = np.concatenate([deltaP, deltaQ])

        err = float(np.max(np.abs(mismatch))) if mismatch.size else 0.0
        history.append(err)

        if err < tol:
            converged = True
            break

        H = np.zeros((n, n))
        N = np.zeros((n, n))
        M = np.zeros((n, n))
        L = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                theta_ij = Va[i] - Va[j]
                if i != j:
                    H[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.sin(theta_ij) - B[i, j] * np.cos(theta_ij))
                    N[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.cos(theta_ij) + B[i, j] * np.sin(theta_ij))
                    M[i, j] = -Vm[i] * Vm[j] * (G[i, j] * np.cos(theta_ij) + B[i, j] * np.sin(theta_ij))
                    L[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.sin(theta_ij) - B[i, j] * np.cos(theta_ij))
                else:
                    H[i, i] = -Q_cal[i] - B[i, i] * Vm[i] ** 2
                    N[i, i] = P_cal[i] + G[i, i] * Vm[i] ** 2
                    M[i, i] = P_cal[i] - G[i, i] * Vm[i] ** 2
                    L[i, i] = Q_cal[i] - B[i, i] * Vm[i] ** 2

        for i in range(n):
            if abs(Vm[i]) < 1e-15:
                raise ZeroDivisionError(f"Bus {i + 1}: module de tension nul.")
            N[:, i] = N[:, i] / Vm[i]
            L[:, i] = L[:, i] / Vm[i]

        J_red = np.vstack([
            np.hstack([H[np.ix_(idx_autres, idx_autres)], N[np.ix_(idx_autres, idx_pq)]]),
            np.hstack([M[np.ix_(idx_pq, idx_autres)], L[np.ix_(idx_pq, idx_pq)]]),
        ])

        dX = _solve_linear(J_red, mismatch, "Newton-Raphson polaire")
        n_ang = len(idx_autres)
        Va[idx_autres] += dX[:n_ang]
        Vm[idx_pq] += dX[n_ang:]

    V = Vm * np.exp(1j * Va)
    return format_power_flow_results(
        data=data,
        V=V,
        method="Newton-Raphson Polar",
        iterations=iteration,
        converged=converged,
        history=history,
        max_error=err,
    )


def newton_raphson_v2(data, tol=1e-5, maxiter=100):
\
\
\
\
\

    Ybus = data.ensure_ybus()
    busdata = data.busdata
    n = data.nbus

    G = np.real(Ybus)
    B = np.imag(Ybus)

    bus_type = convert_bus_types(busdata)
    idx_slack = np.where(bus_type == 1)[0]
    idx_autres = np.array([i for i in range(n) if i not in idx_slack], dtype=int)
    idx_pq = np.where(bus_type == 0)[0]
    idx_pv = np.where(bus_type == 2)[0]

    Vm = busdata[:, 2].astype(float).copy()
    Va = np.deg2rad(busdata[:, 3].astype(float)).copy()

    P_spec, Q_spec = specified_power_pu(busdata, data.basemva)
    V2_spec = busdata[:, 2] ** 2

    history = []
    converged = False
    err = np.inf

    for iteration in range(1, maxiter + 1):
        P_cal, Q_cal = _calc_pq_polar(Ybus, Vm, Va)

        deltaP = P_spec - P_cal
        deltaQ = Q_spec - Q_cal
        deltaV2 = V2_spec - Vm**2

        mismatch = np.concatenate([deltaP[idx_autres], deltaQ[idx_pq], deltaV2[idx_pv]])
        err = float(np.max(np.abs(mismatch))) if mismatch.size else 0.0
        history.append(err)

        if err < tol:
            converged = True
            break

        J1 = np.zeros((n, n))
        J2 = np.zeros((n, n))
        J3 = np.zeros((n, n))
        J4 = np.zeros((n, n))
        J5 = np.zeros((n, n))
        J6 = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                theta_ij = Va[i] - Va[j]
                if i != j:
                    J1[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.sin(theta_ij) - B[i, j] * np.cos(theta_ij))
                    J3[i, j] = -Vm[i] * Vm[j] * (G[i, j] * np.cos(theta_ij) + B[i, j] * np.sin(theta_ij))
                    J2[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.cos(theta_ij) + B[i, j] * np.sin(theta_ij))
                    J4[i, j] = Vm[i] * Vm[j] * (G[i, j] * np.sin(theta_ij) - B[i, j] * np.cos(theta_ij))
                else:
                    J1[i, i] = -Q_cal[i] - B[i, i] * Vm[i] ** 2
                    J2[i, i] = P_cal[i] + G[i, i] * Vm[i] ** 2
                    J3[i, i] = P_cal[i] - G[i, i] * Vm[i] ** 2
                    J4[i, i] = Q_cal[i] - B[i, i] * Vm[i] ** 2
                    J5[i, i] = 0.0
                    J6[i, i] = 2 * Vm[i] ** 2

        J_red = np.vstack([
            np.hstack([J1[np.ix_(idx_autres, idx_autres)], J2[np.ix_(idx_autres, idx_autres)]]),
            np.hstack([J3[np.ix_(idx_pq, idx_autres)], J4[np.ix_(idx_pq, idx_autres)]]),
            np.hstack([J5[np.ix_(idx_pv, idx_autres)], J6[np.ix_(idx_pv, idx_autres)]]),
        ])

        dX = _solve_linear(J_red, mismatch, "Newton-Raphson V2")
        n_inc = len(idx_autres)
        Va[idx_autres] += dX[:n_inc]
        Vm[idx_autres] += dX[n_inc:] * Vm[idx_autres]

    V = Vm * np.exp(1j * Va)
    return format_power_flow_results(
        data=data,
        V=V,
        method="Newton-Raphson V2",
        iterations=iteration,
        converged=converged,
        history=history,
        max_error=err,
    )
