"""Live cat face — tiny, cheap, expressive.

Drawn with cairo on a GTK DrawingArea. Two round eyes blink on a slow
cycle and "attention" when the panel is in a notice state (music,
lyrics, timer, notify). Stays visible even when the panel is collapsed,
so the user gets a small reactive hint at the tray boundary.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gtk, GLib
import cairo

BLINK_CYCLE = 4.2


class CatEyes(Gtk.DrawingArea):
    """Live eyes drawn with cairo."""

    __gtype_name__ = "CatEyes"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_draw_func(self._draw)
        self._notice = False
        self._blink_start = 0.0
        GLib.idle_add(self._schedule_blink, priority=GLib.PRIORITY_LOW_IDLE)

    def set_notice(self, value: bool) -> None:
        self._notice = bool(value)
        if value:
            self._blink_start = 0.0

    def is_notice(self) -> bool:
        return self._notice

    def _schedule_blink(self) -> bool:
        self._blink_start = GLib.get_monotonic_time() / 1e6
        interval = BLINK_CYCLE
        if self._notice:
            interval = 0.4 + self._notice * 0.6
        GLib.timeout_add(int(interval * 1000), self._tick)
        return False

    def _tick(self) -> bool:
        self.queue_draw()
        return False

    def _draw(self, cr: cairo.Context, width: float, height: float) -> None:
        cr.save()
        cx = width / 2.0
        cy = height / 2.0
        scale = 0.5 + 0.5 * self._zoom()
        cr.translate(cx, cy)
        cr.scale(scale, scale)
        self._draw_eyes(cr)
        cr.restore()

    def _zoom(self) -> float:
        return 1.0

    def _draw_eyes(self, cr: cairo.Context) -> None:
        gap = 18.0
        sep = 10.0
        for dx, dy in [(-gap, -gap), (gap, -gap)]:
            self._draw_eye(cr, dx, dy, gap, sep)

    def _draw_eye(self, cr: cairo.Context, dx: float, dy: float,
                   gap: float, sep: float) -> None:
        cr.save()
        cr.translate(dx, dy)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.08)
        cr.arc(0, 0, gap + 2, 0, 2 * 3.14159)
        cr.fill()
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        cr.arc(0, 0, gap, 0, 2 * 3.14159)
        cr.fill()
        if self._notice:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            cr.arc(0, -gap * 0.15, gap * 0.6, 0, 2 * 3.14159)
            cr.fill()
        cr.restore()


class CatFace(Gtk.Box):
    """Container holding the live eyes with a notice toggle helper."""

    __gtype_name__ = "CatFace"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(**kwargs)
        self.append(CatEyes())
        self._notice = False

    def set_notice(self, value: bool) -> None:
        self._notice = bool(value)
        for child in self.get_children():
            if isinstance(child, CatEyes):
                child.set_notice(value)

    def is_notice(self) -> bool:
        return self._notice
