"""Scene-specific color timing on the finished image, ahead of title and caption overlays."""

# Keep the black level and the brightest practicals readable in the night grades.
GRADES = {
    "moonlight": (
        "eq=contrast=1.10:brightness=-0.030:saturation=0.93",
        "colorbalance=rs=-.018:bs=.042:rm=-.022:bm=.066:bh=.020:pl=1",
    ),
    "lamplight": (
        "eq=contrast=1.09:brightness=-.025:saturation=1.04",
        "colorbalance=rs=.014:bs=-.018:rm=.055:gm=.008:bm=-.042:rh=.034:pl=1",
    ),
    "sunset": (
        "eq=contrast=1.055:saturation=1.05",
        "colorbalance=rs=-.015:bs=.023:rm=.035:bm=-.025:rh=.045:bh=-.046:pl=1",
    ),
    "neon": (
        "eq=contrast=1.12:brightness=-.026:saturation=1.21",
        "colorbalance=rs=.002:gs=-.026:bs=.074:rm=.036:gm=-.026:bm=.080:bh=.056:pl=1",
    ),
    "dream": (
        "eq=contrast=1.055:saturation=1.12",
        "colorbalance=rs=.040:gs=-.018:bs=.074:bm=.042:rh=.025:bh=.050:pl=1",
    ),
}


def filters(timeline):
    spans = {}
    for take in timeline["shots"]:
        shot = take["shot"]
        place = timeline["places"][shot["place"]]
        if shot.get("selective_color"):
            continue
        default = {"late_sun": "sunset", "night": "moonlight"}.get(place.get("light"), "natural")
        grade = place.get("grade", default if place.get("finish") == "textured" else "natural")
        if grade == "natural":
            continue
        start = round(take["clock"] * timeline["fps"])
        end = start + take["frames"]
        runs = spans.setdefault(grade, [])
        if runs and runs[-1][1] == start:
            runs[-1] = (runs[-1][0], end)
        else:
            runs.append((start, end))
    result = []
    for grade, runs in spans.items():
        when = "+".join(f"gte(n,{a})*lt(n,{b})" for a, b in runs)
        result.extend(f"{filter_expr}:enable='{when}'" for filter_expr in GRADES[grade])
    return result
