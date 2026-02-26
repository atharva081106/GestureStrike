"""
systems/analytics.py
Tracks in-game telemetry: shots, hits, reaction_times, survival_time, difficulty.
"""

from __future__ import annotations
import time
from typing import List


class Analytics:
    """
    Lightweight runtime analytics tracker.
    All data lives in memory; no disk I/O during gameplay.
    """

    def __init__(self) -> None:
        self.total_shots: int        = 0
        self.total_hits: int         = 0
        self.survival_time: float    = 0.0
        self.current_difficulty: int = 1
        self.reaction_times: List[float] = []

        self._last_enemy_appear: float | None = None
        self._session_start: float = time.monotonic()

    # ── Recording ────────────────────────────────────────────────────────────────

    def record_shot(self) -> None:
        self.total_shots += 1

    def record_hit(self) -> None:
        self.total_hits += 1

    def record_enemy_spawn(self) -> None:
        self._last_enemy_appear = time.monotonic()

    def record_damage(self, amount: float) -> None:
        pass   # damage is tracked by DifficultyController; Analytics just notes it

    def record_kill(self) -> None:
        if self._last_enemy_appear is not None:
            rt = time.monotonic() - self._last_enemy_appear
            self.reaction_times.append(rt)
            self._last_enemy_appear = None

    def update(self, dt: float, difficulty: int) -> None:
        self.survival_time += dt
        self.current_difficulty = difficulty

    # ── Derived ──────────────────────────────────────────────────────────────────

    @property
    def accuracy(self) -> float:
        if self.total_shots == 0:
            return 0.0
        return self.total_hits / self.total_shots

    @property
    def accuracy_pct(self) -> int:
        return int(self.accuracy * 100)

    @property
    def avg_reaction_ms(self) -> int:
        if not self.reaction_times:
            return 0
        return int((sum(self.reaction_times) / len(self.reaction_times)) * 1000)

    def summary(self) -> dict:
        return {
            "total_shots":      self.total_shots,
            "total_hits":       self.total_hits,
            "accuracy_pct":     self.accuracy_pct,
            "survival_time":    round(self.survival_time, 1),
            "avg_reaction_ms":  self.avg_reaction_ms,
            "difficulty":       self.current_difficulty,
        }