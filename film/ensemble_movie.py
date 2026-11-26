"""Compile blocking, narration and persistent set state into independently reusable shots."""

from array import array
from copy import deepcopy
import hashlib
import json
import subprocess
import time
from pathlib import Path
from . import assets, audio, planning, storage, ensemble_review, ensemble, grading, vistas, character_props

HERE = Path(__file__).resolve().parent


def named_model(root, prop_id):
    dest = root / "props" / "ensemble-named" / (assets.character_id(prop_id) + ".json")
    if dest.is_file():
        return dest, json.loads(dest.read_text(encoding="utf8"))
    legacy = root / "props" / "named" / (prop_id + ".json")
    if not legacy.is_file():
        return dest, None
    old = json.loads(legacy.read_text(encoding="utf8"))
    parts = (
        [
            dict(
                shape=p["shape"],
                at=[p[k] for k in ("x", "y", "z")],
                size=[p[k] for k in ("width", "depth", "height")],
                rotation=[0, 0, 0],
                color=p["color"],
            )
            for p in old["parts"]
        ]
        if old["kind"] == "custom"
        else []
    )
    return dest, dict(kind=old["kind"], color=old["color"], text=old["label"], parts=parts)


def bind_model(path, model, prop_id, design):
    prop = next((item for item in design["props"] if item["id"] == prop_id), None)
    if prop is None:
        raise ValueError(f"The authored episode has no prop named {prop_id}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with assets.creation_lock(path.parent):
        if path.is_file():
            model = json.loads(path.read_text(encoding="utf8"))
        if model:
            prop.update(model)
        else:
            model = {k: prop[k] for k in ("kind", "color", "text", "parts")}
        if not path.is_file():
            planning.save(path, model)


def timings(lines, seconds, fps, locks=None):
    if locks and any(value is not None for value in locks):
        if len(locks) != len(lines):
            raise ValueError("Each setup needs one duration entry.")
        open_lines = [length for length, value in zip(lines, locks) if value is None]
        available = seconds * fps - sum(v for v in locks if v is not None)
        if available < 3 * len(open_lines) or not open_lines and available:
            raise ValueError("The locked takes do not fit the edit.")
        remaining = iter(timings(open_lines, available / fps, fps) if open_lines else [])
        return [value if value is not None else next(remaining) for value in locks]
    # Give each spoken sentence a breath. Quantize cumulative boundaries once to avoid duration drift.
    weights = [n / audio.RATE + 0.52 for n in lines]
    scale = seconds * fps / sum(weights)
    prior = 0
    running = 0
    result = []
    for n in weights:
        running += n
        nxt = round(running * scale)
        result.append(nxt - prior)
        prior = nxt
    if min(result) < 3:
        raise ValueError("Too much dialogue for this episode duration.")
    return result


def captions_for_line(out, marks, offset, length, speed, style="phrases"):
    if style == "spoken":
        # Give very fast words a readable shared cue. End the group on punctuation or a long word.
        words = []
        start = 0.0
        for i, (word, raw_start) in enumerate(marks):
            if not words:
                start = raw_start / speed
            words.append(word)
            end = min(length, marks[i + 1][1] / speed) if i + 1 < len(marks) else length
            if end - start >= 0.28 or len(words) == 3 or word[-1] in ".,!?" or i + 1 == len(marks):
                out.append((offset + start, offset + end, " ".join(words), False))
                words = []
        return
    chunks = []
    words = []
    begin = 0
    for i, (word, t) in enumerate(marks):
        if not words:
            begin = t
        words.append(word)
        if len(words) >= 5 or len(" ".join(words)) > 24 or word[-1] in ".,!?" or i == len(marks) - 1:
            chunks.append((begin, " ".join(words)))
            words = []
    for i, (t, phrase) in enumerate(chunks):
        end = chunks[i + 1][0] / speed if i + 1 < len(chunks) else length
        out.append((offset + t / speed, offset + end, phrase, False))


def narration_budget(seconds, main, pickup=0):
    available = max(0.08, seconds - min(0.32, seconds * 0.12))
    breath = min(0.45, available * 0.08) if pickup else 0
    speed = max(1, (main + pickup) / (available - breath))
    # Center a short reply in the available silence. A deliberate reaction can still breathe.
    pickup_start = main / speed + max(breath, (available - (main + pickup) / speed) / 2)
    return speed, pickup_start


def pace_voice(raw, speed, folder, ffmpeg):
    if speed <= 1.005:
        return raw
    audio.write_wave(folder / "line.wav", raw)
    audio.run(
        [
            ffmpeg,
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(folder / "line.wav"),
            "-af",
            f"atempo={speed:.8f}",
            str(folder / "paced.wav"),
        ]
    )
    return audio.read_wave(folder / "paced.wav")


def synchronized(shot, line, marks, speed, length):
    if not shot.get("sync"):
        return shot
    # Backends report whitespace tokens. Match the spoken phrase against the normalized word stream.
    times = [time for word, time in marks for _ in ensemble.tokens(word)]
    where = ensemble.phrase_starts(line, shot["sync"])
    knots = [
        (0, 0),
        *[(m["at"], max(0.001, min(0.999, times[i] / speed / length))) for m, i in zip(shot["sync"], where)],
        (1, 1),
    ]
    if any(b[1] <= a[1] for a, b in zip(knots, knots[1:])):
        raise ValueError("Spoken cue anchors share a timestamp.")

    def mapped(t):
        for (x, a), (y, b) in zip(knots, knots[1:]):
            if t <= y:
                return a + (b - a) * (t - x) / (y - x)
        return 1

    result = deepcopy(shot)
    timed = [*result["actors"], *result["events"], *result["cameras"]]
    if "atmosphere" in result:
        timed.append(result["atmosphere"])
    timed.extend(c for a in result["actors"] for c in a["cues"])
    for item in timed:
        for k in ("start", "end"):
            if k in item:
                item[k] = mapped(item[k])
    glances = [g for a in result["actors"] for g in a.get("gaze", [])]
    for cue in [*result["sounds"], *result.get("accents", []), *glances]:
        cue["at"] = mapped(cue["at"])
    return result


def sync_dialogue(shot, line, marks, speed, length):
    if not shot.get("dialogue"):
        return shot
    result = deepcopy(shot)
    actors = {a["id"]: a for a in result["actors"]}
    times = [time / speed / length for word, time in marks for _ in ensemble.tokens(word)]
    for speaker, indices in ensemble.dialogue_ranges(line, shot["dialogue"], actors):
        syllables = actors[speaker].setdefault("syllables", [])
        for i in indices:
            start = times[i]
            stop = times[i + 1] if i + 1 < len(times) else 1
            width = min(0.24 / length, max(0.012 / length, stop - start))
            syllables.append([start + width * 0.5, width * 0.5])
    return result


def render_storyboard(dst, plan, command, ffmpeg):
    out = dst / "storyboard"
    out.mkdir(exist_ok=True)
    data = deepcopy(plan)
    data.update(plates=True, width=288, height=512)
    paths = []
    for index, s in enumerate(data["shots"], 1):
        s["clip"] = str(out / f"setup-{index:03d}.mp4")
        starts = [c["start"] for c in s["shot"]["cameras"]] + [1]
        s["sample_frames"] = [1 + round((a + b) / 2 * (s["frames"] - 1)) for a, b in zip(starts, starts[1:])]
        for v in data.get("vistas", []):
            if v["beat"] == index and v["kind"] == "reaction":
                j = v["camera"] - 1
                lo = round(starts[j] * (s["frames"] - 1))
                s["sample_frames"][j] = 1 + (lo + v["start"] - 1) // 2
        paths.extend((index, f) for f in s["sample_frames"])
    planning.save(out / "plates.json", data)
    with (out / "blender.log").open("w") as log:
        subprocess.run([*command, str(out / "plates.json")], stdout=log, stderr=subprocess.STDOUT, check=True)
    paths.extend(vistas.boards(data, out, command[0]))
    paths.sort()
    for page, start in enumerate(range(0, len(paths), 12), 1):
        take = paths[start : start + 12]
        (out / "stills.txt").write_text("".join(f"file setup-{n:03d}-{f}.png\n" for n, f in take))
        audio.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "1",
                "-i",
                "stills.txt",
                "-vf",
                f"scale=180:320,tile=4x3:nb_frames={len(take)}:padding=3:margin=3",
                "-frames:v",
                "1",
                f"page-{page:02d}.jpg",
            ],
            cwd=out,
        )
    print(f"{len(paths)} camera compositions: {out}", flush=True)
    return out


