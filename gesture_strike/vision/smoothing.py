"""
vision/smoothing.py
Exponential smoothing for cursor position with dead-zone and boundary clamping.
"""

from __future__ import annotations
import numpy as np
from config import SMOOTHING_ALPHA, CURSOR_DEADZONE, SCREEN_WIDTH, SCREEN_HEIGHT


class CursorSmoother:
    """
    Maps normalised hand landmark coords → smoothed screen pixel coords.
    Applies:
      1. Exponential (EMA) smoothing
      2. Dead-zone suppression (prevents micro-jitter)
      3. Hard clamp to window bounds
    """

    def __init__(self,
                 alpha: float = SMOOTHING_ALPHA,
                 deadzone: float = CURSOR_DEADZONE,
                 width: int = SCREEN_WIDTH,
                 height: int = SCREEN_HEIGHT) -> None:
        self._alpha    = alpha
        self._deadzone = deadzone
        self._width    = width
        self._height   = height
        self._smooth   = np.array([width / 2.0, height / 2.0], dtype=float)

    # ── Public API ──────────────────────────────────────────────────────────────

    def update(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        """
        Feed a normalised [0,1] position from MediaPipe.
        Returns integer (x, y) screen coordinates.
        """
        # Map to screen space (note: MediaPipe x is already flipped by tracker)
        raw = np.array([norm_x * self._width, norm_y * self._height], dtype=float)

        # EMA smoothing
        new_smooth = self._alpha * raw + (1.0 - self._alpha) * self._smooth

        # Dead-zone: only update if movement exceeds threshold
        delta = np.linalg.norm(new_smooth - self._smooth)
        if delta > self._deadzone:
            self._smooth = new_smooth

        # Clamp
        x = int(np.clip(self._smooth[0], 0, self._width  - 1))
        y = int(np.clip(self._smooth[1], 0, self._height - 1))
        return x, y

    @property
    def position(self) -> tuple[int, int]:
        """Last computed smoothed position without running a new update."""
        return (int(self._smooth[0]), int(self._smooth[1]))

    def reset(self, x: float | None = None, y: float | None = None) -> None:
        """Hard-reset smoother to a given screen position (defaults to centre)."""
        if x is None:
            x = self._width  / 2.0
        if y is None:
            y = self._height / 2.0
        self._smooth = np.array([x, y], dtype=float)
