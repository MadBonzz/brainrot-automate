"""Measure the native animation before captions and verify the delivered MP4."""

from fractions import Fraction
from itertools import groupby, combinations
from math import dist
from statistics import median
import json
from pathlib import Path
import subprocess
from . import planning


def video_info(file, probe):
    result = subprocess.run(
        [
            probe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,avg_frame_rate,nb_frames,width,height,duration",
            "-of",
            "json",
            str(file),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    streams = json.loads(result.stdout)["streams"]
    return next(s for s in streams if s["codec_type"] == "video"), streams


def correct_clip(file, probe, w, h, fps, frames):
    if not file.is_file():
        return False
    try:
        stream, _ = video_info(file, probe)
        return (
            stream["width"],
            stream["height"],
            Fraction(stream["avg_frame_rate"]),
            int(stream["nb_frames"]),
        ) == (w, h, fps, frames)
    except (ValueError, KeyError, StopIteration, subprocess.CalledProcessError):
        return False


def directing_stats(timeline):
    """Exact editorial timing plus advisory overlap checks for reviewing the boards."""
    fps = timeline["fps"]
    durations = []
    opening = []
    overlaps = []
    modes = set()
    busiest = 0
    moving = []
    untracked = []
    for i, s in enumerate(timeline["shots"], 1):
        shot = s["shot"]
        starts = [round(c["start"] * (s["frames"] - 1)) for c in shot["cameras"]]
        for f, g, c in zip(starts, starts[1:] + [s["frames"]], shot["cameras"]):
            durations.append((g - f) / fps)
            if s["clock"] + f / fps < 15:
                opening.append(round(s["clock"] + f / fps, 2))
            modes.add(c.get("move", "arc" if c["drift"] else "follow"))
        busiest = max(busiest, len(shot["actors"]))
        travel = []
        for actor in shot["actors"]:
            lower, upper = actor.get("lift", (0, 0))
            if dist(actor["at"], actor["to"]) >= 0.35 or abs(upper - lower) >= 0.35:
                travel.append(actor["id"])
                framed = any(
                    actor["id"] in camera["focus"]
                    and min(actor["end"], end / s["frames"]) > max(actor["start"], start / s["frames"])
                    for camera, start, end in zip(shot["cameras"], starts, starts[1:] + [s["frames"]])
                )
                if not framed:
                    untracked.append(dict(setup=i, actor=actor["id"]))
        if travel:
            moving.append(dict(setup=i, actors=travel))

        def position(actor, t):
            u = max(0, min(1, (t - actor["start"]) / (actor["end"] - actor["start"])))
            u = u * u * (3 - 2 * u)
            return [x + u * (y - x) for x, y in zip(actor["at"], actor["to"])]

        for a, b in combinations(shot["actors"], 2):
            scale = min(timeline["looks"][actor["id"]]["height"] for actor in (a, b))
            distances = [dist(position(a, k / 24), position(b, k / 24)) for k in range(25)]
            # A sustained overlap of the torsos warrants a look even if a hug was intentional.
            flags = [d < 0.48 * scale for d in distances]
            longest = max((sum(1 for _ in group) for value, group in groupby(flags) if value), default=0)
            if longest >= 4:
                overlaps.append(
                    dict(setup=i, actors=[a["id"], b["id"]], min_distance=round(min(distances), 2))
                )
    return dict(
        median_shot_seconds=round(median(durations), 2),
        longest_shot_seconds=round(max(durations), 2),
        opening_15s_shot_starts=opening,
        camera_moves=sorted(modes),
        peak_named_actors=busiest,
        sustained_actor_overlaps=overlaps,
        setups_with_actor_travel=moving,
        travel_without_named_camera_target=untracked,
    )


def audit(timeline, movie, ffmpeg="ffmpeg", ffprobe="ffprobe"):
    report = []
    total = 0
    for index, s in enumerate(timeline["shots"], 1):
        clip = Path(s["clip"])
        # Downsample the actual undecorated video; text animation and music cannot pass this check.
        result = subprocess.check_output(
            [
                ffmpeg,
                "-v",
                "error",
                "-xerror",
                "-threads",
                "2",
                "-i",
                str(clip),
                "-an",
                "-vf",
                "scale=96:170:flags=area,format=gray",
                "-f",
                "framemd5",
                "-",
            ],
            text=True,
        )
        digests = [
            line.rsplit(",", 1)[-1].strip()
            for line in result.splitlines()
            if line and not line.startswith("#")
        ]
        if len(digests) != s["frames"]:
            raise ValueError(f"Setup {index} decoded {len(digests)} frames; expected {s['frames']}.")
        runs = [sum(1 for _ in run) for _, run in groupby(digests)]
        report.append(
            dict(
                setup=index,
                frames=len(digests),
                camera_shots=len(s["shot"]["cameras"]),
                equal_adjacent_frames=len(digests) - len(runs),
                longest_identical_run=max(runs),
            )
        )
        total += len(digests)
    stream, streams = video_info(movie, ffprobe)
    if not correct_clip(movie, ffprobe, timeline["width"], timeline["height"], timeline["fps"], total):
        raise ValueError("The muxed output does not match the planned dimensions, cadence or frame count.")
    soundtrack = next(s for s in streams if s["codec_type"] == "audio")
    if abs(float(soundtrack["duration"]) - total / timeline["fps"]) > 1 / timeline["fps"]:
        raise ValueError("Audio and image durations diverge by more than one frame.")
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-xerror",
            "-threads",
            "2",
            "-i",
            str(movie),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ],
        check=True,
    )
    return dict(
        direction=directing_stats(timeline),
        location_views=sum(v["kind"] != "reaction" for v in timeline.get("vistas", [])),
        reaction_angles=sum(v["kind"] == "reaction" for v in timeline.get("vistas", [])),
        spoken_pickups=timeline.get("pickup_count", 0),
        frames=total,
        fps=timeline["fps"],
        width=stream["width"],
        height=stream["height"],
        seconds=total / timeline["fps"],
        video=stream["codec_name"],
        audio=soundtrack["codec_name"],
        camera_shots=sum(x["camera_shots"] for x in report),
        cast=len(timeline["looks"]),
        equal_adjacent_frames=sum(x["equal_adjacent_frames"] for x in report),
        longest_identical_run=max(x["longest_identical_run"] for x in report),
        setups=report,
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("quality_folder", type=Path)
    out = ap.parse_args().quality_folder
    edit = out / "picture-edit.json"
    if not edit.exists():
        edit = out / "timeline.json"
    result = audit(json.loads(edit.read_text(encoding="utf8")), out / "movie.mp4")
    planning.save(out / "render-review.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "setups"}, indent=2))
