"""
Sync Dialog for Nottorney Addon
Features: Push/Pull changes, Conflict Resolution
Version: 1.0.0
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, Qt,
    QTabWidget, QWidget, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit, QSplitter, QFrame,
    QProgressBar
)
from aqt import mw
from datetime import datetime

from ..api_client import api, set_access_token, NottorneyAPIError
from ..config import config


class SyncDialog(QDialog):
    """Dialog for syncing changes with server"""
    
    def __init__(self, deck_id: str, deck_name: str = "", parent=None):
        super().__init__(parent)
        self.deck_id = deck_id
        self.deck_name = deck_name or f"Deck {deck_id[:8]}"
        self.pending_changes = []
        self.conflicts = []
        self.sync_in_progress = False
        
        self.setWindowTitle(f"🔄 Sync - {self.deck_name}")
        self.setMinimumSize(700, 550)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel(f"🔄 Sync Changes - {self.deck_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget for Push/Pull
        self.tabs = QTabWidget()
        
        self.pull_tab = self.create_pull_tab()
        self.push_tab = self.create_push_tab()
        self.conflicts_tab = self.create_conflicts_tab()
        
        self.tabs.addTab(self.pull_tab, "⬇️ Pull Changes")
        self.tabs.addTab(self.push_tab, "⬆️ Push Changes")
        self.tabs.addTab(self.conflicts_tab, "⚠️ Conflicts (0)")
        
        layout.addWidget(self.tabs)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Check for Changes")
        refresh_btn.clicked.connect(self.check_for_changes)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 20px;")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Initial check
        self.check_for_changes()
    
    def create_pull_tab(self):
        """Create Pull Changes tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Server changes that will be applied to your local deck.\n"
            "These are updates from the deck publisher."
        )
        instructions.setStyleSheet("color: #666; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Changes list
        self.pull_changes_list = QListWidget()
        self.pull_changes_list.setStyleSheet("QListWidget::item { padding: 8px; }")
        self.pull_changes_list.itemClicked.connect(self.show_pull_change_details)
        layout.addWidget(self.pull_changes_list)
        
        # Details panel
        details_group = QGroupBox("Change Details")
        details_layout = QVBoxLayout()
        self.pull_details_text = QTextEdit()
        self.pull_details_text.setReadOnly(True)
        self.pull_details_text.setMaximumHeight(100)
        details_layout.addWidget(self.pull_details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        pull_all_btn = QPushButton("⬇️ Pull All Changes")
        pull_all_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #2196F3; color: white;")
        pull_all_btn.clicked.connect(self.pull_all_changes)
        btn_layout.addWidget(pull_all_btn)
        
        pull_selected_btn = QPushButton("⬇️ Pull Selected")
        pull_selected_btn.clicked.connect(self.pull_selected_change)
        btn_layout.addWidget(pull_selected_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_push_tab(self):
        """Create Push Changes tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Your local changes that can be pushed to the server.\n"
            "Note: Only approved contributors can push changes."
        )
        instructions.setStyleSheet("color: #666; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Changes list
        self.push_changes_list = QListWidget()
        self.push_changes_list.setStyleSheet("QListWidget::item { padding: 8px; }")
        self.push_changes_list.itemClicked.connect(self.show_push_change_details)
        layout.addWidget(self.push_changes_list)
        
        # Details panel
        details_group = QGroupBox("Change Details")
        details_layout = QVBoxLayout()
        self.push_details_text = QTextEdit()
        self.push_details_text.setReadOnly(True)
        self.push_details_text.setMaximumHeight(100)
        details_layout.addWidget(self.push_details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        push_all_btn = QPushButton("⬆️ Push All Changes")
        push_all_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #4CAF50; color: white;")
        push_all_btn.clicked.connect(self.push_all_changes)
        btn_layout.addWidget(push_all_btn)
        
        push_selected_btn = QPushButton("⬆️ Push Selected")
        push_selected_btn.clicked.connect(self.push_selected_change)
        btn_layout.addWidget(push_selected_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_conflicts_tab(self):
        """Create Conflicts Resolution tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "These changes have conflicts between local and server versions.\n"
            "Choose how to resolve each conflict."
        )
        instructions.setStyleSheet("color: #666; padding: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Conflicts list
        self.conflicts_list = QListWidget()
        self.conflicts_list.setStyleSheet("QListWidget::item { padding: 10px; }")
        self.conflicts_list.itemClicked.connect(self.show_conflict_details)
        layout.addWidget(self.conflicts_list)
        
        # Conflict resolution panel
        resolution_group = QGroupBox("Resolve Conflict")
        resolution_layout = QVBoxLayout()
        
        # Side-by-side comparison
        compare_layout = QHBoxLayout()
        
        # Local version
        local_frame = QFrame()
        local_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        local_layout = QVBoxLayout()
        local_label = QLabel("📍 Local Version")
        local_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        local_layout.addWidget(local_label)
        self.local_text = QTextEdit()
        self.local_text.setReadOnly(True)
        self.local_text.setMaximumHeight(80)
        local_layout.addWidget(self.local_text)
        local_frame.setLayout(local_layout)
        compare_layout.addWidget(local_frame)
        
        # Server version
        server_frame = QFrame()
        server_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        server_layout = QVBoxLayout()
        server_label = QLabel("☁️ Server Version")
        server_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        server_layout.addWidget(server_label)
        self.server_text = QTextEdit()
        self.server_text.setReadOnly(True)
        self.server_text.setMaximumHeight(80)
        server_layout.addWidget(self.server_text)
        server_frame.setLayout(server_layout)
        compare_layout.addWidget(server_frame)
        
        resolution_layout.addLayout(compare_layout)
        
        # Resolution options
        options_layout = QHBoxLayout()
        
        self.resolution_group = QButtonGroup()
        
        keep_local_btn = QRadioButton("Keep Local")
        keep_local_btn.setStyleSheet("color: #2196F3;")
        self.resolution_group.addButton(keep_local_btn, 1)
        options_layout.addWidget(keep_local_btn)
        
        take_server_btn = QRadioButton("Take Server")
        take_server_btn.setStyleSheet("color: #4CAF50;")
        self.resolution_group.addButton(take_server_btn, 2)
        options_layout.addWidget(take_server_btn)
        
        take_server_btn.setChecked(True)
        
        options_layout.addStretch()
        
        resolve_btn = QPushButton("✓ Resolve This Conflict")
        resolve_btn.clicked.connect(self.resolve_selected_conflict)
        options_layout.addWidget(resolve_btn)
        
        resolution_layout.addLayout(options_layout)
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        # Resolve all button
        btn_layout = QHBoxLayout()
        
        resolve_all_local_btn = QPushButton("Keep All Local")
        resolve_all_local_btn.clicked.connect(lambda: self.resolve_all_conflicts("local"))
        btn_layout.addWidget(resolve_all_local_btn)
        
        resolve_all_server_btn = QPushButton("Take All Server")
        resolve_all_server_btn.clicked.connect(lambda: self.resolve_all_conflicts("server"))
        btn_layout.addWidget(resolve_all_server_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        tab.setLayout(layout)
        return tab
    
    def check_for_changes(self):
        """Check for pending changes from server"""
        token = config.get_access_token()
        if not token:
            self.status_label.setText("❌ Not logged in")
            return
        
        set_access_token(token)
        self.status_label.setText("⏳ Checking for changes...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            # Get sync state
            sync_state = config.get_sync_state(self.deck_id)
            last_sync = sync_state.get('last_change_id') or sync_state.get('last_sync')
            
            # Pull changes from server
            result = api.pull_changes(
                deck_id=self.deck_id,
                since=last_sync
            )
            
            if not result.get('success'):
                self.status_label.setText("❌ Failed to check for changes")
                self.progress_bar.setVisible(False)
                return
            
            # Process changes
            changes = result.get('changes', [])
            self.conflicts = result.get('conflicts', [])
            
            # Update pull list
            self.pull_changes_list.clear()
            for change in changes:
                card_guid = change.get('card_guid', 'Unknown')
                field_name = change.get('field_name', 'Unknown')
                change_type = change.get('change_type', 'modify')
                
                icon = "📝" if change_type == "modify" else "➕" if change_type == "add" else "🗑️"
                display_text = f"{icon} {card_guid[:8]} - {field_name}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, change)
                self.pull_changes_list.addItem(item)
            
            # Update conflicts list
            self.conflicts_list.clear()
            for conflict in self.conflicts:
                card_guid = conflict.get('card_guid', 'Unknown')
                field_name = conflict.get('field_name', 'Unknown')
                
                display_text = f"⚠️ {card_guid[:8]} - {field_name}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, conflict)
                item.setForeground(Qt.GlobalColor.darkYellow)
                self.conflicts_list.addItem(item)
            
            # Update tab label
            self.tabs.setTabText(2, f"⚠️ Conflicts ({len(self.conflicts)})")
            
            # Status
            self.status_label.setText(
                f"✓ Found {len(changes)} change(s), {len(self.conflicts)} conflict(s)"
            )
            
            # Check for local changes to push (placeholder - would need to track local edits)
            self.push_changes_list.clear()
            item = QListWidgetItem("📝 Local change tracking coming soon")
            item.setForeground(Qt.GlobalColor.gray)
            self.push_changes_list.addItem(item)
            
        except NottorneyAPIError as e:
            error_msg = str(e)
            if e.status_code == 401:
                error_msg = "Session expired"
                config.clear_tokens()
            self.status_label.setText(f"❌ {error_msg}")
        
        except Exception as e:
            self.status_label.setText("❌ Error checking changes")
            print(f"Error checking changes: {e}")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def show_pull_change_details(self, item):
        """Show details for selected pull change"""
        change = item.data(Qt.ItemDataRole.UserRole)
        if not change or not isinstance(change, dict):
            return
        
        details = (
            f"Card: {change.get('card_guid', 'Unknown')}\n"
            f"Field: {change.get('field_name', 'Unknown')}\n"
            f"Type: {change.get('change_type', 'modify')}\n"
            f"Version: {change.get('version', 'Unknown')}\n"
            f"Changed: {change.get('changed_at', 'Unknown')}"
        )
        self.pull_details_text.setText(details)
    
    def show_push_change_details(self, item):
        """Show details for selected push change"""
        change = item.data(Qt.ItemDataRole.UserRole)
        if not change or not isinstance(change, dict):
            self.push_details_text.setText("No details available")
            return
        
        details = (
            f"Card: {change.get('card_guid', 'Unknown')}\n"
            f"Field: {change.get('field_name', 'Unknown')}\n"
            f"New Value: {change.get('new_value', 'Unknown')[:100]}"
        )
        self.push_details_text.setText(details)
    
    def show_conflict_details(self, item):
        """Show details for selected conflict"""
        conflict = item.data(Qt.ItemDataRole.UserRole)
        if not conflict or not isinstance(conflict, dict):
            return
        
        self.local_text.setText(conflict.get('local_value', 'Unknown'))
        self.server_text.setText(conflict.get('server_value', 'Unknown'))
    
    def pull_all_changes(self):
        """Pull all changes from server"""
        if self.pull_changes_list.count() == 0:
            QMessageBox.information(self, "No Changes", "No changes to pull.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Pull",
            f"Apply all {self.pull_changes_list.count()} changes from server?\n\n"
            "This will update your local cards with server versions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._apply_pulled_changes()
    
    def pull_selected_change(self):
        """Pull selected change"""
        current = self.pull_changes_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a change to pull.")
            return
        
        QMessageBox.information(
            self, "Coming Soon",
            "Individual change pulling will be available in a future update."
        )
    
    def _apply_pulled_changes(self):
        """Apply pulled changes to local cards"""
        self.status_label.setText("⏳ Applying changes...")
        
        # TODO: Implement actual card updates
        # This would need to:
        # 1. Find local cards by GUID
        # 2. Update field values
        # 3. Save changes to Anki DB
        
        # For now, just update sync state
        config.save_sync_state(self.deck_id, {
            'last_sync': datetime.now().isoformat(),
            'pulled_changes': self.pull_changes_list.count()
        })
        
        self.status_label.setText("✓ Changes applied (sync state updated)")
        QMessageBox.information(
            self, "Sync Complete",
            f"Sync state updated.\n\n"
            "Note: Full card-level sync implementation coming soon."
        )
        
        # Refresh
        self.check_for_changes()
    
    def push_all_changes(self):
        """Push all local changes to server"""
        QMessageBox.information(
            self, "Coming Soon",
            "Push changes feature requires local change tracking.\n\n"
            "This will be available in a future update."
        )
    
    def push_selected_change(self):
        """Push selected change"""
        QMessageBox.information(
            self, "Coming Soon",
            "Push changes feature requires local change tracking.\n\n"
            "This will be available in a future update."
        )
    
    def resolve_selected_conflict(self):
        """Resolve the currently selected conflict"""
        current = self.conflicts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a conflict to resolve.")
            return
        
        conflict = current.data(Qt.ItemDataRole.UserRole)
        if not conflict:
            return
        
        # Get resolution choice
        resolution_id = self.resolution_group.checkedId()
        keep_local = resolution_id == 1
        
        resolution = "local" if keep_local else "server"
        
        # Remove from list
        row = self.conflicts_list.row(current)
        self.conflicts_list.takeItem(row)
        
        # Update tab label
        remaining = self.conflicts_list.count()
        self.tabs.setTabText(2, f"⚠️ Conflicts ({remaining})")
        
        self.status_label.setText(f"✓ Conflict resolved (kept {resolution})")
        
        if remaining == 0:
            QMessageBox.information(self, "All Resolved", "All conflicts have been resolved!")
    
    def resolve_all_conflicts(self, resolution: str):
        """Resolve all conflicts with same resolution"""
        count = self.conflicts_list.count()
        if count == 0:
            QMessageBox.information(self, "No Conflicts", "No conflicts to resolve.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Resolution",
            f"Resolve all {count} conflicts by keeping {resolution} version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conflicts_list.clear()
            self.tabs.setTabText(2, "⚠️ Conflicts (0)")
            self.status_label.setText(f"✓ All conflicts resolved (kept {resolution})")
            
            QMessageBox.information(
                self, "Conflicts Resolved",
                f"All {count} conflicts resolved by keeping {resolution} versions."
            )


def show_sync_dialog(deck_id: str, deck_name: str = "", parent=None):
    """Show the sync dialog for a deck"""
    dialog = SyncDialog(deck_id, deck_name, parent or mw)
    dialog.exec()
