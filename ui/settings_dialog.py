"""
Settings Dialog for Nottorney Addon
Features: General settings, Protected Fields, Notification preferences
Version: 1.0.0
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QTabWidget, QWidget, QCheckBox, QSpinBox, QGroupBox,
    QFormLayout, QComboBox
)
from aqt import mw

from ..api_client import api, set_access_token, NottorneyAPIError
from ..config import config


class SettingsDialog(QDialog):
    """Settings dialog with multiple configuration tabs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Nottorney Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; }")
        
        # Create tabs
        self.general_tab = self.create_general_tab()
        self.protected_fields_tab = self.create_protected_fields_tab()
        self.sync_tab = self.create_sync_tab()
        
        self.tabs.addTab(self.general_tab, "🔧 General")
        self.tabs.addTab(self.protected_fields_tab, "🛡️ Protected Fields")
        self.tabs.addTab(self.sync_tab, "🔄 Sync")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 10px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_general_tab(self):
        """Create General settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # UI Mode
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        
        self.ui_mode_combo = QComboBox()
        self.ui_mode_combo.addItem("Tabbed (Modern)", "tabbed")
        self.ui_mode_combo.addItem("Minimal (Legacy)", "minimal")
        ui_layout.addRow("UI Mode:", self.ui_mode_combo)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Update Checking
        update_group = QGroupBox("Update Checking")
        update_layout = QFormLayout()
        
        self.auto_check_updates = QCheckBox("Automatically check for deck updates")
        update_layout.addRow(self.auto_check_updates)
        
        self.update_interval = QSpinBox()
        self.update_interval.setMinimum(1)
        self.update_interval.setMaximum(168)  # 1 week max
        self.update_interval.setSuffix(" hours")
        update_layout.addRow("Check interval:", self.update_interval)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # Auto Sync
        sync_group = QGroupBox("Progress Sync")
        sync_layout = QFormLayout()
        
        self.auto_sync_enabled = QCheckBox("Automatically sync study progress")
        sync_layout.addRow(self.auto_sync_enabled)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_protected_fields_tab(self):
        """Create Protected Fields settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Protected fields are preserved during sync updates.\n"
            "Add field names that you want to keep from being overwritten."
        )
        instructions.setStyleSheet("color: #666; padding: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Deck selector
        deck_layout = QHBoxLayout()
        deck_label = QLabel("Select Deck:")
        deck_label.setStyleSheet("font-weight: bold;")
        deck_layout.addWidget(deck_label)
        
        self.deck_selector = QComboBox()
        self.deck_selector.setMinimumWidth(300)
        self.deck_selector.currentIndexChanged.connect(self.on_deck_selected)
        deck_layout.addWidget(self.deck_selector)
        
        deck_layout.addStretch()
        layout.addLayout(deck_layout)
        
        # Protected fields list
        fields_group = QGroupBox("Protected Fields for Selected Deck")
        fields_layout = QVBoxLayout()
        
        self.protected_fields_list = QListWidget()
        self.protected_fields_list.setStyleSheet("QListWidget::item { padding: 8px; }")
        fields_layout.addWidget(self.protected_fields_list)
        
        # Add/Remove buttons
        field_btn_layout = QHBoxLayout()
        
        self.new_field_input = QLineEdit()
        self.new_field_input.setPlaceholderText("Enter field name to protect...")
        field_btn_layout.addWidget(self.new_field_input)
        
        add_field_btn = QPushButton("➕ Add")
        add_field_btn.clicked.connect(self.add_protected_field)
        field_btn_layout.addWidget(add_field_btn)
        
        remove_field_btn = QPushButton("➖ Remove Selected")
        remove_field_btn.clicked.connect(self.remove_protected_field)
        field_btn_layout.addWidget(remove_field_btn)
        
        fields_layout.addLayout(field_btn_layout)
        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)
        
        # Fetch from server button
        fetch_btn = QPushButton("🔄 Fetch Protected Fields from Server")
        fetch_btn.clicked.connect(self.fetch_protected_fields)
        layout.addWidget(fetch_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_sync_tab(self):
        """Create Sync settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sync options
        sync_group = QGroupBox("Sync Preferences")
        sync_layout = QFormLayout()
        
        self.sync_tags = QCheckBox("Sync tags with server")
        sync_layout.addRow(self.sync_tags)
        
        self.sync_suspend = QCheckBox("Sync suspend/buried state")
        sync_layout.addRow(self.sync_suspend)
        
        self.sync_note_types = QCheckBox("Sync note type templates")
        sync_layout.addRow(self.sync_note_types)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Sync info
        info_group = QGroupBox("Sync Status")
        info_layout = QVBoxLayout()
        
        last_sync = config.get_last_update_check() or "Never"
        self.last_sync_label = QLabel(f"Last sync check: {last_sync}")
        self.last_sync_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.last_sync_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_settings(self):
        """Load current settings into UI"""
        # General tab
        ui_mode = config.get_ui_mode()
        index = self.ui_mode_combo.findData(ui_mode)
        if index >= 0:
            self.ui_mode_combo.setCurrentIndex(index)
        
        self.auto_check_updates.setChecked(config.get_auto_check_updates())
        self.update_interval.setValue(config.get_update_check_interval_hours())
        self.auto_sync_enabled.setChecked(config.get_auto_sync_enabled())
        
        # Protected fields tab - load decks
        self.load_deck_list()
        
        # Sync tab - these are placeholders for future config
        self.sync_tags.setChecked(True)
        self.sync_suspend.setChecked(True)
        self.sync_note_types.setChecked(True)
    
    def load_deck_list(self):
        """Load downloaded decks into deck selector"""
        self.deck_selector.clear()
        self.deck_selector.addItem("-- Select a deck --", None)
        
        downloaded_decks = config.get_downloaded_decks()
        
        for deck_id, deck_info in downloaded_decks.items():
            # Get deck name from Anki if possible
            anki_deck_id = deck_info.get('anki_deck_id')
            deck_name = f"Deck {deck_id[:8]}"
            
            if anki_deck_id and mw.col:
                try:
                    deck = mw.col.decks.get(int(anki_deck_id))
                    if deck:
                        deck_name = deck['name']
                except:
                    pass
            
            version = deck_info.get('version', '?')
            display_text = f"{deck_name} (v{version})"
            self.deck_selector.addItem(display_text, deck_id)
    
    def on_deck_selected(self, index):
        """Handle deck selection change"""
        self.protected_fields_list.clear()
        
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            return
        
        # Load protected fields for this deck
        protected = config.get_protected_fields(deck_id)
        
        for field_name in protected:
            item = QListWidgetItem(f"🛡️ {field_name}")
            item.setData(Qt.ItemDataRole.UserRole, field_name)
            self.protected_fields_list.addItem(item)
    
    def add_protected_field(self):
        """Add a new protected field"""
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        field_name = self.new_field_input.text().strip()
        if not field_name:
            QMessageBox.warning(self, "Empty Field", "Please enter a field name.")
            return
        
        # Get current protected fields
        protected = list(config.get_protected_fields(deck_id))
        
        if field_name in protected:
            QMessageBox.warning(self, "Already Protected", f"'{field_name}' is already protected.")
            return
        
        # Add to list
        protected.append(field_name)
        config.save_protected_fields(deck_id, protected)
        
        # Update UI
        item = QListWidgetItem(f"🛡️ {field_name}")
        item.setData(Qt.ItemDataRole.UserRole, field_name)
        self.protected_fields_list.addItem(item)
        
        self.new_field_input.clear()
        QMessageBox.information(self, "Added", f"'{field_name}' is now protected.")
    
    def remove_protected_field(self):
        """Remove selected protected field"""
        current = self.protected_fields_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a field to remove.")
            return
        
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            return
        
        field_name = current.data(Qt.ItemDataRole.UserRole)
        
        # Remove from config
        protected = list(config.get_protected_fields(deck_id))
        if field_name in protected:
            protected.remove(field_name)
            config.save_protected_fields(deck_id, protected)
        
        # Update UI
        row = self.protected_fields_list.row(current)
        self.protected_fields_list.takeItem(row)
        
        QMessageBox.information(self, "Removed", f"'{field_name}' is no longer protected.")
    
    def fetch_protected_fields(self):
        """Fetch protected fields from server"""
        deck_id = self.deck_selector.currentData()
        if not deck_id:
            QMessageBox.warning(self, "No Deck Selected", "Please select a deck first.")
            return
        
        token = config.get_access_token()
        if not token:
            QMessageBox.warning(self, "Not Logged In", "Please login first.")
            return
        
        set_access_token(token)
        
        try:
            result = api.get_protected_fields(deck_id)
            
            if result.get('success'):
                server_fields = result.get('protected_fields', [])
                
                if server_fields:
                    # Update local config
                    config.save_protected_fields(deck_id, server_fields)
                    
                    # Reload UI
                    self.on_deck_selected(self.deck_selector.currentIndex())
                    
                    QMessageBox.information(
                        self, "Success",
                        f"Loaded {len(server_fields)} protected field(s) from server."
                    )
                else:
                    QMessageBox.information(
                        self, "No Fields",
                        "No protected fields configured on server for this deck."
                    )
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch from server.")
        
        except NottorneyAPIError as e:
            QMessageBox.critical(self, "API Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch: {e}")
    
    def save_settings(self):
        """Save all settings"""
        try:
            # General settings
            ui_mode = self.ui_mode_combo.currentData()
            config.set_ui_mode(ui_mode)
            
            config.set_auto_check_updates(self.auto_check_updates.isChecked())
            config.set_update_check_interval_hours(self.update_interval.value())
            config.set_auto_sync_enabled(self.auto_sync_enabled.isChecked())
            
            # Protected fields are saved immediately when added/removed
            
            # Show success
            QMessageBox.information(
                self, "Settings Saved",
                "Settings saved successfully!\n\n"
                "Some changes may require restarting Anki."
            )
            
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")


def show_settings_dialog(parent=None):
    """Show the settings dialog"""
    dialog = SettingsDialog(parent or mw)
    dialog.exec()
