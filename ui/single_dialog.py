"""
Enhanced Minimal Dialog with Batch Download & Changelog Support
Now uses /addon-batch-download and /addon-get-changelog endpoints
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, Qt, QWidget, QTextEdit, QScrollArea
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck

# Minimalist stylesheet (same as before)
MINIMAL_STYLE = """
QDialog { background-color: #1a1a1a; color: #e0e0e0; }
QLabel { color: #e0e0e0; font-size: 14px; }
QLabel#title { font-size: 24px; font-weight: bold; color: #ffffff; }
QLabel#status { color: #888; font-size: 13px; }
QPushButton {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; padding: 12px 24px; color: #e0e0e0; font-size: 14px;
}
QPushButton:hover { background-color: #333; border-color: #555; }
QPushButton:disabled { background-color: #1a1a1a; color: #555; }
QPushButton#primary {
    background-color: #4caf50; border: none; color: white; font-weight: bold;
}
QPushButton#primary:hover { background-color: #45a049; }
QPushButton#primary:disabled { background-color: #2a4a2b; color: #666; }
QPushButton#secondary {
    background-color: transparent; border: none; color: #888;
    padding: 8px 16px; font-size: 13px;
}
QPushButton#secondary:hover { color: #aaa; }
QPushButton#notification {
    background-color: #ff5722; border: none; color: white;
    padding: 8px 16px; font-size: 13px; font-weight: bold;
}
QPushButton#notification:hover { background-color: #f4511e; }
QLineEdit {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; padding: 10px; color: #e0e0e0; font-size: 14px;
}
QLineEdit:focus { border-color: #4caf50; }
QProgressBar {
    border: 1px solid #404040; border-radius: 6px;
    background-color: #2a2a2a; text-align: center;
    color: #e0e0e0; height: 24px;
}
QProgressBar::chunk { background-color: #4caf50; border-radius: 5px; }
QListWidget {
    background-color: #2a2a2a; border: 1px solid #404040;
    border-radius: 6px; outline: none; color: #e0e0e0;
}
QListWidget::item { padding: 12px; border-bottom: 1px solid #333; }
QListWidget::item:hover { background-color: #333; }
QListWidget::item:selected { background-color: #4caf50; color: white; }
QTextEdit {
    background-color: #1a1a1a; color: #00ff00;
    border: 1px solid #404040; border-radius: 6px;
    font-family: monospace; font-size: 11px;
}
"""


class MinimalNottorneyDialog(QDialog):
    """Enhanced minimal dialog with batch download & changelog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(MINIMAL_STYLE)
        
        self.decks = []
        self.is_syncing = False
        self.show_advanced = False
        self.show_log = False
        
        self.setup_ui()
        self.run_startup_cleanup()
        self.check_login()
    
    def setup_ui(self):
        """Minimal UI setup"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        self.title_label = QLabel("Nottorney")
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Login section
        self.login_widget = self.create_login_section()
        layout.addWidget(self.login_widget)
        
        # Sync section
        self.sync_widget = self.create_sync_section()
        layout.addWidget(self.sync_widget)
        
        # Advanced section
        self.advanced_widget = self.create_advanced_section()
        layout.addWidget(self.advanced_widget)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Debug log
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        self.log_widget.hide()
        layout.addWidget(self.log_widget)
        
        # Bottom actions
        bottom = QHBoxLayout()
        
        # Notification button (hidden by default)
        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setObjectName("notification")
        self.notif_btn.clicked.connect(self.show_notifications)
        self.notif_btn.setToolTip("View notifications")
        self.notif_btn.hide()
        
        self.cleanup_btn = QPushButton("Clean Tracking")
        self.cleanup_btn.setObjectName("secondary")
        self.cleanup_btn.clicked.connect(self.manual_cleanup)
        self.cleanup_btn.setToolTip("Remove tracking for deleted decks")
        
        self.advanced_btn = QPushButton("Browse Decks")
        self.advanced_btn.setObjectName("secondary")
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        self.advanced_btn.hide()
        
        self.log_btn = QPushButton("Show Log")
        self.log_btn.setObjectName("secondary")
        self.log_btn.clicked.connect(self.toggle_log)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("secondary")
        self.close_btn.clicked.connect(self.accept)
        
        bottom.addWidget(self.notif_btn)
        bottom.addWidget(self.cleanup_btn)
        bottom.addWidget(self.log_btn)
        bottom.addWidget(self.advanced_btn)
        bottom.addStretch()
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
    def create_login_section(self):
        """Login section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.returnPressed.connect(self.handle_login)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primary")
        self.login_btn.clicked.connect(self.handle_login)
        
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_sync_section(self):
        """Sync section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.sync_status = QLabel("")
        
        self.sync_btn = QPushButton("Download All")
        self.sync_btn.setObjectName("primary")
        self.sync_btn.clicked.connect(self.sync_all)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("secondary")
        self.logout_btn.clicked.connect(self.handle_logout)
        
        layout.addWidget(self.sync_status)
        layout.addWidget(self.sync_btn)
        layout.addWidget(self.logout_btn)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def create_advanced_section(self):
        """Advanced section"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        self.search_input.textChanged.connect(self.filter_decks)
        
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.deck_list.itemDoubleClicked.connect(self.show_deck_changelog)
        
        btn_layout = QHBoxLayout()
        
        download_btn = QPushButton("Download Selected")
        download_btn.setObjectName("primary")
        download_btn.clicked.connect(self.download_selected)
        
        changelog_btn = QPushButton("View Changelog")
        changelog_btn.setObjectName("secondary")
        changelog_btn.clicked.connect(lambda: self.show_deck_changelog(self.deck_list.currentItem()))
        
        btn_layout.addWidget(download_btn)
        btn_layout.addWidget(changelog_btn)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.deck_list)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        widget.hide()
        return widget
    
    def log(self, message):
        """Add to debug log"""
        self.log_widget.append(message)
        print(message)
    
    def toggle_log(self):
        """Toggle log visibility"""
        self.show_log = not self.show_log
        self.log_widget.setVisible(self.show_log)
        self.log_btn.setText("Hide Log" if self.show_log else "Show Log")
        self.setMinimumHeight(600 if self.show_log else 400)
    
    def run_startup_cleanup(self):
        """Run automatic cleanup on startup"""
        self.log("\n=== STARTUP CLEANUP ===")
        try:
            cleaned, total = config.cleanup_deleted_decks()
            if cleaned > 0:
                self.log(f"✓ Cleaned up {cleaned} deleted deck(s)")
            else:
                self.log(f"✓ All {total} tracked deck(s) are valid")
        except Exception as e:
            self.log(f"✗ Cleanup error: {e}")
    
    def manual_cleanup(self):
        """Manual cleanup trigger"""
        reply = QMessageBox.question(
            self, "Clean Tracking",
            "Remove tracking for decks that no longer exist in Anki?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            cleaned, total = config.cleanup_deleted_decks()
            if cleaned > 0:
                QMessageBox.information(
                    self, "Cleanup Complete",
                    f"Removed tracking for {cleaned} deleted deck(s).\n\nRemaining: {total - cleaned} deck(s)"
                )
            else:
                QMessageBox.information(
                    self, "No Cleanup Needed",
                    f"All {total} tracked deck(s) exist in Anki."
                )
            
            if config.is_logged_in():
                self.load_deck_status()
        except Exception as e:
            QMessageBox.warning(self, "Cleanup Error", f"Error during cleanup:\n\n{str(e)}")
    
    def check_notifications_silent(self):
        """Silently check for notifications"""
        if not config.is_logged_in():
            return
        
        try:
            self.log("Checking notifications...")
            result = api.check_notifications(mark_as_read=False, limit=5)
            
            if result.get('success'):
                unread_count = result.get('unread_count', 0)
                config.set_unread_notification_count(unread_count)
                config.update_last_notification_check()
                self.log(f"Found {unread_count} unread notification(s)")
                
                if unread_count > 0:
                    self.notif_btn.setText(f"🔔 {unread_count}")
                    self.notif_btn.show()
                else:
                    self.notif_btn.setText("🔔")
                    self.notif_btn.show()
        except Exception as e:
            self.log(f"Notification check failed: {e}")
    
    def show_notifications(self):
        """Show notifications dialog"""
        from .notifications_dialog import NotificationsDialog
        dialog = NotificationsDialog(mw)
        dialog.exec()
        self.check_notifications_silent()
    
    def show_deck_changelog(self, item):
        """Show changelog for a deck (NEW!)"""
        if not item:
            return
        
        deck = item.data(Qt.ItemDataRole.UserRole)
        deck_id = self.get_deck_id(deck)
        deck_title = deck.get('title', 'Unknown')
        
        try:
            self.log(f"Fetching changelog for {deck_title}...")
            changelog = api.get_changelog(deck_id)
            
            if changelog.get('success'):
                self.show_changelog_dialog(changelog)
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch changelog")
        except Exception as e:
            self.log(f"Changelog error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to fetch changelog:\n\n{str(e)}")
    
    def show_changelog_dialog(self, changelog):
        """Display changelog in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Changelog: {changelog.get('title', 'Deck')}")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(MINIMAL_STYLE)
        
        layout = QVBoxLayout()
        
        # Header info
        current_ver = changelog.get('current_version', '')
        synced_ver = changelog.get('user_synced_version', '')
        is_updated = changelog.get('is_up_to_date', True)
        
        header = QLabel(f"<b>Current:</b> v{current_ver} | <b>Your version:</b> v{synced_ver or 'Not downloaded'}")
        if not is_updated:
            header.setText(header.text() + " | <span style='color: #ff5722;'><b>⟳ Update Available</b></span>")
        layout.addWidget(header)
        
        # Version list
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for version in changelog.get('versions', []):
            ver_num = version.get('version', '')
            notes = version.get('version_notes', 'No notes')
            card_count = version.get('card_count', 0)
            is_current = version.get('is_current', False)
            is_synced = version.get('is_synced', False)
            
            status = ""
            if is_current:
                status = " <b style='color: #4caf50;'>[LATEST]</b>"
            if is_synced:
                status += " <b style='color: #2196f3;'>[YOUR VERSION]</b>"
            
            ver_label = QLabel(f"<h3>v{ver_num}{status}</h3><p>{card_count} cards</p><p>{notes}</p><hr>")
            ver_label.setWordWrap(True)
            scroll_layout.addWidget(ver_label)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def check_login(self):
        """Check login state"""
        is_logged_in = config.is_logged_in()
        self.log(f"Login check: {'Logged in' if is_logged_in else 'Not logged in'}")
        
        if is_logged_in:
            self.show_sync_interface()
            self.check_notifications_silent()
        else:
            self.show_login_interface()
    
    def show_login_interface(self):
        """Show login"""
        self.title_label.setText("Nottorney")
        self.status_label.setText("Sign in to sync your decks")
        self.login_widget.show()
        self.sync_widget.hide()
        self.advanced_widget.hide()
        self.advanced_btn.hide()
        self.notif_btn.hide()
        self.email_input.setFocus()
    
    def show_sync_interface(self):
        """Show sync interface"""
        user = config.get_user()
        if user:
            email = user.get('email', 'User')
            self.title_label.setText(f"Nottorney\n{email}")
        else:
            self.title_label.setText("Nottorney")
        
        self.login_widget.hide()
        self.sync_widget.show()
        self.advanced_btn.show()
        self.load_deck_status()
    
    def handle_login(self):
        """Handle login"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.status_label.setText("❌ Enter email and password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        self.status_label.setText("⏳ Authenticating...")
        
        try:
            self.log(f"Attempting login for: {email}")
            result = api.login(email, password)
            
            if result.get('success'):
                self.log("Login successful")
                self.show_sync_interface()
                self.check_notifications_silent()
            else:
                error = result.get('error', 'Login failed')
                self.log(f"Login failed: {error}")
                self.status_label.setText(f"❌ {error}")
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.log(f"Login error: {error_msg}")
            
            if "connection" in error_msg.lower():
                self.status_label.setText("❌ Connection error")
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                self.status_label.setText("❌ Incorrect email or password")
            else:
                self.status_label.setText(f"❌ {error_msg}")
        except Exception as e:
            self.log(f"Unexpected error: {e}")
            self.status_label.setText(f"❌ Error: {str(e)}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")
    
    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, "Logout", "Logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config.clear_tokens()
            config.set_unread_notification_count(0)
            self.log("Logged out")
            self.check_login()
    
    def load_deck_status(self):
        """Load deck status"""
        try:
            self.status_label.setText("⏳ Loading decks...")
            self.log("Fetching purchased decks...")
            
            self.decks = api.get_purchased_decks()
            total = len(self.decks)
            
            # Count new and updated decks
            new = 0
            updates = 0
            
            for deck in self.decks:
                deck_id = self.get_deck_id(deck)
                
                if not config.is_deck_downloaded(deck_id):
                    new += 1
                else:
                    current_version = self.get_deck_version(deck)
                    saved_version = config.get_deck_version(deck_id)
                    if current_version != saved_version:
                        updates += 1
            
            self.log(f"Found {total} decks: {new} new, {updates} updates")
            
            if new + updates == 0:
                self.status_label.setText(f"✓ All {total} decks synced")
                self.sync_status.setText("Everything is up to date")
                self.sync_btn.setText("✓ All Synced")
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
        except Exception as e:
            self.log(f"Error loading decks: {e}")
            self.status_label.setText("❌ Failed to load decks")
            self.sync_status.setText(str(e))
            self.sync_btn.setEnabled(False)
    
    def sync_all(self):
        """Download all new/updated decks using BATCH DOWNLOAD (NEW!)"""
        if self.is_syncing:
            return
        
        decks_to_sync = []
        
        for deck in self.decks:
            deck_id = self.get_deck_id(deck)
            
            if not config.is_deck_downloaded(deck_id):
                decks_to_sync.append(deck)
            else:
                current_version = self.get_deck_version(deck)
                saved_version = config.get_deck_version(deck_id)
                if current_version != saved_version:
                    decks_to_sync.append(deck)
        
        if not decks_to_sync:
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Download {len(decks_to_sync)} deck(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.is_syncing = True
        self.sync_btn.setEnabled(False)
        self.progress.show()
        
        # Use BATCH DOWNLOAD API (max 10 per request)
        self.batch_download_decks(decks_to_sync)
    
    def batch_download_decks(self, decks):
        """Download decks using batch API (NEW!)"""
        success_count = 0
        failed = []
        
        # Split into batches of 10
        batch_size = 10
        total_batches = (len(decks) + batch_size - 1) // batch_size
        
        self.progress.setMaximum(len(decks))
        
        for batch_idx in range(0, len(decks), batch_size):
            batch = decks[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            self.log(f"\n=== Batch {batch_num}/{total_batches} ({len(batch)} decks) ===")
            
            # Get deck IDs for this batch
            deck_ids = [self.get_deck_id(d) for d in batch]
            
            try:
                # Call BATCH DOWNLOAD API
                result = api.batch_download_decks(deck_ids)
                
                if result.get('success'):
                    downloads = result.get('downloads', [])
                    
                    # Process successful downloads
                    for i, download in enumerate(downloads):
                        if download.get('success'):
                            deck_id = download.get('deck_id')
                            title = download.get('title', 'Unknown')
                            version = download.get('version', '1.0')
                            download_url = download.get('download_url')
                            
                            self.progress.setValue(batch_idx + i)
                            self.progress.setFormat(f"Downloading: {title[:30]}...")
                            self.log(f"Downloading: {title}")
                            
                            try:
                                # Download and import
                                deck_content = api.download_deck_file(download_url)
                                anki_deck_id = import_deck(deck_content, title)
                                config.save_downloaded_deck(deck_id, version, anki_deck_id)
                                
                                success_count += 1
                                self.log(f"✓ {title}")
                            except Exception as e:
                                failed.append(f"{title}: {str(e)}")
                                self.log(f"✗ {title}: {e}")
                        else:
                            # Failed in batch response
                            title = download.get('title', 'Unknown')
                            error = download.get('error', 'Unknown error')
                            failed.append(f"{title}: {error}")
                            self.log(f"✗ {title}: {error}")
                    
                    # Process failed decks from API
                    for fail in result.get('failed', []):
                        title = fail.get('title', 'Unknown')
                        error = fail.get('error', 'Unknown error')
                        failed.append(f"{title}: {error}")
                        self.log(f"✗ {title}: {error}")
                
            except Exception as e:
                # Entire batch failed
                self.log(f"✗ Batch {batch_num} failed: {e}")
                for deck in batch:
                    failed.append(f"{deck.get('title', 'Unknown')}: Batch request failed")
        
        self.progress.setValue(len(decks))
        self.is_syncing = False
        self.progress.hide()
        
        # Show results
        if success_count == len(decks):
            QMessageBox.information(self, "Complete", f"✓ Downloaded all {success_count} deck(s)!")
        elif success_count > 0:
            msg = f"Downloaded {success_count}/{len(decks)} deck(s)\n\n"
            if failed:
                msg += "Failed:\n" + "\n".join(failed[:3])
            QMessageBox.warning(self, "Partial Success", msg)
        else:
            QMessageBox.critical(self, "Failed", "All downloads failed")
        
        self.load_deck_status()
    
    def toggle_advanced(self):
        """Toggle advanced section"""
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
        """Populate deck list"""
        self.deck_list.clear()
        
        for deck in self.decks:
            title = deck.get('title', 'Unknown')
            deck_id = self.get_deck_id(deck)
            
            if not config.is_deck_downloaded(deck_id):
                status = "○"
            else:
                current_version = self.get_deck_version(deck)
                saved_version = config.get_deck_version(deck_id)
                if current_version != saved_version:
                    status = "⟳"
                else:
                    status = "✓"
            
            item = QListWidgetItem(f"{status} {title}")
            item.setData(Qt.ItemDataRole.UserRole, deck)
            self.deck_list.addItem(item)
    
    def filter_decks(self, text):
        """Filter decks"""
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def download_selected(self):
        """Download selected decks"""
        selected = self.deck_list.selectedItems()
        if not selected:
            self.status_label.setText("Select decks to download")
            return
        
        decks_to_download = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        self.batch_download_decks(decks_to_download)
    
    def get_deck_id(self, deck):
        """Get deck ID"""
        return deck.get('deck_id') or deck.get('id')
    
    def get_deck_version(self, deck):
        """Get deck version"""
        return deck.get('current_version') or deck.get('version') or '1.0'