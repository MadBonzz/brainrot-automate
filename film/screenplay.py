"""Cut a narrated film to a linear sequence of observable events.

Every line is recorded once. Its recording sets the duration of its picture.
A cut can select an interval of an existing uncaptioned Blender take or use
a new take with individually choreographed actors, props, and cameras.
"""

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from . import audio, ensemble_review, planning

HERE = Path(__file__).resolve().parent
FPS = 30


def check(lines):
    if not lines:
        raise ValueError("A screenplay needs at least one spoken event.")
    planning.check_narration((line["id"], line["say"]) for line in lines)
    ids = set()
    for line in lines:
        if line["id"] in ids or not line["id"] or not line["evidence"].strip():
            raise ValueError("Give each line a unique ID and a visible event to review.")
        ids.add(line["id"])
        if not line.get("shots"):
            raise ValueError(f"Missing picture for {line['id']}")


def native_source(selection, timeline, quality):
    index = selection["beat"]
    if not isinstance(index, int) or not 1 <= index <= len(timeline["shots"]):
        raise ValueError(f"Take {index} does not exist")
    take = timeline["shots"][index - 1]
    clip = Path(take["clip"])
    if not clip.is_file():
        clip = (
            quality / "shots" / clip.name
            if clip.parent.name == "shots"
            else quality / "location-views" / clip.name
        )
    if not clip.is_file():
        raise FileNotFoundError(f"Render the original plan before editing its take {selection['beat']}.")
    return clip, take["frames"]


def available_footage(quality, selections):
    timeline_path = quality / "timeline.json"
    if not timeline_path.is_file():
        return False
    edit_path = quality / "picture-edit.json"
    timeline = json.loads((edit_path if edit_path.is_file() else timeline_path).read_text(encoding="utf8"))
    if any(not Path(a["path"]).is_file() for a in timeline.get("assets", {}).values()):
        return False
    try:
        for selection in selections:
            native_source(selection, timeline, quality)
    except FileNotFoundError:
        return False
    return True


def take_file(folder, name):
    path = (folder / name).resolve()
    if not path.is_relative_to(folder.resolve()) or path.suffix != ".json":
        raise ValueError("A staged take must be a JSON file inside the screenplay folder")
    return path


def save_plan(source, folder):
    """Keep a job's screenplay and the local JSON files its staged shots depend on."""
    spec = json.loads(source.read_text(encoding="utf8"))
    check(spec["lines"])
    folder.mkdir(parents=True, exist_ok=True)
    paths = {shot["take"] for line in spec["lines"] for shot in line["shots"] if "take" in shot}
    for name in list(paths):
        part = json.loads(take_file(source.parent, name).read_text(encoding="utf8"))
        if part.get("objects_from"):
            paths.add(part["objects_from"])
    for name in sorted(paths):
        published = take_file(folder, name)
        published.parent.mkdir(parents=True, exist_ok=True)
        src = take_file(source.parent, name)
        if src != published:
            shutil.copyfile(src, published)
    saved = folder / "screenplay.json"
    if source.resolve() != saved.resolve():
        planning.save(saved, spec)
    return saved


def read_take(folder, name):
    scene = json.loads(take_file(folder, name).read_text(encoding="utf8"))
    common = scene.pop("objects_from", None)
    if common is not None:
        shared = json.loads(take_file(folder, common).read_text(encoding="utf8"))
        scene["objects"] = shared["objects"] + scene["objects"]
    return scene


