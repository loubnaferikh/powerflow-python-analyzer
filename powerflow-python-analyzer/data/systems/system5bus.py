\
\
\
\
\
\


from __future__ import annotations
import numpy as np

name = "system5bus"
source_file = "system5bus.m"

nbus = 5
npq = 2
npv = 2
ns = 1
nbr = 7
basemva = 100.0
accuracy = 0.0001
accel = 1.8
maxiter = 100
Hz = None

busdata = np.array([
    [1.0, 1.0, 1.06, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 50.0, 0.0],
    [2.0, 2.0, 1.045, 0.0, 20.0, 10.0, 40.0, 30.0, 10.0, 50.0, 0.0],
    [3.0, 2.0, 1.03, 0.0, 20.0, 15.0, 30.0, 10.0, 10.0, 40.0, 0.0],
    [4.0, 0.0, 1.0, 0.0, 50.0, 30.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [5.0, 0.0, 1.0, 0.0, 60.0, 40.0, 0.0, 0.0, 0.0, 0.0, 0.0],
], dtype=float)

linedata = np.array([
    [1.0, 2.0, 0.02, 0.06, 0.03, 1.0],
    [1.0, 3.0, 0.08, 0.24, 0.025, 1.0],
    [2.0, 3.0, 0.06, 0.18, 0.02, 1.0],
    [2.0, 4.0, 0.06, 0.18, 0.02, 1.0],
    [2.0, 5.0, 0.04, 0.12, 0.015, 1.0],
    [3.0, 4.0, 0.01, 0.03, 0.01, 1.0],
    [4.0, 5.0, 0.08, 0.24, 0.025, 1.0],
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
