\
\
\
\
\
\


from __future__ import annotations
import numpy as np

name = "system6bus"
source_file = "system6bus.m"

nbus = 6
npq = 3
npv = 2
ns = 1
nbr = 7
basemva = 100.0
accuracy = 0.0001
accel = 1.8
maxiter = 100
Hz = None

busdata = np.array([
    [1.0, 1.0, 1.06, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [2.0, 2.0, 1.04, 0.0, 0.0, 0.0, 150.0, 0.0, 0.0, 140.0, 0.0],
    [3.0, 2.0, 1.03, 0.0, 0.0, 0.0, 100.0, 0.0, 0.0, 90.0, 0.0],
    [4.0, 0.0, 1.0, 0.0, 100.0, 70.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [5.0, 0.0, 1.0, 0.0, 90.0, 30.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [6.0, 0.0, 1.0, 0.0, 160.0, 110.0, 0.0, 0.0, 0.0, 0.0, 0.0],
], dtype=float)

linedata = np.array([
    [1.0, 4.0, 0.035, 0.225, 0.0065, 1.0],
    [1.0, 5.0, 0.025, 0.105, 0.0045, 1.0],
    [1.0, 6.0, 0.04, 0.215, 0.0055, 1.0],
    [2.0, 4.0, 0.0, 0.035, 0.0, 1.0],
    [3.0, 5.0, 0.0, 0.042, 0.0, 1.0],
    [4.0, 6.0, 0.028, 0.125, 0.0035, 1.0],
    [5.0, 6.0, 0.026, 0.175, 0.03, 1.0],
], dtype=float)

gendata = np.array([
    [1.0, 0.0, 0.2, 20.0],
    [2.0, 0.0, 0.15, 4.0],
    [3.0, 0.0, 0.25, 5.0],
], dtype=float)


def create_data():

    from core.power_system_data import PowerSystemData
    return PowerSystemData(
        busdata=busdata.copy(),
        linedata=linedata.copy(),
        gendata=None if gendata is None else gendata.copy(),
        basemva=basemva,
    )
