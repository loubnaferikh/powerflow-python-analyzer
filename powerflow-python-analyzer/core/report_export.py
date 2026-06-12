\
\
\
\


from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime
import math
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


SLACK_COLOR = "#e74c3c"
PQ_COLOR = "#2f80ed"
PV_COLOR = "#2ecc71"
GOLD = "#d9a928"
DARK = "#1f2330"


def _bus_type_codes(busdata: np.ndarray) -> np.ndarray:
    raw = busdata[:, 1].astype(int)
    if 3 in raw:

        return np.array([1 if t == 3 else 2 if t == 2 else 0 for t in raw], dtype=int)
    return raw


def _bus_type_label(code: int) -> str:
    return {1: "Slack", 2: "PV", 0: "PQ", 3: "Slack"}.get(int(code), str(code))


def _fmt(x, digits: int = 4) -> str:
    try:
        x = float(x)
        if not math.isfinite(x):
            return "--"
        return f"{x:.{digits}f}"
    except Exception:
        return str(x)


def _fmt_complex(z, digits: int = 4) -> str:
    try:
        z = complex(z)
        return f"{z.real:.{digits}f}{z.imag:+.{digits}f}j"
    except Exception:
        return str(z)


def _small_matrix_preview(matrix: np.ndarray | None, max_size: int = 10) -> list[list[str]] | None:
    if matrix is None:
        return None
    arr = np.asarray(matrix)
    r = min(arr.shape[0], max_size)
    c = min(arr.shape[1], max_size)
    out = [["", *[f"Bus {j+1}" for j in range(c)]]]
    for i in range(r):
        row = [f"Bus {i+1}"]
        for j in range(c):
            val = arr[i, j]
            if np.iscomplexobj(arr):
                row.append(f"{val.real:.3f}{val.imag:+.3f}j")
            else:
                row.append(f"{float(val):.3f}")
        out.append(row)
    return out


def _make_voltage_histogram(path: Path, data, powerflow_result: dict) -> None:
    vm = np.asarray(powerflow_result["Vm"], dtype=float)
    x = np.arange(1, len(vm) + 1)
    types = _bus_type_codes(data.busdata)
    colors_by_type = {1: SLACK_COLOR, 0: PQ_COLOR, 2: PV_COLOR}
    bar_colors = [colors_by_type.get(int(t), PQ_COLOR) for t in types]

    fig = Figure(figsize=(9, 4.2), dpi=160)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.bar(x, vm, color=bar_colors, edgecolor="#222222", linewidth=0.7)
    ax.axhline(1.05, linestyle="--", linewidth=1.2, color=GOLD, label="Limite haute 1.05 pu")
    ax.axhline(0.95, linestyle="--", linewidth=1.2, color=GOLD, label="Limite basse 0.95 pu")
    ax.set_title("Profil de tension par type de bus")
    ax.set_xlabel("Bus")
    ax.set_ylabel("|V| (pu)")
    if len(x) <= 25:
        ax.set_xticks(x)
    else:
        step = max(1, len(x) // 15)
        ax.set_xticks(x[::step])
    if len(vm):
        ax.set_ylim(min(0.90, float(np.nanmin(vm)) - 0.03), max(1.10, float(np.nanmax(vm)) + 0.03))


    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=SLACK_COLOR, edgecolor="#222222", label="Slack"),
        Patch(facecolor=PQ_COLOR, edgecolor="#222222", label="PQ"),
        Patch(facecolor=PV_COLOR, edgecolor="#222222", label="PV"),
    ]
    line_handles, line_labels = ax.get_legend_handles_labels()
    ax.legend(handles + line_handles, [h.get_label() for h in handles] + line_labels, fontsize=8)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)


