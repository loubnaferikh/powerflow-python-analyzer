

from __future__ import annotations
from pathlib import Path
import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QGroupBox, QLabel, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTableWidget, QTableWidgetItem, QComboBox, QSizePolicy, QHeaderView, QTabWidget, QScrollArea
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    import networkx as nx
except Exception:
    nx = None

from ui.styles import APP_STYLESHEET, BUTTON_STYLES, COLORS
from utils.formatting import matrix_to_strings, safe_float, bus_type_label
from data.loader import load_system, SYSTEMS_DIR, list_builtin_system_files
from core.ybus import build_ybus
from core.zbus import build_zbus_direct, build_zbus_from_ybus
from core.gauss_seidel import gauss_seidel_power_flow
from core.newton_raphson import newton_raphson_rectangular, newton_raphson_polar, newton_raphson_v2
from core.fdlf import fast_decoupled_load_flow
from core.comparison import run_comparison
from core.stability import transient_stability, estimate_critical_clearing_time
from core.report_export import export_pdf_report
from core.fault_analysis import analyze_fault, format_complex


class MplCanvas(FigureCanvas):


    def __init__(self, width: float = 5, height: float = 3, dpi: int = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=COLORS["bg_panel"])
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply_dark_style()

    def apply_dark_style(self) -> None:
        self.ax.set_facecolor(COLORS["bg_panel"])
        self.ax.tick_params(colors=COLORS["text_lo"])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS["border"])
        self.ax.grid(True, alpha=0.25)
        self.fig.tight_layout()

    def clear(self, title: str = "") -> None:
        self.ax.clear()
        self.apply_dark_style()
        if title:
            self.ax.set_title(title, color=COLORS["text_hi"])
        self.draw_idle()


