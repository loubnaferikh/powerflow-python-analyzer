

COLORS = {
    "bg_app": "#121219",
    "bg_side": "#121219",
    "bg_panel": "#1a1a24",
    "bg_card": "#22222e",
    "bg_active": "#243057",
    "blue": "#4799ff",
    "cyan": "#1fd9e0",
    "gold": "#ffd14c",
    "green": "#40e68c",
    "red": "#eb5252",
    "purple": "#b36bff",
    "text_hi": "#f7f7ff",
    "text_lo": "#808ca6",
    "border": "#333347",
}

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {COLORS['bg_app']};
    color: {COLORS['text_hi']};
    font-family: 'Segoe UI';
}}
QFrame, QGroupBox {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QGroupBox {{
    margin-top: 18px;
    font-weight: 700;
    color: {COLORS['gold']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}
QLabel {{
    color: {COLORS['text_hi']};
    background: transparent;
    border: none;
}}
QPushButton {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_hi']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 9px 12px;
    font-weight: 700;
}}
QPushButton:hover {{
    border-color: {COLORS['blue']};
    background: {COLORS['bg_active']};
}}
QPushButton:pressed {{
    background: {COLORS['blue']};
}}
QLineEdit, QComboBox {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_hi']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
}}
QTableWidget {{
    background: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_panel']};
    color: {COLORS['text_hi']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
}}
QHeaderView::section {{
    background: {COLORS['bg_panel']};
    color: {COLORS['gold']};
    padding: 6px;
    border: 1px solid {COLORS['border']};
    font-weight: 700;
}}
QTabWidget::pane {{
    border: none;
}}
QTabBar::tab {{
    background: {COLORS['bg_panel']};
    color: {COLORS['text_lo']};
    padding: 10px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}
QTabBar::tab:selected {{
    background: {COLORS['bg_active']};
    color: {COLORS['cyan']};
}}
"""

BUTTON_STYLES = {
    "primary": f"background:{COLORS['blue']}; color:{COLORS['text_hi']};",
    "success": f"background:#1d6b42; color:{COLORS['text_hi']};",
    "danger": f"background:{COLORS['red']}; color:{COLORS['text_hi']};",
    "gold": f"background:{COLORS['gold']}; color:#171717;",
    "purple": f"background:#53317a; color:{COLORS['text_hi']};",
}
