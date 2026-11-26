"""Compile an authored coverage sheet into a standard ensemble plan.

Each JSON setup specifies the lens order, people, gestures, props and narration.
Units are Blender stage units. An A token is an actor; a P token a practical.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from film import ensemble, planning


def vector(text):
    return [float(v) for v in text.split(",")]


def playback(action):
    if planning.MOTIONS[action].get("loop") or action in {
        "hand_over_hand_pull",
        "compare_two_weights",
        "polish_a_window",
        "sweep_the_floor",
        "turn_a_crank",
        "scan_the_horizon",
        "count_and_confirm",
        "play_a_trumpet",
    }:
        return "cycle"
    if action in {
        "hands_behind_the_back",
        "hands_on_hips",
        "quiet_please",
        "reach",
        "point",
        "look",
        "cover_ears",
        "recoil",
    }:
        return "sustain"
    return "accent"


def compile_sheet(sheet):
    cast = sheet["cast"]
    faces = sheet["looks"]
    if not cast or len(cast) != len(faces):
        raise ValueError("Supply a costume for each member of the cast.")
    lead = cast[0][0]
    people = [dict(id=i, job=job, want=want) for i, job, want in cast]
    looks = [
        dict(id=a[0], coat=l[0], skin=l[1], hair=l[2], hat=l[3], uniform=l[4], badge="", height=l[5])
        for a, l in zip(cast, faces, strict=True)
    ]
    for look in looks:
        look.update(sheet.get("wardrobe", {}).get(look["id"], {}))
    beats = []
    places = []
    props = []
    shots = []
    for n, row in enumerate(sheet["coverage"]):
        kit, blocking, objects, coverage, line = row
        style = kit.split("/")
        kit = style[0]
        light = style[1] if len(style) > 1 else "daylight"
        life = style[2] if len(style) > 2 else "quiet"
        place = f"set-{n + 1}"
        places.append(
            dict(
                id=place,
                kit=kit,
                light=light,
                life=life,
                finish=sheet.get("finish", "textured"),
                sign="",
                wall=sheet["palette"][0],
                trim=sheet["palette"][1],
            )
        )
        actors = []
        events = []
        local = []
        for j, token in enumerate(objects.split()):
            model, mark = token.split("@")
            design = model.split(":")
            kind = design[0]
            color = design[1] if len(design) > 1 and design[1] else sheet["palette"][1]
            scale = float(design[2]) if len(design) > 2 else 1.0
            text = design[3].replace("_", " ") if len(design) > 3 else ""
            name = f"p{n + 1}-{j + 1}"
            motion = mark.split(">")
            if len(motion) > 3:
                raise ValueError(f"Setup {n + 1}: a prop supports at most two sequential destinations.")
            at = vector(motion[0])
            local.append(name)
            props.append(
                dict(id=name, place=place, kind=kind, at=at, scale=scale, color=color, text=text, parts=[])
            )
            for k, dest in enumerate(motion[1:]):
                timing = (0.08, 0.65) if len(motion) == 2 else ((0.04, 0.42), (0.52, 0.90))[k]
                if dest.startswith("hand"):
                    anchor = cast[int(dest[4:])][0] + "@wrist1"
                    to = [0, -0.05, -0.14]
                else:
                    anchor = ""
                    to = vector(dest)
                events.append(
                    dict(id=name, anchor=anchor, to=to, text=text, spin=0, start=timing[0], end=timing[1])
                )
        # Marks are explicit when contacts and crossing paths matter. Defaults preserve screen direction.
        for j, token in enumerate(blocking.split()):
            spec, *mark = token.split("@")
            elements = spec.split(":")
            index = int(elements[0])
            if not 0 <= index < len(cast):
                raise ValueError(f"Setup {n + 1}: unknown actor {index}.")
            name = cast[index][0]
            actions = elements[1].split("+")
            mood = elements[2] if len(elements) > 2 else "calm"
            default = [[-1.02, -0.22], [1.27, 0.30], [-2.70, 1.0], [2.85, 1.20], [0.22, 2.08]]
            if mark:
                ends = mark[0].split(">")
                a = vector(ends[0])
                b = vector(ends[-1])
            else:
                a = b = default[j]
            facing = 16 if a[0] < 0 else -18
            cues = []
            for k, action in enumerate(actions):
                if action == "-":
                    continue
                if action not in planning.MOTIONS:
                    raise ValueError(f"Unknown performance {action}")
                start = (0.04 + 0.035 * (j % 3)) if k == 0 else 0.49 + 0.03 * (j % 3)
                finish = 0.49 if k == 0 and len(actions) > 1 else 0.98
                cues.append(dict(action=action, start=start, end=finish, play=playback(action)))
            actors.append(
                dict(
                    id=name,
                    at=a[:2],
                    to=b[:2],
                    start=0.07,
                    end=0.78,
                    facing=facing,
                    end_facing=facing,
                    mood=mood,
                    cues=cues,
                    look_at="",
                )
            )
            if actions == ["-"]:
                actors[-1]["pose"] = "frozen"
            for k, key in ((2, "lift"), (3, "pitch")):
                if len(a) > k or len(b) > k:
                    actors[-1][key] = [a[k] if len(a) > k else 0, b[k] if len(b) > k else 0]
        ids = [a["id"] for a in actors]

        def resolve(token):
            if len(token) < 2 or not token[1:].isdigit():
                raise ValueError(f"Setup {n + 1}: invalid coverage target {token}.")
            if token[0] in {"P", "A"} and int(token[1:]) >= (len(local) if token[0] == "P" else len(cast)):
                raise ValueError(f"Setup {n + 1}: missing coverage target {token}.")
            if token[0] == "P":
                return local[int(token[1:])]
            if token[0] == "A":
                return cast[int(token[1:])][0]
            raise ValueError("Unknown coverage target " + token)

        for j, a in enumerate(actors):
            a["look_at"] = local[0] if local else (ids[(j + 1) % len(ids)] if len(ids) > 1 else "")
        cams = []
        for item in coverage.split():
            when, focus, lens, move, angle, elevation = item.split(":")
            targets = ids if focus == "W" else [resolve(i) for i in focus.split("+")]
            cams.append(
                dict(
                    start=float(when),
                    focus=targets,
                    size=float(lens),
                    angle=float(angle),
                    elevation=float(elevation),
                    drift=13 if move == "arc" else 0,
                    move=move,
                )
            )
        for j, person in enumerate(actors):
            if person.get("pose") == "frozen":
                continue
            if len(person["cues"]) == 1 and person["cues"][0]["play"] == "accent":
                # Start the full gesture just before its first featured camera, including the recovery.
                hero = next((c["start"] for c in cams if c["focus"] == [person["id"]]), 0)
                if hero:
                    person["cues"][0]["start"] = max(0.035, min(0.82, hero - 0.09))
            glances = []
            previous = person["look_at"]
            for cam in cams[1:]:
                others = [target for target in cam["focus"] if target != person["id"]]
                if others and others[0] != previous:
                    previous = others[0]
                    glances.append(dict(at=min(0.98, cam["start"] + 0.014 * j), focus=previous))
            if glances:
                person["gaze"] = glances
        role = "rule" if n == 0 else "callback" if n == len(sheet["coverage"]) - 1 else "custom"
        beats.append(dict(role=role, because=n, witness=ids[0], visible=coverage, line=line))
        shots.append(
            dict(
                place=place,
                transition="cutaway",
                sync=sheet.get("anchors", {}).get(str(n + 1), []),
                sounds=sheet.get("sounds", {}).get(str(n + 1), []),
                actors=actors,
                events=events,
                cameras=cams,
            )
        )
        if len(style) > 4:
            shots[-1]["selective_color"] = [resolve(t) for t in style[4].partition("=")[2].split(",") if t]
        if len(style) > 3 and style[3] != "none":
            shots[-1]["atmosphere"] = dict(kind=style[3], start=0.05, end=0.94)
    story = dict(
        title=sheet["title"],
        seconds=sheet["seconds"],
        lead=lead,
        rule=sheet["rule"],
        loophole=sheet["turn"],
        cost=sheet["ending"],
        cast=people,
        beats=beats,
        source_cut=sheet["source"],
    )
    direction = dict(looks=looks, places=places, props=props, shots=shots)
    planning.check(story, ensemble.saved_story_schema(story))
    planning.check(direction, ensemble.DIRECTION)
    ensemble.check_story(story)
    ensemble.check_direction(direction, story)
    return story, direction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sheet", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    story, direction = compile_sheet(json.loads(args.sheet.read_text(encoding="utf8")))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in [("story", story), ("direction", direction)]:
        planning.save(args.out / (name + ".json"), data)


if __name__ == "__main__":
    main()
