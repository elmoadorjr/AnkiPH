"""
Nottorney Anki Addon
Main entry point for the addon
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

# Import all modules at the top to catch import errors early
try:
    from .ui.login_dialog import LoginDialog
    from .ui.deck_manager_dialog import DeckManagerDialog
    from .config import config
    from . import sync  # Import the sync module
except ImportError as e:
    # If imports fail, show error and exit gracefully
    def show_import_error():
        showInfo(f"Ottorney addon import error: {str(e)}\n\nPlease reinstall the addon.")
    
    # Set up a minimal menu that shows the error
    def setup_error_menu():
        menu = mw.form.menuTools.addMenu("Ottorney (Error)")
        error_action = QAction("Show Error", mw)
        error_action.triggered.connect(show_import_error)
        menu.addAction(error_action)
    
    setup_error_menu()
    raise  # Re-raise to see full traceback

# Addon metadata
ADDON_NAME = "Ottorney"
ADDON_VERSION = "1.0.0"


def show_login():
    """Show the login dialog"""
    dialog = LoginDialog(mw)
    if dialog.exec():
        showInfo("Login successful!")
        show_deck_manager()


def show_deck_manager():
    """Show the deck manager dialog"""
    if not config.is_logged_in():
        showInfo("Please login first")
        show_login()
        return
    
    dialog = DeckManagerDialog(mw)
    dialog.exec()


def on_sync_progress():
    """Sync progress to server"""
    if not config.is_logged_in():
        return
    
    try:
        sync.sync_progress()
        showInfo("Progress synced successfully!")
    except Exception as e:
        showInfo(f"Error syncing progress: {str(e)}")


def setup_menu():
    """Set up the addon menu in Anki"""
    # Create main menu
    menu = mw.form.menuTools.addMenu(ADDON_NAME)
    
    # Login action
    login_action = QAction("Login", mw)
    login_action.triggered.connect(show_login)
    menu.addAction(login_action)
    
    # Manage Decks action
    manage_action = QAction("Manage Decks", mw)
    manage_action.triggered.connect(show_deck_manager)
    menu.addAction(manage_action)
    
    # Sync Progress action
    sync_action = QAction("Sync Progress", mw)
    sync_action.triggered.connect(on_sync_progress)
    menu.addAction(sync_action)
    
    # Separator
    menu.addSeparator()
    
    # Logout action
    logout_action = QAction("Logout", mw)
    logout_action.triggered.connect(logout)
    menu.addAction(logout_action)


def logout():
    """Logout the user"""
    config.clear_tokens()
    showInfo("Logged out successfully")


def safe_auto_sync():
    """Safely attempt auto-sync without showing errors"""
    try:
        if config.is_logged_in():
            sync.sync_progress()
    except Exception:
        # Silently fail for auto-sync
        pass


# Initialize the addon
def init_addon():
    """Initialize the addon when Anki starts"""
    setup_menu()
    
    # Auto-sync progress on profile load
    gui_hooks.profile_did_open.append(safe_auto_sync)


# Run initialization
init_addon()