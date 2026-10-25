"""Pomodoro timer — fully local, interval-based.

No network and no external audio backend needed. Sessions:
focus 25 minutes, short break 5 minutes, long break 15 minutes,
looping indefinitely.
"""

from __future__ import annotations

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GObject, GLib


class Pomodoro(GObject.Object):
    __gtype_name__ = "Pomodoro"

    tick = GObject.signal_new("tick", GObject.TYPE_OBJECT, 0, GObject.TYPE_INT, ())
    completed = GObject.signal_new("completed", GObject.TYPE_OBJECT, 0, GObject.TYPE_NONE, ())

    FOCUS = 25 * 60
    SHORT_BREAK = 5 * 60
    LONG_BREAK = 15 * 60

    def __init__(self) -> None:
        super().__init__()
        self.session_time = self.FOCUS
        self.remaining = self.FOCUS
        self._running = False
        self._on = True

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._on = True
        self._tick()

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        self.remaining = self.session_time
        self._running = False

    def set_session(self, minutes: int) -> None:
        self.session_time = minutes * 60
        if self.remaining == self.session_time:
            self.remaining = self.session_time

    def _tick(self) -> bool:
        if not self._on:
            return False
        if self.remaining <= 0:
            self._running = False
            if self.session_time == self.FOCUS:
                self._next_session()
            self.completed.emit()
            return False
        self.remaining -= 1
        self.tick.emit(self.remaining)
        return True

    def _next_session(self) -> None:
        if self.session_time == self.FOCUS:
            self.session_time = self.SHORT_BREAK
            self.remaining = self.SHORT_BREAK
        elif self.session_time == self.SHORT_BREAK:
            self.session_time = self.LONG_BREAK
            self.remaining = self.LONG_BREAK
        else:
            self.session_time = self.FOCUS
            self.remaining = self.FOCUS

    @property
    def time_left(self) -> int:
        return self.remaining

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def mode(self) -> str:
        if self.session_time == self.FOCUS:
            return "focus"
        if self.session_time == self.SHORT_BREAK:
            return "break"
        return "long"
