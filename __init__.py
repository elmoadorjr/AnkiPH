"""
Nottorney Anki Addon - Enhanced Version
PyQt6 Compatible - v1.1.0
NEW: Update checking, tabbed UI, notifications
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

# Global reference to prevent garbage collection
_dialog_instance = None

try:
    from .config import config
    from . import sync
    from .api_client import api, set_access_token
    from .update_checker import update_checker
    
    # Import appropriate dialog based on config
    ui_mode = config.get_ui_mode()
    if ui_mode == "tabbed":
        from .ui.tabbed_dialog import NottorneyTabbedDialog as MainDialog
    else:
        from .ui.single_dialog import MinimalNottorneyDialog as MainDialog
        
except ImportError as e:
    def show_error():
        showInfo(f"Nottorney addon import error: {str(e)}\n\nPlease check that all files are present.")
    show_error()
    raise

ADDON_NAME = "Nottorney"
ADDON_VERSION = "1.1.0"


def show_main_dialog():
    """Show main dialog"""
    global _dialog_instance
    
    try:
        # Create new dialog instance
        _dialog_instance = MainDialog(mw)
        _dialog_instance.exec()
        
        # Sync progress after dialog closes if logged in
        if config.is_logged_in():
            try:
                # Set the access token before syncing
                token = config.get_access_token()
                if token:
                    set_access_token(token)
                sync.sync_progress()
                print("✓ Progress synced successfully")
            except Exception as e: 
                print(f"Sync failed (non-critical): {e}")
    except Exception as e:
        showInfo(f"Error opening Nottorney dialog:\n{str(e)}")
        print(f"Dialog error: {e}")
    finally:
        _dialog_instance = None


def on_main_window_did_init():
    """Called when Anki's main window finishes initializing"""
    # Auto-check for updates on startup if logged in
    if config.is_logged_in():
        try:
            update_checker.auto_check_if_needed()
        except Exception as e:
            print(f"Auto-update check failed (non-critical): {e}")


def setup_menu():
    """Setup menu in Anki"""
    try:
        # Create Nottorney menu
        menu = mw.form.menuTools.addMenu("⚖️ Nottorney")
        
        # Add "Open" action
        open_action = QAction("Open Nottorney", mw)
        open_action.triggered.connect(show_main_dialog)
        menu.addAction(open_action)
        
        # Add "Check for Updates" action
        update_action = QAction("Check for Updates", mw)
        update_action.triggered.connect(lambda: update_checker.check_for_updates(silent=False))
        menu.addAction(update_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Settings" action (placeholder for future)
        settings_action = QAction("Settings", mw)
        settings_action.setEnabled(False)  # Disabled for now
        menu.addAction(settings_action)
        
        print(f"✓ Nottorney addon v{ADDON_VERSION} loaded successfully")
        print(f"  UI Mode: {config.get_ui_mode()}")
        print(f"  Auto-update check: {config.get_auto_check_updates()}")
        
    except Exception as e:
        print(f"✗ Error setting up Nottorney menu: {e}")
        showInfo(f"Nottorney addon failed to load:\n{str(e)}")


# Setup hooks
try:
    setup_menu()
    gui_hooks.main_window_did_init.append(on_main_window_did_init)
except Exception as e:
    print(f"✗ Fatal error loading Nottorney addon: {e}")
    showInfo(f"Fatal error loading Nottorney addon:\n{str(e)}")