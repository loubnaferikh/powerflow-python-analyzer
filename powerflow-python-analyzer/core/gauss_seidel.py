

from __future__ import annotations
import numpy as np

from .power_results import (
    convert_bus_types,
    initial_voltage,
    specified_power_pu,
    calculate_power_injections,
    format_power_flow_results,
)


def gauss_seidel_power_flow(data, tol=1e-5, accel=1.6, maxiter=1000):
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

    Ybus = data.ensure_ybus()
    busdata = data.busdata
    nbus = data.nbus

    bus_type = convert_bus_types(busdata)
    V = initial_voltage(busdata).astype(complex)
    P_spec, Q_spec = specified_power_pu(busdata, data.basemva)

    history = []
    converged = False
    error_val = np.inf

    for iteration in range(1, maxiter + 1):
        V_old = V.copy()

        for i in range(nbus):
            if bus_type[i] == 1:
                continue

            if bus_type[i] == 2:
                sum_yv = Ybus[i, :] @ V
                Q_spec[i] = -np.imag(np.conj(V[i]) * sum_yv)

            sum_extra = Ybus[i, :] @ V - Ybus[i, i] * V[i]
            V_temp = (
                ((P_spec[i] - 1j * Q_spec[i]) / np.conj(V[i]) - sum_extra)
                / Ybus[i, i]
            )

            if bus_type[i] == 0:
                V[i] = V[i] + accel * (V_temp - V[i])
            elif bus_type[i] == 2:
                if abs(V_temp) < 1e-15:
                    raise ZeroDivisionError(f"Bus PV {i + 1}: tension temporaire nulle.")
                V[i] = busdata[i, 2] * V_temp / abs(V_temp)

        error_val = float(np.max(np.abs(V - V_old)))
        history.append(error_val)

        if error_val < tol:
            converged = True
            break

    return format_power_flow_results(
        data=data,
        V=V,
        method="Gauss-Seidel",
        iterations=iteration,
        converged=converged,
        history=history,
        max_error=error_val,
    )


if __name__ == "__main__":
    from .power_system_data import PowerSystemData

    busdata = np.array([
        [1, 3, 1.06, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 1.04, 0, 20, 10, 40, 0, 0, 0, 0],
        [3, 1, 1.00, 0, 45, 15, 0, 0, 0, 0, 0],
    ], dtype=float)
    linedata = np.array([
        [1, 2, 0.02, 0.06, 0.03, 1],
        [1, 3, 0.08, 0.24, 0.025, 1],
        [2, 3, 0.06, 0.18, 0.02, 1],
    ], dtype=float)

    data = PowerSystemData(busdata=busdata, linedata=linedata)
    print(gauss_seidel_power_flow(data))
