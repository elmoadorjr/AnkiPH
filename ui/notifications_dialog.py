"""
Notifications Dialog for Nottorney Addon
Shows deck updates and announcements
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, Qt, QTextEdit,
    QGroupBox, QFrame
)
from aqt import mw
from ..api_client import api, NottorneyAPIError
from ..config import config
from datetime import datetime


class NotificationsDialog(QDialog):
    """Dialog for viewing notifications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔔 Notifications")
        self.setMinimumSize(600, 500)
        self.notifications = []
        self.dark_mode = True
        
        self.setup_ui()
        self.apply_theme()
        self.load_notifications()
    
    def get_stylesheet(self):
        """Get dark theme stylesheet"""
        return """
            QDialog { background-color: #1e1e1e; }
            QGroupBox {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; margin-top: 10px; padding-top: 15px;
                font-weight: bold; color: #e0e0e0;
            }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QLabel#headerLabel { 
                color: #e0e0e0; font-size: 24px; 
                font-weight: bold; 
            }
            QLabel#infoLabel {
                background-color: #1565c0; border-left: 4px solid #2196f3;
                border-radius: 6px; padding: 12px; color: #ffffff; font-size: 13px;
            }
            QLabel#emptyLabel {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 6px; padding: 30px; color: #888; 
                font-size: 14px; text-align: center;
            }
            QListWidget {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 8px; padding: 4px; outline: none; color: #e0e0e0;
            }
            QListWidget::item {
                padding: 15px; border: 1px solid #3a3a3a;
                border-radius: 6px; margin: 4px 2px;
                background-color: #2d2d2d;
            }
            QListWidget::item:hover {
                background-color: #353535; border-color: #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #1565c0; color: #ffffff;
                border: 2px solid #2196f3;
            }
            QPushButton {
                background-color: #2d2d2d; border: 1px solid #505050;
                border-radius: 6px; padding: 10px 20px; color: #e0e0e0;
                font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background-color: #353535; border-color: #2196f3; }
            QPushButton:pressed { background-color: #1565c0; }
            QPushButton:disabled { background-color: #1a1a1a; color: #666; }
            QPushButton#primaryButton {
                background-color: #4caf50; color: white; border: none;
                font-weight: bold; padding: 12px 24px;
            }
            QPushButton#primaryButton:hover { background-color: #45a049; }
            QTextEdit {
                background-color: #2d2d2d; border: 1px solid #404040;
                border-radius: 6px; padding: 12px; color: #e0e0e0;
            }
        """
    
    def apply_theme(self):
        """Apply theme"""
        self.setStyleSheet(self.get_stylesheet())
    
    def setup_ui(self):
        """Set up the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔔 Notifications")
        title.setObjectName("headerLabel")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.unread_label = QLabel("0 unread")
        header_layout.addWidget(self.unread_label)
        
        layout.addLayout(header_layout)
        
        # Info/empty state
        self.info_label = QLabel("Loading notifications...")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        self.empty_label = QLabel(
            "📭 No notifications\n\n"
            "You're all caught up!"
        )
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        
        # Notification list
        self.notif_list = QListWidget()
        self.notif_list.itemClicked.connect(self.on_notification_clicked)
        layout.addWidget(self.notif_list)
        
        # Detail view
        detail_group = QGroupBox("📄 Details")
        detail_layout = QVBoxLayout()
        
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setMaximumHeight(150)
        self.detail_view.setText("Select a notification to view details")
        detail_layout.addWidget(self.detail_view)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_notifications)
        
        self.mark_read_btn = QPushButton("✓ Mark All Read")
        self.mark_read_btn.clicked.connect(self.mark_all_read)
        self.mark_read_btn.setEnabled(False)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.mark_read_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_notifications(self):
        """Load notifications from API"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ Loading...")
        self.info_label.setText("Loading notifications...")
        self.info_label.show()
        self.empty_label.hide()
        self.notif_list.clear()
        
        try:
            print("=== Loading notifications ===")
            result = api.check_notifications(mark_as_read=False, limit=20)
            
            if result.get('success'):
                self.notifications = result.get('notifications', [])
                unread_count = result.get('unread_count', 0)
                total_count = result.get('total_count', 0)
                
                print(f"Loaded {len(self.notifications)} notification(s), {unread_count} unread")
                
                # Update config cache
                config.set_unread_notification_count(unread_count)
                config.update_last_notification_check()
                
                # Update UI
                self.unread_label.setText(f"{unread_count} unread")
                
                if not self.notifications:
                    self.info_label.hide()
                    self.empty_label.show()
                    self.mark_read_btn.setEnabled(False)
                else:
                    self.info_label.setText(
                        f"📬 {total_count} total notification(s) • "
                        f"{unread_count} unread"
                    )
                    self.populate_notifications()
                    self.mark_read_btn.setEnabled(unread_count > 0)
            else:
                error = result.get('error', 'Failed to load notifications')
                self.info_label.setText(f"❌ {error}")
                QMessageBox.warning(self, "Error", f"Failed to load notifications:\n\n{error}")
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            print(f"Error loading notifications: {error_msg}")
            self.info_label.setText(f"❌ {error_msg}")
            QMessageBox.warning(self, "Error", f"Failed to load notifications:\n\n{error_msg}")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.info_label.setText(f"❌ Error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load notifications:\n\n{str(e)}")
        
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh")
    
    def populate_notifications(self):
        """Populate notification list"""
        self.notif_list.clear()
        
        for notif in self.notifications:
            notif_type = notif.get('type', 'unknown')
            title = notif.get('title', 'Notification')
            message = notif.get('message', '')
            created_at = notif.get('created_at', '')
            is_read = notif.get('read', False)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%b %d, %I:%M %p')
            except:
                time_str = created_at[:10] if created_at else ''
            
            # Icon based on type
            if notif_type == 'deck_update':
                icon = '⟳'
            elif notif_type == 'announcement':
                icon = '📢'
            else:
                icon = '🔔'
            
            # Unread indicator
            unread_indicator = '● ' if not is_read else ''
            
            # Create display text
            display_text = f"{unread_indicator}{icon} {title}\n   {time_str}"
            if message:
                # Truncate long messages
                short_message = message[:60] + '...' if len(message) > 60 else message
                display_text += f"\n   {short_message}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, notif)
            
            # Bold unread notifications
            if not is_read:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.notif_list.addItem(item)
    
    def on_notification_clicked(self, item):
        """Handle notification click"""
        notif = item.data(Qt.ItemDataRole.UserRole)
        self.show_notification_details(notif)
    
    def show_notification_details(self, notif):
        """Show notification details"""
        notif_type = notif.get('type', 'unknown')
        title = notif.get('title', 'Notification')
        message = notif.get('message', 'No message')
        created_at = notif.get('created_at', '')
        metadata = notif.get('metadata', {})
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_str = dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            time_str = created_at
        
        # Build details HTML
        html = f"<h3>{title}</h3>"
        html += f"<p><small><i>{time_str}</i></small></p>"
        html += f"<p>{message}</p>"
        
        # Add type-specific details
        if notif_type == 'deck_update' and metadata:
            deck_title = metadata.get('deck_title', 'Unknown Deck')
            new_version = metadata.get('new_version', '')
            version_notes = metadata.get('version_notes', '')
            
            html += f"<hr>"
            html += f"<p><b>Deck:</b> {deck_title}</p>"
            if new_version:
                html += f"<p><b>New Version:</b> {new_version}</p>"
            if version_notes:
                html += f"<p><b>What's New:</b><br>{version_notes[:200]}</p>"
        
        elif notif_type == 'announcement' and metadata:
            priority = metadata.get('priority', 'normal')
            if priority == 'high':
                html += f"<p><b>⚠️ Priority:</b> High</p>"
        
        self.detail_view.setHtml(html)
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        reply = QMessageBox.question(
            self, "Mark All Read",
            "Mark all notifications as read?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.mark_read_btn.setEnabled(False)
        self.mark_read_btn.setText("⏳ Marking...")
        
        try:
            # Call API with mark_as_read=True to mark all returned notifications
            result = api.check_notifications(mark_as_read=True, limit=100)
            
            if result.get('success'):
                print("All notifications marked as read")
                QMessageBox.information(self, "Success", "All notifications marked as read!")
                
                # Update config
                config.set_unread_notification_count(0)
                
                # Reload
                self.load_notifications()
            else:
                error = result.get('error', 'Failed to mark as read')
                QMessageBox.warning(self, "Error", error)
        
        except Exception as e:
            print(f"Error marking notifications as read: {e}")
            QMessageBox.warning(self, "Error", f"Failed to mark as read:\n\n{str(e)}")
        
        finally:
            self.mark_read_btn.setEnabled(True)
            self.mark_read_btn.setText("✓ Mark All Read")