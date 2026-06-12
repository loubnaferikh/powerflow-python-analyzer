

from __future__ import annotations
from importlib import import_module

SYSTEMS = {
    "system10bus": "data.systems.system10bus",
    "system118bus": "data.systems.system118bus",
    "system11bus": "data.systems.system11bus",
    "system14bus": "data.systems.system14bus",
    "system26bus": "data.systems.system26bus",
    "system30bus": "data.systems.system30bus",
    "system3bus": "data.systems.system3bus",
    "system47bus": "data.systems.system47bus",
    "system57bus": "data.systems.system57bus",
    "system5bus": "data.systems.system5bus",
    "system5buscours": "data.systems.system5buscours",
    "system68bus": "data.systems.system68bus",
    "system6bus": "data.systems.system6bus",
    "system9bus": "data.systems.system9bus",
}


def load_system(name: str):

    key = name.lower().replace(".py", "")
    if key not in SYSTEMS:
        raise KeyError(f"Système inconnu: {name}. Disponibles: {', '.join(SYSTEMS)}")
    module = import_module(SYSTEMS[key])
    return module.create_data()
