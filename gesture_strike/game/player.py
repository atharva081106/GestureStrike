"""
game/player.py
Orbital defence gun that rotates around the central energy core.
- Gun sits on a ring (ORBIT_RADIUS) around the core
- Gun always points toward the cursor
- Bullets spawn FROM the gun tip, travel TOWARD the cursor
- Auto-reload when ammo hits zero
- Shield still available via fist gesture
"""

from __future__ import annotations
import math
import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_MAX_HEALTH, PLAYER_MAX_AMMO,
    RELOAD_TIME, SHIELD_DURATION, SHIELD_COOLDOWN, SHOOT_COOLDOWN,
    CORE_RADIUS, COL_CORE, COL_CORE_GLOW, COL_SHIELD, COL_HUD_ACCENT,
)

ORBIT_RADIUS  = 90    # px — gun orbits this far from core centre
GUN_LENGTH    = 28    # px — barrel length drawn outward from orbit ring
GUN_WIDTH     = 9     # px — barrel width


class Player:
    RECOIL_MAX     = 5
    RECOIL_MIN     = 2
    RECOIL_RECOVER = 0.12

    def __init__(self) -> None:
        self.core_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.health: int  = PLAYER_MAX_HEALTH
        self.ammo: int    = PLAYER_MAX_AMMO
        self.alive: bool  = True

        # Timers
        self.reload_timer:    float = 0.0
        self.shield_timer:    float = 0.0
        self.shield_cooldown: float = 0.0
        self.shoot_cooldown:  float = 0.0

        # Shield visual
        self.shield_active: bool  = False
        self.shield_pulse:  float = 0.0

        # Recoil (affects gun position along barrel axis)
        self._recoil_offset: float = 0.0
        self._recoil_timer:  float = 0.0
        self._recoil_target: float = 0.0

        # Current gun angle (radians) — updated each frame from cursor
        self._gun_angle: float = 0.0

        # Pre-rendered glow
        self._glow_surf = self._build_glow_surface()

        self.is_reloading: bool = False

    # ── Frame update ───────────────────────────────────────────────────────────

    def update(self, dt: float, cursor_pos: pygame.Vector2) -> None:
        if not self.alive:
            return

        # Point gun at cursor
        to_cursor = cursor_pos - self.core_pos
        if to_cursor.length_squared() > 1:
            self._gun_angle = math.atan2(to_cursor.y, to_cursor.x)

        # Shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)

        # Auto-reload
        if self.is_reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo         = PLAYER_MAX_AMMO
                self.is_reloading = False
                self.reload_timer = 0.0
        elif self.ammo == 0 and not self.is_reloading:
            self._start_auto_reload()

        # Shield active
        if self.shield_active:
            self.shield_timer -= dt
            self.shield_pulse  = (self.shield_pulse + dt * 4) % (2 * math.pi)
            if self.shield_timer <= 0:
                self.shield_active   = False
                self.shield_timer    = 0.0
                self.shield_cooldown = SHIELD_COOLDOWN
        elif self.shield_cooldown > 0:
            self.shield_cooldown = max(0.0, self.shield_cooldown - dt)

        # Recoil recovery
        if self._recoil_timer > 0:
            self._recoil_timer -= dt
            t = max(0.0, self._recoil_timer / self.RECOIL_RECOVER)
            self._recoil_offset = self._recoil_target * t
        else:
            self._recoil_offset = 0.0

        if self.health <= 0:
            self.health = 0
            self.alive  = False

    # ── Firing ─────────────────────────────────────────────────────────────────

    @property
    def gun_pos(self) -> pygame.Vector2:
        """Centre of gun on the orbit ring (with recoil applied)."""
        recoil = self._recoil_offset
        r = ORBIT_RADIUS - recoil
        return self.core_pos + pygame.Vector2(
            math.cos(self._gun_angle) * r,
            math.sin(self._gun_angle) * r,
        )

    @property
    def gun_tip(self) -> pygame.Vector2:
        """Muzzle position — where bullets spawn from."""
        return self.gun_pos + pygame.Vector2(
            math.cos(self._gun_angle) * GUN_LENGTH,
            math.sin(self._gun_angle) * GUN_LENGTH,
        )

    def can_shoot(self) -> bool:
        return (self.ammo > 0
                and not self.is_reloading
                and self.shoot_cooldown <= 0
                and self.alive)

    def consume_ammo(self) -> None:
        self.ammo = max(0, self.ammo - 1)
        self.shoot_cooldown = SHOOT_COOLDOWN
        # Recoil pushes gun back along barrel
        mag = random.uniform(self.RECOIL_MIN, self.RECOIL_MAX)
        self._recoil_target = mag
        self._recoil_timer  = self.RECOIL_RECOVER

    def activate_shield(self) -> bool:
        if self.shield_active or self.shield_cooldown > 0:
            return False
        self.shield_active = True
        self.shield_timer  = SHIELD_DURATION
        return True

    def take_damage(self, amount: int) -> bool:
        if self.shield_active:
            return False
        self.health -= amount
        return True

    # ── Drawing ────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        cx = int(self.core_pos.x)
        cy = int(self.core_pos.y)

        # Core glow
        gr = self._glow_surf.get_rect(center=(cx, cy))
        surface.blit(self._glow_surf, gr, special_flags=pygame.BLEND_ADD)

        # Orbit ring (faint dashed guide)
        self._draw_orbit_ring(surface, cx, cy)

        # Core body
        pygame.draw.circle(surface, COL_CORE, (cx, cy), CORE_RADIUS)
        pygame.draw.circle(surface, (180, 240, 255), (cx, cy), CORE_RADIUS - 6, 2)

        # Gun barrel
        self._draw_gun(surface)

        # Shield bubble
        if self.shield_active:
            self._draw_shield(surface, cx, cy)

    def _draw_orbit_ring(self, surface, cx, cy):
        # Draw dashed circle manually
        steps = 60
        for i in range(0, steps, 2):
            a0 = 2 * math.pi * i / steps
            a1 = 2 * math.pi * (i + 1) / steps
            x0 = cx + int(math.cos(a0) * ORBIT_RADIUS)
            y0 = cy + int(math.sin(a0) * ORBIT_RADIUS)
            x1 = cx + int(math.cos(a1) * ORBIT_RADIUS)
            y1 = cy + int(math.sin(a1) * ORBIT_RADIUS)
            pygame.draw.line(surface, (40, 80, 120), (x0, y0), (x1, y1), 1)

    def _draw_gun(self, surface):
        gp  = self.gun_pos
        tip = self.gun_tip
        angle = self._gun_angle

        # Barrel body (rectangle oriented along gun angle)
        perp_x = -math.sin(angle) * GUN_WIDTH / 2
        perp_y =  math.cos(angle) * GUN_WIDTH / 2

        base_x = gp.x - math.cos(angle) * GUN_LENGTH / 2
        base_y = gp.y - math.sin(angle) * GUN_LENGTH / 2
        tip_x  = tip.x
        tip_y  = tip.y

        barrel_pts = [
            (base_x + perp_x, base_y + perp_y),
            (tip_x  + perp_x, tip_y  + perp_y),
            (tip_x  - perp_x, tip_y  - perp_y),
            (base_x - perp_x, base_y - perp_y),
        ]
        pygame.draw.polygon(surface, (60, 180, 220), barrel_pts)
        pygame.draw.polygon(surface, (0, 240, 255),  barrel_pts, 2)

        # Gun body / mount circle
        pygame.draw.circle(surface, (40, 100, 160),
                           (int(gp.x), int(gp.y)), GUN_WIDTH)
        pygame.draw.circle(surface, (0, 200, 255),
                           (int(gp.x), int(gp.y)), GUN_WIDTH, 2)

        # Muzzle flash dot when ammo not full (cooldown indicator)
        if self.shoot_cooldown > 0:
            flash_alpha = self.shoot_cooldown / SHOOT_COOLDOWN
            flash_r = int(6 * flash_alpha)
            if flash_r > 0:
                pygame.draw.circle(surface, (255, 255, 200),
                                   (int(tip_x), int(tip_y)), flash_r)

    def _draw_shield(self, surface, cx, cy):
        alpha = int(120 + 80 * math.sin(self.shield_pulse))
        shield_surf = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(shield_surf, (*COL_SHIELD, alpha), (130, 130), 120, 4)
        for i in range(6):
            a  = self.shield_pulse + i * (math.pi / 3)
            sx = 130 + int(108 * math.cos(a))
            sy = 130 + int(108 * math.sin(a))
            ex = 130 + int(122 * math.cos(a + 0.3))
            ey = 130 + int(122 * math.sin(a + 0.3))
            pygame.draw.line(shield_surf, (*COL_SHIELD, alpha), (sx, sy), (ex, ey), 2)
        surface.blit(shield_surf,
                     shield_surf.get_rect(center=(cx, cy)),
                     special_flags=pygame.BLEND_RGBA_ADD)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _start_auto_reload(self) -> None:
        self.is_reloading = True
        self.reload_timer = RELOAD_TIME

    @staticmethod
    def _build_glow_surface() -> pygame.Surface:
        size = 140
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        for r in range(cx, 0, -4):
            alpha = int(55 * (1 - r / cx))
            pygame.draw.circle(surf, (*COL_CORE_GLOW, alpha), (cx, cy), r)
        return surf