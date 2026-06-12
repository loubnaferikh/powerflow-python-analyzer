\
\
\
\
\


from __future__ import annotations

from typing import Literal
import numpy as np

from .power_results import calculate_power_injections, get_power_columns, initial_voltage

IntegrationMethod = Literal["euler", "rk4"]


def _require_gendata(data) -> np.ndarray:
    if data.gendata is None:
        raise ValueError("gendata est obligatoire pour la stabilité transitoire.")
    gendata = np.asarray(data.gendata, dtype=float)
    if gendata.ndim != 2 or gendata.shape[1] < 4:
        raise ValueError("gendata doit contenir au moins 4 colonnes : [GenBus, Ra, Xd', H].")
    return gendata


def _power_to_pu_like_matlab(values: np.ndarray, basemva: float) -> np.ndarray:

    arr = np.asarray(values, dtype=float).reshape(-1)
    if arr.size and np.max(np.abs(arr)) > 50:
        return arr / basemva
    return arr.copy()


def _get_initial_state_like_matlab(data) -> tuple[np.ndarray, np.ndarray, np.ndarray]:


    nbus = data.busdata.shape[0]

    if data.V is None:
        V0 = initial_voltage(data.busdata).astype(complex)
    else:
        V0 = np.asarray(data.V, dtype=complex).reshape(-1)

    if V0.size < nbus:
        V0 = np.pad(V0, (0, nbus - V0.size), constant_values=1 + 0j)
    V0 = V0[:nbus]

    if data.Pg is not None:
        Pg_raw = np.asarray(data.Pg, dtype=float).reshape(-1)
    else:
        if data.Ybus is None:
            data.Ybus = data.ensure_ybus()
        P_inj, _ = calculate_power_injections(data.Ybus, V0)
        pc, _, _, _, _ = get_power_columns(data.busdata)
        Pg_raw = (P_inj + pc / data.basemva) * data.basemva

    if data.Qg is not None:
        Qg_raw = np.asarray(data.Qg, dtype=float).reshape(-1)
    else:
        if data.Ybus is None:
            data.Ybus = data.ensure_ybus()
        _, Q_inj = calculate_power_injections(data.Ybus, V0)
        _, qc, _, _, qsh = get_power_columns(data.busdata)
        Qg_raw = (Q_inj + qc / data.basemva - qsh / data.basemva) * data.basemva

    if Pg_raw.size < nbus:
        Pg_raw = np.pad(Pg_raw, (0, nbus - Pg_raw.size))
    if Qg_raw.size < nbus:
        Qg_raw = np.pad(Qg_raw, (0, nbus - Qg_raw.size))

    Pg_pu = _power_to_pu_like_matlab(Pg_raw[:nbus], data.basemva)
    Qg_pu = _power_to_pu_like_matlab(Qg_raw[:nbus], data.basemva)

    return V0, Pg_pu, Qg_pu


def _loads_as_admittance_like_matlab(busdata: np.ndarray, basemva: float, V0: np.ndarray) -> np.ndarray:
    P_load = busdata[:, 4] / basemva
    Q_load = busdata[:, 5] / basemva
    V_mag = np.abs(V0)
    with np.errstate(divide="ignore", invalid="ignore"):
        Y_load = (P_load - 1j * Q_load) / (V_mag**2)
    Y_load[~np.isfinite(Y_load)] = 0.0
    return Y_load.astype(complex)


def _build_network_y_temp_like_matlab(linedata: np.ndarray, nbus: int) -> np.ndarray:
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

    Y_temp = np.zeros((nbus, nbus), dtype=complex)
    linedata = np.asarray(linedata, dtype=float)

    for k, row in enumerate(linedata):
        nl = int(row[0]) - 1
        nr = int(row[1]) - 1
        if nl < 0 or nr < 0 or nl >= nbus or nr >= nbus:
            raise ValueError(f"Ligne {k + 1}: bus invalide ({int(row[0])}, {int(row[1])}).")

        R = float(row[2])
        X = float(row[3])
        Bc = 1j * (float(row[4]) if linedata.shape[1] >= 5 else 0.0)
        a = float(row[5]) if linedata.shape[1] >= 6 else 1.0

        if a == 0:
            a = 1.0
        if X == 0:
            X = 1e-6

        z = R + 1j * X
        if abs(z) < 1e-15:
            raise ZeroDivisionError(f"Ligne {k + 1}: R+jX nul.")
        y = 1.0 / z

        Y_temp[nl, nl] += y / (a**2) + Bc
        Y_temp[nr, nr] += y + Bc
        Y_temp[nl, nr] -= y / a
        Y_temp[nr, nl] -= y / a

    return Y_temp


