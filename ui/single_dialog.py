"""
Fallback MinimalNottorneyDialog to replace a conflicted ui/single_dialog.py.

This minimal implementation avoids complex UI logic and is intended to
get the addon to import cleanly after resolving a merge conflict. If the
original single_dialog.py had additional behavior you need, paste the
resolved version back in or tell me which features to restore.

Place this file at Nottorney_Addon/ui/single_dialog.py (overwriting the
conflicted file), then restart Anki.
"""

from __future__ import annotations

# Try to import Anki's Qt helpers first (common in Anki add-ons). If not available,
# fall back to PyQt6 directly to maximize compatibility.
try:
    # Anki's aqt.qt exports commonly-used Qt classes
    from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton
except Exception:
    try:
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
    except Exception:
        # Very defensive fallback: define minimal stand-ins so module import won't fail.
        class QDialog:
            def __init__(self, *args, **kwargs):
                pass
            def exec(self): pass
            def setWindowTitle(self, *a, **k): pass
        class QVBoxLayout:
            def __init__(self, *a, **k): pass
            def addWidget(self, *a, **k): pass
        class QLabel:
            def __init__(self, *a, **k): pass
        class QPushButton:
            def __init__(self, *a, **k): pass

class MinimalNottorneyDialog(QDialog):
    """
    Minimal dialog to allow addon to import and present a tiny UI when invoked.

    The real single_dialog likely contains a lot more UI and logic; use this
    as a temporary replacement to remove merge markers and get Anki to load.
    """

    def __init__(self, parent=None, title: str = "Nottorney"):
        # QDialog-like initialization
        try:
            super().__init__(parent)
        except Exception:
            # In defensive fallback situations the super call might be no-op
            pass

        try:
            self.setWindowTitle(title)
        except Exception:
            pass

        # Build a very small layout if available
        try:
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Nottorney Add-on"))
            close_btn = QPushButton("Close")
            # connect clicked to close if method exists
            try:
                close_btn.clicked.connect(self._on_close_clicked)  # type: ignore[attr-defined]
            except Exception:
                # fallback: no signal available in this environment
                pass
            layout.addWidget(close_btn)
        except Exception:
            # If any of the Qt classes are missing, we still want the module to import.
            pass

    def _on_close_clicked(self):
        """Close the dialog when close button pressed."""
        try:
            self.close()
        except Exception:
            try:
                self.reject()
            except Exception:
                pass

    def show_modal(self):
        """Show the dialog modally (executes the dialog if supported)."""
        try:
            # PyQt6 / Qt API
            return self.exec()
        except Exception:
            # If exec isn't available, just return
            return None