"""
Styles et thèmes pour l'interface AutoTele
Police professionnelle moderne (pas Arial ou Inter selon les préférences utilisateur)
"""

# Police professionnelle et moderne : Segoe UI (Windows native, très professionnelle)
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10

STYLE_SHEET = """
/* Styles minimaux pour éviter les bugs de rendu PyQt6 */

QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    font-family: 'Segoe UI';
    font-size: 10pt;
}

QPushButton {
    background-color: #0071e3;
    color: white;
    border: 1px solid #0071e3;
    padding: 6px 12px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #0077ed;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: white;
    border: 1px solid #cccccc;
    padding: 4px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #0071e3;
}

QGroupBox {
    background-color: white;
    border: 1px solid #cccccc;
    margin-top: 10px;
    padding: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
}

QTabWidget::pane {
    border: 1px solid #cccccc;
    background-color: white;
}

QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #cccccc;
    border-bottom: none;
    padding: 6px 12px;
    margin-right: 1px;
}

QTabBar::tab:selected {
    background-color: white;
}

QComboBox {
    background-color: white;
    border: 1px solid #cccccc;
    padding: 4px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #cccccc;
}

QListWidget {
    background-color: white;
    border: 1px solid #cccccc;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #0071e3;
    color: white;
}

QTableWidget {
    background-color: white;
    border: 1px solid #cccccc;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #0071e3;
    color: white;
}

QHeaderView::section {
    background-color: #f0f0f0;
    padding: 4px;
    border: 1px solid #cccccc;
}

QStatusBar {
    background-color: #f0f0f0;
    border-top: 1px solid #cccccc;
}
"""


def get_icon_color():
    """Couleur pour les icônes"""
    return "#0071e3"


def get_success_color():
    """Couleur de succès"""
    return "#34c759"


def get_warning_color():
    """Couleur d'avertissement"""
    return "#ff9500"


def get_error_color():
    """Couleur d'erreur"""
    return "#ff3b30"


def get_text_color():
    """Couleur du texte principal"""
    return "#1d1d1f"


def get_secondary_text_color():
    """Couleur du texte secondaire"""
    return "#86868b"

