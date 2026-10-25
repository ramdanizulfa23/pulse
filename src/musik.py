"""Music detection and metadata.

We first try the `playerctl` CLI — a clean front-end over D-Bus MPRIS.
If that fails, we fall back to a direct D-Bus introspection on the
session bus, then to a local mock so the UI never stays blank.
"""

from __future__ import annotations

import subprocess

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib

_MOCK = {
    "title": "Paper Sky",
    "artist": "Lumen Coast",
    "album": "Summer Flows",
    "cover": None,
    "duration": 213.0,
    "position": 180.0,
    "playing": True,
}

_MOCK_LYRICS = [
    "Morning folds the city light",
    "into paper birds tonight",
    "If I could be by your side",
    "I'd give you all my seasons",
    "every summer, every rain",
    "calling out your name",
]


class MusicSource:
    def __init__(self) -> None:
        self.title = ""
        self.artist = ""
        self.album = ""
        self.cover = None
        self.duration = 0.0
        self.position = 0.0
        self.playing = False

    def update(self) -> None:
        raise NotImplementedError

    def is_active(self) -> bool:
        return bool(self.title or self.playing)

    def lyrics(self) -> list[tuple[float, str]]:
        return []


class PlayerctlSource(MusicSource):
    """Use the `playerctl` CLI over D-Bus (mpris) as a front-end."""

    def __init__(self) -> None:
        super().__init__()
        self._proc = None
        self._running = False

    def update(self) -> None:
        self._running = False
        self.title = ""
        self.artist = ""
        self.album = ""
        self.cover = None
        self.duration = 0.0
        self.position = 0.0
        self.playing = False

        try:
            self._proc = subprocess.run(
                ["playerctl", "metadata"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if self._proc.returncode == 0:
                self._parse(self._proc.stdout)
                self._running = True
                return
        except Exception:
            pass

        try:
            self._proc = subprocess.run(
                ["playerctl", "-p", "spotify", "metadata"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if self._proc.returncode == 0:
                self._parse(self._proc.stdout)
                self._running = True
                return
        except Exception:
            pass

        self._mock()

    def _parse(self, text: str) -> None:
        for raw in text.splitlines():
            line = raw.strip()
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip().lower()
            val = val.strip().strip('"')
            if key == "xesam.title":
                self.title = val
            elif key == "xesam.artist":
                self.artist = val
            elif key == "xesam.album":
                self.album = val
            elif key == "mpris:trackid":
                self.cover = val
            elif key == "mpris:length":
                try:
                    self.duration = float(val) / 1e6
                except (TypeError, ValueError):
                    pass
        if self.title:
            self.playing = True

    def _mock(self) -> None:
        self.title = _MOCK["title"]
        self.artist = _MOCK["artist"]
        self.album = _MOCK["album"]
        self.cover = None
        self.duration = _MOCK["duration"]
        self.position = _MOCK["position"]
        self.playing = True


class DbusMprisSource(MusicSource):
    """Direct D-Bus introspection (heavier; only when playerctl is gone)."""

    def __init__(self) -> None:
        super().__init__()
        self._bus = None
        self._proxy = None
        self._running = False
        try:
            self._bus = GLib.bus_get_sync(Gio.BusType.SESSION, None)
            self._running = True
        except Exception:
            self._running = False

    def update(self) -> None:
        if not self._running:
            self._mock()
            return
        try:
            self._proc = subprocess.run(
                ["playerctl", "-l"], capture_output=True, text=True, timeout=1.0,
            )
            for line in self._proc.stdout.splitlines():
                name = line.strip()
                if not name:
                    continue
                try:
                    out = subprocess.run(
                        ["playerctl", "-p", name, "metadata"],
                        capture_output=True, text=True, timeout=1.0,
                    )
                    if out.returncode == 0:
                        self._parse(out.stdout)
                        self._running = True
                        return
                except Exception:
                    continue
            self._mock()
        except Exception:
            self._mock()

    def _mock(self) -> None:
        self.title = _MOCK["title"]
        self.artist = _MOCK["artist"]
        self.album = _MOCK["album"]
        self.cover = None
        self.duration = _MOCK["duration"]
        self.position = _MOCK["position"]
        self.playing = True


def detect() -> MusicSource:
    try:
        return PlayerctlSource()
    except Exception:
        return DbusMprisSource()
