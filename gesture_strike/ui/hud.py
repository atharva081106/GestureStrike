"""
ui/hud.py
Minimal, clean heads-up display:
  - Health bar
  - Ammo counter (dots)
  - Shield status + cooldown ring
  - Reload indicator
  - Wave & score
  - Accuracy live readout
  - Gesture indicator
  - FPS (debug)
"""

from __future__ import annotations
import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_MAX_HEALTH, PLAYER_MAX_AMMO,
    COL_HUD_TEXT, COL_HUD_ACCENT, COL_SHIELD,
    SHIELD_DURATION, SHIELD_COOLDOWN,
)
from vision.gesture_engine import Gesture


class HUD:
    """Stateless renderer — call .draw() every frame."""

    MARGIN     = 20
    BAR_W      = 160
    BAR_H      = 12
    AMMO_DOT_R = 5

    def __init__(self) -> None:
        pygame.font.init()
        self._font_lg = pygame.font.SysFont("Consolas", 22, bold=True)
        self._font_sm = pygame.font.SysFont("Consolas", 16)
        self._font_xs = pygame.font.SysFont("Consolas", 13)
        self._reload_surf: pygame.Surface | None = None

    # ── Public ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             health: int, ammo: int,
             is_reloading: bool, reload_timer: float,
             shield_active: bool, shield_timer: float, shield_cooldown: float,
             wave: int, score: int,
             accuracy_pct: int,
             gesture: Gesture,
             fps: float) -> None:

        m = self.MARGIN

        # ── Health bar ──────────────────────────────────────────────────────────
        self._draw_label(surface, "CORE", m, m)
        ratio = health / PLAYER_MAX_HEALTH
        col   = self._health_color(ratio)
        self._draw_bar(surface, m, m + 20, self.BAR_W, self.BAR_H, ratio, col,
                       (30, 30, 40))
        hp_txt = self._font_xs.render(f"{health}/{PLAYER_MAX_HEALTH}", True, COL_HUD_TEXT)
        surface.blit(hp_txt, (m + self.BAR_W + 6, m + 20))

        # ── Ammo dots ───────────────────────────────────────────────────────────
        self._draw_label(surface, "AMMO", m, m + 48)
        for i in range(PLAYER_MAX_AMMO):
            cx = m + i * (self.AMMO_DOT_R * 2 + 3) + self.AMMO_DOT_R
            cy = m + 68
            color = COL_HUD_ACCENT if i < ammo else (50, 50, 70)
            pygame.draw.circle(surface, color, (cx, cy), self.AMMO_DOT_R)

        if is_reloading:
            pct = 1.0 - (reload_timer / 1.5)
            reload_txt = self._font_sm.render(
                f"RELOADING {int(pct*100)}%", True, (255, 220, 0))
            surface.blit(reload_txt, (m, m + 82))

        # ── Shield ──────────────────────────────────────────────────────────────
        sy = m + 108
        self._draw_label(surface, "SHIELD", m, sy)
        if shield_active:
            pct = shield_timer / SHIELD_DURATION
            self._draw_ring(surface, m + 50, sy + 8,
                            14, pct, COL_SHIELD, (20, 20, 60))
            active_txt = self._font_xs.render("ACTIVE", True, (100, 180, 255))
            surface.blit(active_txt, (m + 68, sy + 2))
        elif shield_cooldown > 0:
            cd_pct = 1.0 - (shield_cooldown / SHIELD_COOLDOWN)
            self._draw_ring(surface, m + 50, sy + 8,
                            14, cd_pct, (100, 100, 180), (20, 20, 60))
            cd_txt = self._font_xs.render(f"CD {shield_cooldown:.1f}s",
                                          True, (130, 130, 160))
            surface.blit(cd_txt, (m + 68, sy + 2))
        else:
            ready_txt = self._font_xs.render("READY", True, (100, 200, 100))
            surface.blit(ready_txt, (m + 50, sy + 2))

        # ── Wave & Score ────────────────────────────────────────────────────────
        wave_txt  = self._font_lg.render(f"WAVE {wave}", True, COL_HUD_ACCENT)
        score_txt = self._font_sm.render(f"SCORE {score}", True, COL_HUD_TEXT)
        surface.blit(wave_txt,  (SCREEN_WIDTH - m - wave_txt.get_width(), m))
        surface.blit(score_txt, (SCREEN_WIDTH - m - score_txt.get_width(), m + 30))

        # ── Accuracy ────────────────────────────────────────────────────────────
        acc_txt = self._font_sm.render(f"ACC  {accuracy_pct}%", True, COL_HUD_TEXT)
        surface.blit(acc_txt, (SCREEN_WIDTH - m - acc_txt.get_width(), m + 54))

        # ── Gesture indicator ───────────────────────────────────────────────────
        gesture_names = {
            Gesture.AIM:    ("AIM",    (0, 220, 180)),
            Gesture.SHOOT:  ("FIRING", (0, 240, 255)),
            Gesture.SHIELD: ("SHIELD", COL_SHIELD),
            Gesture.NONE:   ("--",     (80, 80, 100)),
        }
        gname, gcol = gesture_names.get(gesture, ("--", (80, 80, 100)))
        g_surf = self._font_sm.render(f"GESTURE: {gname}", True, gcol)
        surface.blit(g_surf, (SCREEN_WIDTH - m - g_surf.get_width(),
                               SCREEN_HEIGHT - m - 20))

        # ── FPS ─────────────────────────────────────────────────────────────────
        fps_col = (0, 200, 80) if fps >= 50 else (255, 150, 0) if fps >= 35 else (255, 50, 50)
        fps_surf = self._font_xs.render(f"FPS {fps:.0f}", True, fps_col)
        surface.blit(fps_surf, (m, SCREEN_HEIGHT - m - 15))

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _draw_label(self, surface, text, x, y):
        surf = self._font_xs.render(text, True, (140, 140, 160))
        surface.blit(surf, (x, y))

    def _draw_bar(self, surface, x, y, w, h, ratio, fg, bg):
        pygame.draw.rect(surface, bg,  (x, y, w, h), border_radius=4)
        pygame.draw.rect(surface, fg,  (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(surface, (60, 60, 80), (x, y, w, h), 1, border_radius=4)

    def _draw_ring(self, surface, cx, cy, radius, pct, fg, bg):
        pygame.draw.circle(surface, bg, (cx, cy), radius, 3)
        if pct > 0:
            end_angle = -math.pi/2 + pct * 2 * math.pi
            rect = pygame.Rect(cx - radius, cy - radius, radius*2, radius*2)
            pygame.draw.arc(surface, fg, rect, -math.pi/2, end_angle, 3)

    @staticmethod
    def _health_color(ratio: float) -> tuple:
        if ratio > 0.6:
            return (0, 200, 80)
        elif ratio > 0.3:
            return (220, 180, 0)
        return (220, 50, 50)