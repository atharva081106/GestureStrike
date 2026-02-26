"""
GestureStrike: Defense Protocol
Global configuration constants.
"""

# ── Display ────────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

# ── Player ─────────────────────────────────────────────────────────────────────
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_AMMO   = 15
CORE_RADIUS       = 30

# ── Bullet ─────────────────────────────────────────────────────────────────────
BULLET_SPEED    = 900
BULLET_LIFETIME = 1.2
BULLET_RADIUS   = 5
BULLET_SPREAD   = 2          # degrees ± spread

# ── Timing ─────────────────────────────────────────────────────────────────────
RELOAD_TIME     = 1.5
SHIELD_DURATION = 3.0
SHIELD_COOLDOWN = 5.0
SHOOT_COOLDOWN  = 0.2

# ── Enemies ────────────────────────────────────────────────────────────────────
ENEMY_BASE_SPEED          = 120
ENEMY_BASE_HEALTH         = 2
ENEMY_SPAWN_INTERVAL      = 2.0
ENEMY_RADIUS              = 18
ENEMY_DODGE_THRESHOLD     = 50      # px — cursor proximity triggers dodge
ENEMY_DODGE_TRIGGER_TIME  = 0.7     # seconds cursor must be close before dodge
ENEMY_DODGE_DURATION      = 0.5     # seconds of dodge movement
ENEMY_STAGGER_DURATION    = 0.1
ENEMY_STAGGER_FACTOR      = 0.7     # speed multiplier when staggered

# ── Gesture ────────────────────────────────────────────────────────────────────
PINCH_THRESHOLD       = 0.04
GESTURE_CONFIRM_FRAMES = 3

# ── Smoothing ──────────────────────────────────────────────────────────────────
SMOOTHING_ALPHA = 0.35
CURSOR_DEADZONE = 5            # pixels

# ── Camera Shake ───────────────────────────────────────────────────────────────
SHAKE_SMALL_AMPLITUDE = 2
SHAKE_SMALL_DURATION  = 0.10
SHAKE_BIG_AMPLITUDE   = 6
SHAKE_BIG_DURATION    = 0.25

# ── Particles ──────────────────────────────────────────────────────────────────
MAX_PARTICLES = 300

# ── Difficulty ─────────────────────────────────────────────────────────────────
DIFFICULTY_EVAL_INTERVAL = 10.0   # seconds
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 10

# ── Colours ────────────────────────────────────────────────────────────────────
COL_BG_TOP       = (5,   5,  20)
COL_BG_BOTTOM    = (10, 10,  40)
COL_CORE         = (80, 200, 255)
COL_CORE_GLOW    = (40, 120, 200)
COL_BULLET       = (0,  240, 255)
COL_ENEMY        = (220,  50,  50)
COL_ENEMY_GLOW   = (255, 100,  30)
COL_SHIELD       = (60, 140, 255)
COL_HUD_TEXT     = (230, 230, 230)
COL_HUD_ACCENT   = (0,  200, 255)
COL_RETICLE      = (0,  255, 180)
COL_STAR         = (200, 200, 220)

# ── Paths ──────────────────────────────────────────────────────────────────────
SOUNDS_DIR = "assets/sounds"
MUSIC_DIR  = "assets/music"

SOUND_FILES = {
    "shoot":      "shoot.wav",
    "reload":     "reload.wav",
    "shield_on":  "shield_on.wav",
    "shield_loop":"shield_loop.wav",
    "enemy_hit":  "enemy_hit.wav",
    "explosion":  "explosion.wav",
    "player_hit": "player_hit.wav",
}

MUSIC_TRACKS = {
    "ambient": "ambient.wav",
    "medium":  "medium.wav",
    "intense": "intense.wav",
}

MUSIC_CROSSFADE_MS = 1200

# ── Wave → Music mapping ───────────────────────────────────────────────────────
def music_for_wave(wave: int) -> str:
    if wave <= 3:
        return "ambient"
    elif wave <= 7:
        return "medium"
    return "intense"