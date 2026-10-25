"""Volume control via PulseAudio/PipeWire (fallback to mock)."""

from __future__ import annotations

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gio, GLib

_MOCK = {"volume": 85.0, "muted": False}


class VolumeSource:
    def __init__(self) -> None:
        self.volume = 85.0
        self.muted = False

    def update(self) -> None:
        raise NotImplementedError

    def set_volume(self, value: float) -> None:
        self.volume = max(0.0, min(100.0, float(value)))

    def mute(self, mute: bool) -> None:
        self.muted = mute

    @property
    def percent(self) -> int:
        return int(round(self.volume))


class PulseAudioSource(VolumeSource):
    def __init__(self) -> None:
        super().__init__()
        self._bus = None
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except Exception:
            pass

    def update(self) -> None:
        if self._bus is None:
            self._load_mock()
            return
        try:
            proxy = Gio.DBusProxy.new_for_bus_sync(
                self._bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.PulseAudio1",
                "/org/freedesktop/PulseAudio1",
                "org.freedesktop.PulseAudio1",
                None,
            )
            volume = proxy.get_cached_property("SinkInputVolume")
            if volume:
                self.volume = float(volume) / 65536.0 * 100.0
            else:
                self._load_mock()
        except Exception:
            self._load_mock()

    def _load_mock(self) -> None:
        self.volume = _MOCK["volume"]
        self.muted = _MOCK["muted"]


class MockVolumeSource(VolumeSource):
    def __init__(self) -> None:
        super().__init__()
        self.volume = _MOCK["volume"]
        self.muted = _MOCK["muted"]
