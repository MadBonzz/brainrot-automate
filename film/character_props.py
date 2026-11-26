"""Dress an articulated figure with a reusable face while preserving its moving limbs."""

from copy import deepcopy


def features(style, z):
    def part(pos, size, shade, shape="sphere", rotation=(0, 0, 0)):
        x, y, height = pos
        return dict(at=[x, y, height + z], size=list(size), color=shade, shape=shape, rotation=list(rotation))

    paper = style == "creased"
    flesh = "C0BBA9" if paper else "EDE9DA"
    out = [part((0, -0.235, 0), (0.73, 0.40, 0.76), flesh)]
    for side in (-1, 1):
        out.append(part((side * 0.18, -0.405, 0.10), (0.175, 0.08, 0.105 if paper else 0.15), "514D45"))
        out.append(part((side * 0.18, -0.451, 0.105), (0.052, 0.026, 0.054), "DDD8BC"))
        out.append(
            part(
                (side * 0.20, -0.420, 0.185),
                (0.28, 0.058, 0.058),
                "A29B87" if paper else flesh,
                "box",
                (0, side * (13 if paper else -6), 0),
            )
        )
    if paper:
        out.append(part((0, -0.447, -0.134), (0.36, 0.045, 0.22), "413C37"))
        for j in range(6):
            x = (j - 2.5) * 0.057
            out.append(
                part(
                    (x, -0.474, -0.068),
                    (0.045, 0.03, 0.084 - 0.008 * abs(j - 2.5)),
                    "E3DCC3",
                    "cone",
                    (180, 0, 0),
                )
            )
        for j in range(8):
            side = 1 if j % 2 else -1
            out.append(
                part(
                    (side * (0.18 + 0.034 * (j % 3)), -0.408, -0.005 - (j // 2) * 0.043),
                    (0.14, 0.033, 0.022),
                    "8D877B",
                    "box",
                    (0, side * (16 + j * 2), 0),
                )
            )
    else:
        # A painted crescent keeps the visitors' expression unnaturally fixed as the limbs move.
        for j in range(-4, 5):
            x = j * 0.058
            out.append(
                part(
                    (x, -0.443, -0.19 + 0.105 * (abs(j) / 4) ** 1.7),
                    (0.086, 0.047, 0.063),
                    "413936",
                    "sphere",
                    (0, -j * 8, 0),
                )
            )
    return flesh, out


def expand(direction):
    chosen = [p for p in direction["props"] if p.get("face_model", "plain") != "plain"]
    if not chosen:
        # A model-generated explicit default should share footage with an older saved plan.
        if not any("face_model" in p for p in direction["props"]):
            return direction
        return dict(
            direction, props=[{k: v for k, v in p.items() if k != "face_model"} for p in direction["props"]]
        )
    result = deepcopy(direction)
    used = {p["id"] for p in result["props"]} | {a["id"] for a in result["looks"]}
    for prop in list(result["props"]):
        style = prop.pop("face_model", "plain")
        if style == "plain":
            continue
        name = prop["id"]
        overlay = name + "-face"
        while overlay in used:
            overlay += "-face"
        used.add(overlay)
        stages = [s for s in result["shots"] if s["place"] == prop["place"]]
        held = any(e["id"] == name and e["anchor"] for s in stages for e in s["events"])
        height = 0 if held else 2.47 * prop["scale"]
        shade, parts = features(style, 2.47 if held else 0)
        prop["color"] = shade

        def raised(point):
            return [point[0], point[1], point[2] + height]

        face = dict(prop, id=overlay, kind="custom", parts=parts, at=raised(prop["at"]))
        result["props"].append(face)
        for shot in stages:
            shot["events"].extend(
                [dict(e, id=overlay, to=raised(e["to"])) for e in shot["events"] if e["id"] == name]
            )
            if name in shot.get("selective_color", []):
                shot["selective_color"].append(overlay)
            if held:
                continue
            for camera in shot["cameras"]:
                if camera["focus"] == [name] and camera["size"] <= 2.8:
                    camera["focus"] = [overlay]
    return result
