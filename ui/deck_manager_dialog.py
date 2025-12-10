"""
Enhanced Deck Manager Dialog for Nottorney Addon
Features: Clean UI, Basic/Advanced modes, better styling
FIXED: List item display issues
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
    """Enhanced dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney Deck Manager")
        self.setMinimumSize(1000, 750)
        self.decks = []
        self.filtered_decks = []
        self.show_updates_only = False
        self.search_text = ""
        self.sort_by = "title"
        self.advanced_mode = False
        
        # Apply modern stylesheet
        self.setStyleSheet(self.get_stylesheet())
        
        self.setup_ui()
        self.load_decks()
    
    def get_stylesheet(self):
        """Return the modern stylesheet for the dialog"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
            }
            
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
                outline: none;
                color: #2c3e50;
            }
            
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 6px;
                margin: 2px;
                color: #2c3e50;
                background-color: white;
            }
            
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 2px solid #2196f3;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            QPushButton {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px 16px;
                color: #2c3e50;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #2196f3;
            }
            
            QPushButton:pressed {
                background-color: #e3f2fd;
            }
            
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999;
                border-color: #e0e0e0;
            }
            
            QPushButton#primaryButton {
                background-color: #4caf50;
                color: white;
                border: none;
                font-weight: bold;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#primaryButton:disabled {
                background-color: #cccccc;
            }
            
            QPushButton#dangerButton {
                background-color: #f44336;
                color: white;
                border: none;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #da190b;
            }
            
            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #2196f3;
            }
            
            QLabel {
                color: #2c3e50;
            }
            
            QLabel#headerLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
            }
            
            QLabel#infoLabel {
                background-color: white;
                border-left: 4px solid #2196f3;
                border-radius: 6px;
                padding: 12px;
                color: #2c3e50;
            }
            
            QLabel#statsLabel {
                background-color: #e3f2fd;
                border-radius: 6px;
                padding: 8px 12px;
                color: #1976d2;
                font-weight: bold;
            }
            
            QLabel#detailsLabel {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                color: #2c3e50;
            }
            
            QTextEdit#debugLog {
                background-color: #2b2b2b;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border-radius: 6px;
            }
            
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #d0d0d0;
            }
            
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
            }
            
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #666;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #2196f3;
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #e3f2fd;
            }
        """
    
    def setup_ui(self):
        """Set up the enhanced UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Section
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Mode Toggle
        mode_toggle = self.create_mode_toggle()
        layout.addWidget(mode_toggle)
        
        # Tab Widget for Basic/Advanced
        self.tab_widget = QTabWidget()
        
        # Basic Mode Tab
        basic_tab = self.create_basic_mode_tab()
        self.tab_widget.addTab(basic_tab, "📚 My Decks")
        
        # Advanced Mode Tab
        advanced_tab = self.create_advanced_mode_tab()
        self.tab_widget.addTab(advanced_tab, "⚙️ Advanced")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Bottom Buttons
        button_layout = self.create_bottom_buttons()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_header(self):
        """Create the header section"""
        layout = QVBoxLayout()
        
        # Title row
        title_layout = QHBoxLayout()
        title = QLabel("📚 Your Nottorney Decks")
        title.setObjectName("headerLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # User info
        user = config.get_user()
        if user:
            user_label = QLabel(f"👤 {user.get('email', 'User')}")
            user_label.setStyleSheet("color: #666; font-size: 14px;")
            title_layout.addWidget(user_label)
        
        layout.addLayout(title_layout)
        
        # Info/Status bar
        self.info_label = QLabel("Loading decks...")
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)
        
        return layout
    
    def create_mode_toggle(self):
        """Create mode toggle button"""
        layout = QHBoxLayout()
        
        self.mode_button = QPushButton("🔧 Switch to Advanced Mode")
        self.mode_button.clicked.connect(self.toggle_mode)
        self.mode_button.setMaximumWidth(200)
        
        layout.addStretch()
        layout.addWidget(self.mode_button)
        
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    def toggle_mode(self):
        """Toggle between Basic and Advanced modes"""
        self.advanced_mode = not self.advanced_mode
        
        if self.advanced_mode:
            self.mode_button.setText("📚 Switch to Basic Mode")
            self.tab_widget.setCurrentIndex(1)
        else:
            self.mode_button.setText("🔧 Switch to Advanced Mode")
            self.tab_widget.setCurrentIndex(0)
    
    def create_basic_mode_tab(self):
        """Create the Basic Mode tab - simple and clean"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Simple search
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 18px;")
        self.basic_search_input = QLineEdit()
        self.basic_search_input.setPlaceholderText("Search your decks...")
        self.basic_search_input.textChanged.connect(self.on_search_changed)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.basic_search_input)
        layout.addLayout(search_layout)
        
        # Quick filters
        filter_layout = QHBoxLayout()
        
        self.show_all_btn = QPushButton("📚 All Decks")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)
        self.show_all_btn.clicked.connect(lambda: self.quick_filter("all"))
        
        self.show_downloaded_btn = QPushButton("✓ Downloaded")
        self.show_downloaded_btn.setCheckable(True)
        self.show_downloaded_btn.clicked.connect(lambda: self.quick_filter("downloaded"))
        
        self.show_updates_btn = QPushButton("⟳ Updates Available")
        self.show_updates_btn.setCheckable(True)
        self.show_updates_btn.clicked.connect(lambda: self.quick_filter("updates"))
        
        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_downloaded_btn)
        filter_layout.addWidget(self.show_updates_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Stats summary
        self.stats_label = QLabel("0 decks")
        self.stats_label.setObjectName("statsLabel")
        layout.addWidget(self.stats_label)
        
        # Deck list
        self.deck_list = QListWidget()
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.deck_list.itemDoubleClicked.connect(self.download_selected_deck)
        layout.addWidget(self.deck_list)
        
        # Quick action buttons
        quick_actions = QHBoxLayout()
        
        self.check_updates_button = QPushButton("🔄 Check for Updates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        
        quick_actions.addWidget(self.check_updates_button)
        quick_actions.addStretch()
        
        layout.addLayout(quick_actions)
        
        widget.setLayout(layout)
        return widget
    
    def create_advanced_mode_tab(self):
        """Create the Advanced Mode tab - detailed controls"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Advanced filters
        filter_group = QGroupBox("🔍 Filters & Sorting")
        filter_layout = QVBoxLayout()
        
        # Search row
        search_row = QHBoxLayout()
        self.adv_search_input = QLineEdit()
        self.adv_search_input.setPlaceholderText("Search by title, subject, or description...")
        self.adv_search_input.textChanged.connect(self.on_search_changed)
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self.adv_search_input)
        filter_layout.addLayout(search_row)
        
        # Sort row
        sort_row = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Title (A-Z)",
            "Title (Z-A)", 
            "Subject",
            "Card Count",
            "Recently Downloaded",
            "Updates Available"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        sort_row.addWidget(QLabel("Sort by:"))
        sort_row.addWidget(self.sort_combo)
        sort_row.addStretch()
        filter_layout.addLayout(sort_row)
        
        # Filter checkboxes
        checkbox_row = QHBoxLayout()
        self.updates_checkbox = QCheckBox("Show Updates Only")
        self.updates_checkbox.stateChanged.connect(self.filter_decks)
        self.downloaded_checkbox = QCheckBox("Show Downloaded Only")
        self.downloaded_checkbox.stateChanged.connect(self.filter_decks)
        
        checkbox_row.addWidget(self.updates_checkbox)
        checkbox_row.addWidget(self.downloaded_checkbox)
        checkbox_row.addStretch()
        filter_layout.addLayout(checkbox_row)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Split view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Deck list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        self.adv_stats_label = QLabel("0 decks")
        self.adv_stats_label.setObjectName("statsLabel")
        left_layout.addWidget(self.adv_stats_label)
        
        self.adv_deck_list = QListWidget()
        self.adv_deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.adv_deck_list.itemDoubleClicked.connect(self.download_selected_deck)
        left_layout.addWidget(self.adv_deck_list)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right: Details
        right_widget = self.create_details_panel()
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter, 1)
        
        widget.setLayout(layout)
        return widget
    
    def create_details_panel(self):
        """Create the details panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        details_header = QLabel("<h3>📋 Deck Details</h3>")
        layout.addWidget(details_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.details_label = QLabel("Select a deck to view details")
        self.details_label.setObjectName("detailsLabel")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.details_label)
        layout.addWidget(scroll, 1)
        
        # Debug log (collapsible)
        debug_group = QGroupBox("🐛 Debug Log")
        debug_group.setCheckable(True)
        debug_group.setChecked(False)
        debug_layout = QVBoxLayout()
        
        self.debug_log = QTextEdit()
        self.debug_log.setObjectName("debugLog")
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(150)
        debug_layout.addWidget(self.debug_log)
        debug_group.setLayout(debug_layout)
        
        layout.addWidget(debug_group)
        
        widget.setLayout(layout)
        return widget
    
    def quick_filter(self, filter_type):
        """Handle quick filter buttons"""
        # Update button states
        self.show_all_btn.setChecked(filter_type == "all")
        self.show_downloaded_btn.setChecked(filter_type == "downloaded")
        self.show_updates_btn.setChecked(filter_type == "updates")
        
        # Update checkboxes in advanced mode
        if filter_type == "all":
            self.updates_checkbox.setChecked(False)
            self.downloaded_checkbox.setChecked(False)
        elif filter_type == "downloaded":
            self.updates_checkbox.setChecked(False)
            self.downloaded_checkbox.setChecked(True)
        elif filter_type == "updates":
            self.updates_checkbox.setChecked(True)
            self.downloaded_checkbox.setChecked(False)
        
        self.filter_decks()
    
    def create_bottom_buttons(self):
        """Create bottom action buttons"""
        layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.load_decks)
        
        self.sync_button = QPushButton("☁️ Sync Progress")
        self.sync_button.clicked.connect(self.sync_progress)
        
        self.download_button = QPushButton("⬇️ Download/Update Deck")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        
        close_button = QPushButton("✕ Close")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.sync_button)
        layout.addStretch()
        layout.addWidget(self.download_button)
        layout.addWidget(close_button)
        
        return layout
    
    def log(self, message):
        """Add message to debug log"""
        self.debug_log.append(message)
        print(message)
    
    def on_search_changed(self, text):
        """Handle search text change"""
        self.search_text = text.lower()
        # Sync both search boxes
        if self.sender() == self.basic_search_input:
            self.adv_search_input.setText(text)
        else:
            self.basic_search_input.setText(text)
        self.filter_decks()
    
    def on_sort_changed(self, index):
        """Handle sort change"""
        sort_map = {
            0: "title_asc",
            1: "title_desc",
            2: "subject",
            3: "card_count",
            4: "downloaded_date",
            5: "has_update"
        }
        self.sort_by = sort_map.get(index, "title_asc")
        self.filter_decks()
    
    def filter_decks(self):
        """Filter and sort decks based on current criteria"""
        if not self.decks:
            self.populate_deck_list([])
            return
        
        filtered = self.decks.copy()
        
        # Apply search filter
        if self.search_text:
            filtered = [d for d in filtered if 
                       self.search_text in d.get('title', '').lower() or
                       self.search_text in d.get('subject', '').lower() or
                       self.search_text in d.get('description', '').lower()]
        
        # Apply checkbox filters
        if self.updates_checkbox.isChecked():
            filtered = [d for d in filtered if self.has_update(d)]
        
        if self.downloaded_checkbox.isChecked():
            filtered = [d for d in filtered if self.is_downloaded(d)]
        
        # Sort
        filtered = self.sort_decks(filtered)
        
        self.filtered_decks = filtered
        self.populate_deck_list(filtered)
    
    def sort_decks(self, decks):
        """Sort decks based on current sort criteria"""
        if self.sort_by == "title_asc":
            return sorted(decks, key=lambda d: d.get('title', '').lower())
        elif self.sort_by == "title_desc":
            return sorted(decks, key=lambda d: d.get('title', '').lower(), reverse=True)
        elif self.sort_by == "subject":
            return sorted(decks, key=lambda d: d.get('subject', '').lower())
        elif self.sort_by == "card_count":
            return sorted(decks, key=lambda d: d.get('card_count', 0), reverse=True)
        elif self.sort_by == "downloaded_date":
            def get_date(d):
                deck_id = self.get_deck_id(d)
                if not deck_id or not config.is_deck_downloaded(deck_id):
                    return ""
                info = config.get_downloaded_decks().get(deck_id, {})
                return info.get('downloaded_at', '')
            return sorted(decks, key=get_date, reverse=True)
        elif self.sort_by == "has_update":
            return sorted(decks, key=lambda d: self.has_update(d), reverse=True)
        
        return decks
    
    def has_update(self, deck):
        """Check if deck has an update available"""
        deck_id = self.get_deck_id(deck)
        if not deck_id or not config.is_deck_downloaded(deck_id):
            return False
        
        current_version = self.get_deck_version(deck)
        downloaded_version = config.get_deck_version(deck_id)
        
        return downloaded_version != current_version
    
    def is_downloaded(self, deck):
        """Check if deck is downloaded"""
        deck_id = self.get_deck_id(deck)
        return deck_id and config.is_deck_downloaded(deck_id)
    
    def get_deck_id(self, deck):
        """Safely extract deck_id"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Safely extract version"""
        return (deck.get('current_version') or 
                deck.get('version') or 
                deck.get('latest_version') or '1.0')
    
    def check_for_updates(self):
        """Check for updates on all decks"""
        self.check_updates_button.setEnabled(False)
        self.info_label.setText("⏳ Checking for updates...")
        
        try:
            self.log("\n=== Checking for updates ===")
            result = api.check_updates()
            
            updates_count = result.get('updates_available', 0)
            total = result.get('total_decks', 0)
            
            if updates_count > 0:
                self.info_label.setText(f"✨ {updates_count} update(s) available!")
                QMessageBox.information(
                    self, "Updates Available",
                    f"🎉 {updates_count} deck update(s) available!\n\n"
                    f"Total decks: {total}\n\n"
                    "Check the 'Updates Available' filter to see them."
                )
            else:
                self.info_label.setText(f"✅ All {total} decks are up to date!")
            
            self.load_decks()
            
        except NottorneyAPIError as e:
            self.log(f"Update check error: {str(e)}")
            self.info_label.setText("❌ Failed to check updates")
            QMessageBox.warning(self, "Error", f"Failed to check updates:\n\n{str(e)}")
        finally:
            self.check_updates_button.setEnabled(True)
    
    def sync_progress(self):
        """Sync progress to server"""
        try:
            from .. import sync
            
            self.sync_button.setEnabled(False)
            self.sync_button.setText("⏳ Syncing...")
            
            result = sync.sync_progress()
            
            if result:
                synced = result.get('synced_count', 0)
                QMessageBox.information(
                    self, "Sync Complete",
                    f"✅ Successfully synced progress for {synced} deck(s)!"
                )
            else:
                QMessageBox.information(
                    self, "Nothing to Sync",
                    "No downloaded decks to sync. Download some decks first!"
                )
        except Exception as e:
            self.log(f"Sync error: {str(e)}")
            QMessageBox.warning(self, "Sync Error", f"Failed to sync:\n\n{str(e)}")
        finally:
            self.sync_button.setEnabled(True)
            self.sync_button.setText("☁️ Sync Progress")
    
    def load_decks(self):
        """Load decks from API"""
        self.info_label.setText("⏳ Loading decks...")
        
        # Get active list widget based on mode
        active_list = self.deck_list if not self.advanced_mode else self.adv_deck_list
        active_list.clear()
        
        self.details_label.setText("Loading...")
        
        # Disable controls
        self.refresh_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        try:
            self.log("\n=== Fetching decks ===")
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("📭 No purchased decks found")
                self.stats_label.setText("0 decks")
                self.adv_stats_label.setText("0 decks")
                return
            
            total = len(self.decks)
            downloaded = sum(1 for d in self.decks if self.is_downloaded(d))
            updates = sum(1 for d in self.decks if self.has_update(d))
            
            self.info_label.setText(
                f"📚 {total} deck(s) • ✓ {downloaded} downloaded • ⟳ {updates} updates"
            )
            
            self.log(f"Loaded {total} decks")
            self.filter_decks()
            
        except NottorneyAPIError as e:
            self.log(f"API Error: {str(e)}")
            self.info_label.setText(f"❌ Error: {str(e)}")
            if "auth" in str(e).lower():
                QMessageBox.warning(
                    self, "Authentication Error",
                    f"{str(e)}\n\nPlease login again."
                )
        except Exception as e:
            self.log(f"Exception: {str(e)}\n{traceback.format_exc()}")
            self.info_label.setText(f"❌ Unexpected error")
            QMessageBox.critical(self, "Error", f"Unexpected error:\n\n{str(e)}")
        finally:
            self.refresh_button.setEnabled(True)
            self.check_updates_button.setEnabled(True)
    
    def populate_deck_list(self, decks):
        """Populate both deck lists with proper text formatting"""
        self.deck_list.clear()
        self.adv_deck_list.clear()
        
        if not decks:
            self.stats_label.setText("0 decks found")
            self.adv_stats_label.setText("0 decks found")
            self.details_label.setText("No decks match your filters")
            return
        
        stats_text = f"{len(decks)} deck(s)"
        self.stats_label.setText(stats_text)
        self.adv_stats_label.setText(stats_text)
        
        for deck in decks:
            deck_id = self.get_deck_id(deck)
            if not deck_id:
                continue
            
            title = deck.get('title', 'Unknown')
            subject = deck.get('subject', 'N/A')
            cards = deck.get('card_count', 0)
            version = self.get_deck_version(deck)
            
            is_downloaded = self.is_downloaded(deck)
            has_update = self.has_update(deck)
            
            # Status icon
            if has_update:
                icon = "⟳"
                status = "Update Available"
            elif is_downloaded:
                icon = "✓"
                status = "Downloaded"
            else:
                icon = "○"
                status = "Not Downloaded"
            
            # Format display text - Use plain text with newlines
            display = f"{icon} {title}\n"
            display += f"📖 {subject} • 🃏 {cards} cards • v{version}\n"
            display += f"{status}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            
            # Add visual styling through item properties
            if has_update:
                # Orange-ish for updates
                item.setForeground(Qt.GlobalColor.darkYellow)
            elif is_downloaded:
                # Green for downloaded
                item.setForeground(Qt.GlobalColor.darkGreen)
            
            # Add to both lists (create separate items for each list)
            item2 = QListWidgetItem(display)
            item2.setData(Qt.ItemDataRole.UserRole, deck)
            if has_update:
                item2.setForeground(Qt.GlobalColor.darkYellow)
            elif is_downloaded:
                item2.setForeground(Qt.GlobalColor.darkGreen)
            
            self.deck_list.addItem(item)
            self.adv_deck_list.addItem(item2)
    
    def on_selection_changed(self):
        """Handle deck selection"""
        # Get selection from active list
        if self.advanced_mode:
            items = self.adv_deck_list.selectedItems()
        else:
            items = self.deck_list.selectedItems()
        
        if not items:
            self.download_button.setEnabled(False)
            self.details_label.setText("Select a deck to view details")
            return
        
        self.download_button.setEnabled(True)
        deck = items[0].data(Qt.ItemDataRole.UserRole)
        self.show_deck_details(deck)
    
    def show_deck_details(self, deck):
        """Show detailed deck information"""
        title = deck.get('title', 'Unknown')
        desc = deck.get('description', 'No description available')
        subject = deck.get('subject', 'N/A')
        cards = deck.get('card_count', 0)
        version = self.get_deck_version(deck)
        deck_id = self.get_deck_id(deck)
        
        is_downloaded = self.is_downloaded(deck)
        has_update = self.has_update(deck)
        
        # Build clean HTML
        html = f"<h2 style='color: #2196f3; margin-bottom: 10px;'>{title}</h2>"
        html += f"<p style='color: #666; margin-bottom: 20px; font-style: italic;'>{desc}</p>"
        
        html += "<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>"
        html += f"<p style='margin: 5px 0;'><strong>📖 Subject:</strong> {subject}</p>"
        html += f"<p style='margin: 5px 0;'><strong>🃏 Cards:</strong> {cards}</p>"
        html += f"<p style='margin: 5px 0;'><strong>📌 Version:</strong> v{version}</p>"
        
        if is_downloaded:
            downloaded_ver = config.get_deck_version(deck_id)
            html += f"<p style='margin: 5px 0;'><strong>💾 Downloaded:</strong> v{downloaded_ver}</p>"
            
            dl_info = config.get_downloaded_decks().get(deck_id, {})
            dl_date = dl_info.get('downloaded_at', 'Unknown')
            if dl_date != 'Unknown':
                try:
                    dl_date = dl_date.split('T')[0]
                except:
                    pass
            html += f"<p style='margin: 5px 0;'><strong>📅 Downloaded On:</strong> {dl_date}</p>"
        
        html += "</div>"
        
        if has_update:
            downloaded_ver = config.get_deck_version(deck_id)
            html += "<div style='background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;'>"
            html += "<p style='margin: 0; font-weight: bold; color: #856404;'>🎉 Update Available!</p>"
            html += f"<p style='margin: 5px 0 0 0; color: #856404;'>v{downloaded_ver} → v{version}</p>"
            html += "</div>"
        elif is_downloaded:
            html += "<div style='background: #d4edda; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;'>"
            html += "<p style='margin: 0; font-weight: bold; color: #155724;'>✅ Up to Date</p>"
            html += "</div>"
        else:
            html += "<div style='background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;'>"
            html += "<p style='margin: 0; font-weight: bold; color: #0d47a1;'>⬇️ Ready to Download</p>"
            html += "<p style='margin: 5px 0 0 0; color: #0d47a1;'>Click the download button below to add this deck</p>"
            html += "</div>"
        
        self.details_label.setText(html)
    
    def download_selected_deck(self):
        """Download/update the selected deck"""
        # Get selection from active list
        if self.advanced_mode:
            items = self.adv_deck_list.selectedItems()
        else:
            items = self.deck_list.selectedItems()
            
        if not items:
            return
        
        deck = items[0].data(Qt.ItemDataRole.UserRole)
        deck_id = self.get_deck_id(deck)
        deck_version = self.get_deck_version(deck)
        deck_title = deck.get('title', 'Unknown')
        
        self.log(f"\n=== Download: {deck_title} ===")
        
        # Confirm if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_ver = config.get_deck_version(deck_id)
            
            if downloaded_ver == deck_version:
                reply = QMessageBox.question(
                    self, "Re-download Deck",
                    f"You already have {deck_title} v{deck_version}.\n\nDownload again?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            else:
                reply = QMessageBox.question(
                    self, "Update Deck",
                    f"Update {deck_title}?\n\nv{downloaded_ver} → v{deck_version}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Progress dialog
        progress = QProgressDialog("Preparing download...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Downloading Deck")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        
        try:
            # Step 1: Get download URL
            progress.setLabelText("Getting download link...")
            progress.setValue(20)
            
            download_info = api.download_deck(deck_id)
            download_url = download_info.get('download_url')
            
            if not download_url:
                raise NottorneyAPIError("No download URL received")
            
            # Step 2: Download file
            progress.setLabelText("Downloading deck file...")
            progress.setValue(40)
            
            deck_content = api.download_deck_file(download_url)
            self.log(f"Downloaded {len(deck_content)} bytes")
            
            # Step 3: Import
            progress.setLabelText("Importing into Anki...")
            progress.setValue(70)
            
            anki_deck_id = import_deck(deck_content, deck_title)
            self.log(f"Imported as deck ID: {anki_deck_id}")
            
            # Step 4: Save config
            progress.setValue(90)
            actual_version = download_info.get('version', deck_version)
            config.save_downloaded_deck(deck_id, actual_version, anki_deck_id)
            
            progress.setValue(100)
            progress.close()
            
            self.log("=== Download Complete ===")
            
            QMessageBox.information(
                self, "Success!",
                f"✅ Successfully imported:\n\n{deck_title} (v{actual_version})\n\n"
                "The deck is now available in your Anki collection."
            )
            
            self.load_decks()
            
        except NottorneyAPIError as e:
            progress.close()
            self.log(f"API Error: {str(e)}")
            QMessageBox.warning(
                self, "Download Failed",
                f"Failed to download deck:\n\n{str(e)}"
            )
        except Exception as e:
            progress.close()
            self.log(f"Exception: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error",
                f"Unexpected error:\n\n{str(e)}"
            )