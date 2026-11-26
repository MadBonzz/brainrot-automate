"""Timing in real seconds shared by the Blender director and tests."""

import math


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def performance_sample(elapsed, window, recipe, mode="accent"):
    """Window is the available screen time. Pose sheets use a 24 fps authoring clock."""
    if elapsed <= 0 or elapsed >= window:
        return 0.0, 0.0
    frames = recipe["frames"]
    if mode == "cycle" or recipe.get("loop") and mode == "accent":
        # Fit complete cycles, with each cycle near its authored running time.
        cycles = max(1, round(window * 24 / frames))
        phase = elapsed * cycles / window % 1
        # Older one-shot recipes may end in a held pose. Fade it out before restarting.
        return min(1.0, phase / 0.88) * frames, 1 - smooth((phase - 0.88) / 0.12)
    if mode == "sustain":
        peak = recipe.get("hold_frame", frames)
        attack = max(0.001, min(window * 0.65, peak / 24))
        release = min(0.18, window * 0.20)
        return min(1, elapsed / attack) * peak, 1 - smooth((elapsed - window + release) / release)
    duration = min(window, frames / 24 + 0.16)
    attack = max(0.001, duration - min(0.16, duration * 0.20))
    release_at = attack
    key = min(elapsed / attack, 1) * frames
    weight = 1 - smooth((elapsed - release_at) / (duration - attack))
    return key, weight


def camera_width(width, progress, move):
    if move == "punch":
        return width * (1 - 0.22 * smooth(progress / 0.28))
    if move == "reveal":
        return width * (0.69 + 0.31 * smooth(progress / 0.70))
    return width


def crowd_path(clock, lane, start, span):
    """A back-and-forth errand with a gradual turn at each end, continuous across cuts."""
    phase = clock * (0.47 + 0.035 * (lane % 3)) + 2.17 * lane
    return start + span * math.sin(phase), math.cos(phase)
