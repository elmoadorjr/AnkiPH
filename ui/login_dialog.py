"""
Enhanced Login Dialog for Nottorney Addon
Clean, modern UI with better user experience
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from ..api_client import api, NottorneyAPIError


class LoginDialog(QDialog):
    """Modern dialog for user login"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚖️ Nottorney Login")
        self.setMinimumWidth(450)
        self.setStyleSheet(self.get_stylesheet())
        self.setup_ui()
    
    def get_stylesheet(self):
        """Return modern stylesheet for login dialog"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
                border-radius: 10px;
                padding: 20px;
            }
            
            QLabel#headerLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#subtitleLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
            }
            
            QLabel#fieldLabel {
                color: #2c3e50;
                font-weight: 500;
                font-size: 13px;
            }
            
            QLineEdit {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #2c3e50;
            }
            
            QLineEdit:focus {
                border: 2px solid #2196f3;
                background-color: #fafafa;
            }
            
            QLineEdit:hover {
                border-color: #bdbdbd;
            }
            
            QPushButton {
                background-color: white;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                padding: 12px 24px;
                color: #2c3e50;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #2196f3;
            }
            
            QPushButton:pressed {
                background-color: #e3f2fd;
            }
            
            QPushButton#loginButton {
                background-color: #4caf50;
                color: white;
                border: none;
                font-size: 15px;
                padding: 14px 28px;
            }
            
            QPushButton#loginButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#loginButton:pressed {
                background-color: #388e3c;
            }
            
            QPushButton#loginButton:disabled {
                background-color: #cccccc;
                color: #666;
            }
            
            QLabel#errorLabel {
                background-color: #ffebee;
                color: #c62828;
                border: 1px solid #ef9a9a;
                border-radius: 6px;
                padding: 10px;
            }
            
            QLabel#infoLabel {
                background-color: #e3f2fd;
                color: #1565c0;
                border: 1px solid #90caf9;
                border-radius: 6px;
                padding: 10px;
            }
        """
    
    def setup_ui(self):
        """Set up the modern UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with gradient background
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("⚖️ Nottorney")
        title.setObjectName("headerLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Sign in to access your flashcard decks")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_frame.setLayout(header_layout)
        
        layout.addWidget(header_frame)
        
        # Info message
        info_label = QLabel("💡 Use your Nottorney account credentials")
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Email field
        email_label = QLabel("📧 Email Address")
        email_label.setObjectName("fieldLabel")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("🔒 Password")
        password_label.setObjectName("fieldLabel")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        # Error message label (hidden by default)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Add some spacing
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        self.login_button = QPushButton("🔐 Sign In")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setDefault(True)
        
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Footer help text
        footer_label = QLabel(
            "<p style='color: #666; text-align: center; font-size: 12px;'>"
            "Don't have an account? "
            "<a href='https://nottorney.lovable.app' style='color: #2196f3;'>Visit Nottorney</a>"
            "</p>"
        )
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer_label)
        
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Focus on email input
        self.email_input.setFocus()
    
    def handle_login(self):
        """Handle the login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not email:
            self.show_error("⚠️ Please enter your email address")
            self.email_input.setFocus()
            return
        
        if not password:
            self.show_error("⚠️ Please enter your password")
            self.password_input.setFocus()
            return
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            self.show_error("⚠️ Please enter a valid email address")
            self.email_input.setFocus()
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("🔄 Signing in...")
        self.hide_error()
        
        try:
            # Call the API
            result = api.login(email, password)
            
            if result.get('success'):
                # Login successful
                user_email = result.get('user', {}).get('email', 'User')
                QMessageBox.information(
                    self,
                    "✅ Login Successful",
                    f"Welcome back!\n\n"
                    f"Logged in as: {user_email}\n\n"
                    f"You can now access your purchased decks."
                )
                self.accept()
            else:
                self.show_error("❌ Login failed. Please check your credentials.")
        
        except NottorneyAPIError as e:
            error_msg = str(e)
            # Make error messages more user-friendly
            if "connection" in error_msg.lower():
                error_msg = "❌ Connection error. Please check your internet connection."
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                error_msg = "❌ Incorrect email or password. Please try again."
            elif "timeout" in error_msg.lower():
                error_msg = "❌ Request timed out. Please try again."
            else:
                error_msg = f"❌ {error_msg}"
            
            self.show_error(error_msg)
        
        except Exception as e:
            self.show_error(f"❌ Unexpected error: {str(e)}")
        
        finally:
            # Re-enable button
            self.login_button.setEnabled(True)
            self.login_button.setText("🔐 Sign In")
    
    def show_error(self, message):
        """Show an error message"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def hide_error(self):
        """Hide the error message"""
        self.error_label.hide()