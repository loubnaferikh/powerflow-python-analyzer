

import numpy as np

from data.systems import load_system
from core.ybus import build_ybus
from core.zbus import build_zbus_direct, build_zbus_from_ybus
from core.newton_raphson import newton_raphson_polar
from core.stability import transient_stability


def test_zbus_consistency():
    for name in ["system5bus", "system9bus", "system14bus"]:
        data = load_system(name)
        Y = build_ybus(data.linedata, data.nbus)
        Z_inv = build_zbus_from_ybus(Y)
        Z_direct = build_zbus_direct(data.linedata, data.nbus)
        assert np.max(np.abs(Z_direct - Z_inv)) < 1e-10
        assert np.max(np.abs(Y @ Z_direct - np.eye(data.nbus))) < 1e-10


def test_stability_runs_on_system9():
    data = load_system("system9bus")
    newton_raphson_polar(data, tol=1e-3, maxiter=100)
    result = transient_stability(
        data,
        fault_bus=1,
        fault_line=1,
        clearing_time=0.2,
        simulation_time=0.5,
        dt=0.01,
        method="euler",
    )
    assert "delta" in result
    assert "omega" in result
    assert result["delta"].shape[0] == data.gendata.shape[0]
    assert result["omega"].shape == result["delta"].shape


if __name__ == "__main__":
    test_zbus_consistency()
    test_stability_runs_on_system9()
    print("Tests corrections OK")
