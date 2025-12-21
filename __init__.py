"""
AnkiPH Anki Addon - Simplified Version
PyQt6 Compatible - v3.3.0
SIMPLIFIED: Subscription-only model, auto-sync on startup
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo, tooltip

# Global reference to prevent garbage collection
_dialog_instance = None

# Initialize logger as None first
logger = None

try:
    # Import logger FIRST before anything else
    from .logger import logger
    
    from .config import config
    from . import sync
    from .api_client import api, set_access_token
    from .update_checker import update_checker
    from .constants import ADDON_NAME, ADDON_VERSION
    
    # Use simplified main dialog (v3.0.0)
    from .ui.main_dialog import AnkiPHMainDialog as MainDialog
    from .ui.login_dialog import show_login_dialog
        
except ImportError as e:
    # Defer error display until Anki is ready (mw might not be initialized yet)
    _import_error = str(e)
    
    def show_startup_error():
        from aqt.utils import showInfo
        showInfo(f"AnkiPH addon import error: {_import_error}\n\nPlease check that all files are present.")
    
    from aqt import gui_hooks
    gui_hooks.main_window_did_init.append(show_startup_error)
    # Don't raise - allow Anki to continue loading
    pass


def show_settings_dialog():
    """Show settings dialog"""
    try:
        from .ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(mw)
        dialog.exec()
    except Exception as e:
        showInfo(f"Error opening settings:\n{str(e)}")
        if logger:
            logger.exception(f"Settings dialog error: {e}")


def on_menu_action(*args):
    """Smart menu action: Login -> Main Dialog"""
    try:
        # If not logged in, show login dialog first
        if not config.is_logged_in():
            if show_login_dialog(mw):
                # If login successful, proceed to main dialog
                show_main_dialog()
        else:
            # Already logged in, show main dialog
            show_main_dialog()
            
    except Exception as e:
        showInfo(f"Error opening AnkiPH:\n{str(e)}")
        if logger:
            logger.exception(f"Menu action error: {e}")


def show_main_dialog():
    """Show main dialog"""
    global _dialog_instance
    
    if _dialog_instance:
        _dialog_instance.raise_()
        _dialog_instance.activateWindow()
        return

    try:
        # Create new dialog instance
        _dialog_instance = MainDialog(mw)
        _dialog_instance.finished.connect(lambda: _on_dialog_finished())
        _dialog_instance.show()
        
    except Exception as e:
        showInfo(f"Error opening AnkiPH dialog:\n{str(e)}")
        if logger:
            logger.exception(f"Dialog error: {e}")
        _dialog_instance = None


def _on_dialog_finished():
    """Cleanup when dialog is closed"""
    global _dialog_instance
    _dialog_instance = None
    
    # Sync progress after dialog closes if logged in
    if config.is_logged_in():
        try:
            # Set the access token before syncing
            token = config.get_access_token()
            if token:
                set_access_token(token)
            sync.sync_progress()
            if logger:
                logger.info("Progress synced successfully after dialog close")
        except Exception as e: 
            if logger:
                logger.warning(f"Sync failed (non-critical): {e}")


def on_main_window_did_init():
    """Called when Anki's main window finishes initializing"""
    if not config.is_logged_in():
        return
    
    try:
        # Set access token
        token = config.get_access_token()
        if token:
            set_access_token(token)
        
        # Check for updates
        updates = update_checker.check_for_updates(silent=True)
        
        # Auto-apply updates if any available
        if updates and len(updates) > 0:
            count = len(updates)
            tooltip(f"⚖️ AnkiPH: {count} deck update(s) available")
            
            # Try to auto-apply updates silently
            try:
                update_checker.auto_apply_updates()
            except Exception as e:
                print(f"Auto-apply updates failed (non-critical): {e}")
                
    except Exception as e:
        if logger:
            logger.warning(f"AnkiPH startup check failed (non-critical): {e}")


def setup_menu():
    """Setup menu in Anki - direct action in menu bar next to Help"""
    try:
        # Create AnkiPH action for the top menu bar
        action = QAction(f"⚖️ AnkiPH", mw)
        action.triggered.connect(on_menu_action)
        
        # Insert before Help menu (Help is typically the last menu)
        # Get the menubar and insert before Help
        menubar = mw.form.menubar
        help_menu = mw.form.menuHelp
        menubar.insertAction(help_menu.menuAction(), action)
        
        if logger:
            logger.info(f"AnkiPH addon v{ADDON_VERSION} loaded successfully")
            logger.info(f"Auto-update check: {config.get_auto_check_updates()}")
        
    except Exception as e:
        if logger:
            logger.error(f"Error setting up AnkiPH menu: {e}")
        showInfo(f"AnkiPH addon failed to load:\n{str(e)}")


# Setup hooks
try:
    setup_menu()
    gui_hooks.main_window_did_init.append(on_main_window_did_init)
except Exception as e:
    print(f"✗ Fatal error loading AnkiPH addon: {e}")
    showInfo(f"Fatal error loading AnkiPH addon:\n{str(e)}")