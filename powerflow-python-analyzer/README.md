# PowerFlow Python Analyzer

A desktop Python application for power-system analysis and electrical network studies.  
The project provides a PySide6 graphical interface and numerical modules for admittance/impedance matrices, load-flow studies, method comparison, transient stability analysis, fault analysis, and PDF report generation.

## Features

- **Network matrices**: construction of `Ybus`, `Zbus`, and validation of `Ybus × Zbus`.
- **Power flow methods**:
  - Gauss-Seidel;
  - Newton-Raphson rectangular formulation;
  - Newton-Raphson polar formulation;
  - second Newton-Raphson formulation;
  - Fast Decoupled Load Flow, FDLF.
- **Method comparison**: voltage profile, active losses, convergence and execution time.
- **Fault analysis**:
  - three-phase fault;
  - line-to-ground fault;
  - line-to-line fault;
  - double-line-to-ground fault.
- **Transient stability**:
  - Euler predictor-corrector;
  - fourth-order Runge-Kutta method;
  - critical clearing time estimation.
- **PDF export**: automatic generation of a report from the available results.
- **Built-in test systems**: 3-bus, 5-bus, 6-bus, 9-bus, 10-bus, 11-bus, 14-bus, 26-bus, 30-bus, 47-bus, 57-bus, 68-bus and 118-bus systems.

## Project structure

```text
powerflow-python-analyzer/
├── core/                 # Numerical algorithms and electrical calculations
├── data/                 # Data loader and built-in power-system test cases
│   └── systems/          # Predefined bus systems
├── tests/                # Unit tests
├── ui/                   # PySide6 graphical interface
├── utils/                # Formatting helpers
├── main.py               # Application entry point
├── requirements.txt      # Runtime dependencies
└── requirements-dev.txt  # Development and test dependencies
```

## Installation

Clone the repository:

```bash
git clone https://github.com/USERNAME/powerflow-python-analyzer.git
cd powerflow-python-analyzer
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the application

```bash
python main.py
```

## Run tests

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
pytest -q
```

## Built-in systems

The built-in systems are located in:

```text
data/systems/
```

Each system file contains the network data, such as `busdata`, `linedata`, and optionally `gendata`.

## Technologies used

- Python
- PySide6
- NumPy
- SciPy
- Pandas
- Matplotlib
- NetworkX
- ReportLab
- Pytest

## Academic context

This project was developed as an academic power-system analysis tool. It can be used to study load-flow methods, fault analysis, network matrices and transient stability in electrical power networks.

## License

No license has been added yet. Add a license file before publishing if you want to define how others can use, modify, or distribute the project.
