# GestureStrike: Defense Protocol

Real-time 2D adaptive survival shooter controlled by webcam hand gestures.

## Requirements

- Python 3.10+
- Webcam (built-in or USB)
- The packages in `requirements.txt`

## Install & Run

```bash
# 1. Clone / extract the project
cd gesture_strike

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

> **Note:** On first run the game auto-generates placeholder WAV audio files
> in `assets/sounds/` and `assets/music/` if they are missing.
> Replace them with your own WAV/OGG files for better audio quality.

## Controls (Gestures)

| Gesture | Action |
|---|---|
| Index finger extended (others folded) | **AIM** — move cursor |
| Thumb + index pinch | **SHOOT** |
| All five fingers open | **RELOAD** |
| Closed fist | **SHIELD** (blocks all damage for 3 s; 5 s cooldown) |

- **SPACE** — skip camera and go straight to calibration
- **R** — restart after Game Over
- **ESC** — quit

## Game Rules

- Protect the central energy core.
- Enemies spawn from all edges and seek the core.
- Each wave increases enemy count and difficulty.
- Accuracy > 70% + low damage taken → difficulty goes up (max 10).
- Music adapts: ambient (waves 1–3), medium (4–7), intense (8+).

## Asset Folder

```
assets/
  sounds/
    shoot.wav        # weapon fire
    reload.wav       # reload sound
    shield_on.wav    # shield activation
    shield_loop.wav  # looping shield hum
    enemy_hit.wav    # enemy hit confirm
    explosion.wav    # enemy kill
    player_hit.wav   # core damage
  music/
    ambient.ogg      # waves 1-3 background track
    medium.ogg       # waves 4-7 background track
    intense.ogg      # wave 8+ background track
```

Replace any of the above files with your own audio to customise the experience.
All sounds are preloaded at startup.

## Architecture

```
gesture_strike/
├── main.py                 # Game loop + state machine
├── config.py               # All constants
├── vision/
│   ├── hand_tracker.py     # MediaPipe webcam integration
│   ├── gesture_engine.py   # Rule-based gesture classifier
│   └── smoothing.py        # Exponential cursor smoothing
├── game/
│   ├── player.py           # Player / core turret
│   ├── bullet.py           # Bullet pool
│   ├── enemy.py            # Enemy + EnemyManager
│   ├── ai_behavior.py      # Enemy state machine (SEEK/DODGE/AGGRESSIVE)
│   └── collision.py        # Circle collision detection
├── systems/
│   ├── difficulty_controller.py   # Adaptive difficulty
│   ├── analytics.py               # Session telemetry
│   ├── camera_shake.py            # Decaying sine-wave shake
│   ├── particle_system.py         # Pooled particle effects
│   └── audio_manager.py           # Sound + adaptive music
└── ui/
    └── hud.py              # Heads-up display renderer
```