def render(
    job, story, d, quality, blender, ffmpeg, root, directory, names, storyboard=False, prepare_only=False
):
    d = character_props.expand(d)
    fps = 30
    ffprobe = str(Path(ffmpeg).with_name("ffprobe" + Path(ffmpeg).suffix))
    w, h = {"preview": (432, 768), "review": (720, 1280), "final": (1080, 1920)}[quality]
    dst = job / quality
    dst.mkdir(exist_ok=True)
    clips = dst / "shots"
    clips.mkdir(exist_ok=True)
    src = [blender, "-b", "-t", "4", "-noaudio", "--factory-startup", "--python-exit-code", "1", "--python"]
    looks = {a["id"]: a for a in d["looks"]}
    cast = []
    witness = next((a["id"] for a in story["cast"] if a["id"] != story["lead"]), None)
    for k, a in looks.items():
        role = "lead" if k == story["lead"] else "witness" if k == witness else "ensemble"
        outfit = {j: v for j, v in a.items() if j not in ("badge", "height")}
        if a["uniform"] == "gown":
            outfit["costume_revision"] = 2
        identity = names.get(role) or (k + "-" + assets.digest(outfit)[:10])
        cast.append(
            dict(
                id=k,
                kind="character",
                path=str(directory / (identity + ".blend")),
                role=role,
                coat=a["coat"],
                look=a,
            )
        )
    files = assets.ensure_models(job, directory, cast, [*src, str(HERE / "animate.py"), "--"])
    planning.save(job / "cast.json", files)
    utterances = [audio.narration(b["line"], job, ffmpeg, root) for b in story["beats"]]
    counts = timings(
        [len(raw) for raw, _ in utterances],
        story["seconds"],
        fps,
        [b.get("edit_frames") for b in story["beats"]],
    )
    states = {p["id"]: dict(to=p["at"], text=p["text"], spin=0, anchor="") for p in d["props"]}
    places = {p["id"]: p for p in d["places"]}
    versions = hashlib.sha256()
    for path in [
        HERE / "ensemble_render.py",
        HERE / "festival.py",
        HERE / "shot_rhythm.py",
        HERE / "world_art.py",
        HERE / "story_objects.py",
        HERE / "story_sets.py",
        HERE / "surface_art.py",
        HERE / "atmosphere.py",
        HERE / "animate.py",
        *sorted((HERE / "props").glob("*.py")),
    ]:
        versions.update(path.read_bytes())
    engine = subprocess.check_output([blender, "--version"], text=True).splitlines()[0]
    shots = []
    location_views = []
    speech = array("h")
    captions = []
    effects = []
    caption_style = story.get("caption_style", "spoken")
    introductions = []
    offset = 0
    for n, (shot, count, (raw, marks)) in enumerate(zip(d["shots"], counts, utterances), 1):
        shot = dict(shot)
        stage_clock = shot.pop("stage_clock", offset / fps)
        length = count / fps
        beat = story["beats"][n - 1]
        pickup = audio.narration(beat["pickup"], job, ffmpeg, root) if beat.get("pickup") else None
        extra = len(pickup[0]) / audio.RATE if pickup else 0
        speed, pickup_start = narration_budget(length, len(raw) / audio.RATE, extra)
        raw = pace_voice(raw, speed, dst, ffmpeg)
        shot = synchronized(shot, story["beats"][n - 1]["line"], marks, speed, length)
        shot = sync_dialogue(shot, story["beats"][n - 1]["line"], marks, speed, length)
        shot, inserts = vistas.extract(shot, n, count)
        location_views.extend(inserts)
        begin = offset / fps
        for card in story.get("introductions", []):
            if card["beat"] != n:
                continue
            at = ensemble.phrase_starts(story["beats"][n - 1]["line"], [dict(at=0.5, words=card["words"])])[0]
            token_times = [t / speed for word, t in marks for _ in ensemble.tokens(word)]
            start = begin + token_times[at]
            introductions.append((start, min(begin + length, start + 1.75), card["label"]))
        effects.extend((begin + length * fx["at"], fx["kind"]) for fx in shot["sounds"])
        captions_for_line(captions, marks, begin, len(raw) / audio.RATE, speed, caption_style)
        capacity = round((offset + count) * audio.RATE / fps) - len(speech)
        clip = raw[:capacity]
        if pickup:
            take = pace_voice(pickup[0], speed, dst, ffmpeg)
            start_sample = min(capacity, max(len(clip), round(pickup_start * audio.RATE)))
            take = take[: capacity - start_sample]
            clip.extend(array("h", [0]) * (start_sample - len(clip)))
            clip.extend(take)
            captions_for_line(
                captions, pickup[1], begin + start_sample / audio.RATE, len(take) / audio.RATE, speed, caption_style
            )
        speech.extend(clip)
        offset += count
        speech.extend(array("h", [0]) * (capacity - len(clip)))
        local = [p for p in d["props"] if p["place"] == shot["place"]]
        before = {p["id"]: states[p["id"]] for p in local}
        for e in shot["events"]:
            states[e["id"]] = {k: e[k] for k in ("to", "text", "spin", "anchor")}
        ids = [a["id"] for a in shot["actors"]]
        recipes = {c["action"]: planning.MOTIONS[c["action"]] for a in shot["actors"] for c in a["cues"]}
        key = assets.digest(
            [
                versions.hexdigest(),
                engine,
                w,
                h,
                fps,
                count,
                stage_clock,
                shot,
                before,
                {k: v for k, v in places[shot["place"]].items() if k != "grade"},
                local,
                [[looks[i], files[i]["sha256"]] for i in ids],
                recipes,
            ]
        )
        clip = clips / f"{n:03d}-{key[:12]}.mp4"
        shared = root / "ensemble-shots" / (key + ".mp4")
        if clip.exists() and not ensemble_review.correct_clip(clip, ffprobe, w, h, fps, count):
            clip.unlink()
        if not clip.is_file() and ensemble_review.correct_clip(shared, ffprobe, w, h, fps, count):
            storage.copy_file(shared, clip)
        shots.append(
            dict(
                shot=shot,
                before=before,
                clock=begin,
                stage_clock=stage_clock,
                frames=count,
                clip=str(clip),
                shared=str(shared),
            )
        )
    plan = dict(
        width=w,
        height=h,
        fps=fps,
        assets=files,
        looks=looks,
        places=places,
        props=d["props"],
        vistas=location_views,
        pickup_count=sum(bool(b.get("pickup")) for b in story["beats"]),
        motions=planning.MOTIONS,
        shots=shots,
    )
    planning.save(dst / "timeline.json", plan)
    command = [*src, str(HERE / "ensemble_render.py"), "--"]
    if storyboard:
        planning.save(dst / "blocking-review.json", ensemble_review.directing_stats(plan))
        return render_storyboard(dst, plan, command, ffmpeg)
    audio.make_captions(dst / "lines.ass", captions, introductions, caption_style)
    audio.soundtrack(dst / "mix.wav", speech, effects, "wonder", root)
    if prepare_only:
        return dst / "timeline.json"
    cached = sum(Path(s["clip"]).is_file() for s in shots)
    print(
        f"{len(shots)} setups, {sum(len(s['shot']['cameras']) for s in shots)} camera shots, {offset} frames. {cached} setups cached.",
        flush=True,
    )
    if cached < len(shots):
        with (dst / "blender.log").open("w") as log:
            proc = subprocess.Popen(
                [*command, str(dst / "timeline.json")], stdout=log, stderr=subprocess.STDOUT
            )
            try:
                done = cached
                while proc.poll() is None:
                    completed = sum(Path(s["clip"]).is_file() for s in shots)
                    if completed != done:
                        print(f"  Rendered setups {completed}/{len(shots)}", flush=True)
                        done = completed
                    time.sleep(1)
            except BaseException:
                proc.terminate()
                proc.wait()
                raise
            if proc.returncode:
                raise RuntimeError(f"Blender stopped. See {dst / 'blender.log'}.")
    edit = vistas.apply(plan, dst, root, blender, ffmpeg, ffprobe)
    (dst / "clips.txt").write_text(
        "\n".join("file " + Path(s["clip"]).relative_to(dst).as_posix() for s in edit["shots"]) + "\n"
    )
    # Matroska/MP4 fragment time bases can round each cut by a fraction of a frame. Re-clock exact frame order.
    audio.run(
        [
            ffmpeg,
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            "clips.txt",
            "-i",
            "mix.wav",
            "-vf",
            ",".join([f"setpts=N/({fps}*TB)", *grading.filters(plan), "ass=lines.ass"]),
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-threads",
            "4",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "movie.partial.mp4",
        ],
        cwd=dst,
    )
    proof = ensemble_review.audit(edit, dst / "movie.partial.mp4", ffmpeg, ffprobe)
    if location_views:
        planning.save(dst / "picture-edit.json", edit)
    else:
        (dst / "picture-edit.json").unlink(missing_ok=True)
    planning.save(dst / "render-review.json", proof)
    (dst / "movie.partial.mp4").replace(dst / "movie.mp4")
    print(f"Finished: {dst / 'movie.mp4'} ({offset / fps:.2f}s)", flush=True)
    return dst / "movie.mp4"
