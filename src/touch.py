"""Panel positioning and hover handling."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Gdk, GLib

_HOVER_TIMEOUT = 140  # ms before we expand


class TouchHandler:
    """Track mouse enter/leave on the panel, expand on hover."""

    def __init__(self, panel) -> None:
        self.panel = panel
        self._hover = False
        self._hover_timeout = None
        self._window = panel.get_root()
        if self._window is not None:
            self._enter_cb = self._window.connect(
                "enter-notify-event", self._on_enter
            )
            self._leave_cb = self._window.connect(
                "leave-notify-event", self._on_leave
            )

    def _on_enter(self, *args):
        self._hover = True
        if self._hover_timeout is not None:
            GLib.source_remove(self._hover_timeout)
            self._hover_timeout = None
        self._expand()

    def _on_leave(self, *args):
        self._hover = False
        if self._hover_timeout is not None:
            GLib.source_remove(self._hover_timeout)
            self._hover_timeout = None
        self._collapse()

    def _expand(self):
        self._hover_timeout = GLib.timeout_add(_HOVER_TIMEOUT, self._do_expand)

    def _collapse(self):
        if self._hover_timeout is not None:
            GLib.source_remove(self._hover_timeout)
            self._hover_timeout = None
        self.panel.collapse_on_leave()

    def _do_expand(self):
        self.panel.expand_on_hover()
        return False

    def detach(self):
        if self._window is not None:
            self._window.disconnect(self._enter_cb)
            self._window.disconnect(self._leave_cb)

def init(app) -> None:
    """Dispatch touch handling to the panel if present."""
    if app.window is not None:
        from app import PulsePanel
        if isinstance(app.window, PulsePanel):
            TouchHandler(app.window)