def _make_comparison_bar_chart(path: Path, comparison_data: dict, metric: str) -> None:
    rows = comparison_data.get("rows", [])
    names = [r.get("method", "") for r in rows]
    if metric == "losses":
        values = [float(r.get("losses_p", 0.0) or 0.0) for r in rows]
        title = "Comparaison des pertes actives"
        ylabel = "Pertes actives (MW)"
    elif metric == "times":
        values = [float(r.get("time_s", 0.0) or 0.0) for r in rows]
        title = "Comparaison des temps d'exécution"
        ylabel = "Temps (s)"
    else:
        values = [float(r.get("vm_mean", 0.0) or 0.0) for r in rows]
        title = "Comparaison des tensions moyennes"
        ylabel = "|V| moyen (pu)"

    fig = Figure(figsize=(9, 4.2), dpi=160)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    ax.bar(names, values, edgecolor="#222222", linewidth=0.7)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)


def _make_comparison_voltage_chart(path: Path, comparison_data: dict) -> None:
    results = comparison_data.get("results", {})
    fig = Figure(figsize=(9, 4.2), dpi=160)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    for name, res in results.items():
        vm = np.asarray(res.get("Vm", []), dtype=float)
        if vm.size:
            ax.plot(np.arange(1, len(vm) + 1), vm, marker="o", linewidth=1.4, label=name)
    ax.axhline(1.05, linestyle="--", linewidth=1.0, color=GOLD)
    ax.axhline(0.95, linestyle="--", linewidth=1.0, color=GOLD)
    ax.set_title("Profils de tension par méthode")
    ax.set_xlabel("Bus")
    ax.set_ylabel("|V| (pu)")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)


def _make_stability_chart(path: Path, stability_result: dict) -> None:
    t = np.asarray(stability_result.get("time", []), dtype=float)
    delta = np.asarray(stability_result.get("delta", []), dtype=float)
    omega = np.asarray(stability_result.get("omega", []), dtype=float)
    gen_bus = stability_result.get("gen_bus", None)

    fig = Figure(figsize=(9, 5.5), dpi=160)
    FigureCanvasAgg(fig)
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    if delta.size:
        delta_deg = np.rad2deg(delta)

        if delta_deg.shape[0] > 1:
            delta_plot = delta_deg - delta_deg[0:1, :]
            ylabel = "Δδ (deg)"
        else:
            delta_plot = delta_deg
            ylabel = "δ (deg)"
        for k in range(delta_plot.shape[0]):
            label = f"Gen Bus {int(gen_bus[k])}" if gen_bus is not None else f"Gen {k+1}"
            ax1.plot(t, delta_plot[k, :], linewidth=1.2, label=label)
        ax1.set_ylabel(ylabel)
        ax1.set_title("Angle rotorique")
        ax1.grid(True, alpha=0.25)
        ax1.legend(fontsize=7)

    if omega.size:
        for k in range(omega.shape[0]):
            label = f"Gen Bus {int(gen_bus[k])}" if gen_bus is not None else f"Gen {k+1}"
            ax2.plot(t, omega[k, :], linewidth=1.2, label=label)
        ax2.axhline(1.0, linestyle="--", linewidth=1.0, color="#333333")
        ax2.set_xlabel("Temps (s)")
        ax2.set_ylabel("ω (pu)")
        ax2.set_title("Vitesse rotorique")
        ax2.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(path)


def _table_style(header_bg=colors.HexColor(DARK)) -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f5f7")]),
    ])


