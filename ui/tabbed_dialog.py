"""
Modern Tabbed Dialog for Nottorney Addon
Features: My Decks, Browse, Updates, Notifications tabs
Version: 1.1.0
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, Qt,
    QTabWidget, QWidget, QTextEdit, QGroupBox
)
from aqt import mw
import sys
import os

# Get parent directory to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import api, set_access_token, NottorneyAPIError
from config import config
from deck_importer import import_deck_with_progress
from update_checker import update_checker


class NottorneyTabbedDialog(QDialog):
    """Modern tabbed dialog for Nottorney operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney Deck Manager")
        self.setMinimumSize(800, 600)
        self.all_decks = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚖️ Nottorney Deck Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Check if logged in
        if not config.is_logged_in():
            self.setup_login_ui(layout)
        else:
            self.setup_tabbed_ui(layout)
        
        self.setLayout(layout)
    
    def setup_login_ui(self, layout):
        """Setup login interface"""
        # Login message
        msg = QLabel("Please login to access your purchased decks")
        msg.setStyleSheet("color: #555; font-size: 14px; padding: 15px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        # Login form
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: bold;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        
        # Password
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-weight: bold;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("padding: 10px; font-weight: bold; font-size: 14px;")
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def setup_tabbed_ui(self, layout):
        """Setup tabbed interface"""
        # User info bar
        user_bar = QWidget()
        user_layout = QHBoxLayout()
        user_layout.setContentsMargins(5, 5, 5, 5)
        
        user_label = QLabel("✓ Logged in")
        user_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 13px;")
        user_layout.addWidget(user_label)
        
        user_layout.addStretch()
        
        # Check for updates badge
        update_count = update_checker.get_update_count()
        if update_count > 0:
            update_badge = QLabel(f"🔔 {update_count} update(s)")
            update_badge.setStyleSheet(
                "background-color: #ff9800; color: white; "
                "padding: 5px 10px; border-radius: 10px; font-weight: bold;"
            )
            user_layout.addWidget(update_badge)
        
        user_bar.setLayout(user_layout)
        layout.addWidget(user_bar)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; }")
        
        # Create tabs
        self.my_decks_tab = self.create_my_decks_tab()
        self.browse_tab = self.create_browse_tab()
        self.updates_tab = self.create_updates_tab()
        
        self.tabs.addTab(self.my_decks_tab, "📚 My Decks")
        self.tabs.addTab(self.browse_tab, "🔍 Browse")
        self.tabs.addTab(self.updates_tab, f"🔄 Updates ({update_count})")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        logout_btn = QPushButton("Logout")
        logout_btn.setToolTip("Logout and clear credentials")
        logout_btn.clicked.connect(self.logout)
        button_layout.addWidget(logout_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Load initial data
        self.load_my_decks()
        self.load_browse_decks()
        self.load_updates()
    
    def create_my_decks_tab(self):
        """Create My Decks tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Your Downloaded Decks")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header)
        
        # Deck list
        self.my_decks_list = QListWidget()
        self.my_decks_list.setStyleSheet("QListWidget::item { padding: 10px; }")
        layout.addWidget(self.my_decks_list)
        
        # Status
        self.my_decks_status = QLabel("")
        self.my_decks_status.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.my_decks_status)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_my_decks)
        btn_layout.addWidget(refresh_btn)
        
        sync_btn = QPushButton("📊 Sync Progress")
        sync_btn.setToolTip("Sync your study progress to server")
        sync_btn.clicked.connect(self.sync_progress)
        btn_layout.addWidget(sync_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_browse_tab(self):
        """Create Browse tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search decks by name...")
        self.search_input.textChanged.connect(self.filter_browse_decks)
        layout.addWidget(self.search_input)
        
        # Deck list
        self.browse_list = QListWidget()
        self.browse_list.setStyleSheet("QListWidget::item { padding: 10px; }")
        self.browse_list.itemDoubleClicked.connect(self.download_selected_deck)
        layout.addWidget(self.browse_list)
        
        # Status
        self.browse_status = QLabel("")
        self.browse_status.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.browse_status)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_browse_decks)
        btn_layout.addWidget(refresh_btn)
        
        download_btn = QPushButton("⬇️ Download Selected")
        download_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        download_btn.clicked.connect(self.download_selected_deck)
        btn_layout.addWidget(download_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_updates_tab(self):
        """Create Updates tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Available Updates")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        check_btn = QPushButton("🔍 Check Now")
        check_btn.clicked.connect(self.check_updates_now)
        header_layout.addWidget(check_btn)
        
        layout.addLayout(header_layout)
        
        # Updates list
        self.updates_list = QListWidget()
        self.updates_list.setStyleSheet("QListWidget::item { padding: 12px; }")
        layout.addWidget(self.updates_list)
        
        # Status
        self.updates_status = QLabel("")
        self.updates_status.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.updates_status)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        update_all_btn = QPushButton("⬇️ Update All")
        update_all_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #4CAF50; color: white;")
        update_all_btn.clicked.connect(self.update_all_decks)
        btn_layout.addWidget(update_all_btn)
        
        update_selected_btn = QPushButton("⬇️ Update Selected")
        update_selected_btn.clicked.connect(self.update_selected_deck)
        btn_layout.addWidget(update_selected_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    # === LOGIN/LOGOUT ===
    
    def login(self):
        """Login user"""
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both email and password.")
            return
        
        try:
            self.email_input.setEnabled(False)
            self.password_input.setEnabled(False)
            
            result = api.login(email, password)
            
            if result.get('success'):
                access_token = result.get('access_token')
                refresh_token = result.get('refresh_token')
                expires_at = result.get('expires_at')
                
                if access_token:
                    config.save_tokens(access_token, refresh_token, expires_at)
                    set_access_token(access_token)
                    
                    QMessageBox.information(self, "Success", 
                                          "Login successful! Reopen Nottorney to browse decks.")
                    self.accept()
                else:
                    raise Exception("No access token received")
            else:
                error_msg = result.get('message', 'Login failed')
                QMessageBox.warning(self, "Login Failed", error_msg)
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Invalid email or password."
            QMessageBox.critical(self, "Login Error", error_msg)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed:\n{str(e)}")
        
        finally:
            self.email_input.setEnabled(True)
            self.password_input.setEnabled(True)
    
    def logout(self):
        """Logout user"""
        reply = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            set_access_token(None)
            QMessageBox.information(self, "Logged Out", 
                                  "You have been logged out successfully.")
            self.accept()
    
    # === MY DECKS TAB ===
    
    def load_my_decks(self):
        """Load user's downloaded decks"""
        self.my_decks_status.setText("⏳ Loading...")
        self.my_decks_list.clear()
        
        try:
            downloaded_decks = config.get_downloaded_decks()
            
            if not downloaded_decks:
                self.my_decks_status.setText("No decks downloaded yet")
                return
            
            for deck_id, deck_info in downloaded_decks.items():
                version = deck_info.get('version', '1.0')
                anki_id = deck_info.get('anki_deck_id')
                
                # Check if update available
                has_update = config.has_update_available(deck_id)
                update_indicator = "🟡 " if has_update else "🟢 "
                
                display_text = f"{update_indicator}Deck {deck_id[:8]} (v{version})"
                if has_update:
                    display_text += " - Update available!"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, {'deck_id': deck_id, 'deck_info': deck_info})
                
                if has_update:
                    item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    item.setForeground(Qt.GlobalColor.darkGreen)
                
                self.my_decks_list.addItem(item)
            
            self.my_decks_status.setText(f"✓ {len(downloaded_decks)} deck(s) downloaded")
        
        except Exception as e:
            self.my_decks_status.setText(f"❌ Failed to load decks")
            print(f"Error loading my decks: {e}")
    
    def sync_progress(self):
        """Sync progress to server"""
        try:
            from sync import sync_progress
            
            self.my_decks_status.setText("⏳ Syncing progress...")
            sync_progress()
            self.my_decks_status.setText("✓ Progress synced successfully")
            QMessageBox.information(self, "Success", "Progress synced successfully!")
        
        except Exception as e:
            self.my_decks_status.setText("❌ Sync failed")
            QMessageBox.critical(self, "Sync Error", f"Failed to sync progress:\n{str(e)}")
    
    # === BROWSE TAB ===
    
    def load_browse_decks(self):
        """Load available decks"""
        token = config.get_access_token()
        if not token:
            self.browse_status.setText("❌ Not logged in")
            return
        
        set_access_token(token)
        
        try:
            self.browse_status.setText("⏳ Loading decks...")
            self.browse_list.clear()
            self.all_decks = []
            
            result = api.browse_decks()
            
            if "decks" in result or result.get('success'):
                decks = result.get('decks', [])
                self.all_decks = decks
                
                downloaded_decks = config.get_downloaded_decks()
                
                for deck in decks:
                    deck_id = deck.get('id')
                    deck_name = deck.get('title') or deck.get('name', 'Unknown Deck')
                    deck_version = deck.get('version', '1.0')
                    
                    is_downloaded = deck_id in downloaded_decks
                    
                    display_text = f"{'✓ ' if is_downloaded else ''}{deck_name} (v{deck_version})"
                    
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, deck)
                    
                    if is_downloaded:
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    
                    self.browse_list.addItem(item)
                
                self.browse_status.setText(f"✓ Loaded {len(decks)} deck(s)")
            else:
                error_msg = result.get('message', 'Failed to load decks')
                self.browse_status.setText(f"❌ {error_msg}")
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Session expired. Please login again."
                config.clear_tokens()
            self.browse_status.setText(f"❌ {error_msg}")
        
        except Exception as e:
            self.browse_status.setText("❌ Load failed")
            print(f"Error loading browse decks: {e}")
    
    def filter_browse_decks(self):
        """Filter browse deck list"""
        query = self.search_input.text().lower()
        
        for i in range(self.browse_list.count()):
            item = self.browse_list.item(i)
            matches = query in item.text().lower()
            item.setHidden(not matches)
    
    def download_selected_deck(self):
        """Download selected deck from browse tab"""
        current = self.browse_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a deck to download.")
            return
        
        deck = current.data(Qt.ItemDataRole.UserRole)
        self._download_deck(deck)
    
    # === UPDATES TAB ===
    
    def load_updates(self):
        """Load available updates"""
        self.updates_list.clear()
        
        updates = config.get_available_updates()
        
        if not updates:
            self.updates_status.setText("All decks are up to date! ✓")
            item = QListWidgetItem("No updates available")
            item.setForeground(Qt.GlobalColor.gray)
            self.updates_list.addItem(item)
            return
        
        for deck_id, update_info in updates.items():
            current_ver = update_info.get('current_version')
            latest_ver = update_info.get('latest_version')
            summary = update_info.get('changelog_summary', '')
            
            display_text = f"Deck {deck_id[:8]}: {current_ver} → {latest_ver}"
            if summary:
                display_text += f"\n  {summary}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, update_info)
            item.setForeground(Qt.GlobalColor.darkYellow)
            
            self.updates_list.addItem(item)
        
        self.updates_status.setText(f"{len(updates)} update(s) available")
    
    def check_updates_now(self):
        """Manually check for updates"""
        self.updates_status.setText("⏳ Checking for updates...")
        updates = update_checker.check_for_updates(silent=False)
        
        if updates is not None:
            self.load_updates()
            # Update tab badge
            self.tabs.setTabText(2, f"🔄 Updates ({len(updates)})")
    
    def update_all_decks(self):
        """Update all decks with available updates"""
        updates = config.get_available_updates()
        
        if not updates:
            QMessageBox.information(self, "No Updates", "All decks are up to date!")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Update All",
            f"Update {len(updates)} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for deck_id in updates.keys():
                # Get deck info to download
                # This is a placeholder - in real implementation,
                # we'd need to fetch deck details from API
                pass
    
    def update_selected_deck(self):
        """Update selected deck"""
        current = self.updates_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a deck to update.")
            return
        
        update_info = current.data(Qt.ItemDataRole.UserRole)
        deck_id = update_info.get('deck_id')
        
        # Download updated version
        # This is a placeholder - in real implementation,
        # we'd call download_deck with this deck_id
        pass
    
    # === COMMON DOWNLOAD LOGIC ===
    
    def _download_deck(self, deck):
        """Common deck download logic"""
        deck_id = deck.get('id')
        deck_name = deck.get('title') or deck.get('name', 'Unknown')
        deck_version = deck.get('version', '1.0')
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            reply = QMessageBox.question(
                self, "Already Downloaded",
                f"'{deck_name}' is already downloaded.\n\nDownload again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        token = config.get_access_token()
        if not token:
            QMessageBox.warning(self, "Not Logged In", "Please login first.")
            return
        
        set_access_token(token)
        
        try:
            self.browse_status.setText(f"⏳ Downloading {deck_name}...")
            
            result = api.download_deck(deck_id)
            
            if not result.get('success'):
                error_msg = result.get('message', 'Download failed')
                raise Exception(error_msg)
            
            download_url = result.get('download_url')
            if not download_url:
                raise Exception("No download URL received")
            
            self.browse_status.setText(f"⏳ Fetching deck file...")
            deck_content = api.download_deck_file(download_url)
            
            if not deck_content:
                raise Exception("Downloaded file is empty")
            
            self.browse_status.setText(f"⏳ Importing into Anki...")
            
            def on_success(anki_deck_id):
                success = config.save_downloaded_deck(deck_id, deck_version, anki_deck_id)
                
                if success:
                    # Clear update notification if this was an update
                    update_checker.clear_update(deck_id)
                    
                    self.browse_status.setText(f"✓ '{deck_name}' imported successfully!")
                    QMessageBox.information(self, "Success", 
                                          f"'{deck_name}' has been imported successfully!")
                    
                    # Reload tabs
                    self.load_my_decks()
                    self.load_browse_decks()
                    self.load_updates()
                else:
                    self.browse_status.setText(f"⚠️ Import succeeded but tracking failed")
            
            def on_failure(error_msg):
                self.browse_status.setText(f"❌ Import failed")
                QMessageBox.critical(self, "Import Failed", 
                                   f"Failed to import '{deck_name}':\n\n{error_msg}")
            
            import_deck_with_progress(deck_content, deck_name, 
                                    on_success=on_success, on_failure=on_failure)
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 403:
                error_msg = f"You don't have access to '{deck_name}'.\n\nPlease purchase it first."
            elif e.status_code == 401:
                error_msg = "Session expired. Please login again."
                config.clear_tokens()
            
            self.browse_status.setText(f"❌ Download failed")
            QMessageBox.critical(self, "Download Error", error_msg)
        
        except Exception as e:
            self.browse_status.setText(f"❌ Download failed")
            QMessageBox.critical(self, "Error", f"Failed to download '{deck_name}':\n\n{str(e)}")