"""
systems/difficulty_controller.py
Adaptive difficulty: evaluates performance every 10 seconds and adjusts
enemy speed, spawn rate, and enemy health.
"""

from __future__ import annotations
from config import (
    DIFFICULTY_MIN, DIFFICULTY_MAX, DIFFICULTY_EVAL_INTERVAL,
    ENEMY_SPAWN_INTERVAL,
)


class DifficultyController:
    """
    Evaluates player performance (accuracy + damage_taken) every
    DIFFICULTY_EVAL_INTERVAL seconds and adjusts difficulty level 1–10.
    Exposes multipliers used by EnemyManager.
    """

    def __init__(self) -> None:
        self.level: int          = 1
        self._eval_timer: float  = 0.0

        # Metrics window (reset each eval period)
        self._shots_window: int        = 0
        self._hits_window: int         = 0
        self._damage_window: float     = 0.0

    # ── Public API ──────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._eval_timer += dt
        if self._eval_timer >= DIFFICULTY_EVAL_INTERVAL:
            self._eval_timer -= DIFFICULTY_EVAL_INTERVAL
            self._evaluate()

    def record_shot(self) -> None:
        self._shots_window += 1

    def record_hit(self) -> None:
        self._hits_window += 1

    def record_damage(self, amount: float) -> None:
        self._damage_window += amount

    # ── Derived multipliers ──────────────────────────────────────────────────────

    @property
    def speed_multiplier(self) -> float:
        return 1.0 + (self.level - 1) * 0.12

    @property
    def health_multiplier(self) -> float:
        return 1.0 + (self.level - 1) * 0.15

    @property
    def spawn_interval(self) -> float:
        base = ENEMY_SPAWN_INTERVAL
        reduction = (self.level - 1) * 0.12
        return max(0.5, base - reduction)

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _evaluate(self) -> None:
        if self._shots_window > 0:
            accuracy = self._hits_window / self._shots_window
        else:
            accuracy = 0.5   # assume neutral if no shots

        damage = self._damage_window

        if accuracy > 0.70 and damage < 10:
            self.level = min(self.level + 1, DIFFICULTY_MAX)
        elif accuracy < 0.40:
            # Slightly reduce spawn pressure (clamp at level 1)
            self.level = max(self.level - 1, DIFFICULTY_MIN)

        # Reset window
        self._shots_window  = 0
        self._hits_window   = 0
        self._damage_window = 0.0
