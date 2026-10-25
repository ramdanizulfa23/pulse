"""System-tray integration for Pulse on GNOME (Wayland).

GNOME's shell does not expose a native tray icon API on Wayland, so we
register a StatusNotifierItem over the session D-Bus. The wrapper is a
lightweight GTK widget that toggles the floating panel when clicked and
offers a small context menu for quick actions.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gio", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GObject, GLib


class TrayIcon(Gtk.EventBox):
    """Clickable tray wrapper that toggles the floating panel."""

    __gtype_name__ = "TrayIcon"

    # No custom signal needed; we use a plain property toggle.

    def __init__(self, app) -> None:
        super().__init__()
        self.set_property("visible", True)
        self.set_tooltip_text("Pulse — living notch")
        self._app = app
        self.connect("button-release-event", self._on_click)
        self.connect("enter-notify-event", lambda *a: self.set_tooltip_text("Pulse"))
        self.connect("leave-notify-event", lambda *a: self.set_tooltip_text("Pulse — living notch"))

    def _on_click(self, *args):
        self._app.toggle_panel()
        return True

    def set_toggled(self, value: bool) -> None:
        self.emit("toggled", bool(value))


class TrayMenu(Gtk.PopoverMenu):
    """Small context menu exposed from the tray indicator."""

    __gtype_name__ = "TrayMenu"

    def __init__(self, app) -> None:
        super().__init__()
        self._app = app
        self.set_property("vexpand", False)
        self.set_property("halign", Gtk.Align.END)
        self.set_property("max_width", 260)

        model = Gio.Menu()
        model.append("Open panel", "app.show-panel")
        model.append("Hide", "app.hide-panel")
        model.append("Quit", "app.quit")
        self.set_model(model)
        self.connect("activate", self._on_activate)

    def _on_activate(self, widget, action):
        key = widget.get_ancestor(Gtk.MenuItem).get_attribute("action")
        handler = {
            "app.quit": self._app.quit,
            "app.hide-panel": self._app.hide_panel,
            "app.show-panel": self._app.toggle_panel,
        }.get(key)
        if handler is not None:
            handler()


def attach(app) -> None:
    tray = TrayIcon(app)
    tray.connect("toggled", lambda *a: app.toggle_panel())
    app.add_tray(tray)
    GLib.idle_add(app.show_panel, priority=GLib.PRIORITY_LOW_IDLE)