def _reduced_y_like_matlab(
    busdata: np.ndarray,
    current_linedata: np.ndarray,
    gendata: np.ndarray,
    basemva: float,
    V0: np.ndarray,
    fault_bus: int,
    is_fault: bool,
    fault_admittance: float = 1e8,
) -> np.ndarray:


    nbus = busdata.shape[0]
    ngen = gendata.shape[0]
    gen_bus = gendata[:, 0].astype(int) - 1
    Xd = gendata[:, 2].astype(float).copy()

    Y_temp = _build_network_y_temp_like_matlab(current_linedata, nbus)

    Y_load = _loads_as_admittance_like_matlab(busdata, basemva, V0)
    for k in range(nbus):
        Y_temp[k, k] += Y_load[k]

    if is_fault and fault_bus > 0 and fault_bus <= nbus:
        Y_temp[fault_bus - 1, fault_bus - 1] += fault_admittance

    N_tot = nbus + ngen
    Y_aug = np.zeros((N_tot, N_tot), dtype=complex)
    Y_aug[:nbus, :nbus] = Y_temp

    for k in range(ngen):
        g_bus = gen_bus[k]
        if g_bus < 0 or g_bus >= nbus:
            raise ValueError(f"Bus générateur invalide dans gendata ligne {k + 1}.")
        if Xd[k] == 0:
            Xd[k] = 0.001
        y_machine = 1.0 / (1j * Xd[k])
        internal = nbus + k

        Y_aug[g_bus, g_bus] += y_machine
        Y_aug[internal, internal] = y_machine
        Y_aug[g_bus, internal] = -y_machine
        Y_aug[internal, g_bus] = -y_machine

    Y_NN = Y_aug[:nbus, :nbus]
    Y_ND = Y_aug[:nbus, nbus:]
    Y_DN = Y_aug[nbus:, :nbus]
    Y_DD = Y_aug[nbus:, nbus:]


    try:
        cond = np.linalg.cond(Y_NN)
    except Exception:
        cond = np.inf
    if (not np.isfinite(cond)) or cond > 1e12:
        Y_NN = Y_NN + 1e-8 * np.eye(Y_NN.shape[0], dtype=complex)

    return Y_DD - Y_DN @ np.linalg.solve(Y_NN, Y_ND)


def compute_electrical_power(E0: np.ndarray, delta_cur: np.ndarray, Y_red: np.ndarray) -> np.ndarray:
    E_complex = E0 * np.exp(1j * delta_cur)
    I_gen = Y_red @ E_complex
    return np.real(E_complex * np.conj(I_gen))


def _derivs(
    delta_cur: np.ndarray,
    omega_cur: np.ndarray,
    Y_cur: np.ndarray,
    E0: np.ndarray,
    Pm: np.ndarray,
    H: np.ndarray,
    w_syn: float,
) -> tuple[np.ndarray, np.ndarray]:
    Pe = compute_electrical_power(E0, delta_cur, Y_cur)
    d_delta = (omega_cur - 1.0) * w_syn
    d_omega = (Pm - Pe) / (2.0 * H)
    d_delta[~np.isfinite(d_delta)] = 0.0
    d_omega[~np.isfinite(d_omega)] = 0.0
    return d_delta, d_omega


