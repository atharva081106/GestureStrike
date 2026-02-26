"""
main.py
GestureStrike: Defense Protocol
Entry point — owns the state machine, game loop, and all subsystem wiring.

States: MENU → CALIBRATION → PLAYING → GAME_OVER
"""

from __future__ import annotations
import sys
import os
import math
import random
import time

# Add project root to path so sub-packages resolve cleanly
sys.path.insert(0, os.path.dirname(__file__))

import pygame
import numpy as np

from config import *

from vision.hand_tracker   import HandTracker
from vision.gesture_engine import GestureEngine2H, Gesture
from vision.smoothing      import CursorSmoother

from game.player    import Player
from game.bullet    import BulletPool
from game.enemy     import EnemyManager
from game.collision import check_bullet_enemy_collisions, check_enemy_player_collisions

from systems.difficulty_controller import DifficultyController
from systems.analytics              import Analytics
from systems.camera_shake           import CameraShake
from systems.particle_system        import ParticleSystem
from systems.audio_manager          import AudioManager

from ui.hud import HUD


# ──────────────────────────────────────────────────────────────────────────────
# Background & decoration helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build_background(width: int, height: int) -> pygame.Surface:
    surf = pygame.Surface((width, height))
    for y in range(height):
        t  = y / height
        r  = int(COL_BG_TOP[0] * (1-t) + COL_BG_BOTTOM[0] * t)
        g  = int(COL_BG_TOP[1] * (1-t) + COL_BG_BOTTOM[1] * t)
        b  = int(COL_BG_TOP[2] * (1-t) + COL_BG_BOTTOM[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf


def _build_star_layer(width: int, height: int,
                      count: int = 200) -> list[tuple]:
    stars = []
    for _ in range(count):
        x     = random.randint(0, width)
        y     = random.randint(0, height)
        size  = random.choice([1, 1, 1, 2])
        alpha = random.randint(100, 240)
        stars.append((x, y, size, alpha))
    return stars


def _draw_stars(surface: pygame.Surface, stars: list, shake: tuple) -> None:
    ox, oy = shake
    for (x, y, size, alpha) in stars:
        col = (alpha, alpha, min(255, alpha + 20))
        pygame.draw.circle(surface, col, (x + ox // 3, y + oy // 3), size)


def _draw_webcam_overlay(surface: pygame.Surface,
                          tracker: "HandTracker",
                          alpha: int = 210) -> None:
    """
    Renders a small webcam preview in the bottom-right corner.
    Size: 200×150 px with a neon border and corner label.
    """
    cam_surf = tracker.get_frame_surface(width=200)
    if cam_surf is None:
        return

    # Position: bottom-right with 14 px margin
    margin  = 14
    cam_w   = cam_surf.get_width()
    cam_h   = cam_surf.get_height()
    x = SCREEN_WIDTH  - cam_w - margin
    y = SCREEN_HEIGHT - cam_h - margin

    # Semi-transparent backing
    backing = pygame.Surface((cam_w, cam_h))
    backing.blit(cam_surf, (0, 0))
    backing.set_alpha(alpha)
    surface.blit(backing, (x, y))

    # Neon border
    pygame.draw.rect(surface, (0, 200, 255), (x - 1, y - 1, cam_w + 2, cam_h + 2), 2)

    # Corner label
    label_font = pygame.font.SysFont("Consolas", 11)
    label = label_font.render("CAM", True, (0, 200, 255))
    surface.blit(label, (x + 4, y + 4))


def _draw_reticle(surface: pygame.Surface,
                  cx: int, cy: int,
                  gesture: Gesture,
                  pulse: float) -> None:
    """Aim reticle crosshair around cursor."""
    col = {
        Gesture.SHOOT:  (0, 240, 255),
        Gesture.SHIELD: COL_SHIELD,
        Gesture.AIM:    COL_RETICLE,
    }.get(gesture, COL_RETICLE)

    r       = 18 + int(4 * math.sin(pulse))
    gap     = 6
    arm_len = 12

    # Four arms
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        ix  = int(cx + (r + gap)     * math.cos(rad))
        iy  = int(cy + (r + gap)     * math.sin(rad))
        ex  = int(cx + (r + gap + arm_len) * math.cos(rad))
        ey  = int(cy + (r + gap + arm_len) * math.sin(rad))
        pygame.draw.line(surface, col, (ix, iy), (ex, ey), 2)

    # Centre dot
    pygame.draw.circle(surface, col, (cx, cy), 3)

    # Outer ring (dim)
    pygame.draw.circle(surface, (*col[:3], 60),  # type: ignore[arg-type]
                       (cx, cy), r, 1)


# ──────────────────────────────────────────────────────────────────────────────
# State machine states
# ──────────────────────────────────────────────────────────────────────────────

class GameState:
    MENU       = "MENU"
    CALIBRATION= "CALIBRATION"
    PLAYING    = "PLAYING"
    GAME_OVER  = "GAME_OVER"


# ──────────────────────────────────────────────────────────────────────────────
# Main game class
# ──────────────────────────────────────────────────────────────────────────────

class GestureStrikeGame:

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("GestureStrike: Defense Protocol")
        self.clock  = pygame.time.Clock()

        # Pre-render static surfaces
        self._bg            = _build_background(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._stars         = _build_star_layer(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Fonts
        pygame.font.init()
        self._font_title  = pygame.font.SysFont("Consolas", 52, bold=True)
        self._font_large  = pygame.font.SysFont("Consolas", 36, bold=True)
        self._font_medium = pygame.font.SysFont("Consolas", 24)
        self._font_small  = pygame.font.SysFont("Consolas", 18)

        # Vision subsystems
        self.tracker  = HandTracker(max_hands=2)
        self.gesture_engine = GestureEngine2H()
        self.smoother = CursorSmoother()

        # Audio (initialised early so sounds preload)
        self.audio = AudioManager()

        # Game state
        self.state: str = GameState.MENU
        self._init_game_objects()

        # Shared / UI
        self.hud          = HUD()
        self._pulse       = 0.0       # global animation timer
        self._cursor_pos  = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self._gesture     = Gesture.NONE

        # Calibration
        self._calib_timer = 3.0

        # Game over data
        self._go_wave     = 1
        self._go_accuracy = 0
        self._go_time     = 0.0

        # Shield sound state
        self._shield_was_active = False

    def _init_game_objects(self) -> None:
        """Reinitialise all play-field objects for a fresh game."""
        self.player     = Player()
        self.bullets    = BulletPool(pool_size=80)
        self.enemies    = EnemyManager()
        self.difficulty = DifficultyController()
        self.analytics  = Analytics()
        self.shake      = CameraShake()
        self.particles  = ParticleSystem()
        self.score      = 0
        self._prev_shield_active = False

    # ──────────────────────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────────────────────

    def run(self) -> None:
        running = True
        while running:
            dt  = self.clock.tick(FPS) / 1000.0
            dt  = min(dt, 0.05)   # clamp to avoid spiral of death
            fps = self.clock.get_fps()

            # ── Events ──────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                        self._restart()
                    if event.key == pygame.K_SPACE and self.state == GameState.MENU:
                        self.state = GameState.CALIBRATION
                        self._calib_timer = 3.0

            # ── Vision update ───────────────────────────────────────────────
            self.tracker.update()
            hands = self.tracker.hands          # list of 0-2 HandData
            # Build list of [lm0, lm1] with None padding
            lm_list = [h.landmarks for h in hands]
            while len(lm_list) < 2:
                lm_list.append(None)

            self._gesture, aim_lm = self.gesture_engine.update(lm_list)

            if aim_lm is not None:
                # Index tip (landmark 8) drives the cursor
                ix, iy = aim_lm[8][0], aim_lm[8][1]
                self._cursor_pos = self.smoother.update(ix, iy)
            # (if no hand, cursor freezes at last position)

            # ── State dispatch ───────────────────────────────────────────────
            self._pulse += dt * 2.5

            if self.state == GameState.MENU:
                self._update_menu(dt)
                self._draw_menu(fps)
            elif self.state == GameState.CALIBRATION:
                self._update_calibration(dt)
                self._draw_calibration()
            elif self.state == GameState.PLAYING:
                self._update_playing(dt, fps)
                self._draw_playing(fps)
            elif self.state == GameState.GAME_OVER:
                self._draw_game_over()

            pygame.display.flip()

        self.tracker.release()
        pygame.quit()

    # ──────────────────────────────────────────────────────────────────────────
    # MENU
    # ──────────────────────────────────────────────────────────────────────────

    def _update_menu(self, dt: float) -> None:
        # Auto-advance when hand detected
        if self.tracker.is_hand_detected and self._gesture != Gesture.NONE:
            self.state        = GameState.CALIBRATION
            self._calib_timer = 3.0

    def _draw_menu(self, fps: float) -> None:
        self.screen.blit(self._bg, (0, 0))
        _draw_stars(self.screen, self._stars, (0, 0))

        # Pulsing core decoration
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        for r in range(80, 10, -8):
            alpha_ratio = 1 - r / 80
            col = (int(COL_CORE_GLOW[0] * alpha_ratio),
                   int(COL_CORE_GLOW[1] * alpha_ratio),
                   int(COL_CORE_GLOW[2] * alpha_ratio))
            pygame.draw.circle(self.screen, col, (cx, cy), r)
        pygame.draw.circle(self.screen, COL_CORE, (cx, cy), 30)

        title = self._font_title.render("GESTURE STRIKE", True, COL_HUD_ACCENT)
        sub   = self._font_medium.render("Defense Protocol", True, (160, 200, 220))

        pulse_y = int(math.sin(self._pulse * 0.8) * 6)
        hint_col = (180, 180, 200) if int(self._pulse) % 2 == 0 else (120, 120, 150)
        hint = self._font_small.render("Raise your hand to begin  ·  SPACE to skip camera",
                                        True, hint_col)

        self.screen.blit(title, (cx - title.get_width()//2, 200))
        self.screen.blit(sub,   (cx - sub.get_width()//2,   265))
        self.screen.blit(hint,  (cx - hint.get_width()//2,  420 + pulse_y))

        # Controls legend
        controls = [
            ("☝   index finger",        "AIM  (cursor moves)"),
            ("🖐   open palm",           "SHOOT  (hold = auto-fire)"),
            ("✊   fist",               "SHIELD  (blocks damage)"),
            ("",                         "Auto-reload when empty"),
        ]
        for i, (gest, action) in enumerate(controls):
            row = self._font_small.render(f"{gest:18s}  →  {action}", True, (140, 160, 180))
            self.screen.blit(row, (cx - row.get_width()//2, 490 + i * 28))

        self._draw_fps_overlay(fps)

    # ──────────────────────────────────────────────────────────────────────────
    # CALIBRATION
    # ──────────────────────────────────────────────────────────────────────────

    def _update_calibration(self, dt: float) -> None:
        self._calib_timer -= dt
        if self._calib_timer <= 0:
            self.state = GameState.PLAYING
            self.audio.update_music_for_wave(1)

    def _draw_calibration(self) -> None:
        self.screen.blit(self._bg, (0, 0))
        _draw_stars(self.screen, self._stars, (0, 0))

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        title = self._font_large.render("CALIBRATING...", True, COL_HUD_ACCENT)
        self.screen.blit(title, (cx - title.get_width()//2, 200))

        # Live cursor
        mx, my = self._cursor_pos
        _draw_reticle(self.screen, mx, my, self._gesture, self._pulse)

        instr = self._font_medium.render(
            "🖐 Open palm = SHOOT  |  ✊ Fist = SHIELD", True, (180, 200, 220))
        self.screen.blit(instr, (cx - instr.get_width()//2, 300))

        instr2 = self._font_small.render(
            "Point at enemies and open your palm — hold to keep firing!",
            True, (130, 150, 170))
        self.screen.blit(instr2, (cx - instr2.get_width()//2, 335))

        # Corner alignment targets
        targets = [(80, 80), (SCREEN_WIDTH-80, 80),
                   (80, SCREEN_HEIGHT-80), (SCREEN_WIDTH-80, SCREEN_HEIGHT-80)]
        for tx, ty in targets:
            pygame.draw.circle(self.screen, (60, 120, 200), (tx, ty), 12, 2)
            pygame.draw.line(self.screen, (60, 120, 200),
                             (tx-8, ty), (tx+8, ty), 1)
            pygame.draw.line(self.screen, (60, 120, 200),
                             (tx, ty-8), (tx, ty+8), 1)

        # Countdown
        pct      = max(0.0, self._calib_timer / 3.0)
        bar_rect = pygame.Rect(cx - 120, 380, 240, 12)
        pygame.draw.rect(self.screen, (30, 30, 50), bar_rect, border_radius=6)
        pygame.draw.rect(self.screen, COL_HUD_ACCENT,
                         (bar_rect.x, bar_rect.y, int(240 * (1-pct)), 12),
                         border_radius=6)

        hand_txt = self._font_small.render(
            "Hand detected ✓" if self.tracker.is_hand_detected else "No hand detected...",
            True,
            (0, 220, 80) if self.tracker.is_hand_detected else (200, 80, 80))
        self.screen.blit(hand_txt, (cx - hand_txt.get_width()//2, 410))

        # Webcam overlay
        _draw_webcam_overlay(self.screen, self.tracker)

    # ──────────────────────────────────────────────────────────────────────────
    # PLAYING — update
    # ──────────────────────────────────────────────────────────────────────────

    def _update_playing(self, dt: float, fps: float) -> None:
        p = self.player
        cursor = pygame.Vector2(*self._cursor_pos)

        # ── Gesture → actions ────────────────────────────────────────────────
        if self.tracker.is_hand_detected:
            g = self._gesture

            # SHOOT: palm open → continuous fire until palm closes or ammo runs out
            if g == Gesture.SHOOT and p.can_shoot():
                fired = self.bullets.fire(p.gun_tip, cursor)
                if fired:
                    p.consume_ammo()
                    self.shake.small_shake()
                    self.audio.play_shoot(self._cursor_pos[0])
                    self.analytics.record_shot()
                    self.difficulty.record_shot()

            elif g == Gesture.SHIELD and not p.shield_active:
                if p.activate_shield():
                    self.audio.play("shield_on")
                    self.audio.start_shield_loop()

        # Shield sound stop
        if self._prev_shield_active and not p.shield_active:
            self.audio.stop_shield_loop()
        self._prev_shield_active = p.shield_active

        # ── Subsystem updates ────────────────────────────────────────────────
        p.update(dt, cursor)
        self.bullets.update(dt)
        self.difficulty.update(dt)
        self.analytics.update(dt, self.difficulty.level)
        self.shake.update(dt)
        self.particles.update(dt)

        self.enemies.update(
            dt,
            target_pos    = p.core_pos,
            cursor_pos    = cursor,
            spawn_interval= self.difficulty.spawn_interval,
            speed_mult    = self.difficulty.speed_multiplier,
            health_mult   = self.difficulty.health_multiplier,
        )

        # ── Collisions ───────────────────────────────────────────────────────
        active_bullets = self.bullets.active_bullets
        live_enemies   = self.enemies.enemies

        bullet_hits = check_bullet_enemy_collisions(active_bullets, live_enemies)
        for evt in bullet_hits:
            killed = evt.enemy.hit(evt.enemy.max_health)   # one-shot kill
            self.particles.emit_bullet_impact(evt.point.x, evt.point.y)
            self.audio.play("enemy_hit")
            self.analytics.record_hit()
            self.difficulty.record_hit()
            if killed:
                self.particles.emit_explosion(evt.enemy.pos.x, evt.enemy.pos.y)
                self.shake.big_shake()
                self.audio.play("explosion")
                self.enemies.register_kill()
                self.analytics.record_kill()
                self.score += 100 * self.difficulty.level

        player_hits = check_enemy_player_collisions(live_enemies, p.core_pos, CORE_RADIUS)
        for evt in player_hits:
            damage = 10
            applied = p.take_damage(damage)
            if applied:
                self.shake.big_shake()
                self.audio.play("player_hit")
                self.analytics.record_damage(damage)
                self.difficulty.record_damage(damage)
            else:
                self.particles.emit_shield_hit(p.core_pos.x, p.core_pos.y)
                self.shake.small_shake()

        # ── Adaptive music ───────────────────────────────────────────────────
        self.audio.update_music_for_wave(self.enemies.wave)

        # ── Death check ──────────────────────────────────────────────────────
        if not p.alive:
            self.audio.stop_music()
            self._go_wave     = self.enemies.wave
            self._go_accuracy = self.analytics.accuracy_pct
            self._go_time     = self.analytics.survival_time
            self.state = GameState.GAME_OVER

    # ──────────────────────────────────────────────────────────────────────────
    # PLAYING — draw
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_playing(self, fps: float) -> None:
        shake_off = self.shake.offset

        self.screen.blit(self._bg, (0, 0))
        _draw_stars(self.screen, self._stars, shake_off)

        self.particles.draw(self.screen, shake_off)
        self.bullets.draw(self.screen, shake_off)
        self.enemies.draw(self.screen, shake_off)
        self.player.draw(self.screen)

        # Cursor reticle
        _draw_reticle(self.screen, *self._cursor_pos, self._gesture, self._pulse)

        # HUD
        p = self.player
        self.hud.draw(
            surface        = self.screen,
            health         = p.health,
            ammo           = p.ammo,
            is_reloading   = p.is_reloading,
            reload_timer   = p.reload_timer,
            shield_active  = p.shield_active,
            shield_timer   = p.shield_timer,
            shield_cooldown= p.shield_cooldown,
            wave           = self.enemies.wave,
            score          = self.score,
            accuracy_pct   = self.analytics.accuracy_pct,
            gesture        = self._gesture,
            fps            = fps,
        )

        # Webcam overlay (bottom-right)
        _draw_webcam_overlay(self.screen, self.tracker)

        # Hand status hint
        hand_count = len(self.tracker.hands)
        if hand_count == 0:
            warn = self._font_medium.render(
                "⚠  No hand detected — aim frozen", True, (220, 100, 50))
            self.screen.blit(warn, (SCREEN_WIDTH//2 - warn.get_width()//2,
                                    SCREEN_HEIGHT - 60))
        # (no hint needed for 1-2 hands — controls are simple)

    # ──────────────────────────────────────────────────────────────────────────
    # GAME OVER
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_game_over(self) -> None:
        self.screen.blit(self._bg, (0, 0))
        _draw_stars(self.screen, self._stars, (0, 0))

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        # Vignette overlay
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 120))
        self.screen.blit(vignette, (0, 0))

        title = self._font_title.render("CORE BREACHED", True, (220, 60, 60))
        self.screen.blit(title, (cx - title.get_width()//2, cy - 180))

        summary = [
            (f"Wave Reached",          str(self._go_wave)),
            (f"Survival Time",         f"{self._go_time:.1f}s"),
            (f"Accuracy",              f"{self._go_accuracy}%"),
            (f"Score",                 str(self.score)),
            (f"Difficulty Reached",    str(self.difficulty.level)),
        ]
        for i, (label, value) in enumerate(summary):
            row = self._font_medium.render(
                f"{label:<22} {value}", True, COL_HUD_TEXT)
            self.screen.blit(row, (cx - row.get_width()//2, cy - 80 + i * 38))

        # Blinking restart prompt
        if int(self._pulse * 1.5) % 2 == 0:
            restart = self._font_medium.render(
                "Press  R  to restart", True, COL_HUD_ACCENT)
            self.screen.blit(restart, (cx - restart.get_width()//2, cy + 130))

        exit_hint = self._font_small.render("ESC to quit", True, (100, 100, 120))
        self.screen.blit(exit_hint, (cx - exit_hint.get_width()//2, cy + 180))

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _restart(self) -> None:
        self._init_game_objects()
        self.state = GameState.CALIBRATION
        self._calib_timer = 2.0
        self.audio.update_music_for_wave(1)

    def _draw_fps_overlay(self, fps: float) -> None:
        col  = (0, 200, 80) if fps >= 50 else (255, 150, 0)
        surf = pygame.font.SysFont("Consolas", 13).render(f"FPS {fps:.0f}", True, col)
        self.screen.blit(surf, (SCREEN_WIDTH - 70, SCREEN_HEIGHT - 24))


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    game = GestureStrikeGame()
    game.run()