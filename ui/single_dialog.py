"""
Minimalist Nottorney Dialog
LESS IS BEST - Single dialog for all operations
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, Qt
)
from aqt import mw

# Minimalist stylesheet - dark, clean, simple
MINIMAL_STYLE = """
QDialog {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
    font-size: 14px;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#status {
    color: #888;
    font-size: 13px;
}

QPushButton {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 12px 24px;
    color: #e0e0e0;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #333;
    border-color: #555;
}

QPushButton#primary {
    background-color: #4caf50;
    border: none;
    color: white;
    font-weight: bold;
}

QPushButton#primary:hover {
    background-color: #45a049;
}

QPushButton#primary:disabled {
    background-color: #2a4a2b;
    color: #666;
}

QPushButton#secondary {
    background-color: transparent;
    border: none;
    color: #888;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton#secondary:hover {
    color: #aaa;
}

QLineEdit {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 10px;
    color: #e0e0e0;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #4caf50;
}

QProgressBar {
    border: 1px solid #404040;
    border-radius: 6px;
    background-color: #2a2a2a;
    text-align: center;
    color: #e0e0e0;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #4caf50;
    border-radius: 5px;
}

QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #404040;
    border-radius: 6px;
    outline: none;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #333;
}

QListWidget::item:hover {
    background-color: #333;
}

