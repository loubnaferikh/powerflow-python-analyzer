\
\
\
\
\
\


from __future__ import annotations

from pathlib import Path
import importlib.util
import re
import numpy as np

from core.power_system_data import PowerSystemData


PROJECT_DIR = Path(__file__).resolve().parent.parent
SYSTEMS_DIR = PROJECT_DIR / "data" / "systems"


def _strip_comments(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        cleaned.append(line.split("%", 1)[0])
    return "\n".join(cleaned)


def _extract_scalar(text: str, name: str, default: float | None = None) -> float | None:
    m = re.search(rf"\b{name}\s*=\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*;", text)
    if not m:
        return default
    return float(m.group(1))


def _extract_matrix(text: str, name: str) -> np.ndarray | None:
    pattern = rf"\b{name}\s*=\s*\[(.*?)\]\s*;"
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return None

    block = m.group(1).replace("...", " ")
    rows: list[list[float]] = []
    for physical_line in block.splitlines():
        line = physical_line.strip().strip(";")
        if not line:
            continue
        parts = [part.strip() for part in line.split(";") if part.strip()]
        for part in parts:
            values = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", part)
            if values:
                rows.append([float(v) for v in values])

    if not rows:
        return None

    max_len = max(len(r) for r in rows)
    padded = [r + [0.0] * (max_len - len(r)) for r in rows]
    return np.asarray(padded, dtype=float)


def load_python_system(path: str | Path) -> PowerSystemData:
\
\
\
\


    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    if not path.name.startswith("system") or path.suffix.lower() != ".py":
        raise ValueError("Choisissez un fichier Python converti de type system*.py.")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible d'importer {path.name}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "create_data"):
        data = module.create_data()
    else:
        if not hasattr(module, "busdata") or not hasattr(module, "linedata"):
            raise ValueError(f"{path.name} doit contenir busdata et linedata.")
        data = PowerSystemData(
            busdata=module.busdata,
            linedata=module.linedata,
            gendata=getattr(module, "gendata", None),
            basemva=getattr(module, "basemva", 100.0),
        )

    data.results["source_file"] = str(path)
    data.results["accuracy"] = float(getattr(module, "accuracy", data.results.get("accuracy", 1e-3)))
    data.results["accel"] = float(getattr(module, "accel", data.results.get("accel", 1.6)))
    data.results["maxiter"] = int(getattr(module, "maxiter", data.results.get("maxiter", 100)))
    hz = getattr(module, "Hz", None)
    if hz is not None:
        data.results["Hz"] = float(hz)
    return data


def load_matlab_system(path: str | Path) -> PowerSystemData:


    path = Path(path)
    text = _strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    busdata = _extract_matrix(text, "busdata")
    linedata = _extract_matrix(text, "linedata")
    gendata = _extract_matrix(text, "gendata")

    if busdata is None:
        raise ValueError("Le fichier ne contient pas de matrice busdata=[...].")
    if linedata is None:
        raise ValueError("Le fichier ne contient pas de matrice linedata=[...].")

    basemva = _extract_scalar(text, "basemva", 100.0) or 100.0
    data = PowerSystemData(busdata=busdata, linedata=linedata, gendata=gendata, basemva=basemva)
    data.results["source_file"] = str(path)
    data.results["accuracy"] = _extract_scalar(text, "accuracy", 1e-3) or 1e-3
    data.results["accel"] = _extract_scalar(text, "accel", 1.6) or 1.6
    data.results["maxiter"] = int(_extract_scalar(text, "maxiter", 100) or 100)
    return data


def load_system(path: str | Path) -> PowerSystemData:


    path = Path(path)
    if path.suffix.lower() == ".py":
        return load_python_system(path)
    if path.suffix.lower() == ".m":
        return load_matlab_system(path)
    raise ValueError("Format non supporté. Utilisez system*.py ou system*.m.")


def list_builtin_system_files() -> list[Path]:


    SYSTEMS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in SYSTEMS_DIR.glob("system*.py") if p.name != "__init__.py")
