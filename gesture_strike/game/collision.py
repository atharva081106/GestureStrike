"""
game/collision.py
Circle-based collision detection for bullets↔enemies and enemies↔player.
Returns lists of collision events to be processed by the game loop.
"""

from __future__ import annotations
import math
import pygame
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from game.bullet import Bullet
    from game.enemy  import Enemy


@dataclass(slots=True)
class BulletHitEvent:
    bullet: "Bullet"
    enemy:  "Enemy"
    point:  pygame.Vector2


@dataclass(slots=True)
class PlayerHitEvent:
    enemy:  "Enemy"


def check_bullet_enemy_collisions(
        bullets: List["Bullet"],
        enemies: List["Enemy"]) -> List[BulletHitEvent]:
    """
    O(B × E) — acceptable for B < 60, E < 40.
    Each bullet can only hit one enemy per frame (first hit wins).
    """
    events: List[BulletHitEvent] = []
    for bullet in bullets:
        if not bullet.active:
            continue
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx  = bullet.pos.x - enemy.pos.x
            dy  = bullet.pos.y - enemy.pos.y
            dist_sq = dx * dx + dy * dy
            radius_sum = bullet.radius + enemy.radius  # type: ignore[attr-defined]
            if dist_sq < radius_sum * radius_sum:
                hit_point = pygame.Vector2(
                    (bullet.pos.x + enemy.pos.x) / 2,
                    (bullet.pos.y + enemy.pos.y) / 2,
                )
                events.append(BulletHitEvent(bullet, enemy, hit_point))
                bullet.active = False
                break   # bullet consumed

    return events


def check_enemy_player_collisions(
        enemies: List["Enemy"],
        player_pos: pygame.Vector2,
        player_radius: float) -> List[PlayerHitEvent]:
    """
    Check if any live enemy has reached the central core.
    """
    events: List[PlayerHitEvent] = []
    for enemy in enemies:
        if not enemy.alive:
            continue
        dx = enemy.pos.x - player_pos.x
        dy = enemy.pos.y - player_pos.y
        dist_sq    = dx * dx + dy * dy
        radius_sum = enemy.radius + player_radius
        if dist_sq < radius_sum * radius_sum:
            events.append(PlayerHitEvent(enemy))
            enemy.alive = False     # enemy is consumed on contact

    return events