def picture_filter(finish, width, height):
    if finish == "gray_with_red":
        return "colorhold=color=0xbd5051:similarity=0.14:blend=0.065"
    if not re.fullmatch(r"sky:[a-fA-F0-9]{6}", finish):
        raise ValueError(f"Unknown picture treatment: {finish}")
    red, green, blue = (int(finish[i : i + 2], 16) for i in (4, 6, 8))
    # Workbench can encode unoccupied background as nearly black. Replace only the
    # region touching a screen edge, preserving disconnected dark clothes or props.
    filters = [
        "format=gbrp",
        "lutrgb=r='if(lt(val,13),0,val)':g='if(lt(val,13),0,val)':b='if(lt(val,13),0,val)'",
    ]
    points = [(round((width - 1) * f), 1) for f in (0.002, 0.20, 0.40, 0.60, 0.80, 0.998)]
    points.extend([(1, height // 6), (width - 2, height // 6), (1, height // 3), (width - 2, height // 3)])
    for x, y in points:
        filters.append(f"floodfill=x={x}:y={y}:s0=0:s1=0:s2=0:d0={green}:d1={blue}:d2={red}")
    return ",".join(filters)


def speech_time_map(scene, line, marks, lead, offset, length, fps):
    from bisect import bisect_right
    from .ensemble import phrase_starts, tokens

    old_end = (scene["frames"] - 1) / fps
    new_end = (length - 1) / fps
    anchors = scene.pop("speech_cues", [])
    if not anchors:
        factor = (length - 1) / max(1, scene["frames"] - 1)
        return lambda t: t * factor
    source = [0.0]
    target = [0.0]
    word_times = [t for word, t in marks for _ in tokens(word)]
    cues = [{"at": a["time"] / old_end, "words": a["words"]} for a in anchors]
    for anchor, idx in zip(anchors, phrase_starts(line, cues)):
        at = lead + word_times[idx] - offset / fps + anchor.get("nudge", 0)
        if not target[-1] < at < new_end:
            raise ValueError(f"Spoken cue falls outside its shot: {anchor['words']}")
        source.append(anchor["time"])
        target.append(at)
    source.append(old_end)
    target.append(new_end)

    def remap(t):
        t = max(0.0, min(t, old_end))
        idx = min(len(source) - 2, bisect_right(source, t) - 1)
        u = (t - source[idx]) / (source[idx + 1] - source[idx])
        return target[idx] + u * (target[idx + 1] - target[idx])

    return remap


def render(plan_file, quality, output, assets, ffmpeg="ffmpeg", blender="blender"):
    spec = json.loads(plan_file.read_text(encoding="utf8"))
    check(spec["lines"])
    timeline = json.loads((quality / "timeline.json").read_text(encoding="utf8"))
    edit_path = quality / "picture-edit.json"
    picture = json.loads(edit_path.read_text(encoding="utf8")) if edit_path.exists() else timeline
    output.mkdir(parents=True, exist_ok=True)
    (output / "shots").mkdir(exist_ok=True)
    ffmpeg = shutil.which(ffmpeg) or ffmpeg
    probe = str(Path(ffmpeg).with_name("ffprobe" + Path(ffmpeg).suffix))
    fps, width, height = (timeline[k] for k in ("fps", "width", "height"))
    if fps != FPS:
        raise ValueError("Screenplays currently use a 30-frame editing timeline")
    speech = array("h")
    captions, manifest, cuts = [], [], []
    frame = 0
    recipe = {k: timeline[k] for k in ("looks", "places", "assets", "width", "height", "fps")}
    from .screening import dialogue_check, movie_hash, review_page

    with tempfile.TemporaryDirectory(dir=output) as temp:
        staging = Path(temp)
        for line in spec["lines"]:
            raw, marks = audio.narration(line["say"], output, ffmpeg, assets)
            if any(
                "take" in selection and "speech_cues" in read_take(plan_file.parent, selection["take"])
                for selection in line["shots"]
            ):
                from .flite_timing import onsets

                marks = onsets(line["say"], marks, len(raw) / audio.RATE)
            start = len(speech)
            lead = round(audio.RATE * line.get("lead", 0.10))
            tail = round(audio.RATE * line.get("tail", 0.24))
            frames = math.ceil((lead + len(raw) + tail) * fps / audio.RATE)
            start_frame = frame
            frame += frames
            speech.extend([0] * lead)
            speech.extend(raw)
            speech.extend([0] * (round(frame * audio.RATE / fps) - len(speech)))
            # Prefer sentence-sized captions. The phrases are always contiguous slices of the spoken text.
            words = line["say"].split()
            chunks = []
            group = []
            for word in words:
                group.append(word)
                if len(group) >= 5 or re.search(r"[.!?]$", word):
                    chunks.append(" ".join(group))
                    group = []
            if group:
                chunks.append(" ".join(group))
            word = 0
            for chunk in chunks:
                begin = marks[min(word, len(marks) - 1)][1]
                word += len(chunk.split())
                end = marks[word][1] if word < len(marks) else len(raw) / audio.RATE
                when = (start + lead) / audio.RATE
                captions.append((when + begin, when + end, chunk, False))
            spans = line["shots"]
            weights = [s.get("weight", 1) for s in spans]
            if any(w <= 0 for w in weights):
                raise ValueError(f"Picture durations must be positive at {line['id']}")
            offset = 0
            for j, selection in enumerate(spans):
                stop = round(frames * sum(weights[: j + 1]) / sum(weights))
                length = stop - offset
                if length < 2:
                    raise ValueError(f"Camera at {line['id']} is too short")
                finish = selection.get("finish")
                if "take" in selection:
                    scene = read_take(plan_file.parent, selection["take"])
                    finish = scene.pop("finish", finish)
                    move_time = speech_time_map(
                        scene, line["say"], marks, lead / audio.RATE, offset, length, fps
                    )
                    for obj in scene["tracks"]:
                        for key in obj["keys"]:
                            key[0] = move_time(key[0])
                    for cam in scene["cameras"]:
                        cam["at"] = move_time(cam["at"])
                        for key in cam["keys"]:
                            key[0] = move_time(key[0])
                    for item in scene.get("holds", []):
                        for key in item["anchors"]:
                            key[0] = move_time(key[0])
                    scene.update(frames=length)
                    scene.pop("proof", None)
                    scene.pop("output", None)
                    digest = hashlib.sha256()
                    for module in (
                        "stage_take.py",
                        "animate.py",
                        "world_art.py",
                        "story_objects.py",
                        "story_sets.py",
                    ):
                        digest.update((HERE / module).read_bytes())
                    identity = [
                        scene,
                        digest.hexdigest(),
                        width,
                        height,
                        fps,
                        timeline["looks"],
                        {k: v["sha256"] for k, v in timeline["assets"].items()},
                        recipe["places"].get(scene.get("place")),
                        subprocess.check_output([blender, "--version"]).splitlines()[0].decode(),
                    ]
                    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
                    clip = output / "shots" / (key + ".mp4")
                    if not ensemble_review.correct_clip(clip, probe, width, height, fps, length):
                        shot = dict(scene, output=str(clip))
                        job = staging / "take.json"
                        planning.save(job, dict(plan=recipe, shots=[shot]))
                        with (output / "stage.log").open("a") as log:
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
                                    str(HERE / "stage_take.py"),
                                    "--",
                                    str(job),
                                ],
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                check=True,
                            )
                else:
                    clip, native_frames = native_source(selection, picture, quality)
                    source = clip
                    a, b = selection.get("range", [0, 1])
                    if not 0 <= a < b <= 1:
                        raise ValueError(f"Invalid take interval at {line['id']}")
                    first = min(native_frames - 1, round(a * native_frames))
                    last = min(native_frames, max(first + 1, round(b * native_frames)))
                    # Retain the selected action while borrowing the handles on either side
                    # before slowing motion to fill a long sentence.
                    wanted = min(native_frames, max(last - first, math.ceil(length * 0.86)))
                    first = max(0, min(native_frames - wanted, first - (wanted - (last - first)) // 2))
                    last = first + wanted
                    # The director can choose an exact before/contact/after interval. The edit never loops an action.
                    key = hashlib.sha256(
                        repr(
                            (
                                str(source),
                                source.stat().st_size,
                                source.stat().st_mtime_ns,
                                first,
                                last,
                                length,
                            )
                        ).encode()
                    ).hexdigest()[:20]
                    clip = output / "shots" / (key + ".mp4")
                    if not ensemble_review.correct_clip(clip, probe, width, height, fps, length):
                        dest = staging / "cut.mp4"
                        filters = f"trim=start_frame={first}:end_frame={last},setpts=(PTS-STARTPTS)*{length}/{last - first},fps={fps},tpad=stop_mode=clone:stop_duration=0.15,trim=end_frame={length},setsar=1"
                        subprocess.run(
                            [
                                ffmpeg,
                                "-nostdin",
                                "-v",
                                "error",
                                "-y",
                                "-threads",
                                "1",
                                "-i",
                                str(source),
                                "-an",
                                "-filter_threads",
                                "1",
                                "-vf",
                                filters,
                                "-frames:v",
                                str(length),
                                "-c:v",
                                "libx264",
                                "-threads",
                                "2",
                                "-preset",
                                "veryfast",
                                "-crf",
                                "17",
                                "-pix_fmt",
                                "yuv420p",
                                str(dest),
                            ],
                            check=True,
                        )
                        dest.replace(clip)
                if not ensemble_review.correct_clip(clip, probe, width, height, fps, length):
                    raise ValueError(f"Incorrect frame count for {line['id']} camera {j + 1}")
                if finish:
                    vf = picture_filter(finish, width, height)
                    key = hashlib.sha256((clip.name + vf).encode()).hexdigest()[:20]
                    graded = output / "shots" / (key + ".mp4")
                    if not ensemble_review.correct_clip(graded, probe, width, height, fps, length):
                        dest = staging / "grade.mp4"
                        subprocess.run(
                            [
                                ffmpeg,
                                "-nostdin",
                                "-v",
                                "error",
                                "-y",
                                "-threads",
                                "1",
                                "-i",
                                str(clip),
                                "-an",
                                "-filter_threads",
                                "1",
                                "-vf",
                                vf,
                                "-pix_fmt",
                                "yuv420p",
                                "-threads",
                                "2",
                                "-c:v",
                                "libx264",
                                "-preset",
                                "veryfast",
                                "-crf",
                                "17",
                                str(dest),
                            ],
                            check=True,
                        )
                        if not ensemble_review.correct_clip(dest, probe, width, height, fps, length):
                            raise ValueError(f"Picture treatment changed the length at {line['id']}")
                        dest.replace(graded)
                    clip = graded
                cuts.append(clip.relative_to(output).as_posix())
                offset = stop
            manifest.append(
                dict(
                    id=line["id"],
                    start=start_frame / fps,
                    end=frame / fps,
                    speech_start=(start + lead) / audio.RATE,
                    speech_end=(start + lead + len(raw)) / audio.RATE,
                    say=line["say"],
                    evidence=line["evidence"],
                )
            )
        audio.write_wave(staging / "dialogue.wav", speech)
        audio.make_captions(staging / "lines.ass", captions, style="phrases")
        # The input order is the authored story order. The final file contains one new dialogue stream.
        (output / "screenplay-clips.txt").write_text(
            "".join("file " + s + "\n" for s in cuts), encoding="utf8"
        )
        dest = staging / "picture.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "1",
                "-i",
                str(output / "screenplay-clips.txt"),
                "-i",
                "dialogue.wav",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-filter_threads",
                "2",
                "-vf",
                f"settb=1/{fps},setpts=N,ass=lines.ass",
                "-r",
                str(fps),
                "-fps_mode",
                "cfr",
                "-frames:v",
                str(frame),
                "-threads",
                "3",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(dest),
            ],
            cwd=staging,
            check=True,
        )
        if not ensemble_review.correct_clip(dest, probe, width, height, fps, frame):
            actual = ensemble_review.video_info(dest, probe)[0]
            raise ValueError(f"Expected {frame} frames at {fps} fps, got {actual}")
        subprocess.run(
            [ffmpeg, "-v", "error", "-xerror", "-threads", "1", "-i", str(dest), "-f", "null", "-"],
            check=True,
        )
        checks = dialogue_check(dest, manifest, ffmpeg, assets)
        movie_digest = movie_hash(dest)
        dest.replace(output / "movie.mp4")
    data = dict(title=spec["title"], frames=frame, fps=fps, lines=manifest, sha256=movie_digest)
    planning.save(output / "screening.json", data)
    planning.save(output / "audio-checks.json", dict(sha256=movie_digest, dialogue=checks))
    review_page(output / "movie.mp4", data)
    return output / "movie.mp4"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screenplay", type=Path)
    parser.add_argument("quality_folder", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--assets", type=Path)
    args = parser.parse_args()
    print(
        render(
            args.screenplay.resolve(), args.quality_folder.resolve(), args.output.resolve(), args.assets
        ),
        flush=True,
    )
