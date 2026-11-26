"""Measure the native animation before captions and verify the delivered MP4."""

from fractions import Fraction
from itertools import groupby
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
    result = audit(json.loads((out / "timeline.json").read_text(encoding="utf8")), out / "movie.mp4")
    planning.save(out / "render-review.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "setups"}, indent=2))
