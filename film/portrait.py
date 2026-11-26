"""Compose a tighter vertical portrait from an existing performance before lettering the frame."""

from statistics import median


def angles(timeline):
    fps = timeline["fps"]
    cuts = []
    for index, take in enumerate(timeline["shots"], 1):
        shot = take["shot"]
        cast = {a["id"]: a for a in shot["actors"]}
        cameras = shot["cameras"]
        frames = take["frames"]
        starts = [round(c["start"] * (frames - 1)) for c in cameras] + [frames]
        clock = round(take["clock"] * fps)
        for camera, start, end in zip(cameras, starts, starts[1:]):
            focus = camera["focus"]
            if (
                len(focus) != 1
                or focus[0] not in cast
                or camera["size"] > 2.38
                or camera.get("move") == "reveal"
            ):
                continue
            actor = cast[focus[0]]
            low, high = actor.get("lift", (0, 0))
            if (
                actor.get("pose") == "frozen"
                or abs(high - low) > 0.6
                or max(map(abs, actor.get("pitch", (0, 0)))) > 27
            ):
                continue
            length = end - start
            if length < round(0.4 * fps):
                continue
            # Let the medium shot establish the action before cutting to a face on longer takes.
            first = start + round(0.43 * length) if length >= round(2.06 * fps) else start
            scale = 1.60 if camera.get("move") in ("punch", "hold") else 1.47
            cuts.append(
                dict(setup=index, actor=focus[0], start=clock + first, stop=clock + end,
                     scale=scale, cut_in=first != start)
            )
    return cuts


def filters(angles, width, height, fps):
    if not angles:
        return []
    # Each span is half open. A fixed crop at a cut avoids subpixel jitter during the native motion.
    terms = []
    for scale in sorted({angle["scale"] for angle in angles}):
        spans = [f"between(on,{a['start']},{a['stop'] - 1})" for a in angles if a["scale"] == scale]
        terms.append(f"+{scale - 1:.3g}*({'+'.join(spans)})")
    zoom = "1" + "".join(terms)
    return [f"zoompan=z='{zoom}':x='iw*.5*(1-1/zoom)':y='ih*.47*(1-1/zoom)':d=1:s={width}x{height}:fps={fps}"]


def review(timeline, angles):
    fps = timeline["fps"]
    cuts = {a["start"] for a in angles if a["cut_in"]}
    end = 0
    for take in timeline["shots"]:
        clock = round(take["clock"] * fps)
        end = clock + take["frames"]
        for camera in take["shot"]["cameras"]:
            cuts.add(clock + round(camera["start"] * (take["frames"] - 1)))
    ordered = sorted(cuts | {end})
    durations = [(b - a) / fps for a, b in zip(ordered, ordered[1:])]
    return dict(
        portrait_angles=len(angles),
        portrait_cutins=sum(a["cut_in"] for a in angles),
        picture_shots=len(durations),
        median_picture_shot_seconds=round(median(durations), 2),
    )
