"""
game/bullet.py
Bullet objects with object pooling for performance.
Each bullet is a cyan neon streak with velocity physics.
"""

from __future__ import annotations
import math
import random
import pygame
from typing import List, Tuple
from config import (
    BULLET_SPEED, BULLET_LIFETIME, BULLET_RADIUS,
    BULLET_SPREAD, COL_BULLET,
)


class Bullet:
    """Single poolable bullet instance."""

    __slots__ = ("pos", "vel", "age", "active", "tail", "radius")

    def __init__(self) -> None:
        self.pos: pygame.Vector2    = pygame.Vector2()
        self.vel: pygame.Vector2    = pygame.Vector2()
        self.age: float             = 0.0
        self.active: bool           = False
        self.radius: int            = BULLET_RADIUS
        self.tail: List[Tuple[float, float]] = []   # trail history

    def spawn(self, origin: pygame.Vector2, target: pygame.Vector2) -> None:
        direction = target - origin
        if direction.length_squared() < 1e-6:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        # Apply spread
        spread_rad = math.radians(random.uniform(-BULLET_SPREAD, BULLET_SPREAD))
        cos_s, sin_s = math.cos(spread_rad), math.sin(spread_rad)
        dx = direction.x * cos_s - direction.y * sin_s
        dy = direction.x * sin_s + direction.y * cos_s

        self.pos   = pygame.Vector2(origin)
        self.vel   = pygame.Vector2(dx * BULLET_SPEED, dy * BULLET_SPEED)
        self.age   = 0.0
        self.active = True
        self.tail.clear()

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.tail.append((self.pos.x, self.pos.y))
        if len(self.tail) > 6:
            self.tail.pop(0)
        self.pos += self.vel * dt
        self.age += dt
        if self.age >= BULLET_LIFETIME:
            self.active = False

    def draw(self, surface: pygame.Surface, shake: Tuple[int, int]) -> None:
        if not self.active:
            return
        ox, oy = shake
        sx = int(self.pos.x) + ox
        sy = int(self.pos.y) + oy

        # Draw neon trail
        for i, (tx, ty) in enumerate(self.tail):
            alpha_ratio = (i + 1) / len(self.tail)
            r = max(1, int(BULLET_RADIUS * alpha_ratio))
            col = (
                int(COL_BULLET[0] * alpha_ratio),
                int(COL_BULLET[1] * alpha_ratio),
                int(COL_BULLET[2] * alpha_ratio),
            )
            pygame.draw.circle(surface, col, (int(tx) + ox, int(ty) + oy), r)

        # Main bullet dot
        pygame.draw.circle(surface, COL_BULLET, (sx, sy), BULLET_RADIUS)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(1, BULLET_RADIUS - 2))


class BulletPool:
    """
    Fixed-size pool of Bullet objects.
    Avoids per-frame allocation.
    """

    def __init__(self, pool_size: int = 60) -> None:
        self._pool: List[Bullet] = [Bullet() for _ in range(pool_size)]

    def fire(self, origin: pygame.Vector2, target: pygame.Vector2) -> bool:
        """Returns True if a bullet was successfully fired from the pool."""
        for b in self._pool:
            if not b.active:
                b.spawn(origin, target)
                return True
        return False   # pool exhausted

    def update(self, dt: float) -> None:
        for b in self._pool:
            if b.active:
                b.update(dt)

    def draw(self, surface: pygame.Surface, shake: Tuple[int, int]) -> None:
        for b in self._pool:
            if b.active:
                b.draw(surface, shake)

    @property
    def active_bullets(self) -> List[Bullet]:
        return [b for b in self._pool if b.active]

    def clear(self) -> None:
        for b in self._pool:
            b.active = False