"""
systems/particle_system.py
Lightweight particle system capped at MAX_PARTICLES.
Supports: bullet impact, explosion, shield hit effects.
Uses a flat array pool for cache efficiency.
"""

from __future__ import annotations
import math
import random
import pygame
import numpy as np
from typing import Tuple
from config import MAX_PARTICLES


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "r", "g", "b", "size", "active")

    def __init__(self) -> None:
        self.active = False

    def spawn(self, x: float, y: float,
              vx: float, vy: float,
              life: float,
              r: int, g: int, b: int,
              size: float) -> None:
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = self.max_life = life
        self.r = r; self.g = g; self.b = b
        self.size = size
        self.active = True

    def update(self, dt: float) -> None:
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.vy   += 60 * dt   # slight downward drift (gravity feel)
        self.life -= dt
        if self.life <= 0:
            self.active = False

    def draw(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        if not self.active:
            return
        alpha = self.life / self.max_life
        size  = max(1, int(self.size * alpha))
        col   = (int(self.r * alpha), int(self.g * alpha), int(self.b * alpha))
        cx    = int(self.x) + ox
        cy    = int(self.y) + oy
        pygame.draw.circle(surface, col, (cx, cy), size)


class ParticleSystem:
    """Fixed-size pool; new particles evict oldest if pool full."""

    def __init__(self, capacity: int = MAX_PARTICLES) -> None:
        self._pool    = [Particle() for _ in range(capacity)]
        self._capacity = capacity
        self._cursor  = 0

    # ── Emitters ────────────────────────────────────────────────────────────────

    def emit_bullet_impact(self, x: float, y: float) -> None:
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 200)
            self._spawn(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.2, 0.5),
                0, random.randint(180, 255), random.randint(200, 255),
                random.uniform(2, 4),
            )

    def emit_explosion(self, x: float, y: float) -> None:
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 350)
            self._spawn(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.4, 1.0),
                random.randint(200, 255), random.randint(60, 150), 0,
                random.uniform(3, 7),
            )

    def emit_shield_hit(self, x: float, y: float) -> None:
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 150)
            self._spawn(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.2, 0.6),
                60, 140, random.randint(220, 255),
                random.uniform(2, 5),
            )

    # ── Per-frame ───────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        for p in self._pool:
            if p.active:
                p.update(dt)

    def draw(self, surface: pygame.Surface, shake: Tuple[int, int]) -> None:
        ox, oy = shake
        for p in self._pool:
            if p.active:
                p.draw(surface, ox, oy)

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _spawn(self, x, y, vx, vy, life, r, g, b, size) -> None:
        self._pool[self._cursor].spawn(x, y, vx, vy, life, r, g, b, size)
        self._cursor = (self._cursor + 1) % self._capacity
