"""
vision/hand_tracker.py
Tracks up to TWO hands using MediaPipe 0.10+ Tasks API (or legacy <0.10).
Returns a list of up to 2 HandData objects ordered by wrist X position.
"""

from __future__ import annotations
import cv2
from dataclasses import dataclass
from typing import Optional, List
import mediapipe as mp

_USE_TASKS = not hasattr(mp, "solutions")

if _USE_TASKS:
    from mediapipe.tasks import python as _mpt
    from mediapipe.tasks.python import vision as _mpv
    import os, urllib.request
    _MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

    def _ensure_model():
        if not os.path.exists(_MODEL):
            url = ("https://storage.googleapis.com/mediapipe-models/"
                   "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
            print("[HandTracker] Downloading model (~8 MB):", url)
            urllib.request.urlretrieve(url, _MODEL)
            print("[HandTracker] Saved to:", _MODEL)
else:
    _mp_hands = mp.solutions.hands


@dataclass
class HandData:
    landmarks: List[tuple]   # 21 (x,y,z) normalised
    handedness: str          # "Left" or "Right"


class HandTracker:
    """
    Pull model — call .update() each frame, read .hands (list of up to 2 HandData).
    Supports MediaPipe 0.10+ Tasks API and legacy <0.10 API.
    """

    def __init__(self, camera_index: int = 0,
                 max_hands: int = 2,
                 det_conf: float = 0.7,
                 track_conf: float = 0.6):

        self._cap = cv2.VideoCapture(camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        self._hands_data: List[HandData] = []
        self._latest_frame = None          # BGR numpy frame for overlay
        self._legacy = not _USE_TASKS

        if _USE_TASKS:
            _ensure_model()
            base = _mpt.BaseOptions(model_asset_path=_MODEL)
            opts = _mpv.HandLandmarkerOptions(
                base_options=base,
                running_mode=_mpv.RunningMode.VIDEO,
                num_hands=max_hands,
                min_hand_detection_confidence=det_conf,
                min_hand_presence_confidence=det_conf,
                min_tracking_confidence=track_conf,
            )
            self._landmarker = _mpv.HandLandmarker.create_from_options(opts)
            self._ts_ms: int = 0
        else:
            self._mp_hands = _mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=det_conf,
                min_tracking_confidence=track_conf,
            )

    def update(self) -> None:
        ret, frame = self._cap.read()
        if not ret:
            self._hands_data = []
            self._latest_frame = None
            return
        frame = cv2.flip(frame, 1)
        self._latest_frame = frame          # store for webcam overlay
        if self._legacy:
            self._update_legacy(frame)
        else:
            self._update_tasks(frame)

    def _update_legacy(self, frame) -> None:
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = self._mp_hands.process(rgb)
        out = []
        if res.multi_hand_landmarks and res.multi_handedness:
            for lm_obj, h_obj in zip(res.multi_hand_landmarks, res.multi_handedness):
                lm = [(l.x, l.y, l.z) for l in lm_obj.landmark]
                out.append(HandData(lm, h_obj.classification[0].label))
        self._hands_data = out

    def _update_tasks(self, frame) -> None:
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._ts_ms += 33
        res = self._landmarker.detect_for_video(img, self._ts_ms)
        out = []
        if res.hand_landmarks and res.handedness:
            for lm_list, h_list in zip(res.hand_landmarks, res.handedness):
                lm = [(l.x, l.y, l.z) for l in lm_list]
                out.append(HandData(lm, h_list[0].display_name))
        self._hands_data = out

    @property
    def hands(self) -> List[HandData]:
        return self._hands_data

    @property
    def hand(self) -> Optional[HandData]:
        """First hand (backwards compat)."""
        return self._hands_data[0] if self._hands_data else None

    @property
    def is_hand_detected(self) -> bool:
        return len(self._hands_data) > 0

    def get_frame_surface(self, width: int = 200) -> "pygame.Surface | None":
        """
        Returns the latest webcam frame as a pygame Surface scaled to `width` px wide.
        Returns None if no frame is available yet.
        """
        if self._latest_frame is None:
            return None
        import cv2 as _cv2
        import pygame as _pg
        frame = self._latest_frame
        h, w  = frame.shape[:2]
        new_h = int(h * width / w)
        small = _cv2.resize(frame, (width, new_h), interpolation=_cv2.INTER_LINEAR)
        rgb   = _cv2.cvtColor(small, _cv2.COLOR_BGR2RGB)
        # pygame wants (width, height, 3) with contiguous memory
        rgb   = rgb.transpose(1, 0, 2).copy()   # swap axes for pygame
        surf  = _pg.surfarray.make_surface(rgb)
        return surf

    def release(self) -> None:
        self._cap.release()
        if self._legacy:
            self._mp_hands.close()
        else:
            self._landmarker.close()

    def __del__(self):
        try: self.release()
        except: pass