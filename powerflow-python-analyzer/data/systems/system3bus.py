\
\
\
\
\
\


from __future__ import annotations
import numpy as np

name = "system3bus"
source_file = "system3bus.m"

nbus = 3
npq = 1
npv = 1
ns = 1
nbr = 3
basemva = 100.0
accuracy = 0.0001
accel = 1.8
maxiter = 100
Hz = None

busdata = np.array([
    [1.0, 1.0, 1.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [2.0, 0.0, 1.0, 0.0, 400.0, 250.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [3.0, 2.0, 1.04, 0.0, 0.0, 0.0, 200.0, 0.0, 0.0, 0.0, 0.0],
], dtype=float)

linedata = np.array([
    [1.0, 2.0, 0.02, 0.04, 0.0, 1.0],
    [1.0, 3.0, 0.01, 0.03, 0.0, 1.0],
    [2.0, 3.0, 0.0125, 0.025, 0.0, 1.0],
], dtype=float)

gendata = None


def create_data():

    from core.power_system_data import PowerSystemData
    return PowerSystemData(
        busdata=busdata.copy(),
        linedata=linedata.copy(),
        gendata=None if gendata is None else gendata.copy(),
        basemva=basemva,
    )
