"""Compare two edits using the same image-change detector. Accepts local media files."""

import argparse
import json
import math
import statistics
import subprocess
from pathlib import Path

SAMPLE_FPS = 8
FRAME_BYTES = 32 * 46 * 3


def change_summary(differences, frames, sample_fps=SAMPLE_FPS):
    """Find isolated large changes. Slow action and similar-color camera cuts can be missed."""
    peaks = []
    for i, value in enumerate(differences):
        neighbors = differences[max(0, i - 2) : i + 3]
        time = (i + 1) / sample_fps
        if value > 0.19 and value == max(neighbors) and (not peaks or time - peaks[-1] > 0.45):
            peaks.append(time)
    duration = frames / sample_fps
    excluded = {j for t in peaks for j in range(round(t * sample_fps) - 2, round(t * sample_fps) + 2)}
    quiet = [v for i, v in enumerate(differences) if i not in excluded]
    return {
        "sampled_seconds": round(duration, 2),
        "large_changes": len(peaks),
        "large_changes_per_minute": round(len(peaks) * 60 / duration, 1),
        "median_gap_between_large_changes": round(
            statistics.median(b - a for a, b in zip(peaks, peaks[1:])), 2
        )
        if len(peaks) >= 2
        else None,
        "median_other_pixel_change_percent": round(statistics.median(quiet) * 100, 2) if quiet else None,
        "first_15s_changes": [t for t in peaks if t < 15],
    }


def measure(file, offset=0, seconds=None, rate=1, ffmpeg="ffmpeg"):
    if offset < 0 or not math.isfinite(offset) or rate <= 0 or not math.isfinite(rate):
        raise ValueError("Use a nonnegative offset and a positive source rate.")
    args = [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-threads", "1", "-ss", str(offset)]
    if seconds is not None:
        if seconds <= 0 or not math.isfinite(seconds):
            raise ValueError("Source seconds must be positive.")
        args.extend(["-t", str(seconds * rate)])
    # Upper center avoids the usual lower caption band and the edges of reposts.
    filters = (
        f"setpts=(PTS-STARTPTS)/{rate},fps={SAMPLE_FPS},scale=40:68:flags=area,crop=32:46:4:4,format=rgb24"
    )
    args.extend(
        ["-i", str(file), "-map", "0:v:0", "-an", "-vf", filters, "-threads", "1", "-f", "rawvideo", "-"]
    )
    deltas = []
    with subprocess.Popen(args, stdout=subprocess.PIPE) as proc:
        previous = proc.stdout.read(FRAME_BYTES)
        if len(previous) != FRAME_BYTES:
            raise ValueError(f"Could not decode a frame from {file} at {offset}s.")
        while frame := proc.stdout.read(FRAME_BYTES):
            if len(frame) != FRAME_BYTES:
                raise ValueError(f"Incomplete frame in {file}")
            deltas.append(sum(abs(a - b) for a, b in zip(frame, previous)) / (255 * FRAME_BYTES))
            previous = frame
        if proc.wait():
            raise subprocess.CalledProcessError(proc.returncode, args)
    return change_summary(deltas, len(deltas) + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("remake", type=Path)
    parser.add_argument("--source-offset", type=float, default=0, help="Seconds into a longer source file")
    parser.add_argument("--source-seconds", type=float, help="Duration on the original storytelling clock")
    parser.add_argument("--source-rate", type=float, default=1, help="Media seconds per original second")
    args = parser.parse_args()
    result = {
        "source": measure(args.source, args.source_offset, args.source_seconds, args.source_rate),
        "remake": measure(args.remake),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
