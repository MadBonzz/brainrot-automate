"""Render wide geography shots and cut them into the performance at exact camera boundaries."""

import json
import subprocess
import tempfile
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from . import ensemble_review

KINDS = [
    "serpent_streets",
    "canyon_town",
    "desert_queue",
    "balloon_fleet",
    "halo_city",
    "flooded_gym",
    "paper_districts",
    "red_border",
    "cell_tower",
    "dark_shop",
    "torch_detail",
    "endless_hall",
    "lift_square",
    "clock_town",
    "apartment_landing",
    "paper_detail",
    "phone_detail",
    "canyon_dusk",
    "balloon_departure",
]
HERE = Path(__file__).resolve().parent


def extract(shot, beat, frames, fps=30):
    """Remove the optional second-unit angle from the reusable actor take's cache identity."""
    views = []
    cameras = [dict(c) for c in shot["cameras"]]
    cuts = [round(c["start"] * (frames - 1)) for c in cameras] + [frames]
    for i, camera in enumerate(cameras):
        name = camera.pop("vista", "stage")
        text = camera.pop("vista_text", "")
        reactions = camera.pop("reactions", [])
        if reactions:
            if name != "stage" or len(reactions) != 1:
                raise ValueError(f"Choose one reaction or one location view at setup {beat}, camera {i + 1}.")
            available = cuts[i + 1] - cuts[i]
            # In a very short cut the original angle already carries the accent.
            if available >= round(fps * 1.30):
                length = min(round(fps * 1.45), round(available * 0.46))
                views.append(
                    dict(
                        beat=beat,
                        camera=i + 1,
                        kind="reaction",
                        **reactions[0],
                        start=cuts[i + 1] - length,
                        stop=cuts[i + 1],
                    )
                )
        if name == "stage":
            continue
        if name not in KINDS or cuts[i] >= cuts[i + 1]:
            raise ValueError(f"Invalid location view at setup {beat}, camera {i + 1}.")
        if len(text) > 72 or (name in ("paper_detail", "phone_detail") and not text.strip()):
            raise ValueError(
                f"Give the detail insert at setup {beat}, camera {i + 1} a short readable inscription."
            )
        views.append(
            {"beat": beat, "camera": i + 1, "kind": name, "text": text, "start": cuts[i], "stop": cuts[i + 1]}
        )
    return dict(shot, cameras=cameras), views


