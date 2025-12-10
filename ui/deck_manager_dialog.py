"""
Enhanced Deck Manager Dialog for Nottorney Addon
Features: Dark Mode, Bulk Downloads, Clean UI
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog,
    Qt, QTextEdit, QCheckBox, QLineEdit, QComboBox, QGroupBox,
    QSplitter, QWidget, QScrollArea, QFrame, QTabWidget
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck
import traceback


class DeckManagerDialog(QDialog):
    """Enhanced dialog for managing purchased decks with dark mode"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney Deck Manager")
        self.setMinimumSize(1000, 750)
        self.decks = []
        self.filtered_decks = []
        self.show_updates_only = False
        self.search_text = ""
        self.sort_by = "title"
        self.dark_mode = False
        
        self.setup_ui()
        self.apply_theme()
        self.load_decks()
    
    def get_light_stylesheet(self):
        """Light theme stylesheet"""
        return """
            QDialog { background-color: #f8f9fa; }
            QGroupBox {
                background-color: white; border: 1px solid #e0e0e0;
                border-radius: 8px; margin-top: 10px; padding-top: 15px;
                font-weight: bold; color: #2c3e50;
            }
            QListWidget {
                background-color: white; border: 1px solid #e0e0e0;
                border-radius: 8px; padding: 5px; outline: none; color: #2c3e50;
            }
            QListWidget::item {
                padding: 15px; border-bottom: 1px solid #f0f0f0;
                border-radius: 6px; margin: 2px; color: #2c3e50; background-color: white;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd; color: #1976d2; border: 2px solid #2196f3;
            }
            QPushButton {
                background-color: white; border: 1px solid #d0d0d0;
                border-radius: 6px; padding: 8px 16px; color: #2c3e50; font-weight: 500;
            }
            QPushButton#primaryButton {
                background-color: #4caf50; color: white; border: none; font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: white; border: 1px solid #d0d0d0;
                border-radius: 6px; padding: 8px; color: #2c3e50;
            }
            QLabel { color: #2c3e50; }
            QLabel#headerLabel { color: #2c3e50; font-size: 24px; font-weight: bold; }
            QLabel#infoLabel {
                background-color: white; border-left: 4px solid #2196f3;
                border-radius: 6px; padding: 12px; color: #2c3e50;
            }
            QLabel#statsLabel {
                background-color: #e3f2fd; border-radius: 6px;
                padding: 8px 12px; color: #1976d2; font-weight: bold;
            }
        """
    
    def get_dark_stylesheet(self):
        """Dark theme stylesheet"""
        return """
            QDialog { background-color: #1e1e1e; }
            QGroupBox {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; margin-top: 10px; padding-top: 15px;
                font-weight: bold; color: #e0e0e0;
            }
            QListWidget {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; padding: 5px; outline: none; color: #e0e0e0;
            }
            QListWidget::item {
                padding: 15px; border-bottom: 1px solid #404040;
                border-radius: 6px; margin: 2px; color: #e0e0e0; background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #1565c0; color: #ffffff; border: 2px solid #2196f3;
            }
            QPushButton {
                background-color: #2d2d2d; border: 1px solid #505050;
                border-radius: 6px; padding: 8px 16px; color: #e0e0e0; font-weight: 500;
            }
            QPushButton#primaryButton {
                background-color: #4caf50; color: white; border: none; font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d2d; border: 1px solid #505050;
                border-radius: 6px; padding: 8px; color: #e0e0e0;
            }
            QLabel { color: #e0e0e0; }
            QLabel#headerLabel { color: #e0e0e0; font-size: 24px; font-weight: bold; }
            QLabel#infoLabel {
                background-color: #2d2d2d; border-left: 4px solid #2196f3;
                border-radius: 6px; padding: 12px; color: #e0e0e0;
            }
            QLabel#statsLabel {
                background-color: #1565c0; border-radius: 6px;
                padding: 8px 12px; color: #ffffff; font-weight: bold;
            }
        """
    
    def apply_theme(self):
        """Apply current theme"""
        self.setStyleSheet(self.get_dark_stylesheet() if self.dark_mode else self.get_light_stylesheet())
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.theme_button.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")
    
    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_decks_tab(), "📚 My Decks")
        self.tab_widget.addTab(self.create_settings_tab(), "⚙️ Settings")
        layout.addWidget(self.tab_widget, 1)
        
        # Bottom buttons
        layout.addLayout(self.create_bottom_buttons())
        self.setLayout(layout)
    
    def create_header(self):
        """Create header"""
        layout = QVBoxLayout()
        
        title_layout = QHBoxLayout()
        title = QLabel("📚 Your Nottorney Decks")
        title.setObjectName("headerLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Theme toggle
        self.theme_button = QPushButton("🌙 Dark Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setMaximumWidth(150)
        title_layout.addWidget(self.theme_button)
        
        user = config.get_user()
        if user:
            user_label = QLabel(f"👤 {user.get('email', 'User')}")
            title_layout.addWidget(user_label)
        
        layout.addLayout(title_layout)
        
        self.info_label = QLabel("Loading decks...")
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)
        
        return layout
    
    def create_decks_tab(self):
        """Create main decks tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(QLabel("🔍"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Quick filters
        filter_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("📚 All")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)
        self.show_all_btn.clicked.connect(lambda: self.quick_filter("all"))
        
        self.show_downloaded_btn = QPushButton("✓ Downloaded")
        self.show_downloaded_btn.setCheckable(True)
        self.show_downloaded_btn.clicked.connect(lambda: self.quick_filter("downloaded"))
        
        self.show_updates_btn = QPushButton("⟳ Updates")
        self.show_updates_btn.setCheckable(True)
        self.show_updates_btn.clicked.connect(lambda: self.quick_filter("updates"))
        
        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_downloaded_btn)
        filter_layout.addWidget(self.show_updates_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Stats
        self.stats_label = QLabel("0 decks")
        self.stats_label.setObjectName("statsLabel")
        layout.addWidget(self.stats_label)
        
        # Deck list (multi-select)
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.deck_list)
        
        # Bulk actions
        bulk_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(lambda: self.deck_list.selectAll())
        
        self.deselect_btn = QPushButton("☐ Clear")
        self.deselect_btn.clicked.connect(lambda: self.deck_list.clearSelection())
        
        self.check_updates_button = QPushButton("🔄 Check Updates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        
        bulk_layout.addWidget(self.select_all_btn)
        bulk_layout.addWidget(self.deselect_btn)
        bulk_layout.addStretch()
        bulk_layout.addWidget(self.check_updates_button)
        layout.addLayout(bulk_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Sort options
        sort_group = QGroupBox("📊 Sorting")
        sort_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Title (A-Z)", "Title (Z-A)", "Subject",
            "Card Count", "Recently Downloaded", "Updates Available"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        sort_layout.addWidget(QLabel("Sort by:"))
        sort_layout.addWidget(self.sort_combo)
        sort_group.setLayout(sort_layout)
        layout.addWidget(sort_group)
        
        # Details
        details_group = QGroupBox("📋 Details")
        details_layout = QVBoxLayout()
        self.details_label = QLabel("Select deck(s) to view details")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group, 1)
        
        # Debug log
        debug_group = QGroupBox("🐛 Debug Log")
        debug_group.setCheckable(True)
        debug_group.setChecked(False)
        debug_layout = QVBoxLayout()
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(150)
        self.debug_log.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace;")
        debug_layout.addWidget(self.debug_log)
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_bottom_buttons(self):
        """Create bottom buttons"""
        layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.load_decks)
        
        self.sync_button = QPushButton("☁️ Sync Progress")
        self.sync_button.clicked.connect(self.sync_progress)
        
        self.download_all_button = QPushButton("⬇️⬇️ Download All")
        self.download_all_button.setObjectName("primaryButton")
        self.download_all_button.clicked.connect(self.download_all_decks)
        
        self.download_button = QPushButton("⬇️ Download Selected")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        
        close_button = QPushButton("✕ Close")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.sync_button)
        layout.addStretch()
        layout.addWidget(self.download_all_button)
        layout.addWidget(self.download_button)
        layout.addWidget(close_button)
        
        return layout
    
    def log(self, message):
        """Log message"""
        self.debug_log.append(message)
        print(message)
    
    def on_search_changed(self, text):
        """Handle search"""
        self.search_text = text.lower()
        self.filter_decks()
    
    def on_sort_changed(self, index):
        """Handle sort change"""
        sort_map = {0: "title_asc", 1: "title_desc", 2: "subject",
                    3: "card_count", 4: "downloaded_date", 5: "has_update"}
        self.sort_by = sort_map.get(index, "title_asc")
        self.filter_decks()
    
    def quick_filter(self, filter_type):
        """Quick filter"""
        self.show_all_btn.setChecked(filter_type == "all")
        self.show_downloaded_btn.setChecked(filter_type == "downloaded")
        self.show_updates_btn.setChecked(filter_type == "updates")
        self.filter_decks()
    
    def filter_decks(self):
        """Filter decks"""
        if not self.decks:
            self.populate_deck_list([])
            return
        
        filtered = self.decks.copy()
        
        if self.search_text:
            filtered = [d for d in filtered if 
                       self.search_text in d.get('title', '').lower() or
                       self.search_text in d.get('subject', '').lower()]
        
        if self.show_downloaded_btn.isChecked() and not self.show_all_btn.isChecked():
            filtered = [d for d in filtered if self.is_downloaded(d)]
        
        if self.show_updates_btn.isChecked() and not self.show_all_btn.isChecked():
            filtered = [d for d in filtered if self.has_update(d)]
        
        self.filtered_decks = self.sort_decks(filtered)
        self.populate_deck_list(self.filtered_decks)
    
    def sort_decks(self, decks):
        """Sort decks"""
        if self.sort_by == "title_asc":
            return sorted(decks, key=lambda d: d.get('title', '').lower())
        elif self.sort_by == "title_desc":
            return sorted(decks, key=lambda d: d.get('title', '').lower(), reverse=True)
        elif self.sort_by == "card_count":
            return sorted(decks, key=lambda d: d.get('card_count', 0), reverse=True)
        elif self.sort_by == "has_update":
            return sorted(decks, key=lambda d: self.has_update(d), reverse=True)
        return decks
    
    def has_update(self, deck):
        """Check if has update"""
        deck_id = self.get_deck_id(deck)
        if not deck_id or not config.is_deck_downloaded(deck_id):
            return False
        return config.get_deck_version(deck_id) != self.get_deck_version(deck)
    
    def is_downloaded(self, deck):
        """Check if downloaded"""
        deck_id = self.get_deck_id(deck)
        return deck_id and config.is_deck_downloaded(deck_id)
    
    def get_deck_id(self, deck):
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        return deck.get('current_version') or deck.get('version') or '1.0'
    
    def load_decks(self):
        """Load decks"""
        self.info_label.setText("⏳ Loading...")
        self.deck_list.clear()
        
        try:
            self.log("\n=== Loading decks ===")
            self.decks = api.get_purchased_decks()
            
            total = len(self.decks)
            downloaded = sum(1 for d in self.decks if self.is_downloaded(d))
            updates = sum(1 for d in self.decks if self.has_update(d))
            
            self.info_label.setText(f"📚 {total} • ✓ {downloaded} • ⟳ {updates}")
            self.filter_decks()
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))
    
    def populate_deck_list(self, decks):
        """Populate list"""
        self.deck_list.clear()
        self.stats_label.setText(f"{len(decks)} deck(s)")
        
        for deck in decks:
            title = deck.get('title', 'Unknown')
            subject = deck.get('subject', 'N/A')
            cards = deck.get('card_count', 0)
            version = self.get_deck_version(deck)
            
            is_dl = self.is_downloaded(deck)
            has_upd = self.has_update(deck)
            
            icon = "⟳" if has_upd else ("✓" if is_dl else "○")
            display = f"{icon} {title}\n📖 {subject} • 🃏 {cards} cards • v{version}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            self.deck_list.addItem(item)
    
    def on_selection_changed(self):
        """Handle selection"""
        items = self.deck_list.selectedItems()
        self.download_button.setEnabled(len(items) > 0)
        
        if len(items) == 1:
            deck = items[0].data(Qt.ItemDataRole.UserRole)
            self.show_deck_details(deck)
        elif len(items) > 1:
            self.details_label.setText(f"✅ {len(items)} decks selected")
    
    def show_deck_details(self, deck):
        """Show details"""
        title = deck.get('title', 'Unknown')
        desc = deck.get('description', 'No description')
        cards = deck.get('card_count', 0)
        version = self.get_deck_version(deck)
        
        html = f"<h2>{title}</h2><p>{desc}</p><p><b>Cards:</b> {cards} • <b>Version:</b> v{version}</p>"
        self.details_label.setText(html)
    
    def check_for_updates(self):
        """Check updates"""
        try:
            result = api.check_updates()
            updates = result.get('updates_available', 0)
            
            if updates > 0:
                QMessageBox.information(self, "Updates", f"🎉 {updates} update(s) available!")
            else:
                QMessageBox.information(self, "Updates", "✅ All decks up to date!")
            
            self.load_decks()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def sync_progress(self):
        """Sync progress"""
        try:
            from .. import sync
            result = sync.sync_progress()
            
            if result:
                QMessageBox.information(self, "Sync", 
                    f"✅ Synced {result.get('synced_count', 0)} deck(s)!")
            else:
                QMessageBox.information(self, "Sync", "No decks to sync")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def download_selected_deck(self):
        """Download selected decks"""
        items = self.deck_list.selectedItems()
        if not items:
            return
        
        decks_to_download = [item.data(Qt.ItemDataRole.UserRole) for item in items]
        self.download_decks(decks_to_download)
    
    def download_all_decks(self):
        """Download all filtered decks"""
        if not self.filtered_decks:
            QMessageBox.information(self, "Info", "No decks to download")
            return
        
        reply = QMessageBox.question(self, "Download All",
            f"Download all {len(self.filtered_decks)} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_decks(self.filtered_decks)
    
    def download_decks(self, decks):
        """Download multiple decks"""
        total = len(decks)
        
        progress = QProgressDialog(f"Downloading {total} deck(s)...", "Cancel", 0, total, self)
        progress.setWindowTitle("Bulk Download")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        success_count = 0
        failed = []
        
        for i, deck in enumerate(decks):
            if progress.wasCanceled():
                break
            
            deck_title = deck.get('title', 'Unknown')
            progress.setLabelText(f"Downloading {i+1}/{total}: {deck_title}")
            progress.setValue(i)
            
            try:
                deck_id = self.get_deck_id(deck)
                version = self.get_deck_version(deck)
                
                # Download
                download_info = api.download_deck(deck_id)
                deck_content = api.download_deck_file(download_info['download_url'])
                
                # Import
                anki_deck_id = import_deck(deck_content, deck_title)
                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                
                success_count += 1
                self.log(f"✓ Downloaded: {deck_title}")
                
            except Exception as e:
                failed.append(f"{deck_title}: {str(e)}")
                self.log(f"✗ Failed: {deck_title} - {str(e)}")
        
        progress.setValue(total)
        progress.close()
        
        # Summary
        msg = f"✅ Successfully downloaded {success_count}/{total} deck(s)"
        if failed:
            msg += f"\n\n❌ Failed ({len(failed)}):\n" + "\n".join(failed[:5])
            if len(failed) > 5:
                msg += f"\n... and {len(failed)-5} more"
        
        QMessageBox.information(self, "Download Complete", msg)
        self.load_decks()