"""
Styles modernes et professionnels pour AutoTele
Thème élégant avec dégradés et ombres
"""

# Police moderne et professionnelle
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10

# Palette de couleurs moderne
COLORS = {
    # Couleurs principales
    "primary": "#4A90E2",  # Bleu moderne
    "primary_hover": "#357ABD",
    "primary_dark": "#2E5F8D",
    
    # Couleurs secondaires
    "success": "#4CAF50",  # Vert succès
    "warning": "#FF9800",  # Orange avertissement
    "danger": "#F44336",   # Rouge danger
    "info": "#2196F3",     # Bleu info
    
    # Couleurs neutres
    "background": "#F5F7FA",
    "surface": "#FFFFFF",
    "surface_hover": "#F8FAFB",
    
    # Texte
    "text_primary": "#2C3E50",
    "text_secondary": "#7F8C8D",
    "text_disabled": "#BDC3C7",
    
    # Bordures
    "border": "#E1E8ED",
    "border_hover": "#CBD6E2",
}

MODERN_STYLE = f"""
/* ========================================
   STYLES GÉNÉRAUX
   ======================================== */

QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    font-family: '{FONT_FAMILY}';
    font-size: {FONT_SIZE}pt;
    color: {COLORS['text_primary']};
}}

/* ========================================
   BOUTONS
   ======================================== */

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLORS['primary']},
                                stop:1 {COLORS['primary_hover']});
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 500;
    min-width: 100px;
    font-size: 10pt;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLORS['primary_hover']},
                                stop:1 {COLORS['primary_dark']});
}}

QPushButton:pressed {{
    background: {COLORS['primary_dark']};
    padding: 11px 19px 9px 21px;
}}

QPushButton:disabled {{
    background: {COLORS['text_disabled']};
    color: white;
}}

/* Bouton succès */
QPushButton[class="success"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #4CAF50,
                                stop:1 #388E3C);
}}

QPushButton[class="success"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #388E3C,
                                stop:1 #2E7D32);
}}

/* Bouton secondaire */
QPushButton[class="secondary"] {{
    background: white;
    color: {COLORS['primary']};
    border: 2px solid {COLORS['primary']};
}}

QPushButton[class="secondary"]:hover {{
    background: {COLORS['surface_hover']};
    border: 2px solid {COLORS['primary_hover']};
}}

/* Bouton danger */
QPushButton[class="danger"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F44336,
                                stop:1 #D32F2F);
}}

QPushButton[class="danger"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #D32F2F,
                                stop:1 #C62828);
}}

/* ========================================
   CHAMPS DE SAISIE
   ======================================== */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    selection-background-color: {COLORS['primary']};
    font-size: 10pt;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['surface_hover']};
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border: 2px solid {COLORS['border_hover']};
}}

/* ========================================
   LABELS ET TEXTES
   ======================================== */

QLabel {{
    color: {COLORS['text_primary']};
}}

QLabel[class="title"] {{
    font-size: 24pt;
    font-weight: 700;
    color: {COLORS['text_primary']};
    margin-bottom: 5px;
}}

QLabel[class="subtitle"] {{
    font-size: 14pt;
    font-weight: 600;
    color: {COLORS['text_primary']};
    margin-bottom: 5px;
}}

QLabel[class="hint"] {{
    font-size: 9pt;
    color: {COLORS['text_secondary']};
    font-style: italic;
}}

QLabel[class="error"] {{
    color: {COLORS['danger']};
    font-weight: 500;
    padding: 10px;
    background-color: #FFEBEE;
    border-radius: 6px;
    border-left: 4px solid {COLORS['danger']};
}}

QLabel[class="success"] {{
    color: {COLORS['success']};
    font-weight: 500;
    padding: 10px;
    background-color: #E8F5E9;
    border-radius: 6px;
    border-left: 4px solid {COLORS['success']};
}}

QLabel[class="warning"] {{
    color: {COLORS['warning']};
    font-weight: 500;
    padding: 10px;
    background-color: #FFF3E0;
    border-radius: 6px;
    border-left: 4px solid {COLORS['warning']};
}}

/* ========================================
   GROUPBOX - CARTES ÉLÉGANTES
   ======================================== */

QGroupBox {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 25px;
    padding: 20px;
    font-weight: 600;
    font-size: 11pt;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 15px;
    background-color: white;
    color: {COLORS['primary']};
    border-radius: 6px;
    left: 10px;
    top: -12px;
}}

/* ========================================
   TABS - ONGLETS MODERNES
   ======================================== */

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: white;
    padding: 10px;
    top: -1px;
}}

QTabBar::tab {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 12px 24px;
    margin-right: 3px;
    font-weight: 500;
    color: {COLORS['text_secondary']};
}}

QTabBar::tab:selected {{
    background: white;
    color: {COLORS['primary']};
    border-bottom: 3px solid {COLORS['primary']};
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background: {COLORS['surface_hover']};
    color: {COLORS['primary_hover']};
}}

/* ========================================
   LISTES
   ======================================== */

QListWidget {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 5px;
}}

QListWidget::item {{
    padding: 12px;
    border-radius: 6px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLORS['primary']},
                                stop:1 {COLORS['primary_hover']});
    color: white;
}}

QListWidget::item:hover {{
    background-color: {COLORS['surface_hover']};
}}

/* Checkboxes dans les listes */
QListWidget::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background-color: white;
}}

QListWidget::indicator:hover {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['surface_hover']};
}}

QListWidget::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNNiAxMC4yTDMuOCA4bC0xLjQgMS40TDYgMTMgMTQgNWwtMS40LTEuNHoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=);
}}

QListWidget::indicator:checked:hover {{
    background-color: {COLORS['primary_hover']};
}}

/* ========================================
   COMBOBOX - SÉLECTEURS ÉLÉGANTS
   ======================================== */

QComboBox {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    padding-right: 35px;
    min-width: 150px;
    color: {COLORS['text_primary']};
}}

QComboBox:hover {{
    border: 2px solid {COLORS['border_hover']};
}}

QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 35px;
    border: none;
    background: transparent;
}}

QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 8px 6px 0 6px;
    border-color: {COLORS['text_primary']} transparent transparent transparent;
}}

QComboBox:hover::down-arrow {{
    border-top-color: {COLORS['primary']};
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['primary']};
    selection-color: white;
    padding: 5px;
    color: {COLORS['text_primary']};
}}

QComboBox QAbstractItemView::item {{
    padding: 10px;
    border-radius: 6px;
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {COLORS['surface_hover']};
    color: {COLORS['text_primary']};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

/* ========================================
   CHECKBOX - CASES MODERNES
   ======================================== */

QCheckBox {{
    spacing: 10px;
    font-size: 10pt;
}}

QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    background-color: white;
}}

QCheckBox::indicator:hover {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['surface_hover']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: none;
}}

QCheckBox::indicator:checked:hover {{
    background-color: {COLORS['primary_hover']};
}}

/* ========================================
   TABLES - TABLEAUX ÉLÉGANTS
   ======================================== */

QTableWidget {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 10px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QTableWidget::item:hover {{
    background-color: {COLORS['surface_hover']};
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 white,
                                stop:1 {COLORS['surface_hover']});
    padding: 12px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

/* ========================================
   SCROLLBAR - BARRES DE DÉFILEMENT
   ======================================== */

QScrollBar:vertical {{
    background-color: {COLORS['background']};
    width: 14px;
    border-radius: 7px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_hover']};
    border-radius: 7px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['background']};
    height: 14px;
    border-radius: 7px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_hover']};
    border-radius: 7px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_secondary']};
}}

/* ========================================
   PROGRESSBAR - BARRES DE PROGRESSION
   ======================================== */

QProgressBar {{
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    text-align: center;
    background-color: white;
    height: 25px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {COLORS['primary']},
                                stop:1 {COLORS['primary_hover']});
    border-radius: 6px;
    margin: 1px;
}}

/* ========================================
   STATUSBAR - BARRE D'ÉTAT
   ======================================== */

QStatusBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 white,
                                stop:1 {COLORS['background']});
    border-top: 2px solid {COLORS['border']};
    padding: 5px;
    color: {COLORS['text_secondary']};
}}

/* ========================================
   DATETIME EDIT
   ======================================== */

QDateTimeEdit {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    min-width: 200px;
}}

QDateTimeEdit:focus {{
    border: 2px solid {COLORS['primary']};
}}

QDateTimeEdit::drop-down {{
    border: none;
    width: 30px;
}}

QDateTimeEdit::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
}}

/* ========================================
   TOOLTIP
   ======================================== */

QToolTip {{
    background-color: {COLORS['text_primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 9pt;
}}
"""

def get_modern_style():
    """Retourne le style moderne"""
    return MODERN_STYLE

def get_colors():
    """Retourne la palette de couleurs"""
    return COLORS

