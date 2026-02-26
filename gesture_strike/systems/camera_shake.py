"""
systems/camera_shake.py
Decaying sine-wave camera shake effect.
Provides an (offset_x, offset_y) tuple that gets added to all draw calls.
"""

from __future__ import annotations
import math
import random
from typing import Tuple
from config import (
    SHAKE_SMALL_AMPLITUDE, SHAKE_SMALL_DURATION,
    SHAKE_BIG_AMPLITUDE,   SHAKE_BIG_DURATION,
)


class CameraShake:
    """
    Accumulates shake requests (amplitude + duration).
    Returns a pixel offset via .offset each frame.
    Multiple concurrent shakes blend together.
    """

    def __init__(self) -> None:
        self._shakes: list[dict] = []

    # ── Public API ──────────────────────────────────────────────────────────────

    def small_shake(self) -> None:
        self._add(SHAKE_SMALL_AMPLITUDE, SHAKE_SMALL_DURATION)

    def big_shake(self) -> None:
        self._add(SHAKE_BIG_AMPLITUDE, SHAKE_BIG_DURATION)

    def update(self, dt: float) -> None:
        for s in self._shakes:
            s["elapsed"] += dt
        self._shakes = [s for s in self._shakes if s["elapsed"] < s["duration"]]

    @property
    def offset(self) -> Tuple[int, int]:
        if not self._shakes:
            return (0, 0)
        ox = oy = 0.0
        for s in self._shakes:
            t         = s["elapsed"] / s["duration"]
            decay     = (1.0 - t) ** 2
            freq      = s["freq"]
            amp       = s["amplitude"] * decay
            phase_x   = s["phase_x"]
            phase_y   = s["phase_y"]
            ox += amp * math.sin(s["elapsed"] * freq + phase_x)
            oy += amp * math.sin(s["elapsed"] * freq * 1.3 + phase_y)
        return (int(ox), int(oy))

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _add(self, amplitude: float, duration: float) -> None:
        self._shakes.append({
            "amplitude": amplitude,
            "duration":  duration,
            "elapsed":   0.0,
            "freq":      random.uniform(30, 50),
            "phase_x":   random.uniform(0, math.pi * 2),
            "phase_y":   random.uniform(0, math.pi * 2),
        })
