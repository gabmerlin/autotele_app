"""
ComboBox simple et propre
"""
from PyQt6.QtWidgets import QComboBox


class SearchableComboBox(QComboBox):
    """ComboBox standard (sans recherche pour éviter les bugs UI)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ComboBox simple et propre
        self.setEditable(False)

