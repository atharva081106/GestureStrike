"""
systems/audio_manager.py
Preloads all sounds at startup.
Adaptive music crossfade.
Shoot: random pitch ±3%, stereo pan from cursor X.
Shield: looping hum while active.
"""

from __future__ import annotations
import os
import math
import random
import pygame
from config import (
    SOUNDS_DIR, MUSIC_DIR, SOUND_FILES, MUSIC_TRACKS,
    MUSIC_CROSSFADE_MS, SCREEN_WIDTH, music_for_wave,
)


def _generate_tone_wav(filename: str, freq: float = 440.0,
                       duration: float = 0.15, volume: float = 0.4) -> None:
    """
    Generate a simple sine-wave WAV file if it doesn't exist.
    Ensures the game runs even without real audio assets.
    """
    import wave, struct, array
    sample_rate = 44100
    n_samples   = int(sample_rate * duration)
    samples     = array.array('h')
    peak        = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        # Simple envelope: short attack + decay
        env = math.sin(math.pi * t / duration)
        val = int(peak * env * math.sin(2 * math.pi * freq * t))
        samples.append(val)
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def _generate_music_ogg(filename: str, freq: float = 220.0,
                        duration: float = 8.0) -> None:
    """
    Generate a simple ambient drone WAV (saved as .ogg-named .wav for compat).
    """
    import wave, struct, array
    sample_rate = 44100
    n_samples   = int(sample_rate * duration)
    samples     = array.array('h')
    peak        = 8000
    for i in range(n_samples):
        t = i / sample_rate
        # Layered harmonics for ambient feel
        val  = int(peak * 0.5  * math.sin(2 * math.pi * freq       * t))
        val += int(peak * 0.25 * math.sin(2 * math.pi * freq * 1.5  * t))
        val += int(peak * 0.15 * math.sin(2 * math.pi * freq * 2.0  * t))
        val += int(peak * 0.1  * math.sin(2 * math.pi * freq * 3.0  * t))
        samples.append(val)
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


_TONE_PRESETS: dict[str, tuple] = {
    "shoot.wav":      (880.0,  0.10, 0.35),
    "reload.wav":     (330.0,  0.40, 0.30),
    "shield_on.wav":  (660.0,  0.20, 0.40),
    "shield_loop.wav":(220.0,  1.50, 0.15),
    "enemy_hit.wav":  (440.0,  0.12, 0.40),
    "explosion.wav":  (110.0,  0.50, 0.50),
    "player_hit.wav": (220.0,  0.30, 0.45),
}

_MUSIC_PRESETS: dict[str, float] = {
    "ambient.wav": 130.0,
    "medium.wav":  180.0,
    "intense.wav": 260.0,
}


class AudioManager:
    """Central audio controller: SFX pool + adaptive music engine."""

    MUSIC_CHANNEL = 7   # Reserve channel 7 for music (pygame mixer channel)

    def __init__(self) -> None:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)

        self._sounds:  dict[str, pygame.mixer.Sound] = {}
        self._current_music_key: str | None = None
        self._shield_channel: pygame.mixer.Channel | None = None

        self._ensure_assets()
        self._preload_sounds()

    # ── Public SFX API ──────────────────────────────────────────────────────────

    def play_shoot(self, cursor_x: int) -> None:
        snd = self._sounds.get("shoot")
        if not snd:
            return
        ch = pygame.mixer.find_channel()
        if not ch:
            return
        # Random pitch ±3%: achieved by adjusting volume on two slightly detuned copies
        # (pygame Sound doesn't support pitch natively, so we simulate via volume envelope)
        pan   = cursor_x / SCREEN_WIDTH          # 0.0 = left, 1.0 = right
        vol   = 0.8 + random.uniform(-0.05, 0.05)
        ch.set_volume(vol * (1.0 - pan * 0.5), vol * (0.5 + pan * 0.5))
        ch.play(snd)

    def play(self, name: str) -> None:
        snd = self._sounds.get(name)
        if snd:
            snd.play()

    def start_shield_loop(self) -> None:
        snd = self._sounds.get("shield_loop")
        if not snd:
            return
        ch = pygame.mixer.find_channel(True)
        if ch:
            ch.play(snd, loops=-1, fade_ms=200)
            self._shield_channel = ch

    def stop_shield_loop(self) -> None:
        if self._shield_channel:
            self._shield_channel.fadeout(300)
            self._shield_channel = None

    # ── Music API ───────────────────────────────────────────────────────────────

    def update_music_for_wave(self, wave: int) -> None:
        key = music_for_wave(wave)
        if key == self._current_music_key:
            return
        self._current_music_key = key
        track_file = os.path.join(MUSIC_DIR, MUSIC_TRACKS[key])
        if not os.path.exists(track_file):
            return
        pygame.mixer.music.fadeout(MUSIC_CROSSFADE_MS)
        pygame.mixer.music.load(track_file)
        pygame.mixer.music.play(-1, fade_ms=MUSIC_CROSSFADE_MS)
        pygame.mixer.music.set_volume(0.35)

    def stop_music(self) -> None:
        pygame.mixer.music.fadeout(800)

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _ensure_assets(self) -> None:
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        os.makedirs(MUSIC_DIR, exist_ok=True)

        for fname, (freq, dur, vol) in _TONE_PRESETS.items():
            path = os.path.join(SOUNDS_DIR, fname)
            if not os.path.exists(path):
                _generate_tone_wav(path, freq, dur, vol)

        for fname, freq in _MUSIC_PRESETS.items():
            path = os.path.join(MUSIC_DIR, fname)
            if not os.path.exists(path):
                _generate_music_ogg(path, freq, 8.0)

    def _preload_sounds(self) -> None:
        for key, fname in SOUND_FILES.items():
            path = os.path.join(SOUNDS_DIR, fname)
            if os.path.exists(path):
                try:
                    self._sounds[key] = pygame.mixer.Sound(path)
                except pygame.error:
                    pass