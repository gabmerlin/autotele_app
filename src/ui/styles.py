"""
Styles et thèmes pour l'interface AutoTele
Police professionnelle moderne (pas Arial ou Inter selon les préférences utilisateur)
"""

# Police professionnelle et moderne : Segoe UI (Windows native, très professionnelle)
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10

STYLE_SHEET = f"""
QMainWindow {{
    background-color: #f5f5f7;
}}

/* Styles généraux */
QWidget {{
    font-family: '{FONT_FAMILY}';
    font-size: {FONT_SIZE}pt;
    color: #1d1d1f;
}}

/* Boutons principaux */
QPushButton {{
    background-color: #0071e3;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    min-width: 100px;
}}

QPushButton:hover {{
    background-color: #0077ed;
}}

QPushButton:pressed {{
    background-color: #006edb;
}}

QPushButton:disabled {{
    background-color: #e0e0e0;
    color: #999999;
}}

/* Boutons secondaires */
QPushButton[class="secondary"] {{
    background-color: #f5f5f7;
    color: #0071e3;
    border: 2px solid #0071e3;
}}

QPushButton[class="secondary"]:hover {{
    background-color: #e8e8ed;
}}

/* Boutons danger */
QPushButton[class="danger"] {{
    background-color: #ff3b30;
}}

QPushButton[class="danger"]:hover {{
    background-color: #ff453a;
}}

/* Champs de saisie */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: #0071e3;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid #0071e3;
    padding: 7px 11px;
}}

/* Labels */
QLabel {{
    color: #1d1d1f;
}}

QLabel[class="title"] {{
    font-size: 24pt;
    font-weight: 700;
    color: #1d1d1f;
    margin-bottom: 10px;
}}

QLabel[class="subtitle"] {{
    font-size: 14pt;
    font-weight: 600;
    color: #1d1d1f;
    margin-bottom: 8px;
}}

QLabel[class="hint"] {{
    font-size: 9pt;
    color: #86868b;
}}

QLabel[class="error"] {{
    color: #ff3b30;
    font-weight: 500;
}}

QLabel[class="success"] {{
    color: #34c759;
    font-weight: 500;
}}

/* Tables */
QTableWidget {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    gridline-color: #e5e5ea;
}}

QTableWidget::item {{
    padding: 8px;
}}

QTableWidget::item:selected {{
    background-color: #0071e3;
    color: white;
}}

QHeaderView::section {{
    background-color: #f5f5f7;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #d2d2d7;
    font-weight: 600;
}}

/* Listes */
QListWidget {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
}}

QListWidget::item {{
    padding: 10px;
    border-bottom: 1px solid #e5e5ea;
}}

QListWidget::item:selected {{
    background-color: #0071e3;
    color: white;
}}

QListWidget::item:hover {{
    background-color: #f5f5f7;
}}

/* ComboBox */
QComboBox {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 150px;
}}

QComboBox:hover {{
    border: 1px solid #0071e3;
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox::down-arrow {{
    image: url(none);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #1d1d1f;
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid #d2d2d7;
    selection-background-color: #0071e3;
}}

/* CheckBox */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid #d2d2d7;
    border-radius: 4px;
    background-color: white;
}}

QCheckBox::indicator:checked {{
    background-color: #0071e3;
    border-color: #0071e3;
    image: url(none);
}}

QCheckBox::indicator:hover {{
    border-color: #0071e3;
}}

/* GroupBox */
QGroupBox {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    margin-top: 20px;
    padding: 20px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: #1d1d1f;
}}

/* TabWidget */
QTabWidget::pane {{
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    background-color: white;
    padding: 10px;
}}

QTabBar::tab {{
    background-color: #f5f5f7;
    border: 1px solid #d2d2d7;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: white;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: #e8e8ed;
}}

/* ScrollBar */
QScrollBar:vertical {{
    background-color: #f5f5f7;
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: #d2d2d7;
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #b0b0b5;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ProgressBar */
QProgressBar {{
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    text-align: center;
    background-color: #f5f5f7;
}}

QProgressBar::chunk {{
    background-color: #0071e3;
    border-radius: 7px;
}}

/* MenuBar */
QMenuBar {{
    background-color: white;
    border-bottom: 1px solid #d2d2d7;
}}

QMenuBar::item {{
    padding: 8px 12px;
}}

QMenuBar::item:selected {{
    background-color: #f5f5f7;
}}

QMenu {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
}}

QMenu::item {{
    padding: 8px 25px;
}}

QMenu::item:selected {{
    background-color: #0071e3;
    color: white;
}}

/* StatusBar */
QStatusBar {{
    background-color: #f5f5f7;
    border-top: 1px solid #d2d2d7;
}}

/* ToolTip */
QToolTip {{
    background-color: #1d1d1f;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 9pt;
}}

/* Cards personnalisés */
QFrame[class="card"] {{
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    padding: 20px;
}}

QFrame[class="card-hover"]:hover {{
    border-color: #0071e3;
}}

/* Séparateurs */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: #d2d2d7;
}}
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