def transient_stability(
    data,
    fault_bus: int,
    fault_line: int,
    clearing_time: float,
    simulation_time: float,
    dt: float = 0.01,
    method: IntegrationMethod = "euler",
) -> dict:
\
\
\
\
\


    method = str(method).lower()
    if method not in {"euler", "rk4"}:
        raise ValueError("method doit être 'euler' ou 'rk4'.")
    if dt <= 0:
        raise ValueError("dt doit être strictement positif.")
    if simulation_time <= 0:
        raise ValueError("simulation_time doit être strictement positif.")

    busdata = np.asarray(data.busdata, dtype=float)
    linedata = np.asarray(data.linedata, dtype=float)
    gendata = _require_gendata(data)
    basemva = float(data.basemva)

    nbus = busdata.shape[0]
    ngen = gendata.shape[0]
    gen_bus_zero = gendata[:, 0].astype(int) - 1
    Xd = gendata[:, 2].astype(float).copy()
    H = gendata[:, 3].astype(float).copy()

    if np.any(H <= 0):
        raise ValueError("Les constantes H doivent être strictement positives.")


    f0 = getattr(data, "Hz", None)
    if f0 is None:
        f0 = data.results.get("Hz", 60.0) if hasattr(data, "results") else 60.0
    f0 = float(f0)
    w_syn = 2.0 * np.pi * f0

    V0, Pg_pu, Qg_pu = _get_initial_state_like_matlab(data)


    E_prime = np.zeros(ngen, dtype=complex)

    for k in range(ngen):
        ib = gen_bus_zero[k]
        if ib < 0 or ib >= nbus:
            raise ValueError(f"Bus générateur invalide dans gendata ligne {k + 1}.")
        if Xd[k] == 0:
            Xd[k] = 0.001
        if abs(V0[ib]) < 1e-12:
            V0[ib] = 1.0 + 0.0j
        Sg = Pg_pu[ib] + 1j * Qg_pu[ib]
        Ig = np.conj(Sg / V0[ib])
        E_prime[k] = V0[ib] + 1j * Xd[k] * Ig

    E0 = np.abs(E_prime)
    delta0 = np.angle(E_prime)


    Y_pre = _reduced_y_like_matlab(
        busdata, linedata, gendata, basemva, V0, fault_bus=int(fault_bus), is_fault=False
    )
    Pm = compute_electrical_power(E0, delta0, Y_pre)
    Y_fault = _reduced_y_like_matlab(
        busdata, linedata, gendata, basemva, V0, fault_bus=int(fault_bus), is_fault=True
    )

    idx_line = int(fault_line) - 1
    if idx_line < 0 or idx_line >= linedata.shape[0]:
        raise ValueError(f"fault_line={fault_line} invalide. Les lignes vont de 1 à {linedata.shape[0]}.")
    linedata_post = np.delete(linedata, idx_line, axis=0)
    Y_post = _reduced_y_like_matlab(
        busdata, linedata_post, gendata, basemva, V0, fault_bus=int(fault_bus), is_fault=False
    )


    Nt = int(np.floor(simulation_time / dt + 1e-12)) + 1
    t = np.arange(Nt, dtype=float) * dt

    t = t[t <= simulation_time + 1e-12]
    Nt = len(t)

    delta = np.zeros((ngen, Nt), dtype=float)
    omega = np.zeros((ngen, Nt), dtype=float)
    delta[:, 0] = delta0
    omega[:, 0] = 1.0

    Te_eff = min(max(float(clearing_time), 0.0), float(simulation_time))

    def advance_state(delta_cur: np.ndarray, omega_cur: np.ndarray, Y_step: np.ndarray, h: float) -> tuple[np.ndarray, np.ndarray]:
        if h <= 0:
            return delta_cur.copy(), omega_cur.copy()
        if method == "euler":
            d_delta, d_omega = _derivs(delta_cur, omega_cur, Y_step, E0, Pm, H, w_syn)
            return delta_cur + h * d_delta, omega_cur + h * d_omega
        k1_d, k1_w = _derivs(delta_cur, omega_cur, Y_step, E0, Pm, H, w_syn)
        k2_d, k2_w = _derivs(delta_cur + 0.5 * h * k1_d, omega_cur + 0.5 * h * k1_w, Y_step, E0, Pm, H, w_syn)
        k3_d, k3_w = _derivs(delta_cur + 0.5 * h * k2_d, omega_cur + 0.5 * h * k2_w, Y_step, E0, Pm, H, w_syn)
        k4_d, k4_w = _derivs(delta_cur + h * k3_d, omega_cur + h * k3_w, Y_step, E0, Pm, H, w_syn)
        return (
            delta_cur + (h / 6.0) * (k1_d + 2.0 * k2_d + 2.0 * k3_d + k4_d),
            omega_cur + (h / 6.0) * (k1_w + 2.0 * k2_w + 2.0 * k3_w + k4_w),
        )

    for it in range(Nt - 1):
        t_cur = float(t[it])
        t_next = float(t[it + 1])
        delta_cur = delta[:, it].copy()
        omega_cur = omega[:, it].copy()

        if t_next <= Te_eff + 1e-12:
            delta_new, omega_new = advance_state(delta_cur, omega_cur, Y_fault, t_next - t_cur)
        elif t_cur >= Te_eff - 1e-12:
            delta_new, omega_new = advance_state(delta_cur, omega_cur, Y_post, t_next - t_cur)
        else:
            delta_mid, omega_mid = advance_state(delta_cur, omega_cur, Y_fault, Te_eff - t_cur)
            delta_new, omega_new = advance_state(delta_mid, omega_mid, Y_post, t_next - Te_eff)

        if not np.all(np.isfinite(delta_new)) or not np.all(np.isfinite(omega_new)):
            delta_new = delta_cur
            omega_new = omega_cur

        delta[:, it + 1] = delta_new
        omega[:, it + 1] = omega_new

    delta_deg = np.rad2deg(delta)

    max_diff = 0.0
    max_unwrapped_diff = 0.0
    max_speed_deviation = float(np.max(np.abs(omega - 1.0))) if omega.size else 0.0
    delta_coi = np.average(delta, axis=0, weights=H)
    delta_plot_deg = np.rad2deg(delta - delta_coi.reshape(1, -1))

    for i in range(ngen):
        for j in range(i + 1, ngen):
            diff_unwrapped = np.abs(delta_deg[i, :] - delta_deg[j, :])
            max_unwrapped_diff = max(max_unwrapped_diff, float(np.max(diff_unwrapped)))
            diff_wrapped = np.abs((delta_deg[i, :] - delta_deg[j, :] + 180.0) % 360.0 - 180.0)
            max_diff = max(max_diff, float(np.max(diff_wrapped)))

    if ngen == 1:
        max_unwrapped_diff = float(np.max(np.abs(delta_plot_deg))) if delta_plot_deg.size else 0.0
        max_diff = max_unwrapped_diff

    is_stable = bool(max_unwrapped_diff < 180.0 and max_speed_deviation < 1.0)

    result = {
        "time": t,
        "t": t,
        "delta": delta,
        "delta_deg": delta_deg,
        "delta_plot_deg": delta_plot_deg,
        "omega": omega,
        "gen_bus": gendata[:, 0].astype(int),
        "is_stable": bool(is_stable),
        "stable": bool(is_stable),
        "max_angle_diff": float(max_unwrapped_diff),
        "max_angle_diff_wrapped": float(max_diff),
        "max_speed_deviation": float(max_speed_deviation),
        "method": method,
        "message": "Système stable" if is_stable else "Système potentiellement instable",
        "critical_info": {
            "fault_bus": int(fault_bus),
            "fault_line": int(fault_line),
            "clearing_time": float(clearing_time),
            "simulation_time": float(simulation_time),
            "dt": float(dt),
            "E_prime": E_prime,
            "E0": E0,
            "delta0": delta0,
            "Pm": Pm,
            "Pg_pu": Pg_pu,
            "Qg_pu": Qg_pu,
        },
        "Y_pre": Y_pre,
        "Y_fault": Y_fault,
        "Y_post": Y_post,
    }
    data.results["Transient Stability"] = result
    return result


