from data.systems.system3bus import create_data
from core.newton_raphson import newton_raphson_polar
from core.fault_analysis import analyze_fault


def main():
    data = create_data()
    newton_raphson_polar(data, tol=1e-4, maxiter=50)
    for fault_type in ["3PH", "LG", "LL", "LLG"]:
        res = analyze_fault(data, fault_bus=2, fault_type=fault_type, zf=0j, zg=0j)
        assert res["ifault_pu"] >= 0
        assert res["V_phase_all"].shape[0] == 3
        assert res["V_phase_all"].shape[1] == data.nbus
    print("Tests analyse des défauts OK")


if __name__ == "__main__":
    main()
