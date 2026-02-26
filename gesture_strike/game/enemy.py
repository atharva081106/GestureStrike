"""
game/enemy.py
Enemy drone: red glowing drone that seeks the central core.
Wraps AIBehavior state machine.
Every 2-3 waves enemies get visually distinct and harder:
  Wave 1-2:  Basic red drones (slow, 1 HP after one-shot always dies)
  Wave 3-5:  Orange armoured drones (faster, bigger)
  Wave 6-8:  Purple elite drones (much faster, erratic movement)
  Wave 9+:   Boss drones (large, very fast, aggressive zigzag)
"""

from __future__ import annotations
import math
import random
import pygame
from typing import Tuple
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    ENEMY_RADIUS, ENEMY_BASE_SPEED, ENEMY_BASE_HEALTH,
    COL_ENEMY, COL_ENEMY_GLOW,
)
from game.ai_behavior import AIBehavior, EnemyState


# ── Wave tier definitions ──────────────────────────────────────────────────────

def _tier(wave: int) -> int:
    """Return enemy tier 1-4 based on wave number."""
    if wave <= 2:  return 1
    if wave <= 5:  return 2
    if wave <= 8:  return 3
    return 4


_TIER_PROPS = {
    # tier: (color_body, color_glow, radius_mult, speed_mult, label)
    1: ((210,  50,  50), (255, 100,  30), 1.0, 1.0,  "DRONE"),
    2: ((220, 120,  20), (255, 180,  40), 1.2, 1.3,  "ARMOURED"),
    3: ((160,  40, 220), (200,  80, 255), 1.1, 1.65, "ELITE"),
    4: ((255,  20,  80), (255,  80, 120), 1.5, 2.1,  "BOSS"),
}


class Enemy:
    """Single enemy drone."""

    def __init__(self, wave: int, speed_mult: float, health_mult: float) -> None:
        self.wave   = wave
        self.tier   = _tier(wave)
        props       = _TIER_PROPS[self.tier]

        self._col_body = props[0]
        self._col_glow = props[1]
        radius_m       = props[2]
        tier_speed_m   = props[3]

        self.pos    = self._random_edge_spawn()
        self.radius = int(ENEMY_RADIUS * radius_m)
        self.alive  = True

        speed  = ENEMY_BASE_SPEED * speed_mult * tier_speed_m
        health = 1   # always one-shot kill regardless of tier

        self.health: int     = health
        self.max_health: int = health

        self.ai = AIBehavior(base_speed=speed, wave=wave)

        self._pulse_phase = random.uniform(0, math.pi * 2)
        self._glow_surf   = self._build_glow_surf(self._col_glow)

    # ── Public API ──────────────────────────────────────────────────────────────

    def update(self, dt: float,
               target_pos: pygame.Vector2,
               cursor_pos: pygame.Vector2) -> None:
        if not self.alive:
            return
        self._pulse_phase += dt * 3.0
        vel = self.ai.update(dt, self.pos, target_pos, cursor_pos)
        self.pos += vel * dt

    def hit(self, damage: int = 1) -> bool:
        """Apply damage. Returns True if killed."""
        self.health -= damage
        self.ai.trigger_stagger()
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface, shake: Tuple[int, int]) -> None:
        if not self.alive:
            return
        ox, oy = shake
        cx = int(self.pos.x) + ox
        cy = int(self.pos.y) + oy

        # Pulsing glow
        alpha = int(120 + 80 * math.sin(self._pulse_phase))
        glow  = self._glow_surf.copy()
        glow.set_alpha(alpha)
        gr = glow.get_rect(center=(cx, cy))
        surface.blit(glow, gr, special_flags=pygame.BLEND_ADD)

        # Body
        pygame.draw.circle(surface, self._col_body, (cx, cy), self.radius)

        # Tier-specific inner ring colour
        ring_col = tuple(min(255, c + 80) for c in self._col_body)
        pygame.draw.circle(surface, ring_col, (cx, cy), self.radius - 4, 2)

        # Boss: extra outer ring
        if self.tier == 4:
            pygame.draw.circle(surface, self._col_glow, (cx, cy), self.radius + 4, 2)

    # ── Internal ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _random_edge_spawn() -> pygame.Vector2:
        margin = 40
        side = random.randint(0, 3)
        if side == 0:
            return pygame.Vector2(random.randint(0, SCREEN_WIDTH), -margin)
        elif side == 1:
            return pygame.Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + margin)
        elif side == 2:
            return pygame.Vector2(-margin, random.randint(0, SCREEN_HEIGHT))
        else:
            return pygame.Vector2(SCREEN_WIDTH + margin, random.randint(0, SCREEN_HEIGHT))

    @staticmethod
    def _build_glow_surf(col) -> pygame.Surface:
        size = ENEMY_RADIUS * 5
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for r in range(cx, 0, -3):
            a = int(50 * (1 - r / cx))
            pygame.draw.circle(surf, (*col, a), (cx, cy), r)
        return surf


class EnemyManager:
    """Manages spawning, updating, drawing enemies and wave progression."""

    def __init__(self) -> None:
        self.enemies: list[Enemy] = []
        self._spawn_timer: float  = 0.0
        self._next_spawn: float   = random.uniform(2.0, 3.0)
        self.wave: int            = 1
        self.enemies_killed: int  = 0
        self._kills_this_wave: int = 0
        self._kills_to_advance: int = 6   # kills needed to go to next wave

    def update(self, dt: float,
               target_pos: pygame.Vector2,
               cursor_pos: pygame.Vector2,
               spawn_interval: float,
               speed_mult: float,
               health_mult: float) -> None:

        # Spawn with randomised 2-3 second intervals (difficulty-scaled)
        self._spawn_timer += dt
        if self._spawn_timer >= self._next_spawn:
            self._spawn_timer = 0.0
            self._next_spawn  = random.uniform(spawn_interval,
                                               spawn_interval + 1.0)
            self.enemies.append(Enemy(self.wave, speed_mult, health_mult))

        for e in self.enemies:
            e.update(dt, target_pos, cursor_pos)

        self.enemies = [e for e in self.enemies if e.alive]

    def register_kill(self) -> None:
        self.enemies_killed  += 1
        self._kills_this_wave += 1
        if self._kills_this_wave >= self._kills_to_advance:
            self.wave              += 1
            self._kills_this_wave   = 0
            # Waves get longer to complete as difficulty climbs
            self._kills_to_advance  = int(self._kills_to_advance * 1.25)

    def draw(self, surface: pygame.Surface, shake: Tuple[int, int]) -> None:
        for e in self.enemies:
            e.draw(surface, shake)

    def clear(self) -> None:
        self.enemies.clear()