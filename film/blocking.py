"""Resolve a performer's entrance or exit against the other people in a shot."""

from copy import deepcopy
from math import cos, dist, radians, sin

SIDES = {"left": (-1, 0), "right": (1, 0), "front": (0, -1), "back": (0, 1)}


def position(actor, t):
    x = max(0, min(1, (t - actor["start"]) / max(0.00001, actor["end"] - actor["start"])))
    u = x * x * (3 - 2 * x)
    return [a + (b - a) * u for a, b in zip(actor["at"], actor["to"])]


def sample_times(actor):
    start, end = actor["start"], actor["end"]
    return {start + (end - start) * i / 24 for i in range(25)}


def resolve(shot, heights):
    if not any("travel" in actor for actor in shot["actors"]):
        return shot
    shot = deepcopy(shot)
    tracked = {}
    for actor in shot["actors"]:
        cue = actor.pop("travel", None)
        if not cue or cue["kind"] == "as_blocked":
            continue
        distance = cue["distance"]
        if cue["side"] not in SIDES or not 0.2 <= distance <= 12:
            raise ValueError("Specify a travel distance of 0.2–12 stage units from a named side.")
        if actor["at"] != actor["to"] or actor.get("pose") == "frozen":
            raise ValueError("An entrance or exit needs a live actor with one marked position.")
        move_start = cue["kind"] == "enter"
        if not move_start and cue["kind"] != "exit":
            raise ValueError("Choose enter or exit for an actor's travel.")
        mark = actor["to"] if move_start else actor["at"]
        field = "at" if move_start else "to"
        dx, dy = SIDES[cue["side"]]
        # Keep the requested side and the contact mark. Bend the lane if a bystander blocks it.
        others = [other for other in shot["actors"] if other is not actor]
        ticks = {0.0, 1.0, *sample_times(actor)}
        ticks.update(t for other in others for t in sample_times(other))
        if any(person["id"] not in heights for person in shot["actors"]):
            raise ValueError("Give every walking performer and bystander a known cast ID.")
        for angle in (0, 24, -24, 44, -44):
            rad = radians(angle)
            actor[field] = [
                round(mark[0] + distance * (dx * cos(rad) - dy * sin(rad)), 3),
                round(mark[1] + distance * (dx * sin(rad) + dy * cos(rad)), 3),
            ]
            if all(
                dist(position(actor, t), position(other, t))
                >= 0.56 * min(heights[actor["id"]], heights[other["id"]])
                for other in others
                for t in ticks
            ):
                break
        else:
            raise ValueError(
                f"No clear {cue['side']} lane for {actor['id']}. Change its approach or marked position."
            )
        if cue.get("coverage") == "follow":
            cameras = shot["cameras"]
            options = []
            for i, camera in enumerate(cameras):
                if camera.get("vista", "stage") != "stage" or camera.get("reactions"):
                    continue
                until = cameras[i + 1]["start"] if i + 1 < len(cameras) else 1.0
                overlap = min(actor["end"], until) - max(actor["start"], camera["start"])
                if overlap > 0:
                    options.append((overlap, i))
            if options:
                _, angle = max(options)
                tracked.setdefault(angle, []).append(actor["id"])
    for index, ids in tracked.items():
        camera = shot["cameras"][index]
        camera.update(focus=ids, size=max(camera["size"], 3.2 if len(ids) == 1 else 3.9), move="follow")
    return shot


def expand(direction):
    heights = {look["id"]: look["height"] for look in direction["looks"]}
    shots = [resolve(shot, heights) for shot in direction["shots"]]
    return dict(direction, shots=shots)
