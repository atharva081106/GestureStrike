"""
game/ai_behavior.py
State machine and movement logic for enemy drones.
States: SEEK, DODGE, AGGRESSIVE, STAGGER
"""

from __future__ import annotations
import math
import random
import pygame
from enum import Enum, auto
from config import (
    ENEMY_DODGE_THRESHOLD, ENEMY_DODGE_TRIGGER_TIME, ENEMY_DODGE_DURATION,
    ENEMY_STAGGER_DURATION, ENEMY_STAGGER_FACTOR,
)


class EnemyState(Enum):
    SEEK       = auto()
    DODGE      = auto()
    AGGRESSIVE = auto()
    STAGGER    = auto()


class AIBehavior:
    """
    Handles per-enemy state transitions and velocity computation.
    Plugged into Enemy; decoupled from rendering.
    """

    def __init__(self, base_speed: float, wave: int) -> None:
        self.base_speed = base_speed
        self.wave       = wave
        self.state      = EnemyState.SEEK

        # DODGE state
        self._cursor_close_timer: float = 0.0
        self._dodge_timer: float        = 0.0
        self._dodge_dir: pygame.Vector2 = pygame.Vector2(0, 0)

        # STAGGER state
        self._stagger_timer: float = 0.0

        # AGGRESSIVE zig-zag
        self._zz_timer:     float = 0.0
        self._zz_phase:     float = random.uniform(0, math.pi * 2)
        self._zz_frequency: float = random.uniform(2.0, 4.0)
        self._zz_amplitude: float = random.uniform(40, 80)

    # ── Public ──────────────────────────────────────────────────────────────────

    def update(self, dt: float,
               enemy_pos: pygame.Vector2,
               target_pos: pygame.Vector2,
               cursor_pos: pygame.Vector2) -> pygame.Vector2:
        """
        Returns the velocity vector for this frame.
        """
        self._zz_timer += dt

        # Transition into STAGGER if timer active
        if self._stagger_timer > 0:
            self._stagger_timer -= dt
            self.state = EnemyState.STAGGER
        elif self.state == EnemyState.STAGGER:
            self.state = EnemyState.SEEK

        # Check cursor proximity for DODGE
        dist_to_cursor = (cursor_pos - enemy_pos).length()
        if dist_to_cursor < ENEMY_DODGE_THRESHOLD:
            self._cursor_close_timer += dt
        else:
            self._cursor_close_timer = 0.0

        if (self.state in (EnemyState.SEEK, EnemyState.AGGRESSIVE)
                and self._cursor_close_timer >= ENEMY_DODGE_TRIGGER_TIME):
            self._start_dodge(enemy_pos, target_pos)

        # DODGE countdown
        if self.state == EnemyState.DODGE:
            self._dodge_timer -= dt
            if self._dodge_timer <= 0:
                self.state = EnemyState.SEEK if self.wave < 5 else EnemyState.AGGRESSIVE

        # Compute velocity based on state
        return self._compute_velocity(dt, enemy_pos, target_pos)

    def trigger_stagger(self) -> None:
        self._stagger_timer = ENEMY_STAGGER_DURATION

    # ── Internal ────────────────────────────────────────────────────────────────

    def _start_dodge(self, enemy_pos: pygame.Vector2,
                     target_pos: pygame.Vector2) -> None:
        to_target = (target_pos - enemy_pos)
        if to_target.length_squared() < 1e-6:
            perp = pygame.Vector2(1, 0)
        else:
            to_target = to_target.normalize()
            perp = pygame.Vector2(-to_target.y, to_target.x)
            if random.random() < 0.5:
                perp = -perp
        self._dodge_dir   = perp
        self._dodge_timer = ENEMY_DODGE_DURATION
        self.state        = EnemyState.DODGE
        self._cursor_close_timer = 0.0

    def _compute_velocity(self, dt: float,
                          enemy_pos: pygame.Vector2,
                          target_pos: pygame.Vector2) -> pygame.Vector2:
        speed = self.base_speed

        if self.state == EnemyState.STAGGER:
            speed *= ENEMY_STAGGER_FACTOR

        if self.state == EnemyState.DODGE:
            return self._dodge_dir * speed

        to_target = target_pos - enemy_pos
        if to_target.length_squared() < 1e-6:
            return pygame.Vector2(0, 0)
        direction = to_target.normalize()

        if self.state == EnemyState.AGGRESSIVE and self.wave >= 5:
            # Zig-zag: add sinusoidal perpendicular component
            perp   = pygame.Vector2(-direction.y, direction.x)
            zz_val = math.sin(self._zz_timer * self._zz_frequency + self._zz_phase)
            direction = (direction * speed + perp * zz_val * self._zz_amplitude)
            if direction.length_squared() > 0:
                direction = direction.normalize() * speed
            return direction

        return direction * speed