def run_blender(pieces, folder, blender, plan):
    folder.mkdir(parents=True, exist_ok=True)
    if not pieces:
        return
    with tempfile.TemporaryDirectory(dir=folder) as temp:
        job = Path(temp) / "views.json"
        data = {k: plan[k] for k in ("width", "height", "fps")}
        stage_views = [v for v in pieces if v["kind"] in ("reaction", "torch_detail")]
        if stage_views:
            data.update({k: plan[k] for k in ("assets", "looks", "places", "props", "motions")})
            data["takes"] = {
                str(v["beat"]): plan["shots"][v["beat"] - 1] for v in stage_views
            }
        entry = "torch_view.py" if any(v["kind"] == "torch_detail" for v in pieces) else "vista_render.py"
        job.write_text(json.dumps(dict(data, pieces=pieces)), encoding="utf8")
        with (folder / "location-views.log").open("a") as log:
            subprocess.run(
                [
                    blender,
                    "-b",
                    "-t",
                    "2",
                    "--factory-startup",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(HERE / entry),
                    "--",
                    str(job),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )


def boards(plan, folder, blender):
    pieces = []
    added = []
    for view in plan.get("vistas", []):
        shot = plan["shots"][view["beat"] - 1]
        f = shot["sample_frames"][view["camera"] - 1]
        if view["kind"] == "reaction":
            f = 1 + (view["start"] + view["stop"] - 1) // 2
            added.append((view["beat"], f))
        output = folder / f"setup-{view['beat']:03d}-{f}.png"
        pieces.append(dict(view, output=str(output), still=f - view["start"]))
    run_blender(pieces, folder, blender, plan)
    return added


def cut(base, views, frames, folder, ffmpeg, fps, probe, w, h):
    """Select original footage and native inserts by frame, including adjacent inserts."""
    source = Path(base)
    digest = sha256(json.dumps([source.name, views, frames, fps], sort_keys=True).encode()).hexdigest()[:16]
    target = folder / f"edit-{digest}.mp4"
    if ensemble_review.correct_clip(target, probe, w, h, fps, frames):
        return target
    pieces = []
    pos = 0
    for i, view in enumerate(views, 1):
        if pos < view["start"]:
            pieces.append((0, pos, view["start"]))
        pieces.append((i, 0, view["stop"] - view["start"]))
        pos = view["stop"]
    if pos < frames:
        pieces.append((0, pos, frames))
    inputs = [str(source), *(v["output"] for v in views)]
    args = [ffmpeg, "-v", "error", "-xerror", "-y", "-filter_complex_threads", "1"]
    for file in inputs:
        args.extend(["-threads", "1", "-i", file])
    filters = [
        f"[{i}:v]trim=start_frame={a}:end_frame={b},setpts=N/({fps}*TB)[p{j}]"
        for j, (i, a, b) in enumerate(pieces)
    ]
    filters.append("".join(f"[p{j}]" for j in range(len(pieces))) + f"concat=n={len(pieces)}:v=1:a=0[out]")
    with tempfile.TemporaryDirectory(dir=folder) as temp:
        movie = Path(temp) / "view.mp4"
        subprocess.run(
            [
                *args,
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[out]",
                "-an",
                "-r",
                str(fps),
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-threads",
                "2",
                "-preset",
                "veryfast",
                "-crf",
                "15",
                str(movie),
            ],
            check=True,
        )
        movie.replace(target)
    return target


def capture(plan, folder, root, blender, probe):
    folder.mkdir(parents=True, exist_ok=True)
    cache = root / "location-views"
    cache.mkdir(parents=True, exist_ok=True)
    version = sha256()
    for path in (HERE / "vista_render.py", HERE / "animate.py", HERE / "surface_art.py"):
        version.update(path.read_bytes())
    version.update(subprocess.check_output([blender, "--version"]).splitlines()[0])
    w, h, fps = (plan[k] for k in ("width", "height", "fps"))
    torch_version = sha256((HERE / "torch_view.py").read_bytes()).hexdigest() if any(
        v["kind"] == "torch_detail" for v in plan["vistas"]
    ) else None
    missing = {}
    by_beat = defaultdict(list)
    for view in plan["vistas"]:
        frames = view["stop"] - view["start"]
        identity = [version.hexdigest(), view["kind"], view.get("text", ""), frames, w, h, fps]
        if view["kind"] == "torch_detail":
            take = plan["shots"][view["beat"] - 1]
            identity.extend([Path(take["shared"]).stem, view["camera"], view["start"], torch_version])
        if view["kind"] == "reaction":
            take = plan["shots"][view["beat"] - 1]
            identity.extend(
                [
                    Path(take["shared"]).stem,
                    view["actor"],
                    view["action"],
                    view["start"],
                    plan["motions"][view["action"]],
                ]
            )
        key = sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        file = cache / (key + ".mp4")
        item = dict(view, output=str(file))
        if not ensemble_review.correct_clip(file, probe, w, h, fps, frames):
            missing[key] = item
        by_beat[view["beat"]].append(item)
    run_blender(list(missing.values()), folder, blender, plan)
    return by_beat


def apply(plan, dst, root, blender, ffmpeg, probe):
    if not plan.get("vistas"):
        return plan
    folder = dst / "location-views"
    by_beat = capture(plan, folder, root, blender, probe)
    w, h, fps = (plan[k] for k in ("width", "height", "fps"))
    shots = [dict(s) for s in plan["shots"]]
    for beat, views in by_beat.items():
        s = shots[beat - 1]
        cameras = list(s["shot"]["cameras"])
        for v in views:
            if v["kind"] == "reaction":
                camera = dict(
                    cameras[v["camera"] - 1],
                    start=v["start"] / (s["frames"] - 1),
                    focus=[v["actor"]],
                    move="punch",
                    size=2.06,
                    angle=27,
                    drift=0,
                )
                cameras.append(camera)
        s["shot"] = dict(s["shot"], cameras=sorted(cameras, key=lambda c: c["start"]))
        s["clip"] = str(cut(s["clip"], views, s["frames"], folder, ffmpeg, fps, probe, w, h))
        if not ensemble_review.correct_clip(Path(s["clip"]), probe, w, h, fps, s["frames"]):
            raise ValueError(f"Location view edit at setup {beat} has an incorrect frame count.")
    return dict(plan, shots=shots)
