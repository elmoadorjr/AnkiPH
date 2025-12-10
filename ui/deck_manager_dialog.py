"""
Deck manager dialog UI for the Nottorney addon
Shows purchased decks with update checking and allows downloading them
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, Qt, QTextEdit, QCheckBox
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck
import traceback
import json


class DeckManagerDialog(QDialog):
    """Dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Deck Manager")
        self.setMinimumSize(750, 650)
        self.decks = []
        self.show_updates_only = False
        self.setup_ui()
        self.load_decks()
    
    def setup_ui(self):
        """Set up the UI elements"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Your Purchased Decks</h2>")
        layout.addWidget(title)
        
        # User info
        user = config.get_user()
        if user:
            user_label = QLabel(f"Logged in as: <b>{user.get('email', 'Unknown')}</b>")
            layout.addWidget(user_label)
        
        # Info label
        self.info_label = QLabel("Loading decks...")
        layout.addWidget(self.info_label)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        self.updates_checkbox = QCheckBox("Show updates only")
        self.updates_checkbox.stateChanged.connect(self.filter_decks)
        filter_layout.addWidget(self.updates_checkbox)
        filter_layout.addStretch()
        
        self.check_updates_button = QPushButton("Check for Updates")
        self.check_updates_button.clicked.connect(self.check_for_updates)
        filter_layout.addWidget(self.check_updates_button)
        
        layout.addLayout(filter_layout)
        
        # Deck list with better formatting
        self.deck_list = QListWidget()
        self.deck_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.deck_list.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        layout.addWidget(self.deck_list)
        
        # Deck details label
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.details_label)
        
        # DEBUG LOG (collapsible)
        debug_label = QLabel("<b>Debug Log:</b>")
        layout.addWidget(debug_label)
        
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setMaximumHeight(120)
        self.debug_log.setStyleSheet("background-color: #f0f0f0; font-family: monospace; font-size: 9px;")
        layout.addWidget(self.debug_log)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download/Update Deck")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.load_decks)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def log(self, message):
        """Add a message to the debug log"""
        self.debug_log.append(message)
        print(message)  # Also print to console
    
    def get_deck_id(self, deck):
        """Safely extract deck_id from deck object"""
        return deck.get('deck_id') or deck.get('id') or deck.get('_id') or None
    
    def get_deck_version(self, deck):
        """Safely extract version from deck object"""
        return (deck.get('current_version') or 
                deck.get('version') or 
                deck.get('deck_version') or 
                deck.get('latest_version') or
                '1.0')
    
    def check_for_updates(self):
        """Check for updates on all decks"""
        self.check_updates_button.setEnabled(False)
        self.info_label.setText("Checking for updates...")
        
        try:
            self.log("\n=== Checking for updates ===")
            result = api.check_updates()
            
            updates_available = result.get('updates_available', 0)
            total_decks = result.get('total_decks', 0)
            
            if updates_available > 0:
                self.info_label.setText(f"Found {updates_available} update(s) available!")
                QMessageBox.information(
                    self,
                    "Updates Available",
                    f"{updates_available} deck update(s) available out of {total_decks} decks.\n\n"
                    "Check 'Show updates only' to see them."
                )
            else:
                self.info_label.setText(f"All {total_decks} decks are up to date!")
                QMessageBox.information(
                    self,
                    "No Updates",
                    f"All your {total_decks} decks are up to date!"
                )
            
            # Refresh the deck list
            self.load_decks()
            
        except NottorneyAPIError as e:
            self.log(f"Update check error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to check for updates:\n\n{str(e)}")
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Unexpected error:\n\n{str(e)}")
        finally:
            self.check_updates_button.setEnabled(True)
    
    def filter_decks(self):
        """Filter the deck list based on checkbox state"""
        self.show_updates_only = self.updates_checkbox.isChecked()
        self.populate_deck_list()
    
    def load_decks(self):
        """Load purchased decks from the API"""
        self.info_label.setText("Loading decks...")
        self.deck_list.clear()
        self.details_label.setText("")
        self.refresh_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        try:
            self.log("Fetching decks from API...")
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("No purchased decks found.")
                self.log("No decks returned from API")
                return
            
            self.info_label.setText(f"Found {len(self.decks)} purchased deck(s)")
            self.log(f"Received {len(self.decks)} decks")
            
            # Log first deck structure
            if self.decks:
                self.log(f"\nFirst deck fields: {list(self.decks[0].keys())}")
            
            self.populate_deck_list()
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.info_label.setText(f"Error: {error_msg}")
            self.log(f"API ERROR: {error_msg}")
            
            if "login" in error_msg.lower() or "auth" in error_msg.lower():
                QMessageBox.warning(self, "Authentication Error", 
                    f"{error_msg}\n\nPlease login again.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load decks: {error_msg}")
        
        except Exception as e:
            self.info_label.setText(f"Unexpected error: {str(e)}")
            self.log(f"EXCEPTION: {str(e)}")
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
        
        finally:
            self.refresh_button.setEnabled(True)
            self.check_updates_button.setEnabled(True)
    
    def populate_deck_list(self):
        """Populate the deck list widget"""
        self.deck_list.clear()
        
        if not self.decks:
            return
        
        displayed_count = 0
        
        for i, deck in enumerate(self.decks):
            deck_id = self.get_deck_id(deck)
            
            if not deck_id:
                self.log(f"WARNING: Deck {i+1} has no ID!")
                continue
            
            deck_title = deck.get('title', 'Unknown Deck')
            deck_subject = deck.get('subject', 'N/A')
            deck_version = self.get_deck_version(deck)
            card_count = deck.get('card_count', 0)
            
            is_downloaded = config.is_deck_downloaded(deck_id)
            downloaded_version = config.get_deck_version(deck_id) if is_downloaded else None
            
            has_update = False
            if is_downloaded and downloaded_version != deck_version:
                has_update = True
            
            # Filter by updates if checkbox is checked
            if self.show_updates_only and not has_update:
                continue
            
            status_icon = "✓" if is_downloaded else "○"
            version_text = f"v{deck_version}"
            
            if is_downloaded:
                if has_update:
                    version_text = f"v{downloaded_version} → v{deck_version} (Update Available)"
                    status_icon = "⟳"
                else:
                    version_text = f"v{deck_version} (Downloaded)"
            
            display_text = f"{status_icon} {deck_title}\n   {deck_subject} • {card_count} cards • {version_text}"
            
            item = QListWidgetItem()
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, deck)
            
            self.deck_list.addItem(item)
            displayed_count += 1
        
        if self.show_updates_only:
            self.info_label.setText(f"Showing {displayed_count} deck(s) with updates")
        else:
            self.info_label.setText(f"Showing all {displayed_count} deck(s)")
        
        self.log(f"\nDisplayed {displayed_count} decks in list")
    
    def on_selection_changed(self):
        """Handle deck selection change"""
        selected_items = self.deck_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.download_button.setEnabled(has_selection)
        
        if has_selection:
            deck = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.show_deck_details(deck)
    
    def show_deck_details(self, deck):
        """Show details of the selected deck"""
        deck_title = deck.get('title', 'Unknown')
        deck_description = deck.get('description', 'No description available')
        deck_subject = deck.get('subject', 'N/A')
        card_count = deck.get('card_count', 0)
        deck_version = self.get_deck_version(deck)
        
        deck_id = self.get_deck_id(deck)
        is_downloaded = config.is_deck_downloaded(deck_id) if deck_id else False
        
        details = f"<b>{deck_title}</b><br>"
        details += f"<i>{deck_description}</i><br><br>"
        details += f"Subject: {deck_subject} | Cards: {card_count} | Version: {deck_version}<br>"
        
        if is_downloaded:
            downloaded_version = config.get_deck_version(deck_id)
            if downloaded_version != deck_version:
                details += f"<span style='color: #ff9800;'><b>Update Available:</b> v{downloaded_version} → v{deck_version}</span>"
            else:
                details += f"<span style='color: green;'>Downloaded: v{downloaded_version} (Up to date)</span>"
        
        self.details_label.setText(details)
    
    def download_selected_deck(self):
        """Download the selected deck"""
        selected_items = self.deck_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        deck = item.data(Qt.ItemDataRole.UserRole)
        
        deck_id = self.get_deck_id(deck)
        deck_version = self.get_deck_version(deck)
        deck_title = deck.get('title', 'Unknown Deck')
        
        self.log(f"\n=== DOWNLOAD ATTEMPT ===")
        self.log(f"Deck Title: {deck_title}")
        self.log(f"Deck ID: {deck_id}")
        self.log(f"Deck Version: {deck_version}")
        
        if not deck_id:
            error_msg = f"Missing deck ID! Fields available: {list(deck.keys())}"
            self.log(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            return
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_version = config.get_deck_version(deck_id)
            if downloaded_version == deck_version:
                reply = QMessageBox.question(
                    self, "Already Downloaded",
                    f"You already have v{downloaded_version}. Re-download?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            else:
                reply = QMessageBox.question(
                    self, "Update Available",
                    f"Update from v{downloaded_version} to v{deck_version}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Show progress dialog
        progress = QProgressDialog("Preparing...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Downloading")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        
        try:
            # Step 1: Get download URL
            self.log("Step 1: Requesting download URL from API...")
            progress.setLabelText("Getting download link...")
            progress.setValue(20)
            
            # Try without version first
            try:
                self.log(f"  Attempt: download_deck('{deck_id}', version=None)")
                download_info = api.download_deck(deck_id, version=None)
                self.log(f"  SUCCESS: {download_info}")
            except NottorneyAPIError as e:
                self.log(f"  FAILED: {str(e)}")
                if "version" in str(e).lower():
                    self.log(f"  Retry: download_deck('{deck_id}', version='{deck_version}')")
                    download_info = api.download_deck(deck_id, version=deck_version)
                    self.log(f"  SUCCESS: {download_info}")
                else:
                    raise
            
            download_url = download_info.get('download_url')
            if not download_url:
                raise NottorneyAPIError("No download_url in response")
            
            self.log(f"Download URL: {download_url[:80]}...")
            
            # Step 2: Download file
            self.log("Step 2: Downloading deck file...")
            progress.setLabelText("Downloading deck file...")
            progress.setValue(40)
            
            deck_content = api.download_deck_file(download_url)
            self.log(f"Downloaded {len(deck_content)} bytes")
            
            if not deck_content:
                raise NottorneyAPIError("Downloaded file is empty")
            
            # Step 3: Import into Anki
            self.log("Step 3: Importing into Anki...")
            progress.setLabelText("Importing...")
            progress.setValue(70)
            
            anki_deck_id = import_deck(deck_content, deck_title)
            self.log(f"Imported! Anki deck ID: {anki_deck_id}")
            
            # Step 4: Save to config
            self.log("Step 4: Saving to config...")
            progress.setValue(90)
            
            actual_version = download_info.get('version', deck_version)
            config.save_downloaded_deck(deck_id, actual_version, anki_deck_id)
            
            progress.setValue(100)
            progress.close()
            
            self.log("=== DOWNLOAD COMPLETE ===\n")
            
            QMessageBox.information(
                self, "Success",
                f"Successfully imported:\n\n'{deck_title}' (v{actual_version})"
            )
            
            self.load_decks()
        
        except NottorneyAPIError as e:
            progress.close()
            error_msg = str(e)
            self.log(f"API ERROR: {error_msg}")
            
            QMessageBox.warning(self, "Download Error", 
                f"Download failed:\n\n{error_msg}\n\nCheck the debug log for details.")
        
        except Exception as e:
            progress.close()
            error_msg = str(e)
            self.log(f"EXCEPTION: {error_msg}")
            self.log(traceback.format_exc())
            
            QMessageBox.critical(self, "Error", 
                f"Unexpected error:\n\n{error_msg}\n\nCheck the debug log for details.")