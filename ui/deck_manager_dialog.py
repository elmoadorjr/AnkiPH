"""
Deck manager dialog UI for the Nottorney addon
Shows purchased decks and allows downloading them
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QProgressDialog, Qt
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from ..deck_importer import import_deck


class DeckManagerDialog(QDialog):
    """Dialog for managing purchased decks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nottorney Deck Manager")
        self.setMinimumSize(700, 500)
        self.decks = []
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
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download/Update Deck")
        self.download_button.clicked.connect(self.download_selected_deck)
        self.download_button.setEnabled(False)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_decks)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_deck_id(self, deck):
        """Safely extract deck_id from deck object"""
        # Try different possible field names
        return deck.get('deck_id') or deck.get('id') or deck.get('_id') or None
    
    def load_decks(self):
        """Load purchased decks from the API"""
        self.info_label.setText("Loading decks...")
        self.deck_list.clear()
        self.details_label.setText("")
        self.refresh_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        try:
            self.decks = api.get_purchased_decks()
            
            if not self.decks:
                self.info_label.setText("No purchased decks found. Visit the Nottorney website to purchase decks.")
                return
            
            self.info_label.setText(f"Found {len(self.decks)} purchased deck(s)")
            
            # Debug: Print the first deck to see structure
            if self.decks:
                print(f"Sample deck structure: {self.decks[0]}")
            
            # Add decks to list
            for deck in self.decks:
                item = QListWidgetItem()
                
                # Extract deck info safely
                deck_title = deck.get('title', 'Unknown Deck')
                deck_subject = deck.get('subject', 'N/A')
                deck_version = deck.get('current_version') or deck.get('version', 'N/A')
                card_count = deck.get('card_count', 0)
                deck_id = self.get_deck_id(deck)
                
                if not deck_id:
                    print(f"Warning: Deck has no ID field: {deck}")
                    continue
                
                # Check if already downloaded
                is_downloaded = config.is_deck_downloaded(deck_id)
                downloaded_version = config.get_deck_version(deck_id) if is_downloaded else None
                
                # Format display text
                status_icon = "✓" if is_downloaded else "○"
                version_text = f"v{deck_version}"
                
                if is_downloaded:
                    if downloaded_version != deck_version:
                        version_text = f"v{downloaded_version} → v{deck_version} (Update Available)"
                        status_icon = "⟳"
                    else:
                        version_text = f"v{deck_version} (Downloaded)"
                
                display_text = f"{status_icon} {deck_title}\n   {deck_subject} • {card_count} cards • {version_text}"
                
                item.setText(display_text)
                item.setData(Qt.ItemDataRole.UserRole, deck)  # Store deck data
                
                self.deck_list.addItem(item)
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            self.info_label.setText(f"Error: {error_msg}")
            
            # If authentication error, suggest re-login
            if "login" in error_msg.lower() or "auth" in error_msg.lower():
                QMessageBox.warning(
                    self, 
                    "Authentication Error", 
                    f"{error_msg}\n\nPlease login again from the Tools > Nottorney menu."
                )
            else:
                QMessageBox.warning(self, "Error", f"Failed to load decks: {error_msg}")
        
        except Exception as e:
            self.info_label.setText(f"Unexpected error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}\n\nPlease check the Anki console for details.")
            import traceback
            print(traceback.format_exc())
        
        finally:
            self.refresh_button.setEnabled(True)
    
    def on_selection_changed(self):
        """Handle deck selection change"""
        selected_items = self.deck_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.download_button.setEnabled(has_selection)
        
        if has_selection:
            deck = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.show_deck_details(deck)
        else:
            self.details_label.setText("")
    
    def show_deck_details(self, deck):
        """Show details of the selected deck"""
        deck_title = deck.get('title', 'Unknown')
        deck_description = deck.get('description', 'No description available')
        deck_subject = deck.get('subject', 'N/A')
        card_count = deck.get('card_count', 0)
        deck_version = deck.get('current_version') or deck.get('version', 'N/A')
        
        deck_id = self.get_deck_id(deck)
        is_downloaded = config.is_deck_downloaded(deck_id) if deck_id else False
        
        details = f"<b>{deck_title}</b><br>"
        details += f"<i>{deck_description}</i><br><br>"
        details += f"Subject: {deck_subject} | Cards: {card_count} | Version: {deck_version}<br>"
        
        if is_downloaded:
            downloaded_version = config.get_deck_version(deck_id)
            details += f"<span style='color: green;'>Downloaded version: {downloaded_version}</span>"
        
        self.details_label.setText(details)
    
    def download_selected_deck(self):
        """Download the selected deck"""
        selected_items = self.deck_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        deck = item.data(Qt.ItemDataRole.UserRole)
        
        # Extract deck info
        deck_id = self.get_deck_id(deck)
        
        if not deck_id:
            QMessageBox.critical(
                self,
                "Error",
                f"Invalid deck data: missing deck ID\n\nAvailable fields: {list(deck.keys())}"
            )
            return
        
        deck_title = deck.get('title', 'Unknown Deck')
        deck_version = deck.get('current_version') or deck.get('version')
        
        # Check if already downloaded
        if config.is_deck_downloaded(deck_id):
            downloaded_version = config.get_deck_version(deck_id)
            if downloaded_version == deck_version:
                reply = QMessageBox.question(
                    self,
                    "Already Downloaded",
                    f"You've already downloaded this deck (v{downloaded_version}).\n\nDownload and re-import anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Show progress dialog
        progress = QProgressDialog("Preparing download...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Downloading Deck")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)
        progress.show()
        
        try:
            # Get download URL
            progress.setLabelText("Getting download link...")
            progress.setValue(20)
            
            download_info = api.download_deck(deck_id, deck_version)
            
            download_url = download_info.get('download_url')
            if not download_url:
                raise NottorneyAPIError("No download URL provided by server")
            
            # Download the deck file
            progress.setLabelText("Downloading deck file...")
            progress.setValue(40)
            
            deck_content = api.download_deck_file(download_url)
            
            if not deck_content:
                raise NottorneyAPIError("Downloaded file is empty")
            
            # Import into Anki
            progress.setLabelText("Importing into Anki...")
            progress.setValue(70)
            
            anki_deck_id = import_deck(deck_content, deck_title)
            
            # Save to config
            progress.setLabelText("Finalizing...")
            progress.setValue(90)
            
            config.save_downloaded_deck(deck_id, deck_version, anki_deck_id)
            
            progress.setValue(100)
            progress.close()
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully downloaded and imported:\n\n'{deck_title}' (v{deck_version})\n\nThe deck is now available in your Anki collection!"
            )
            
            # Refresh the list
            self.load_decks()
        
        except NottorneyAPIError as e:
            progress.close()
            QMessageBox.warning(self, "Download Error", f"Download failed:\n\n{str(e)}")
        
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Unexpected error during download:\n\n{str(e)}\n\nCheck the Anki console for details.")
            import traceback
            print(traceback.format_exc())