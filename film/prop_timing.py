"""Shared timing and cut continuity for a recurring scene prop."""


def prop_end(cue, end, fps, action):
    if action == 'still':
        return end
    settle = max(2, round(fps*.33))
    if action == 'pulse':
        settle += max(2, fps//4)
    return max(end, cue+settle)


def next_state(action, angle, visible, delta):
    if action == 'turn':
        angle = (angle+delta)%360
    if action in ('appear','vanish'):
        visible = action == 'appear'
    return angle, visible
