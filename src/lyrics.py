"""LRC lyrics parser with line highlighting."""

from __future__ import annotations

import re


class Lrc:
    """Parse LRC lines and remember the current highlight line."""

    def __init__(self, lines: list[str]) -> None:
        self._raw = list(lines)
        self._parsed: list[tuple[float, str]] = []
        self.cur = 0
        self._parse()

    def _parse(self) -> None:
        for raw in self._raw:
            m = re.match(
                r"^\[(\d+):(\d+)(?:\.(\d+))?\]\s*(.*)$", raw.strip()
            )
            if not m:
                continue
            mins, secs, frac, text = m.groups()
            try:
                total = int(mins) * 60 + int(secs) + (float(frac) if frac else 0.0)
            except ValueError:
                continue
            if text.strip():
                self._parsed.append((total, text.strip()))
        self._parsed.sort(key=lambda item: item[0])

    def current_line(self, pos: float) -> int:
        best = -1
        for idx, (t, _) in enumerate(self._parsed):
            if t <= pos:
                best = idx
            else:
                break
        return best if best >= 0 else 0

    def next_line(self, pos: float) -> int:
        idx = self.current_line(pos)
        return (idx + 1) % len(self._parsed) if self._parsed else 0

    def lyrics(self) -> list[tuple[float, str]]:
        return self._parsed


def from_file(path: str) -> Lrc:
    try:
        with open(path, encoding="utf-8") as fh:
            return Lrc(fh.read().splitlines())
    except Exception:
        return Lrc(["[00:00] Loading lyrics…"])