QListWidget::item:selected {
    background-color: #4caf50;
    color: white;
}
"""


class MinimalNottorneyDialog(QDialog):
    """
    Single dialog for all Nottorney operations
    Minimal UI - maximum clarity
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(MINIMAL_STYLE)
        
        self.decks = []
        self.is_logged_in = False
        self.is_syncing = False
        self.show_advanced = False
        
        self.setup_ui()
        self.check_login()
    
    def setup_ui(self):
        """Minimal UI setup"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Nottorney")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Status line (dynamic)
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Login section (shown when logged out)
        self.login_widget = self.create_login_section()
        layout.addWidget(self.login_widget)
        
        # Sync section (shown when logged in)
        self.sync_widget = self.create_sync_section()
        layout.addWidget(self.sync_widget)
        
        # Advanced section (hidden by default)
        self.advanced_widget = self.create_advanced_section()
        layout.addWidget(self.advanced_widget)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Bottom actions
        bottom = QHBoxLayout()
        
        self.advanced_btn = QPushButton("Browse Decks")
        self.advanced_btn.setObjectName("secondary")
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        self.advanced_btn.hide()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("secondary")
        self.close_btn.clicked.connect(self.accept)
        
        bottom.addWidget(self.advanced_btn)
        bottom.addStretch()
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
    def create_login_section(self):
        """Minimal login - inline, not separate dialog"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primary")
        self.login_btn.clicked.connect(self.handle_login)
        
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        
        widget.setLayout(layout)
        widget.hide()  # Hidden by default
        return widget
    
    def create_sync_section(self):
        """Main sync interface - minimal, clear"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.sync_status = QLabel("")
        
        self.sync_btn = QPushButton("Download All")
        self.sync_btn.setObjectName("primary")
        self.sync_btn.clicked.connect(self.sync_all)
        
        layout.addWidget(self.sync_status)
        layout.addWidget(self.sync_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_advanced_section(self):
        """Browse decks - only shown when requested"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Simple search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        
        # Deck list (simple)
        self.deck_list = QListWidget()
        
        # Single action
        download_btn = QPushButton("Download Selected")
        download_btn.setObjectName("primary")
        download_btn.clicked.connect(self.download_selected)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.deck_list)
        layout.addWidget(download_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def check_login(self):
        """Check if user is logged in and show appropriate UI"""
        # TODO: Replace with actual config check
        # self.is_logged_in = config.is_logged_in()
        
        if self.is_logged_in:
            self.show_sync_interface()
        else:
            self.show_login_interface()
    
    def show_login_interface(self):
        """Show minimal login"""
        self.status_label.setText("Sign in to sync your decks")
        self.login_widget.show()
        self.sync_widget.hide()
        self.advanced_widget.hide()
        self.advanced_btn.hide()
    
    def show_sync_interface(self):
        """Show main sync interface"""
        self.login_widget.hide()
        self.sync_widget.show()
        self.advanced_btn.show()
        
        # Load deck status
        self.load_deck_status()
    
    def handle_login(self):
        """Handle login - minimal feedback"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.status_label.setText("❌ Enter email and password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        
        # TODO: Actual login
        # try:
        #     api.login(email, password)
        #     self.is_logged_in = True
        #     self.show_sync_interface()
        # except Exception as e:
        #     self.status_label.setText(f"❌ {str(e)}")
        # finally:
        #     self.login_btn.setEnabled(True)
        #     self.login_btn.setText("Sign In")
        
        # Mock success
        self.is_logged_in = True
        self.show_sync_interface()
    
    def load_deck_status(self):
        """Load and display deck status - minimal"""
        # TODO: Load actual decks
        # self.decks = api.get_purchased_decks()
        
        # Mock data
        total = 12
        new = 3
        updates = 2
        
        if new + updates == 0:
            self.status_label.setText("✓ All decks synced")
            self.sync_status.setText("Everything is up to date")
            self.sync_btn.setText("All Synced")
            self.sync_btn.setEnabled(False)
        else:
            parts = []
            if new > 0:
                parts.append(f"{new} new")
            if updates > 0:
                parts.append(f"{updates} updates")
            
            status_text = " + ".join(parts)
            self.status_label.setText(f"{total} total decks")
            self.sync_status.setText(f"{status_text} available")
            self.sync_btn.setText(f"Download ({new + updates})")
            self.sync_btn.setEnabled(True)
    
    def sync_all(self):
        """Download all new/updated decks"""
        if self.is_syncing:
            return
        
        # Simple confirm
        reply = QMessageBox.question(
            self, "Confirm",
            "Download all new and updated decks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.is_syncing = True
        self.sync_btn.setEnabled(False)
        self.progress.show()
        
        # TODO: Actual sync logic
        # Mock progress
        self.progress.setMaximum(5)
        for i in range(6):
            self.progress.setValue(i)
            self.progress.setFormat(f"Downloading {i}/5...")
            # In real code: download each deck
        
        self.is_syncing = False
        self.progress.hide()
        self.load_deck_status()
        
        QMessageBox.information(self, "Complete", "All decks synced!")
    
    def toggle_advanced(self):
        """Show/hide advanced deck browser"""
        self.show_advanced = not self.show_advanced
        
        if self.show_advanced:
            self.advanced_widget.show()
            self.advanced_btn.setText("Hide Decks")
            self.setMinimumSize(500, 600)
            self.populate_deck_list()
        else:
            self.advanced_widget.hide()
            self.advanced_btn.setText("Browse Decks")
            self.setMinimumSize(500, 400)
    
    def populate_deck_list(self):
        """Populate deck list - minimal display"""
        self.deck_list.clear()
        
        # TODO: Use actual decks
        # for deck in self.decks:
        
        # Mock decks
        mock_decks = [
            "Contract Law Essentials",
            "Constitutional Law",
            "Criminal Procedure",
            "Civil Procedure Basics",
            "Evidence Rules",
        ]
        
        for deck in mock_decks:
            item = QListWidgetItem(deck)
            self.deck_list.addItem(item)
    
    def filter_decks(self, text):
        """Simple search filter"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def download_selected(self):
        """Download selected decks from list"""
        selected = self.deck_list.selectedItems()
        
        if not selected:
            self.status_label.setText("Select decks to download")
            return
        
        # Simple confirm
        count = len(selected)
        reply = QMessageBox.question(
            self, "Confirm",
            f"Download {count} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Download logic
            QMessageBox.information(self, "Complete", f"Downloaded {count} deck(s)")


# Example usage
if __name__ == "__main__":
    from aqt.qt import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dialog = MinimalNottorneyDialog()
    dialog.show()
    sys.exit(app.exec())