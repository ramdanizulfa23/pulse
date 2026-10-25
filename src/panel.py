"""Pulse panel: floating overlay with live music, lyrics, pomodoro, volume."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gio", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GObject, GLib, Adw

from face import CatFace
import config


def _fmt(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class PulsePanel(Gtk.ApplicationWindow):
    """Floating overlay: cat face, clock, music, lyrics, pomodoro, volume."""

    __gtype_name__ = "PulsePanel"

    SIZE_COLLAPSE = (200, 70)
    SIZE_EXPAND = (260, 180)

    def __init__(self, app) -> None:
        super().__init__(title="Pulse")
        self.set_application(app)
        self._app = app
        self._hover = False
        self._cat = None
        self._clock = None
        self._mood = None
        self._stack = None
        self._music_title = None
        self._music_artist = None
        self._music_prog = None
        self._music_pos = None
        self._music_dur = None
        self._lyr_label = None
        self._pomo_mode = None
        self._pomo_time = None
        self._vol_label = None
        self._vol_slider = None

        self.set_resizable(False)

        root = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        root.set_hexpand(True)
        root.set_valign(Gtk.Align.START)
        root.set_margin_top(8)
        root.set_margin_start(10)
        root.set_margin_end(10)
        root.set_margin_bottom(8)

        # Background for the window
        bg = Gtk.CssProvider()
        bg.load_from_data(b"window { background-color: rgba(0,0,0,0.60); border-radius: 14px; padding: 10px; box-shadow: 0 6px 24px rgba(0,0,0,0.6); }")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), bg, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.add(root)

        # Header: cat face + clock
        hdr = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        hdr.set_hexpand(True)
        hdr.set_valign(Gtk.Align.CENTER)

        cat = CatFace()
        self._cat = cat
        hdr.append(cat)

        clock = Gtk.Label(label="00:00")
        clock.add_css_class("dim")
        self._clock = clock
        hdr.append(clock)

        mood = Gtk.Label(label="idle")
        mood.add_css_class("dim")
        self._mood = mood
        hdr.append(mood)

        root.append(hdr)

        # Feature stack
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(160)
        self._stack.set_vexpand(True)
        root.append(self._stack)

        self._build_pages()

        # Hover wiring
        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)

        # Timers
        GLib.timeout_add(1000, self._timeout_clock)
        GLib.timeout_add(2000, self._timeout_music)

    def _build_pages(self):
        # Idle
        idle = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        idle.set_valign(Gtk.Align.CENTER)
        lbl = Gtk.Label(label="Hover to open")
        lbl.add_css_class("dim")
        idle.append(lbl)
        self._stack.add_toggle_child(idle, name="idle")

        # Music
        music = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        music.set_valign(Gtk.Align.CENTER)
        self._music_title = Gtk.Label(label="—")
        self._music_title.set_halign(Gtk.Align.CENTER)
        self._music_title.add_css_class("bold")
        music.append(self._music_title)
        self._music_artist = Gtk.Label(label="—")
        self._music_artist.set_halign(Gtk.Align.CENTER)
        self._music_artist.add_css_class("dim")
        music.append(self._music_artist)

        prog = Gtk.LevelBar()
        prog.set_min_value(0)
        prog.set_max_value(100)
        prog.set_hexpand(True)
        self._music_prog = prog
        music.append(prog)

        pos_row = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        pos_row.set_halign(Gtk.Align.CENTER)
        self._music_pos = Gtk.Label(label="0:00")
        self._music_pos.add_css_class("dim")
        self._music_dur = Gtk.Label(label="0:00")
        self._music_dur.add_css_class("dim")
        pos_row.append(self._music_pos)
        pos_row.append(self._music_dur)
        music.append(pos_row)
        self._stack.add_toggle_child(music, name="music")

        # Lyrics
        lyrics = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        lyrics.set_valign(Gtk.Align.CENTER)
        self._lyr_label = Gtk.Label(label="—")
        self._lyr_label.set_halign(Gtk.Align.CENTER)
        self._lyr_label.set_xalign(0.5)
        self._lyr_label.add_css_class("bold")
        self._lyr_label.set_wrap(True)
        self._lyr_label.set_max_width_chars(44)
        lyrics.append(self._lyr_label)
        self._stack.add_toggle_child(lyrics, name="lyrics")

        # Pomodoro
        pomo = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        pomo.set_valign(Gtk.Align.CENTER)
        pomo.set_halign(Gtk.Align.CENTER)
        self._pomo_mode = Gtk.Label(label="Focus")
        self._pomo_mode.add_css_class("dim")
        pomo.append(self._pomo_mode)
        self._pomo_time = Gtk.Label(label="25:00")
        self._pomo_time.add_css_class("big")
        pomo.append(self._pomo_time)
        btn_row = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        btn_row.set_halign(Gtk.Align.CENTER)
        for label, name in [("Start", "start"), ("Pause", "pause"), ("Reset", "reset")]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self._on_pomo_click, name)
            btn_row.append(btn)
        pomo.append(btn_row)
        self._stack.add_toggle_child(pomo, name="pomo")

        # Volume
        vol = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        vol.set_valign(Gtk.Align.CENTER)
        vol.set_halign(Gtk.Align.CENTER)
        self._vol_label = Gtk.Label(label="85%")
        self._vol_label.add_css_class("big")
        vol.append(self._vol_label)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_value(85)
        scale.set_hexpand(True)
        scale.set_size_request(180, -1)
        self._vol_slider = scale
        scale.connect("value-changed", self._on_vol_changed)
        vol.append(scale)
        self._stack.add_toggle_child(vol, name="volume")

    # ---- clock ----
    def _timeout_clock(self) -> bool:
        now = GLib.DateTime.new_now_local()
        self._clock.set_label(now.format("%H:%M"))
        return True

    # ---- music ----
    def _timeout_music(self) -> bool:
        music = self._app.current_music
        if music.is_active():
            music.update()
            self._music_title.set_label(music.title)
            self._music_artist.set_label(music.artist)
            dur = max(music.duration, 1.0)
            self._music_prog.set_max_value(dur)
            self._music_prog.set_value(music.position)
            self._music_pos.set_label(_fmt(music.position))
            self._music_dur.set_label(_fmt(dur))
            self._stack.set_visible_child_name("music")
            self._cat.set_notice(True)
        else:
            self._cat.set_notice(False)
            self._stack.set_visible_child_name("idle")
        return True

    # ---- pomodoro ----
    def _on_pomo_click(self, btn, name):
        p = self._app.pomodoro
        if name == "start":
            p.start()
        elif name == "pause":
            p.stop()
        else:
            p.reset()
        self._refresh_pomo()

    def _on_vol_changed(self, scale):
        v = int(scale.get_value())
        self._vol_label.set_label(f"{v}%")
        if self._app.volume:
            self._app.volume.set_volume(v)

    def _refresh_pomo(self):
        p = self._app.pomodoro
        self._pomo_time.set_label(_fmt(p.time_left))
        self._pomo_mode.set_label(p.mode.capitalize())

    # ---- hover ----
    def _on_enter(self, *args):
        self._hover = True
        self._expand()

    def _on_leave(self, *args):
        self._hover = False
        self._collapse()

    def _expand(self):
        self.set_size_request(*self.SIZE_EXPAND)

    def _collapse(self):
        self.set_size_request(*self.SIZE_COLLAPSE)

    def expand_on_hover(self):
        self._expand()

    def collapse_on_leave(self):
        self._collapse()

    def set_status(self, text: str) -> None:
        self._clock.set_label(text)

    def present(self) -> None:
        self.present()

    def show_all(self) -> None:
        self.show_all()