def export_pdf_report(
    output_path: str | Path,
    data,
    current_file: str = "",
    powerflow_result: dict | None = None,
    comparison_data: dict | None = None,
    fault_result: dict | None = None,
    matrix_name: str | None = None,
) -> Path:
\
\
\
\

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="TitleBlue", parent=styles["Title"], textColor=colors.HexColor("#1f5fbf")))
    story = []

    story.append(Paragraph("Rapport automatique - Analyse de réseaux électriques", styles["TitleBlue"]))
    story.append(Paragraph(f"Fichier : <b>{current_file or '--'}</b>", styles["Normal"]))
    story.append(Paragraph(f"Date d'export : {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))


    nbus = getattr(data, "nbus", data.busdata.shape[0])
    nline = data.linedata.shape[0]
    ngen = 0 if getattr(data, "gendata", None) is None else data.gendata.shape[0]
    summary = [
        ["Base MVA", "Nombre de bus", "Nombre de lignes", "Nombre de générateurs"],
        [_fmt(data.basemva, 2), str(nbus), str(nline), str(ngen)],
    ]
    tbl = Table(summary, hAlign="LEFT")
    tbl.setStyle(_table_style(colors.HexColor("#244a6b")))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))


    story.append(Paragraph("1. Données de bus", styles["Heading2"]))
    bus_rows = [["Bus", "Type", "V init", "Angle", "Pc", "Qc", "Pg", "Qg"]]
    types = _bus_type_codes(data.busdata)
    for i, row in enumerate(data.busdata):
        bus_rows.append([
            str(int(row[0])),
            _bus_type_label(types[i]),
            _fmt(row[2], 4),
            _fmt(row[3], 3),
            _fmt(row[4], 2),
            _fmt(row[5], 2),
            _fmt(row[6], 2),
            _fmt(row[7], 2),
        ])
    tbl = Table(bus_rows, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(_table_style())
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))


    if data.Ybus is not None or data.Zbus is not None:
        story.append(PageBreak())
        story.append(Paragraph("2. Matrices réseau", styles["Heading2"]))
        story.append(Paragraph(f"Dernière matrice affichée : {matrix_name or '--'}", styles["Normal"]))
        for name, matrix in [("Ybus", data.Ybus), ("Zbus", data.Zbus)]:
            preview = _small_matrix_preview(matrix, max_size=10)
            if preview is not None:
                story.append(Paragraph(f"Aperçu {name} (10 x 10 maximum)", styles["Heading3"]))
                tbl = Table(preview, repeatRows=1, hAlign="LEFT")
                tbl.setStyle(_table_style(colors.HexColor("#27364a")))
                story.append(tbl)
                story.append(Spacer(1, 0.3 * cm))

    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)


        if powerflow_result is not None:
            story.append(PageBreak())
            story.append(Paragraph("3. Écoulement de puissance", styles["Heading2"]))
            pf = powerflow_result
            story.append(Paragraph(
                f"Méthode : <b>{pf.get('method', '--')}</b> - "
                f"Convergence : <b>{pf.get('converged', False)}</b> - "
                f"Itérations : <b>{pf.get('iterations', '--')}</b>",
                styles["Normal"],
            ))
            pf_rows = [["Bus", "Type", "|V|", "Angle", "Pg", "Qg", "Pc", "Qc"]]
            for i in range(len(pf["Vm"])):
                pf_rows.append([
                    str(int(data.busdata[i, 0])),
                    _bus_type_label(types[i]),
                    _fmt(pf["Vm"][i], 4),
                    _fmt(pf["Va"][i], 3),
                    _fmt(pf["Pg"][i], 3),
                    _fmt(pf["Qg"][i], 3),
                    _fmt(pf["Pc"][i], 3),
                    _fmt(pf["Qc"][i], 3),
                ])
            pf_rows.append([
                "TOTAL", "Réseau", "--", "--",
                _fmt(np.sum(pf["Pg"]), 3), _fmt(np.sum(pf["Qg"]), 3),
                _fmt(np.sum(pf["Pc"]), 3), _fmt(np.sum(pf["Qc"]), 3),
            ])
            tbl = Table(pf_rows, repeatRows=1, hAlign="LEFT")
            style = _table_style(colors.HexColor("#174568"))
            style.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff4cc"))
            style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
            tbl.setStyle(style)
            story.append(tbl)
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(
                f"Pertes actives : <b>{_fmt(pf.get('losses_p', 0), 4)} MW</b> - "
                f"Pertes réactives : <b>{_fmt(pf.get('losses_q', 0), 4)} MVAr</b>",
                styles["Normal"],
            ))
            img_path = tmp / "voltage_hist.png"
            _make_voltage_histogram(img_path, data, pf)
            story.append(Spacer(1, 0.3 * cm))
            story.append(Image(str(img_path), width=23 * cm, height=10.5 * cm))


        if comparison_data is not None:
            story.append(PageBreak())
            story.append(Paragraph("4. Comparaison des méthodes", styles["Heading2"]))
            rows = comparison_data.get("rows", [])
            comp_rows = [["Méthode", "Itérations", "Temps (s)", "Conv.", "|V| moy", "Pertes MW", "Pertes %", "Erreur"]]
            for r in rows:
                comp_rows.append([
                    r.get("method", "--"),
                    str(r.get("iterations", "--")),
                    _fmt(r.get("time_s", 0), 6),
                    "Oui" if r.get("converged", False) else "Non",
                    _fmt(r.get("vm_mean", 0), 5),
                    _fmt(r.get("losses_p", 0), 5),
                    _fmt(r.get("loss_pct", 0), 3),
                    str(r.get("error", "")),
                ])
            tbl = Table(comp_rows, repeatRows=1, hAlign="LEFT")
            tbl.setStyle(_table_style(colors.HexColor("#4f2b70")))
            story.append(tbl)
            if rows:
                volt_path = tmp / "comparison_voltages.png"
                loss_path = tmp / "comparison_losses.png"
                time_path = tmp / "comparison_times.png"
                _make_comparison_voltage_chart(volt_path, comparison_data)
                _make_comparison_bar_chart(loss_path, comparison_data, "losses")
                _make_comparison_bar_chart(time_path, comparison_data, "times")
                story.append(Spacer(1, 0.4 * cm))
                story.append(Paragraph("Profils de tension", styles["Heading3"]))
                story.append(Image(str(volt_path), width=23 * cm, height=10.5 * cm))
                story.append(PageBreak())
                story.append(Paragraph("Pertes actives par méthode", styles["Heading3"]))
                story.append(Image(str(loss_path), width=23 * cm, height=10.5 * cm))
                story.append(PageBreak())
                story.append(Paragraph("Temps d'exécution par méthode", styles["Heading3"]))
                story.append(Image(str(time_path), width=23 * cm, height=10.5 * cm))


        if fault_result is not None:
            story.append(PageBreak())
            story.append(Paragraph("5. Analyse des défauts", styles["Heading2"]))
            zkk = fault_result.get("Zkk", {})
            i_seq = np.asarray(fault_result.get("I_seq", []), dtype=complex)
            i_phase = np.asarray(fault_result.get("I_phase", []), dtype=complex)
            rows_fault = [
                ["Grandeur", "Valeur"],
                ["Type de défaut", fault_result.get("fault_type", "--")],
                ["Bus de défaut", str(fault_result.get("fault_bus", "--"))],
                ["Z0kk", _fmt_complex(zkk.get("Z0", 0j))],
                ["Z1kk", _fmt_complex(zkk.get("Z1", 0j))],
                ["Z2kk", _fmt_complex(zkk.get("Z2", 0j))],
                ["I0", _fmt_complex(i_seq[0]) if i_seq.size >= 3 else "--"],
                ["I1", _fmt_complex(i_seq[1]) if i_seq.size >= 3 else "--"],
                ["I2", _fmt_complex(i_seq[2]) if i_seq.size >= 3 else "--"],
                ["Ia", _fmt_complex(i_phase[0]) if i_phase.size >= 3 else "--"],
                ["Ib", _fmt_complex(i_phase[1]) if i_phase.size >= 3 else "--"],
                ["Ic", _fmt_complex(i_phase[2]) if i_phase.size >= 3 else "--"],
                ["|If|max", _fmt(fault_result.get("ifault_pu", 0), 5) + " pu"],
                ["Scc", _fmt(fault_result.get("scc_mva", 0), 3) + " MVA"],
            ]
            tbl = Table(rows_fault, repeatRows=1, hAlign="LEFT")
            tbl.setStyle(_table_style(colors.HexColor("#806020")))
            story.append(tbl)
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(fault_result.get("formula", ""), styles["Small"]))
            story.append(Paragraph(fault_result.get("sequence_note", ""), styles["Small"]))

        doc.build(story)
    return output_path
