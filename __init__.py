"""
Nottorney Anki Addon - Minimal Version
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

try:
    from . ui. single_dialog import MinimalNottorneyDialog
    from .config import config
    from .  import sync
    from .api_client import api
except ImportError as e:
    def show_error():
        showInfo(f"Nottorney addon error: {str(e)}")
    show_error()
    raise

ADDON_NAME = "Nottorney"
ADDON_VERSION = "1.0.0"


def show_main_dialog():
    """Show main dialog"""
    dialog = MinimalNottorneyDialog(mw)
    dialog.exec()
    if config.is_logged_in():
        try:
            sync.sync_progress()
        except Exception as e: 
            print(f"Sync failed: {e}")


def setup_menu():
    """Setup menu"""
    menu = mw.form.menuTools. addMenu("Nottorney")
    
    action = QAction("Open", mw)
    action.triggered.connect(show_main_dialog)
    menu.addAction(action)


# Setup menu when Anki loads
setup_menu()