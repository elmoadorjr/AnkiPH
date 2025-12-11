"""
Minimal Dialog for Nottorney Addon
"""

from aqt. qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt
)
from aqt import mw
from .. api_client import api
from ..config import config
from ..deck_importer import import_deck


class MinimalNottorneyDialog(QDialog):
    """Minimal dialog for Nottorney operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney")
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Nottorney")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        layout.addWidget(self.search_input)
        
        # Deck list
        self.deck_list = QListWidget()
        layout.addWidget(self.deck_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        download_btn = QPushButton("Download")
        download_btn.clicked. connect(self.download_deck)
        button_layout.addWidget(download_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.load_decks()
    
    def load_decks(self):
        """Load decks from API"""
        try:
            result = api.browse_decks()
            if result.get('success'):
                decks = result.get('decks', [])
                for deck in decks:
                    item = QListWidgetItem(deck. get('name', 'Unknown'))
                    item.setData(Qt.UserRole, deck.get('id'))
                    self.deck_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load decks: {str(e)}")
    
    def filter_decks(self):
        """Filter deck list"""
        query = self.search_input.text().lower()
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item. setHidden(query not in item.text().lower())
    
    def download_deck(self):
        """Download selected deck"""
        current = self.deck_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Select a deck")
            return
        
        deck_id = current.data(Qt.UserRole)
        try:
            result = api.download_deck(deck_id)
            if result.get('success'):
                import_deck(result.get('deck_data'))
                QMessageBox.information(self, "Success", "Deck downloaded!")
            else:
                QMessageBox. warning(self, "Error", result.get('message', 'Download failed'))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))