class MainWindow(QMainWindow):


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analyseur de Réseaux Électriques - ENP")
        self.resize(1450, 850)
        self.setStyleSheet(APP_STYLESHEET)
        self.data = None
        self.current_file = "Aucun fichier chargé"
        self.stab_method = "euler"
        self.stab_graph = "delta"
        self.comparison_data = None
        self.last_powerflow_result = None
        self.last_stability_result = None
        self.last_matrix_name = None
        self.last_fault_result = None
        self._build_ui()


    def _build_ui(self) -> None:
        self.root = QWidget()
        self.setCentralWidget(self.root)
        root_layout = QVBoxLayout(self.root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.topbar = self._create_topbar()
        root_layout.addWidget(self.topbar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root_layout.addLayout(body, 1)

        self.sidebar = self._create_sidebar()
        body.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)

        self.home_page = self._create_home_page()
        self.matrix_page = self._create_matrix_page()
        self.powerflow_page = self._create_powerflow_page()
        self.compare_page = self._create_compare_page()
        self.fault_page = self._create_fault_page()
        self.stability_page = self._create_stability_page()

        for page in [self.home_page, self.matrix_page, self.powerflow_page, self.compare_page, self.fault_page, self.stability_page]:
            self.pages.addWidget(page)
        self.pages.setCurrentWidget(self.home_page)
        self._set_nav_active(None)

    def _create_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(70)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 8, 18, 8)
        title_box = QVBoxLayout()
        title = QLabel("ANALYSEUR DE RÉSEAUX ÉLECTRIQUES")
        title.setStyleSheet(f"color:{COLORS['cyan']}; font-family:Consolas; font-size:18px; font-weight:800;")
        subtitle = QLabel("École Nationale Polytechnique  |  TP Réseaux 2  |  2025-2026")
        subtitle.setStyleSheet(f"color:{COLORS['text_lo']};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box, 1)

        layout.addWidget(QLabel("FICHIER ACTIF :"))
        self.file_path_edit = QLineEdit("Aucun fichier chargé")
        self.file_path_edit.setReadOnly(True)
        layout.addWidget(self.file_path_edit, 2)
        load_btn = QPushButton("CHARGER SYSTÈME")
        load_btn.setStyleSheet(BUTTON_STYLES["gold"])
        load_btn.clicked.connect(self.load_file_dialog)
        layout.addWidget(load_btn)

        export_btn = QPushButton("EXPORT PDF")
        export_btn.setStyleSheet(BUTTON_STYLES["success"])
        export_btn.clicked.connect(self.export_report_dialog)
        layout.addWidget(export_btn)
        return bar

    def _create_sidebar(self) -> QWidget:
        side = QFrame()
        side.setFixedWidth(190)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(14, 18, 14, 18)
        logo = QLabel("ENP")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"color:{COLORS['cyan']}; font-family:Consolas; font-size:30px; font-weight:900;")
        layout.addWidget(logo)
        sub = QLabel("Réseaux\nÉlectriques")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{COLORS['text_lo']};")
        layout.addWidget(sub)
        layout.addSpacing(25)

        self.nav_buttons: dict[str, QPushButton] = {}
        nav = [
            ("Accueil", self.show_home),
            ("Matrices", lambda: self.show_page(self.matrix_page, "Matrices")),
            ("Écoulement", lambda: self.show_page(self.powerflow_page, "Écoulement")),
            ("Comparaison", lambda: self.show_page(self.compare_page, "Comparaison")),
            ("Défauts", lambda: self.show_page(self.fault_page, "Défauts")),
            ("Stabilité", lambda: self.show_page(self.stability_page, "Stabilité")),
        ]
        for name, callback in nav:
            btn = QPushButton(name.upper())
            btn.clicked.connect(callback)
            self.nav_buttons[name] = btn
            layout.addWidget(btn)
        layout.addStretch(1)
        export_btn = QPushButton("EXPORT RAPPORT PDF")
        export_btn.setStyleSheet(BUTTON_STYLES["success"])
        export_btn.clicked.connect(self.export_report_dialog)
        layout.addWidget(export_btn)
        quit_btn = QPushButton("QUITTER")
        quit_btn.setStyleSheet(BUTTON_STYLES["danger"])
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)
        return side

    def _create_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addStretch(1)

        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(12)
        title = QLabel("ÉCOLE NATIONALE POLYTECHNIQUE D'ALGER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{COLORS['cyan']}; font-size:22px; font-weight:800;")
        card_layout.addWidget(title)
        for text in [
            "Département d'Électrotechnique",
            "TP Réseaux Électriques 2",
            "Année Universitaire 2025 - 2026",
            "Proposé par : Prof. A. Hellal",
            "Réalisé par : Loubna FERIKH",
        ]:
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            if "TP" in text:
                label.setStyleSheet(f"color:{COLORS['gold']}; font-size:18px; font-weight:800;")
            else:
                label.setStyleSheet(f"color:{COLORS['text_hi']}; font-size:15px;")
            card_layout.addWidget(label)
        layout.addWidget(card)

        load_row = QHBoxLayout()
        self.home_file_edit = QLineEdit("Aucun fichier chargé")
        self.home_file_edit.setReadOnly(True)
        load_btn = QPushButton("SYSTEM*.PY")
        load_btn.setStyleSheet(BUTTON_STYLES["primary"])
        load_btn.clicked.connect(self.load_file_dialog)
        load_row.addWidget(self.home_file_edit, 1)
        load_row.addWidget(load_btn)
        layout.addLayout(load_row)

        action_row = QHBoxLayout()
        for name, page_obj, color in [
            ("MATRICES", self.matrix_page if hasattr(self, "matrix_page") else None, "success"),
            ("ÉCOULEMENT DE PUISSANCE", None, "primary"),
            ("STABILITÉ TRANSITOIRE", None, "purple"),
        ]:
            btn = QPushButton(name)
            btn.setMinimumHeight(65)
            btn.setStyleSheet(BUTTON_STYLES[color])
            if name.startswith("MATRICES"):
                btn.clicked.connect(lambda: self.show_page(self.matrix_page, "Matrices"))
            elif name.startswith("ÉCOULEMENT"):
                btn.clicked.connect(lambda: self.show_page(self.powerflow_page, "Écoulement"))
            else:
                btn.clicked.connect(lambda: self.show_page(self.stability_page, "Stabilité"))
            action_row.addWidget(btn)
        layout.addLayout(action_row)
        layout.addStretch(1)
        return page

    def _section_title(self, text: str, color: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color:{color}; font-family:Consolas; font-size:22px; font-weight:900;")
        return label


    def _create_matrix_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.addWidget(self._section_title("MATRICES DU RÉSEAU", COLORS["green"]))
        btn_row = QHBoxLayout()
        actions = [
            ("Calculer YBUS", self.run_ybus),
            ("Zbus Direct", self.run_zbus_direct),
            ("Zbus Inverse", self.run_zbus_inverse),
            ("Validation I = Y.Z", self.run_yz_validation),
        ]
        for text, callback in actions:
            btn = QPushButton(text)
            btn.setStyleSheet(BUTTON_STYLES["primary"])
            btn.clicked.connect(callback)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        split = QHBoxLayout()
        self.matrix_table = QTableWidget()
        split.addWidget(self.matrix_table, 3)
        right = QVBoxLayout()
        self.topology_canvas = MplCanvas(width=4, height=5)
        right.addWidget(QLabel("TOPOLOGIE DU RÉSEAU"))
        right.addWidget(self.topology_canvas)
        split.addLayout(right, 2)
        layout.addLayout(split, 1)
        self.matrix_label = QLabel("Aucune matrice calculée.")
        self.matrix_label.setAlignment(Qt.AlignCenter)
        self.matrix_label.setStyleSheet(f"color:{COLORS['gold']}; font-weight:700;")
        layout.addWidget(self.matrix_label)
        return page

    def _create_powerflow_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        top = QHBoxLayout()
        top.addWidget(self._section_title("ÉCOULEMENT DE PUISSANCE", COLORS["blue"]), 1)
        self.method_label = QLabel("Aucune méthode sélectionnée")
        self.method_label.setStyleSheet(f"color:{COLORS['text_lo']};")
        top.addWidget(self.method_label, 1)
        layout.addLayout(top)

        controls = QHBoxLayout()
        self.tol_edit = QLineEdit("0.001")
        self.accel_edit = QLineEdit("1.6")
        for label, widget in [("Tolérance", self.tol_edit), ("Accélération", self.accel_edit)]:
            box = QVBoxLayout()
            box.addWidget(QLabel(label))
            box.addWidget(widget)
            controls.addLayout(box)
        for text, callback in [
            ("GAUSS-SEIDEL", self.run_gs),
            ("NR RECT.", lambda: self.run_nr("rect")),
            ("NR POLAIRE", lambda: self.run_nr("polar")),
            ("NR V2", lambda: self.run_nr("v2")),
            ("FDLF", self.run_fdlf),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            controls.addWidget(btn)
        layout.addLayout(controls)

        self.pf_table = QTableWidget()
        layout.addWidget(self.pf_table, 3)

        bottom = QHBoxLayout()
        self.voltage_canvas = MplCanvas(width=7, height=3)
        bottom.addWidget(self.voltage_canvas, 3)
        losses = QGroupBox("Pertes réseau")
        loss_layout = QVBoxLayout(losses)
        self.loss_p_label = QLabel("P active : -- MW")
        self.loss_q_label = QLabel("Q réactive : -- MVAr")
        self.loss_pct_label = QLabel("% pertes : --")
        for w in [self.loss_p_label, self.loss_q_label, self.loss_pct_label]:
            w.setStyleSheet("font-size:18px; font-weight:800;")
            loss_layout.addWidget(w)
        bottom.addWidget(losses, 1)
        layout.addLayout(bottom, 2)
        return page

    def _create_compare_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.addWidget(self._section_title("COMPARAISON DES MÉTHODES", COLORS["purple"]))
        params = QHBoxLayout()
        self.comp_tol_edit = QLineEdit("0.001")
        self.comp_maxiter_edit = QLineEdit("100")
        self.comp_accel_edit = QLineEdit("1.6")
        for label, widget in [("Tolérance", self.comp_tol_edit), ("Max iter", self.comp_maxiter_edit), ("Accel GS", self.comp_accel_edit)]:
            box = QVBoxLayout()
            box.addWidget(QLabel(label))
            box.addWidget(widget)
            params.addLayout(box)
        run_btn = QPushButton("LANCER LA COMPARAISON")
        run_btn.setStyleSheet(BUTTON_STYLES["success"])
        run_btn.clicked.connect(self.run_all_comparison)
        params.addWidget(run_btn)
        layout.addLayout(params)
        self.compare_table = QTableWidget()
        layout.addWidget(self.compare_table, 2)
        graph_row = QHBoxLayout()
        for text, kind in [("Profils de tensions", "voltages"), ("Pertes actives", "losses"), ("Temps d'exécution", "times")]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked=False, k=kind: self.show_comparison_graph(k))
            graph_row.addWidget(btn)
        layout.addLayout(graph_row)
        self.compare_canvas = MplCanvas(width=10, height=4)
        layout.addWidget(self.compare_canvas, 3)
        return page

    def _create_fault_page(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.addWidget(self._section_title("ANALYSE DES DÉFAUTS", COLORS["gold"]))
        self.fault_info_btn = QPushButton("i")
        self.fault_info_btn.setFixedSize(26, 26)
        self.fault_info_btn.setToolTip("Informations sur l'analyse des défauts")
        self.fault_info_btn.setStyleSheet(
            f"""
            QPushButton {{
                border-radius: 13px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['gold']};
                border: 1px solid {COLORS['gold']};
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_active']};
                color: {COLORS['text_hi']};
            }}
            """
        )
        self.fault_info_btn.clicked.connect(self.show_fault_info)
        title_row.addStretch(1)
        title_row.addWidget(self.fault_info_btn)
        root.addLayout(title_row)

        main_area = QHBoxLayout()
        main_area.setSpacing(12)

        left_area = QVBoxLayout()
        left_area.setSpacing(8)

        graph_box = QGroupBox("Tensions après défaut")
        graph_layout = QVBoxLayout(graph_box)
        graph_layout.setContentsMargins(8, 8, 8, 8)
        self.fault_canvas = MplCanvas(width=9.2, height=3.9)
        graph_layout.addWidget(self.fault_canvas)
        left_area.addWidget(graph_box, 3)

        result_tabs = QTabWidget()
        result_tabs.setMinimumHeight(235)

        self.fault_table = QTableWidget()
        self.fault_table.setAlternatingRowColors(True)
        self.fault_table.horizontalHeader().setStretchLastSection(True)
        self.fault_table.verticalHeader().setVisible(False)
        result_tabs.addTab(self.fault_table, "Résumé numérique")

        self.fault_matrix_table = QTableWidget()
        self.fault_matrix_table.setAlternatingRowColors(True)
        self.fault_matrix_table.horizontalHeader().setStretchLastSection(True)
        self.fault_matrix_table.verticalHeader().setVisible(True)
        result_tabs.addTab(self.fault_matrix_table, "Matrice 012")

        left_area.addWidget(result_tabs, 2)
        main_area.addLayout(left_area, 4)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(370)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_panel = QGroupBox("Paramètres")
        right_scroll.setWidget(right_panel)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        self.fault_analysis_bus_combo = QComboBox()
        self.fault_type_combo = QComboBox()
        self.fault_type_combo.addItems(["3PH - Triphasé symétrique", "LG - Phase-terre", "LL - Biphasé", "LLG - Biphasé-terre"])
        self.fault_zf_r_edit = QLineEdit("0.0")
        self.fault_zf_x_edit = QLineEdit("0.0")
        self.fault_zg_r_edit = QLineEdit("0.0")
        self.fault_zg_x_edit = QLineEdit("0.0")
        self.fault_k0_edit = QLineEdit("1.0")
        self.fault_k2_edit = QLineEdit("1.0")

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(12)
        rows = [
            ("Bus", self.fault_analysis_bus_combo),
            ("Type", self.fault_type_combo),
            ("Rf", self.fault_zf_r_edit),
            ("Xf", self.fault_zf_x_edit),
            ("Rg", self.fault_zg_r_edit),
            ("Xg", self.fault_zg_x_edit),
            ("Z0", self.fault_k0_edit),
            ("Z2", self.fault_k2_edit),
        ]
        for i, (label, widget) in enumerate(rows):
            label_widget = QLabel(label)
            label_widget.setMinimumHeight(36)
            widget.setMinimumHeight(36)
            widget.setMaximumHeight(36)
            form.addWidget(label_widget, i, 0)
            form.addWidget(widget, i, 1)
        right_layout.addLayout(form)

        run_btn = QPushButton("CALCULER")
        run_btn.setMinimumHeight(40)
        run_btn.setStyleSheet(BUTTON_STYLES["gold"])
        run_btn.clicked.connect(self.run_fault_analysis)
        right_layout.addWidget(run_btn)

        self.fault_card_type = QLabel("Type : —")
        self.fault_card_current = QLabel("|If|max : —")
        self.fault_card_scc = QLabel("Scc : —")
        for card in [self.fault_card_type, self.fault_card_current, self.fault_card_scc]:
            card.setAlignment(Qt.AlignCenter)
            card.setMinimumHeight(40)
            card.setStyleSheet(
                f"background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; "
                f"border-radius:10px; color:{COLORS['text_hi']}; font-size:13px; font-weight:800; padding:5px;"
            )
            right_layout.addWidget(card)

        right_layout.addStretch(1)

        main_area.addWidget(right_scroll)
        root.addLayout(main_area, 1)
        return page


    def show_fault_info(self) -> None:

        QMessageBox.information(
            self,
            "Information — Analyse des défauts",
            "Cette partie calcule les courants et tensions pendant un court-circuit sur un bus du réseau.\n\n"
            "Principe utilisé :\n"
            "1) le réseau est remplacé par son équivalent de Thévenin vu du bus de défaut ;\n"
            "2) Zkk est extrait de Zbus ;\n"
            "3) le courant de défaut est calculé selon le type choisi : 3PH, L-G, L-L ou L-L-G ;\n"
            "4) les résultats sont convertis en phases a, b et c.\n\n"
            "Le tableau donne les valeurs numériques principales : Z0kk, Z1kk, Z2kk, I0/I1/I2, Ia/Ib/Ic, "
            "courant maximal et puissance de court-circuit.\n\n"
            "Le graphe affiche les tensions de phase après défaut sur tous les bus. "
            "La ligne verticale rouge indique le bus en défaut.\n\n"
            "Remarque : si le fichier système ne fournit pas directement Z0 et Z2, l'application utilise : "
            "Z2 = k2 × Z1 et Z0 = k0 × Z1. Ces facteurs sont réglables dans les paramètres."
        )

    def _create_stability_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        left = QVBoxLayout()
        left.addWidget(self._section_title("STABILITÉ TRANSITOIRE", COLORS["red"]))
        self.stab_canvas = MplCanvas(width=8, height=6)
        left.addWidget(self.stab_canvas, 1)
        self.stab_status = QLabel("Chargez un fichier de données.")
        self.stab_status.setAlignment(Qt.AlignCenter)
        self.stab_status.setStyleSheet(f"color:{COLORS['gold']}; font-size:16px; font-weight:800;")
        left.addWidget(self.stab_status)
        layout.addLayout(left, 3)

        panel = QGroupBox("Paramètres")
        panel_layout = QVBoxLayout(panel)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Euler", "Runge-Kutta 4"])
        self.method_combo.setCurrentIndex(1)
        panel_layout.addWidget(QLabel("Méthode numérique"))
        panel_layout.addWidget(self.method_combo)
        self.graph_combo = QComboBox()
        self.graph_combo.addItems(["Angle rotorique δ", "Vitesse angulaire ω"])
        panel_layout.addWidget(QLabel("Graphe"))
        panel_layout.addWidget(self.graph_combo)
        self.fault_bus_combo = QComboBox()
        self.fault_line_combo = QComboBox()
        panel_layout.addWidget(QLabel("Nœud de défaut"))
        panel_layout.addWidget(self.fault_bus_combo)
        panel_layout.addWidget(QLabel("Ligne à ouvrir"))
        panel_layout.addWidget(self.fault_line_combo)
        self.te_edit = QLineEdit("0.2")
        self.ts_edit = QLineEdit("0.5")
        self.dt_edit = QLineEdit("0.005")
        for label, widget in [("Te (s)", self.te_edit), ("Ts/Tmax (s)", self.ts_edit), ("dt (s)", self.dt_edit)]:
            panel_layout.addWidget(QLabel(label))
            panel_layout.addWidget(widget)
        run = QPushButton("LANCER SIMULATION")
        run.setStyleSheet(BUTTON_STYLES["danger"])
        run.clicked.connect(self.run_stability)
        panel_layout.addWidget(run)
        critical = QPushButton("CHERCHER TEMPS CRITIQUE")
        critical.setStyleSheet(BUTTON_STYLES["gold"])
        critical.clicked.connect(self.run_critical_time_search)
        panel_layout.addWidget(critical)
        self.critical_status = QLabel("Temps critique : —")
        self.critical_status.setWordWrap(True)
        self.critical_status.setStyleSheet(f"color:{COLORS['text_lo']}; font-size:13px; padding:6px;")
        panel_layout.addWidget(self.critical_status)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page


    def show_home(self) -> None:
        self.pages.setCurrentWidget(self.home_page)
        self._set_nav_active(None)

    def show_page(self, page: QWidget, nav_name: str) -> None:
        self.pages.setCurrentWidget(page)
        self._set_nav_active(nav_name)
        if page is self.stability_page:
            self.refresh_stability_combos()
        if page is self.fault_page:
            self.refresh_fault_combos()

    def _set_nav_active(self, name: str | None) -> None:
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.setStyleSheet(f"background:{COLORS['bg_active']}; color:{COLORS['cyan']};")
            else:
                btn.setStyleSheet("")

    def load_file_dialog(self) -> None:

        SYSTEMS_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un système converti",
            str(SYSTEMS_DIR),
            "Systèmes convertis (system*.py)",
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str) -> None:
        try:
            self.data = load_system(path)
            self.current_file = Path(path).name
            self.file_path_edit.setText(str(path))
            self.home_file_edit.setText(str(path))
            self.statusBar().showMessage(f"Données chargées : {self.current_file}")
            self.refresh_stability_combos()
            self.refresh_fault_combos()
            self.draw_topology()
        except Exception as exc:
            self.show_error("Erreur chargement", str(exc))

    def require_data(self) -> bool:
        if self.data is None:
            self.show_error("Données manquantes", "Chargez d'abord un fichier system*.py.")
            return False
        return True


    def run_ybus(self) -> None:
        if not self.require_data():
            return
        try:
            self.data.Ybus = build_ybus(self.data.linedata, nbus=self.data.nbus)
            self.fill_matrix_table(self.data.Ybus)
            self.matrix_label.setText("Matrice affichée : YBUS (admittances nodales)")
            self.last_matrix_name = "YBUS"
            self.draw_topology()
        except Exception as exc:
            self.show_error("Ybus", str(exc))

    def run_zbus_direct(self) -> None:
        if not self.require_data():
            return
        try:
            self.data.Zbus = build_zbus_direct(self.data.linedata, nbus=self.data.nbus)
            self.fill_matrix_table(self.data.Zbus)
            self.matrix_label.setText("Matrice affichée : ZBUS (méthode directe)")
            self.last_matrix_name = "ZBUS Direct"
            self.draw_topology()
        except Exception as exc:
            self.show_error("Zbus direct", str(exc))

    def run_zbus_inverse(self) -> None:
        if not self.require_data():
            return
        try:
            if self.data.Ybus is None:
                self.data.Ybus = build_ybus(self.data.linedata, nbus=self.data.nbus)
            self.data.Zbus = build_zbus_from_ybus(self.data.Ybus)
            self.fill_matrix_table(self.data.Zbus)
            self.matrix_label.setText("Matrice affichée : ZBUS (inversion de Ybus)")
            self.last_matrix_name = "ZBUS Inverse"
            self.draw_topology()
        except Exception as exc:
            self.show_error("Zbus inverse", str(exc))

    def run_yz_validation(self) -> None:
        if not self.require_data():
            return
        try:
            if self.data.Ybus is None:
                self.data.Ybus = build_ybus(self.data.linedata, nbus=self.data.nbus)
            if self.data.Zbus is None:
                self.data.Zbus = build_zbus_from_ybus(self.data.Ybus)
            ident = self.data.Ybus @ self.data.Zbus
            diag = np.diag(ident).reshape(-1, 1)
            self.fill_matrix_table(diag, headers=["Diag(Ybus.Zbus)"])
            err = np.max(np.abs(ident - np.eye(ident.shape[0])))
            self.matrix_label.setText(f"Validation : YBUS × ZBUS ≈ I | erreur max = {err:.3e}")
        except Exception as exc:
            self.show_error("Validation", str(exc))


    def run_gs(self) -> None:
        if not self.require_data():
            return
        try:
            res = gauss_seidel_power_flow(
                self.data,
                tol=safe_float(self.tol_edit.text(), 1e-3),
                accel=safe_float(self.accel_edit.text(), 1.6),
                maxiter=500,
            )
            self.display_powerflow_result(res, "Méthode : Gauss-Seidel")
        except Exception as exc:
            self.show_error("Gauss-Seidel", str(exc))

    def run_nr(self, kind: str) -> None:
        if not self.require_data():
            return
        try:
            tol = safe_float(self.tol_edit.text(), 1e-3)
            if kind == "rect":
                res = newton_raphson_rectangular(self.data, tol=tol, maxiter=100)
                title = "Méthode : Newton-Raphson rectangulaire"
            elif kind == "polar":
                res = newton_raphson_polar(self.data, tol=tol, maxiter=100)
                title = "Méthode : Newton-Raphson polaire"
            else:
                res = newton_raphson_v2(self.data, tol=tol, maxiter=100)
                title = "Méthode : Newton-Raphson V2"
            self.display_powerflow_result(res, title)
        except Exception as exc:
            self.show_error("Newton-Raphson", str(exc))

    def run_fdlf(self) -> None:
        if not self.require_data():
            return
        try:
            res = fast_decoupled_load_flow(self.data, tol=safe_float(self.tol_edit.text(), 1e-3), maxiter=100)
            self.display_powerflow_result(res, "Méthode : Fast Decoupled Load Flow")
        except Exception as exc:
            self.show_error("FDLF", str(exc))

    def display_powerflow_result(self, res: dict, title: str) -> None:
        self.last_powerflow_result = res
        self.method_label.setText(f"{title} | conv={res['converged']} | iter={res['iterations']}")
        headers = ["Bus", "Type", "|V| (pu)", "Angle (deg)", "Pg (MW)", "Qg (MVAr)", "Pc (MW)", "Qc (MVAr)"]
        self.pf_table.setColumnCount(len(headers))
        self.pf_table.setHorizontalHeaderLabels(headers)

        n = len(res["Vm"])
        total_row = n
        self.pf_table.setRowCount(n + 1)

        raw_types = self.data.busdata[:, 1].astype(int)
        for i in range(n):
            values = [
                int(self.data.busdata[i, 0]),
                bus_type_label(int(raw_types[i])),
                f"{res['Vm'][i]:.4f}",
                f"{res['Va'][i]:.4f}",
                f"{res['Pg'][i]:.3f}",
                f"{res['Qg'][i]:.3f}",
                f"{res['Pc'][i]:.3f}",
                f"{res['Qc'][i]:.3f}",
            ]
            for j, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.pf_table.setItem(i, j, item)


        totals = {
            "Pg": float(np.sum(res["Pg"])),
            "Qg": float(np.sum(res["Qg"])),
            "Pc": float(np.sum(res["Pc"])),
            "Qc": float(np.sum(res["Qc"])),
        }
        total_values = [
            "TOTAL",
            "Réseau",
            "—",
            "—",
            f"{totals['Pg']:.3f}",
            f"{totals['Qg']:.3f}",
            f"{totals['Pc']:.3f}",
            f"{totals['Qc']:.3f}",
        ]
        for j, value in enumerate(total_values):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setFont(QFont("Consolas", 10, QFont.Bold))
            item.setBackground(QBrush(QColor(COLORS["bg_active"])))
            item.setForeground(QBrush(QColor(COLORS["gold"] if j < 4 else COLORS["text_hi"])))
            self.pf_table.setItem(total_row, j, item)

        self.pf_table.resizeColumnsToContents()
        self.loss_p_label.setText(f"P active : {res['losses_p']:.4f} MW")
        self.loss_q_label.setText(f"Q réactive : {res['losses_q']:.4f} MVAr")
        pg_sum = totals["Pg"]
        pct = 100 * res["losses_p"] / pg_sum if abs(pg_sum) > 1e-12 else 0.0
        self.loss_pct_label.setText(f"% pertes : {pct:.3f} %")
        self.plot_voltage_profile(res)


    def run_all_comparison(self) -> None:
        if not self.require_data():
            return
        try:
            self.comparison_data = run_comparison(
                self.data,
                tol=safe_float(self.comp_tol_edit.text(), 1e-3),
                maxiter=int(safe_float(self.comp_maxiter_edit.text(), 100)),
                accel=safe_float(self.comp_accel_edit.text(), 1.6),
            )
            rows = self.comparison_data["rows"]
            headers = ["Méthode", "Iterations", "Temps (s)", "Convergence", "|V| moy", "Pertes (MW)", "Pertes (%)", "Erreur"]
            self.compare_table.setColumnCount(len(headers))
            self.compare_table.setHorizontalHeaderLabels(headers)
            self.compare_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                values = [
                    row["method"], row["iterations"], f"{row['time_s']:.6f}",
                    "Oui" if row["converged"] else "Non", f"{row['vm_mean']:.5f}",
                    f"{row['losses_p']:.5f}", f"{row['loss_pct']:.3f}", row["error"],
                ]
                for j, value in enumerate(values):
                    self.compare_table.setItem(i, j, QTableWidgetItem(str(value)))
            self.compare_table.resizeColumnsToContents()
            self.show_comparison_graph("voltages")
        except Exception as exc:
            self.show_error("Comparaison", str(exc))


    def refresh_fault_combos(self) -> None:
        if not hasattr(self, "fault_analysis_bus_combo"):
            return
        self.fault_analysis_bus_combo.clear()
        if self.data is None:
            self.fault_analysis_bus_combo.addItem("Charger données")
            return
        for i in range(self.data.nbus):
            bus_no = int(self.data.busdata[i, 0])
            self.fault_analysis_bus_combo.addItem(f"Bus {bus_no}", bus_no)

    def _selected_fault_type(self) -> str:
        text = self.fault_type_combo.currentText().upper()
        if text.startswith("LG"):
            return "LG"
        if text.startswith("LLG"):
            return "LLG"
        if text.startswith("LL"):
            return "LL"
        return "3PH"

    def run_fault_analysis(self) -> None:
        if not self.require_data():
            return
        try:

            zf = complex(
                safe_float(self.fault_zf_r_edit.text(), 0.0),
                safe_float(self.fault_zf_x_edit.text(), 0.0),
            )
            zg = complex(
                safe_float(self.fault_zg_r_edit.text(), 0.0),
                safe_float(self.fault_zg_x_edit.text(), 0.0),
            )
            result = analyze_fault(
                self.data,
                fault_bus=int(self.fault_analysis_bus_combo.currentData()),
                fault_type=self._selected_fault_type(),
                zf=zf,
                zg=zg,
                k0=safe_float(self.fault_k0_edit.text(), 1.0),
                k2=safe_float(self.fault_k2_edit.text(), 1.0),
            )
            self.last_fault_result = result
            self.display_fault_result(result)
        except Exception as exc:
            self.show_error("Analyse des défauts", str(exc))

    def display_fault_result(self, result: dict) -> None:
        headers = ["Grandeur", "Valeur"]
        rows = [
            ["Type", result["fault_type"]],
            ["Bus", result["fault_bus"]],
            ["Vk avant défaut", f"{abs(result['Vk_prefault']):.4f} ∠ {np.rad2deg(np.angle(result['Vk_prefault'])):.3f}°"],
            ["Z0kk", format_complex(result["Zkk"]["Z0"])],
            ["Z1kk", format_complex(result["Zkk"]["Z1"])],
            ["Z2kk", format_complex(result["Zkk"]["Z2"])],
            ["I0", format_complex(result["I_seq"][0])],
            ["I1", format_complex(result["I_seq"][1])],
            ["I2", format_complex(result["I_seq"][2])],
            ["Ia", format_complex(result["I_phase"][0])],
            ["Ib", format_complex(result["I_phase"][1])],
            ["Ic", format_complex(result["I_phase"][2])],
            ["|If|max", f"{result['ifault_pu']:.5f} pu"],
            ["Scc", f"{result['scc_mva']:.3f} MVA"],
            ["Formule", result["formula"]],
        ]
        self.fault_table.setColumnCount(2)
        self.fault_table.setHorizontalHeaderLabels(headers)
        self.fault_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.fault_table.setItem(i, j, item)
        self.fault_table.resizeColumnsToContents()
        self.fault_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.fault_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.fault_card_type.setText(f"Type : {result['fault_type']} / Bus {result['fault_bus']}")
        self.fault_card_current.setText(f"|If|max : {result['ifault_pu']:.5f} pu")
        self.fault_card_scc.setText(f"Scc : {result['scc_mva']:.3f} MVA")
        fm = result.get("fault_matrices", {})
        mat = fm.get("Zf_012") if fm.get("Zf_012") is not None else fm.get("Yf_012")
        if mat is not None:
            self.fault_matrix_table.setRowCount(3)
            self.fault_matrix_table.setColumnCount(3)
            self.fault_matrix_table.setHorizontalHeaderLabels(["0", "1", "2"])
            self.fault_matrix_table.setVerticalHeaderLabels(["0", "1", "2"])
            for i in range(3):
                for j in range(3):
                    self.fault_matrix_table.setItem(i, j, QTableWidgetItem(format_complex(mat[i, j], 3)))
        else:
            self.fault_matrix_table.setRowCount(1)
            self.fault_matrix_table.setColumnCount(1)
            self.fault_matrix_table.setHorizontalHeaderLabels(["Info"])
            self.fault_matrix_table.setItem(0, 0, QTableWidgetItem("Matrice non définie pour ce cas ou Zf=0."))
        self.fault_matrix_table.resizeColumnsToContents()
        if self.fault_matrix_table.columnCount() > 1:
            for col in range(self.fault_matrix_table.columnCount()):
                self.fault_matrix_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.plot_fault_voltages(result)

    def plot_fault_voltages(self, result: dict) -> None:
        self.fault_canvas.clear("Tensions de phase après défaut")
        ax = self.fault_canvas.ax
        vabc = np.asarray(result["V_phase_all"], dtype=complex)
        x = np.arange(1, vabc.shape[1] + 1)
        labels = ["|Va|", "|Vb|", "|Vc|"]
        for idx, label in enumerate(labels):
            ax.plot(x, np.abs(vabc[idx, :]), marker="o", linewidth=1.8, markersize=4, label=label)
        fb = int(result["fault_bus"])
        ax.axvline(fb, linestyle="--", linewidth=1.3, color=COLORS["red"], label="Bus défaut")
        ax.axhline(1.0, linestyle=":", linewidth=1.0, color=COLORS["text_lo"], label="1 pu")
        ax.set_xlabel("Bus", color=COLORS["text_lo"])
        ax.set_ylabel("Tension de phase (pu)", color=COLORS["text_lo"])
        ax.set_xticks(x if len(x) <= 20 else x[::max(1, len(x)//15)])
        ymax = max(1.1, float(np.nanmax(np.abs(vabc))) + 0.05) if vabc.size else 1.1
        ax.set_ylim(0.0, ymax)
        ax.legend(fontsize=8, loc="best")
        self.fault_canvas.fig.tight_layout()
        self.fault_canvas.draw_idle()


    def refresh_stability_combos(self) -> None:
        self.fault_bus_combo.clear()
        self.fault_line_combo.clear()
        if self.data is None:
            self.fault_bus_combo.addItem("Charger données")
            self.fault_line_combo.addItem("Charger données")
            return
        for i in range(self.data.nbus):
            self.fault_bus_combo.addItem(f"Bus {int(self.data.busdata[i, 0])}", int(self.data.busdata[i, 0]))
        for i, row in enumerate(self.data.linedata):
            self.fault_line_combo.addItem(f"L{i+1}: Bus {int(row[0])} - Bus {int(row[1])}", i + 1)
        self.stab_status.setText(f"Données chargées : {self.data.nbus} bus, {self.data.linedata.shape[0]} lignes.")

    def run_stability(self) -> None:
        if not self.require_data():
            return
        if self.data.gendata is None:
            self.show_error("Stabilité", "gendata est manquant dans ce système.")
            return
        try:

            try:
                newton_raphson_polar(self.data, tol=1e-3, maxiter=100)
            except Exception:
                fast_decoupled_load_flow(self.data, tol=1e-3, maxiter=100)
            method = "rk4" if self.method_combo.currentIndex() == 1 else "euler"
            result = transient_stability(
                self.data,
                fault_bus=int(self.fault_bus_combo.currentData()),
                fault_line=int(self.fault_line_combo.currentData()),
                clearing_time=safe_float(self.te_edit.text(), 0.2),
                simulation_time=safe_float(self.ts_edit.text(), 0.5),
                dt=safe_float(self.dt_edit.text(), 0.01),
                method=method,
            )
            self.last_stability_result = result
            self.plot_stability(result)

            omega_final = np.asarray(result["omega"])[:, -1]
            omega_ok = bool(np.all(np.abs(omega_final - 1.0) < 0.05))

            if result["stable"] and omega_ok:
                msg = "SYSTÈME STABLE"
                color = COLORS["green"]
            elif result["stable"] and not omega_ok:
                msg = "STABILITÉ MARGINALE"
                color = COLORS["gold"]
            else:
                msg = "SYSTÈME INSTABLE"
                color = COLORS["red"]

            self.stab_status.setStyleSheet(f"color:{color}; font-size:16px; font-weight:800;")
            self.stab_status.setText(msg)
        except Exception as exc:
            self.show_error("Stabilité", str(exc))


    def run_critical_time_search(self) -> None:
        if not self.require_data():
            return
        if self.data.gendata is None:
            self.show_error("Stabilité", "gendata est manquant dans ce système.")
            return
        try:
            try:
                newton_raphson_polar(self.data, tol=1e-3, maxiter=100)
            except Exception:
                fast_decoupled_load_flow(self.data, tol=1e-3, maxiter=100)
            method = "rk4" if self.method_combo.currentIndex() == 1 else "euler"
            tmax = safe_float(self.ts_edit.text(), 0.5)
            dt = safe_float(self.dt_edit.text(), 0.01)
            result = estimate_critical_clearing_time(self.data, fault_bus=int(self.fault_bus_combo.currentData()), fault_line=int(self.fault_line_combo.currentData()), simulation_time=tmax, dt=dt, method=method, search_min=0.0, search_max=tmax, iterations=16)
            tc = result.get("critical_time")
            upper = result.get("upper_unstable_time")
            if tc is None:
                text = result.get("message", "Temps critique non trouvé.")
                color = COLORS["red"]
            elif upper is None:
                text = f"Temps critique > {tc:.4f} s. Le système reste stable jusqu'à Tmax."
                color = COLORS["green"]
            else:
                text = f"Temps critique estimé : {tc:.4f} s. Première borne instable : {upper:.4f} s."
                color = COLORS["gold"]
            self.critical_status.setStyleSheet(f"color:{color}; font-size:13px; font-weight:800; padding:6px;")
            self.critical_status.setText(text)
            cases = result.get("cases", {})
            if cases:
                best_key = min(cases.keys(), key=lambda k: abs(float(k) - float(tc or 0.0)))
                self.last_stability_result = cases[best_key]
                self.plot_stability(cases[best_key])
        except Exception as exc:
            self.show_error("Recherche du temps critique", str(exc))


    def fill_matrix_table(self, matrix: np.ndarray, headers: list[str] | None = None) -> None:
        arr = np.asarray(matrix)
        rows, cols = arr.shape
        self.matrix_table.setRowCount(rows)
        self.matrix_table.setColumnCount(cols)
        if headers is None:
            headers = [f"Bus {i+1}" for i in range(cols)]
        self.matrix_table.setHorizontalHeaderLabels(headers)
        formatted = matrix_to_strings(arr, digits=3)
        for i in range(rows):
            for j in range(cols):
                self.matrix_table.setItem(i, j, QTableWidgetItem(formatted[i][j]))
        self.matrix_table.resizeColumnsToContents()

    def plot_voltage_profile(self, res: dict) -> None:

        self.voltage_canvas.clear("Profil de tension")
        ax = self.voltage_canvas.ax
        vm = np.asarray(res["Vm"], dtype=float)
        x = np.arange(1, len(vm) + 1)

        raw_types = self.data.busdata[:, 1].astype(int) if self.data is not None else np.zeros(len(vm), dtype=int)
        colors = []
        labels_seen = set()
        label_by_type = {1: "Slack", 2: "PV", 0: "PQ", 3: "Slack"}
        color_by_type = {1: "#e74c3c", 3: "#e74c3c", 0: "#2f80ed", 2: "#2ecc71"}

        for t in raw_types:

            if 3 in raw_types:
                mapped = 1 if t == 3 else 2 if t == 2 else 0
            else:
                mapped = int(t)
            colors.append(color_by_type.get(mapped, "#2f80ed"))

        bars = ax.bar(x, vm, width=0.65, color=colors, edgecolor=COLORS["border"], linewidth=0.8)


        for i, t in enumerate(raw_types):
            if 3 in raw_types:
                mapped = 1 if t == 3 else 2 if t == 2 else 0
            else:
                mapped = int(t)
            label = label_by_type.get(mapped, "Bus")
            if label not in labels_seen and i < len(bars):
                bars[i].set_label(label)
                labels_seen.add(label)

        ax.axhline(1.05, linestyle="--", linewidth=1.2, color=COLORS["gold"], label="Limite haute 1.05 pu")
        ax.axhline(0.95, linestyle="--", linewidth=1.2, color=COLORS["gold"], label="Limite basse 0.95 pu")

        ax.set_xlabel("Bus", color=COLORS["text_lo"])
        ax.set_ylabel("|V| (pu)", color=COLORS["text_lo"])
        ax.set_xticks(x)
        if len(x) > 25:
            step = max(1, len(x) // 15)
            ax.set_xticks(x[::step])
        ymin = min(0.90, float(np.nanmin(vm)) - 0.03) if vm.size else 0.90
        ymax = max(1.10, float(np.nanmax(vm)) + 0.03) if vm.size else 1.10
        ax.set_ylim(ymin, ymax)
        ax.legend(fontsize=8, loc="best")
        self.voltage_canvas.fig.tight_layout()
        self.voltage_canvas.draw_idle()

    def draw_topology(self) -> None:
        if self.data is None:
            return
        self.topology_canvas.clear("Topologie du réseau")
        ax = self.topology_canvas.ax
        if nx is None:
            for row in self.data.linedata:
                ax.plot([row[0], row[1]], [0, 0], marker="o")
            ax.set_title("NetworkX non installé", color=COLORS["gold"])
            self.topology_canvas.draw_idle()
            return
        graph = nx.Graph()
        for bus in self.data.busdata[:, 0].astype(int):
            graph.add_node(bus)
        for row in self.data.linedata:
            graph.add_edge(int(row[0]), int(row[1]))
        pos = nx.spring_layout(graph, seed=7)
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color=COLORS["text_lo"], width=1.2)
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=COLORS["blue"], node_size=280)
        nx.draw_networkx_labels(graph, pos, ax=ax, font_color="white", font_size=8)
        ax.set_axis_off()
        self.topology_canvas.draw_idle()

    def show_comparison_graph(self, kind: str) -> None:
        if not self.comparison_data:
            self.compare_canvas.clear("Lancez la comparaison pour afficher les graphes")
            return
        self.compare_canvas.clear()
        ax = self.compare_canvas.ax
        rows = self.comparison_data["rows"]
        results = self.comparison_data["results"]
        if kind == "voltages":
            for name, res in results.items():
                ax.plot(np.arange(1, len(res["Vm"]) + 1), res["Vm"], marker="o", label=name)
            ax.set_title("Profils de tensions", color=COLORS["text_hi"])
            ax.set_xlabel("Bus", color=COLORS["text_lo"])
            ax.set_ylabel("|V| (pu)", color=COLORS["text_lo"])
            ax.legend()
        elif kind == "losses":
            names = [r["method"] for r in rows]
            vals = [r["losses_p"] for r in rows]
            ax.bar(names, vals)
            ax.set_title("Pertes actives", color=COLORS["text_hi"])
            ax.set_ylabel("MW", color=COLORS["text_lo"])
            ax.tick_params(axis="x", rotation=20)
        else:
            names = [r["method"] for r in rows]
            vals = [r["time_s"] for r in rows]
            ax.bar(names, vals)
            ax.set_title("Temps d'exécution", color=COLORS["text_hi"])
            ax.set_ylabel("s", color=COLORS["text_lo"])
            ax.tick_params(axis="x", rotation=20)
        self.compare_canvas.fig.tight_layout()
        self.compare_canvas.draw_idle()

    def plot_stability(self, result: dict) -> None:

        show_omega = self.graph_combo.currentIndex() == 1
        title = "Vitesse angulaire ω" if show_omega else "Différences des angles rotoriques Δδ"
        self.stab_canvas.clear(title)

        ax = self.stab_canvas.ax
        t = np.asarray(result["time"], dtype=float)
        gen_bus = result.get("gen_bus", None)

        if show_omega:
            values = np.asarray(result["omega"], dtype=float)
            for k in range(values.shape[0]):
                label = f"Gen Bus {int(gen_bus[k])}" if gen_bus is not None else f"Gen {k + 1}"
                ax.plot(t, values[k, :], linewidth=1.8, label=label)
            ax.axhline(1.0, linestyle="--", linewidth=1.0, color=COLORS["text_hi"])
            ax.set_ylabel("ω (pu)", color=COLORS["text_lo"])
        else:
            if "delta_plot_deg" in result:
                values = np.asarray(result["delta_plot_deg"], dtype=float)
            else:
                delta_deg = np.rad2deg(np.asarray(result["delta"], dtype=float))
                values = delta_deg - delta_deg[0:1, :] if delta_deg.shape[0] > 1 else delta_deg
            for k in range(values.shape[0]):
                label = f"Gen Bus {int(gen_bus[k])}" if gen_bus is not None else f"Gen {k + 1}"
                ax.plot(t, values[k, :], linewidth=1.8, label=label)
            ax.set_ylabel("Δδ (deg)", color=COLORS["text_lo"])

        te = safe_float(self.te_edit.text(), 0.2)
        if t.size:
            ax.axvline(te, linestyle="--", linewidth=1.2, color=COLORS["red"] if show_omega else COLORS["text_hi"])
            ylims = ax.get_ylim()
            ax.text(te, ylims[1] - 0.08 * (ylims[1] - ylims[0]), f"  Te={te:.2f}s", color=COLORS["text_hi"], fontsize=8)
            ax.set_xlim(0, float(np.max(t)))

        status_text = "SYSTÈME STABLE" if result.get("stable", False) else "SYSTÈME INSTABLE"
        status_color = COLORS["green"] if result.get("stable", False) else COLORS["red"]
        xlims = ax.get_xlim()
        ylims = ax.get_ylim()
        ax.text(
            (xlims[0] + xlims[1]) / 2.0,
            ylims[0] + 0.08 * (ylims[1] - ylims[0]),
            status_text,
            color="white",
            fontsize=10,
            fontweight="bold",
            ha="center",
            bbox={"facecolor": status_color, "edgecolor": "white", "alpha": 0.85},
        )

        ax.set_xlabel("Temps (s)", color=COLORS["text_lo"])
        ax.text(
            0.02,
            0.96,
            f"Écart max = {result.get('max_angle_diff', 0.0):.2f}°",
            transform=ax.transAxes,
            color=COLORS["text_lo"],
            fontsize=8,
            va="top",
            bbox={"facecolor": COLORS["bg_card"], "edgecolor": COLORS["border"], "alpha": 0.75},
        )
        ax.legend(fontsize=8)
        self.stab_canvas.fig.tight_layout()
        self.stab_canvas.draw_idle()

    def export_report_dialog(self) -> None:

        if not self.require_data():
            return
        default_name = Path(self.current_file).stem if self.current_file else "rapport_powerflow"
        output, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le rapport PDF",
            str(Path.home() / f"rapport_{default_name}.pdf"),
            "PDF (*.pdf)",
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
        try:
            export_pdf_report(
                output_path=output,
                data=self.data,
                current_file=self.current_file,
                powerflow_result=self.last_powerflow_result,
                comparison_data=self.comparison_data,
                fault_result=self.last_fault_result,
                matrix_name=self.last_matrix_name,
            )
            QMessageBox.information(self, "Export PDF", f"Rapport exporté avec succès :\n{output}")
        except Exception as exc:
            self.show_error("Export PDF", str(exc))

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
