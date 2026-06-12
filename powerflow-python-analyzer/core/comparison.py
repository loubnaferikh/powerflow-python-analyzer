

from __future__ import annotations
import time
from typing import Callable

from .gauss_seidel import gauss_seidel_power_flow
from .newton_raphson import newton_raphson_rectangular, newton_raphson_polar, newton_raphson_v2
from .fdlf import fast_decoupled_load_flow


def run_comparison(data, tol: float = 1e-3, maxiter: int = 100, accel: float = 1.6) -> dict:

    methods: list[tuple[str, Callable[[], dict]]] = [
        ("Gauss-Seidel", lambda: gauss_seidel_power_flow(data, tol=tol, accel=accel, maxiter=maxiter)),
        ("NR rect.", lambda: newton_raphson_rectangular(data, tol=tol, maxiter=maxiter)),
        ("NR polaire", lambda: newton_raphson_polar(data, tol=tol, maxiter=maxiter)),
        ("NR V2", lambda: newton_raphson_v2(data, tol=tol, maxiter=maxiter)),
        ("FDLF", lambda: fast_decoupled_load_flow(data, tol=tol, maxiter=maxiter)),
    ]
    rows = []
    results = {}
    for name, runner in methods:
        start = time.perf_counter()
        try:
            res = runner()
            elapsed = time.perf_counter() - start
            results[name] = res
            pg_sum = float(res["Pg"].sum()) if "Pg" in res else 0.0
            loss_pct = 100.0 * float(res.get("losses_p", 0.0)) / pg_sum if abs(pg_sum) > 1e-12 else 0.0
            rows.append({
                "method": name,
                "iterations": int(res.get("iterations", 0)),
                "time_s": elapsed,
                "converged": bool(res.get("converged", False)),
                "vm_mean": float(res["Vm"].mean()),
                "losses_p": float(res.get("losses_p", 0.0)),
                "loss_pct": loss_pct,
                "error": "",
            })
        except Exception as exc:
            elapsed = time.perf_counter() - start
            rows.append({
                "method": name,
                "iterations": 0,
                "time_s": elapsed,
                "converged": False,
                "vm_mean": 0.0,
                "losses_p": 0.0,
                "loss_pct": 0.0,
                "error": str(exc),
            })
    return {"rows": rows, "results": results}
