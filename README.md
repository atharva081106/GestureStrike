<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&size=32&duration=3000&pause=1000&color=00C8FF&center=true&vCenter=true&width=600&lines=GestureStrike%3A+Defense+Protocol;Control+With+Your+Hands;No+Mouse.+No+Keyboard." alt="Typing SVG" />

<br/>

> **A real-time 2D survival shooter controlled entirely by your hands via webcam.**
> No mouse. No keyboard. Just you, your gestures, and the enemies closing in.

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.4+-00B140?style=for-the-badge&logo=python&logoColor=white)](https://pygame.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/atharva081106/gesture_strike?style=for-the-badge&color=gold)](https://github.com/atharva081106/gesture_strike/stargazers)
[![Issues](https://img.shields.io/github/issues/atharva081106/gesture_strike?style=for-the-badge&color=red)](https://github.com/atharva081106/gesture_strike/issues)

<br/>

```
 ██████╗ ███████╗███████╗████████╗██╗   ██╗██████╗ ███████╗
██╔════╝ ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝
██║  ███╗█████╗  ███████╗   ██║   ██║   ██║██████╔╝█████╗  
██║   ██║██╔══╝  ╚════██║   ██║   ██║   ██║██╔══██╗██╔══╝  
╚██████╔╝███████╗███████║   ██║   ╚██████╔╝██║  ██║███████╗
 ╚═════╝ ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝
          S T R I K E  :  D E F E N S E  P R O T O C O L
```

</div>

---

## 🎬 What Is This?

**GestureStrike** is a gesture-controlled arcade survival game built entirely in Python. You protect a glowing energy core from waves of enemy drones — using only your hands in front of a webcam.

An **orbital defence gun** rotates around the core and always aims at your fingertip cursor. Open your palm to unleash a burst of fire. Close your fist to raise an electric shield. The game adapts to your skill — play well and enemies get faster, tougher, and more aggressive.

A **live webcam preview** sits in the corner so you can always see what the camera sees.

---

## ✨ Feature Highlights

<table>
<tr>
<td width="50%">

### 🤚 Vision & Input
- Real-time hand tracking via **MediaPipe 21-landmark model**
- Up to **2 hands** tracked simultaneously
- **Exponential cursor smoother** with dead-zone suppression
- 3-frame gesture confirmation — no accidental triggers
- Live **webcam overlay** in-game (bottom-right corner)

</td>
<td width="50%">

### 🎮 Gameplay
- **Orbital gun** rotates around the core — barrel always points at cursor
- **One-shot kills** — every bullet destroys an enemy instantly
- **Auto-reload** — no gesture needed, reloads automatically
- **Electric shield** — fist gesture blocks all damage for 3 seconds
- Enemies **dodge** when your cursor gets too close

</td>
</tr>
<tr>
<td width="50%">

### 👾 Enemy System
- **4 visual tiers** — drones evolve every 2–3 waves
- Enemy AI state machine: **SEEK → DODGE → AGGRESSIVE → STAGGER**
- Zig-zag movement on elite/boss tier enemies
- Randomised **2–3 second spawn intervals**
- Wave quota system — kill more to advance faster

</td>
<td width="50%">

### 💫 Polish & Feel
- **Camera shake** — decaying sine-wave on hits and explosions
- **300-particle pool** — explosions, bullet impacts, shield bursts
- **Adaptive music** — ambient → medium → intense as waves climb
- **Recoil system** — gun kicks back along barrel axis
- Neon cyan bullets with **motion trail**

</td>
</tr>
</table>

---

## 🤚 Gesture Controls

> All controls are **hands-only**. No keyboard needed during gameplay.

| Gesture | Hand Shape | Action |
|:---:|:---|:---|
| ☝️ | Index finger extended, others folded | **AIM** — cursor follows fingertip |
| 🖐️ | All four fingers extended (open palm) | **SHOOT** — hold for continuous auto-fire |
| ✊ | All fingers folded (fist) | **SHIELD** — blocks all damage for 3 s |
| *(auto)* | — | **RELOAD** — happens automatically when ammo hits 0 |

### Two-Hand Split Control *(Optional)*
| Hand | Role |
|:---|:---|
| **Right hand** | AIM — cursor tracks your right index tip |
| **Left hand** | ACTION — open palm fires, fist shields |

---

## 👾 Enemy Wave Tiers

Every **2–3 waves** enemies evolve visually and mechanically:

```
Wave 1-2  ●  🔴  RED DRONE      — Standard speed, basic AI
Wave 3-5  ●  🟠  ARMOURED       — +30% speed, bigger hitbox
Wave 6-8  ●  🟣  ELITE          — +65% speed, aggressive zigzag
Wave 9+   ●  🔥  BOSS           — +110% speed, large, double ring, relentless
```

All enemy tiers feature:
- **Dodge behaviour** when your cursor hovers too close for 0.7 seconds
- **Hit stagger** — slowed for 0.1 s after being shot (redundant with one-shot but visible in future multi-HP modes)
- **Pulsing glow** that syncs to the game's animation timer

---

## 🗺️ Game States

```
  ┌────────┐     ┌─────────────┐     ┌─────────┐     ┌───────────┐
  │  MENU  │────▶│ CALIBRATION │────▶│ PLAYING │────▶│ GAME OVER │
  └────────┘     └─────────────┘     └─────────┘     └─────┬─────┘
       ▲                                                     │
       └──────────────────── Press R ──────────────────────┘
```

| State | Description |
|---|---|
| **MENU** | Controls shown, raise any hand or press `SPACE` to begin |
| **CALIBRATION** | Live cursor preview — align your hand, 3-second countdown |
| **PLAYING** | Full game: HUD, enemies, particles, adaptive music, webcam overlay |
| **GAME OVER** | Wave reached, accuracy %, survival time, final score displayed |

---

## 🏗️ Project Architecture

```
gesture_strike/
│
├── main.py                       # 🎮 Game loop + state machine
├── config.py                     # ⚙️  All constants (speeds, colours, timers)
│
├── vision/
│   ├── hand_tracker.py           # 📷  MediaPipe webcam wrapper (0.10+ & legacy)
│   ├── gesture_engine.py         # 🤚  Rule-based classifier + 2-hand engine
│   └── smoothing.py              # 🎯  Exponential cursor smoother + dead-zone
│
├── game/
│   ├── player.py                 # 🔫  Orbital gun — rotates, recoil, shield
│   ├── bullet.py                 # 💥  Object-pooled bullets with neon trail
│   ├── enemy.py                  # 👾  4-tier enemies, EnemyManager, wave progression
│   ├── ai_behavior.py            # 🧠  SEEK / DODGE / AGGRESSIVE / STAGGER FSM
│   └── collision.py              # 🔵  Circle-circle collision detection
│
├── systems/
│   ├── difficulty_controller.py  # 📈  Adaptive difficulty — evaluates every 10 s
│   ├── analytics.py              # 📊  Session telemetry: shots, hits, times
│   ├── camera_shake.py           # 📳  Decaying sine-wave screen shake
│   ├── particle_system.py        # ✨  300-particle pool
│   └── audio_manager.py          # 🔊  Preloaded SFX, adaptive music, stereo pan
│
├── ui/
│   └── hud.py                    # 🖥️  Health, ammo, shield, wave, score, FPS
│
└── assets/
    ├── sounds/                   # 🔉  WAV files (auto-generated if missing)
    └── music/                    # 🎵  WAV tracks (auto-generated if missing)
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.10+**
- A **webcam** (built-in or USB)
- ~200 MB disk space (MediaPipe model download on first run)

### Step 1 — Clone
```bash
git clone https://github.com/atharva081106/gesture_strike.git
cd gesture_strike
```

### Step 2 — Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run
```bash
python main.py
```

> **First launch only:** MediaPipe downloads the hand landmark model (~8 MB) into `vision/hand_landmarker.task` automatically. Takes ~10 seconds on first run, instant every time after.

> **Audio:** Placeholder sine-wave beeps are generated into `assets/` on first run. Replace with your own WAV files for real sound design.

---

## 📦 Dependencies

```
pygame>=2.4.0
opencv-python>=4.8.0
mediapipe>=0.10.0
numpy>=1.24.0
```

Install all at once:
```bash
pip install pygame opencv-python mediapipe numpy
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|:---:|:---|
| `SPACE` | Skip camera — jump straight to calibration |
| `R` | Restart *(Game Over screen only)* |
| `ESC` | Quit |

---

## ⚙️ Configuration

All tunable parameters live in `config.py`. Key values:

```python
# Gameplay
BULLET_SPEED      = 900    # pixels/second
SHOOT_COOLDOWN    = 0.2    # seconds between shots (fire rate)
RELOAD_TIME       = 1.5    # seconds to auto-reload
PLAYER_MAX_AMMO   = 15     # shots per magazine

# Shield
SHIELD_DURATION   = 3.0    # seconds shield stays active
SHIELD_COOLDOWN   = 5.0    # seconds before shield can reactivate

# Enemies
ENEMY_BASE_SPEED  = 120    # pixels/second base speed
ENEMY_SPAWN_INTERVAL = 2.0 # base seconds between spawns

# Vision
SMOOTHING_ALPHA   = 0.35   # cursor smoothing (0.0=frozen, 1.0=raw/jittery)
GESTURE_CONFIRM_FRAMES = 3 # frames gesture must persist before activating

# Difficulty
DIFFICULTY_EVAL_INTERVAL = 10.0  # seconds between difficulty evaluations
```

---

## 🧠 Adaptive Difficulty

Every **10 seconds** the game silently evaluates your performance:

```
Accuracy > 70%  AND  damage taken < 10  →  Difficulty UP   (max level 10)
Accuracy < 40%                          →  Difficulty DOWN  (min level 1)
```

Difficulty affects:
- **Enemy speed** multiplier
- **Spawn rate** (enemies arrive faster)  
- **Music intensity** (ambient → medium → intense)
- **Enemy health** (future multi-HP modes)

---

## 🎵 Adaptive Music System

| Waves | Track |
|:---|:---|
| 1 – 3 | `ambient.wav` — slow, eerie drone |
| 4 – 7 | `medium.wav` — building tension |
| 8+    | `intense.wav` — full action mode |

Tracks crossfade over **1.2 seconds**. Shoot sounds include **random ±5% volume variation** and **stereo panning** based on cursor X position.

---

## 🔭 Roadmap / Ideas

- [ ] High score leaderboard with local persistence
- [ ] Power-up drops from elite enemies
- [ ] Multi-HP boss enemies with health bars
- [ ] Second player via second webcam
- [ ] Different weapon types unlockable by wave
- [ ] Post-game replay / heatmap of cursor movement
- [ ] Custom gesture binding UI

---

## 🤝 Contributing

Pull requests welcome! For major changes please open an issue first.

```bash
# Fork → Clone → Branch → Change → PR
git checkout -b feature/your-feature-name
git commit -m "✨ Add your feature"
git push origin feature/your-feature-name
```

---

## 📄 License

```
MIT License — free to use, modify, and distribute.
See LICENSE file for full text.
```

---

## 👤 Author

<div align="center">

**Atharva**

[![GitHub](https://img.shields.io/badge/GitHub-atharva081106-181717?style=for-the-badge&logo=github)](https://github.com/atharva081106)

*Built with Python, Pygame, MediaPipe, and a lot of hand-waving* 🤚

<br/>

⭐ **If you enjoyed this project, please give it a star!** ⭐

</div>
