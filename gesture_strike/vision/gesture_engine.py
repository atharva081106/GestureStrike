"""
vision/gesture_engine.py

GESTURES:
  🖐 Open palm (all 4 fingers extended)  -> SHOOT  (held = continuous fire)
  ✊ Closed fist / any non-open pose     -> STOP firing
  ✊ Full fist held                       -> SHIELD

  TWO-HAND MODE:
    One hand open palm  -> SHOOT + cursor follows that hand's index tip
    Both hands detected -> cursor follows right-side hand, either open = shoot

  No RELOAD gesture — reload is automatic.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Optional, List
from config import GESTURE_CONFIRM_FRAMES


class Gesture(Enum):
    NONE   = auto()
    AIM    = auto()     # index pointing (cursor moves, no fire)
    SHOOT  = auto()     # open palm → fire continuously
    SHIELD = auto()     # fist → activate shield


WRIST     = 0
INDEX_PIP = 6;  INDEX_TIP  = 8
MIDDLE_PIP= 10; MIDDLE_TIP = 12
RING_PIP  = 14; RING_TIP   = 16
PINKY_PIP = 18; PINKY_TIP  = 20


def _up(lm, tip, pip) -> bool:
    return lm[tip][1] < lm[pip][1]


def classify_landmarks(lm: list) -> Gesture:
    i = _up(lm, INDEX_TIP,  INDEX_PIP)
    m = _up(lm, MIDDLE_TIP, MIDDLE_PIP)
    r = _up(lm, RING_TIP,   RING_PIP)
    p = _up(lm, PINKY_TIP,  PINKY_PIP)

    # Open palm = all 4 fingers up → SHOOT
    if i and m and r and p:
        return Gesture.SHOOT

    # Full fist = all folded → SHIELD
    if not i and not m and not r and not p:
        return Gesture.SHIELD

    # Index only → AIM (cursor, no fire)
    if i and not m and not r and not p:
        return Gesture.AIM

    return Gesture.NONE


class _ConfirmEngine:
    def __init__(self):
        self._cand  = Gesture.NONE
        self._count = 0
        self._conf  = Gesture.NONE

    def update(self, lm: Optional[list]) -> Gesture:
        if lm is None:
            self._cand, self._count, self._conf = Gesture.NONE, 0, Gesture.NONE
            return self._conf
        raw = classify_landmarks(lm)
        if raw == self._cand:
            self._count += 1
        else:
            self._cand, self._count = raw, 1
        if self._count >= GESTURE_CONFIRM_FRAMES:
            self._conf = self._cand
        return self._conf

    @property
    def confirmed(self): return self._conf


GestureEngine = _ConfirmEngine


class GestureEngine2H:
    """
    Two-hand engine.
    Cursor follows whichever hand is aiming / shooting.
    Open palm on either hand = SHOOT.
    Fist = SHIELD.
    """

    def __init__(self):
        self._eng  = [_ConfirmEngine(), _ConfirmEngine()]
        self.confirmed: Gesture            = Gesture.NONE
        self.aim_lm: Optional[List[tuple]] = None

    def update(self,
               landmarks_list: List[Optional[List[tuple]]]
               ) -> tuple[Gesture, Optional[List[tuple]]]:

        live = [(i, lm) for i, lm in enumerate(landmarks_list) if lm is not None]

        present = {i for i, _ in live}
        for i in range(2):
            if i not in present:
                self._eng[i].update(None)

        if not live:
            self.confirmed, self.aim_lm = Gesture.NONE, None
            return self.confirmed, self.aim_lm

        if len(live) == 1:
            idx, lm = live[0]
            g = self._eng[idx].update(lm)
            self.confirmed, self.aim_lm = g, lm
            return self.confirmed, self.aim_lm

        # Two hands
        (i0, lm0), (i1, lm1) = live
        g0 = self._eng[i0].update(lm0)
        g1 = self._eng[i1].update(lm1)

        # Right-side hand (larger wrist.x) drives cursor
        if lm0[WRIST][0] >= lm1[WRIST][0]:
            aim_lm = lm0
        else:
            aim_lm = lm1

        # Either hand open = shoot
        if g0 == Gesture.SHOOT or g1 == Gesture.SHOOT:
            self.confirmed, self.aim_lm = Gesture.SHOOT, aim_lm
            return self.confirmed, self.aim_lm

        # Either hand fist = shield
        if g0 == Gesture.SHIELD or g1 == Gesture.SHIELD:
            self.confirmed, self.aim_lm = Gesture.SHIELD, aim_lm
            return self.confirmed, self.aim_lm

        self.confirmed = g0 if g0 != Gesture.NONE else g1
        self.aim_lm    = aim_lm
        return self.confirmed, aim_lm