def estimate_critical_clearing_time(
    data,
    fault_bus: int,
    fault_line: int,
    simulation_time: float,
    dt: float = 0.01,
    method: IntegrationMethod = "euler",
    search_min: float = 0.0,
    search_max: float | None = None,
    iterations: int = 12,
) -> dict:
    if search_max is None:
        search_max = simulation_time
    search_min = max(0.0, float(search_min))
    search_max = min(float(search_max), float(simulation_time))
    if search_max <= search_min:
        raise ValueError("Intervalle de recherche du temps critique invalide.")
    cache = {}
    def run_case(tcr: float) -> dict:
        key = round(float(tcr), 10)
        if key not in cache:
            cache[key] = transient_stability(
                data,
                fault_bus=fault_bus,
                fault_line=fault_line,
                clearing_time=float(tcr),
                simulation_time=float(simulation_time),
                dt=float(dt),
                method=method,
            )
        return cache[key]
    low_result = run_case(search_min)
    high_result = run_case(search_max)
    if not low_result.get("stable", False):
        return {"critical_time": None, "lower_stable_time": None, "upper_unstable_time": search_min, "stable_at_min": False, "stable_at_max": high_result.get("stable", False), "iterations": 0, "message": "Même le temps minimal testé est instable.", "cases": cache}
    if high_result.get("stable", False):
        return {"critical_time": search_max, "lower_stable_time": search_max, "upper_unstable_time": None, "stable_at_min": True, "stable_at_max": True, "iterations": 0, "message": "Le système reste stable jusqu'au temps maximal testé.", "cases": cache}
    low = search_min
    high = search_max
    used = 0
    for _ in range(max(1, int(iterations))):
        mid = 0.5 * (low + high)
        mid_result = run_case(mid)
        used += 1
        if mid_result.get("stable", False):
            low = mid
        else:
            high = mid
    return {"critical_time": low, "lower_stable_time": low, "upper_unstable_time": high, "stable_at_min": True, "stable_at_max": False, "iterations": used, "message": f"Temps critique estimé entre {low:.4f} s et {high:.4f} s.", "cases": cache}
