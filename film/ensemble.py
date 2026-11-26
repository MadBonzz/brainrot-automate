"""Story and blocking contracts shared by the writer, director and renderer."""

import json
import math
import re
from . import planning as p
from . import assets
from .props import CATALOG

S, N, I, obj, arr, enum = p.S, p.N, p.I, p.obj, p.arr, p.choices
ROLES = "rule custom desire attempt clue choice outcome callback"
STORY = obj(
    title=S,
    seconds=I,
    rule=S,
    loophole=S,
    cost=S,
    lead=S,
    cast=arr(obj(id=S, job=S, want=S)),
    beats=arr(obj(role=enum(ROLES), because=I, witness=S, visible=S, line=S)),
)
STORY["properties"]["introductions"] = arr(obj(beat=I, actor=S, words=S, label=S))
STORY["properties"]["beats"]["items"]["properties"]["also_because"] = arr(I)
V = arr(N)
LOOK = obj(
    id=S,
    coat=p.COLOR,
    skin=enum("amber umber rose bronze"),
    hair=p.COLOR,
    hat=enum("none cap beret bun crown visor curls helmet bow veil"),
    uniform=enum("jacket apron sash satchel tunic bandleader gown"),
    badge=S,
    height=N,
)
PLACE = obj(
    id=S,
    kit=enum("arcade depot theater garden harbor boathouse fairground glasshouse"),
    sign=S,
    trim=p.COLOR,
    wall=p.COLOR,
)
PART = obj(shape=enum("box sphere cylinder cone ring sail"), at=V, size=V, rotation=V, color=p.COLOR)
PROP_KINDS = (
    "raincloud bouquet cistern cake clock radio lantern signal mark custom lamp drum mirror hatch board door parcel trophy trumpet goose bench stand "
    + " ".join(CATALOG)
)
PROP = obj(id=S, kind=enum(PROP_KINDS), place=S, at=V, scale=N, color=p.COLOR, text=S, parts=arr(PART))
CUE = obj(action=enum(" ".join(p.MOTIONS)), start=N, end=N)
ACTOR = obj(
    id=S,
    look_at=S,
    at=V,
    to=V,
    facing=N,
    end_facing=N,
    start=N,
    end=N,
    mood=enum("calm worried proud surprised"),
    cues=arr(CUE),
)
EVENT = obj(id=S, anchor=S, to=V, text=S, spin=N, start=N, end=N)
CAM = obj(start=N, focus=arr(S), size=N, angle=N, elevation=N, drift=N)
# These keys may be absent in saved plans. Fresh model output supplies them explicitly.
PLACE["properties"]["light"] = enum("daylight late_sun night")
PLACE["properties"]["life"] = enum("quiet shoppers workers audience")
CAM["properties"]["move"] = enum("hold follow arc punch reveal")
CUE["properties"]["play"] = enum("accent sustain cycle")
SOUND = obj(kind=enum("bell knock click rumble honk brass clatter"), at=N)
SYNC = obj(at=N, words=S)
SHOT = obj(
    place=S,
    sync=arr(SYNC),
    transition=enum("continuous ellipsis cutaway"),
    sounds=arr(SOUND),
    actors=arr(ACTOR),
    events=arr(EVENT),
    cameras=arr(CAM),
)
SHOT["properties"]["accents"] = arr(obj(kind=enum("splash petals dust glint"), focus=S, at=N))
SHOT["properties"]["dialogue"] = arr(obj(actor=S, words=S))
DIRECTION = obj(looks=arr(LOOK), places=arr(PLACE), props=arr(PROP), shots=arr(SHOT))


def unique(items, label):
    ids = [x["id"] for x in items]
    if len(ids) != len(set(ids)) or any(assets.character_id(i) != i for i in ids):
        raise ValueError("Use distinct lowercase IDs for " + label)
    return set(ids)


def check_story(story):
    if not 12 <= story["seconds"] <= 180:
        raise ValueError("Duration must be 12–180 seconds.")
    cast = unique(story["cast"], "cast")
    beats = story["beats"]
    if not 4 <= len(cast) <= 10 or story["lead"] not in cast:
        raise ValueError("Give the lead and 3–9 other townspeople distinct jobs and wants.")
    for card in story.get("introductions", []):
        if (
            card["actor"] not in cast
            or not 1 <= card["beat"] <= len(beats)
            or not 0 < len(card["label"]) <= 28
        ):
            raise ValueError("A cast introduction needs a known actor, beat, and label of 1–28 characters.")
        phrase_starts(beats[card["beat"] - 1]["line"], [dict(at=0.5, words=card["words"])])
    order = [b["role"] for b in beats]
    if not all(r in order for r in ROLES.split()) or order[0] != "rule" or order[-1] != "callback":
        raise ValueError("Open with the rule, include all eight story functions, close on the callback.")
    if not (
        order.index("desire") < order.index("attempt") < order.index("choice") < order.index("outcome")
        and order.index("clue") < order.index("choice")
    ):
        raise ValueError(
            "Plant the clue and let the ordinary attempt fail before the choice and consequence."
        )
    for n, b in enumerate(beats, 1):
        if not (0 <= b["because"] < n) or (
            b["role"] in ("attempt", "choice", "outcome", "callback") and not b["because"]
        ):
            raise ValueError(f"Beat {n} needs a valid earlier cause (one-based index).")
        extra = b.get("also_because", [])
        if any(not 0 < parent < n or parent == b["because"] for parent in extra) or len(set(extra)) != len(
            extra
        ):
            raise ValueError(f"Beat {n} needs distinct, earlier secondary causes.")
        if b["witness"] not in cast or not all(b[k].strip() for k in ("visible", "line")):
            raise ValueError(f"Beat {n} needs a cast member, visible evidence and a spoken line.")
        if b["role"] == "choice" and b["witness"] != story["lead"]:
            raise ValueError("The protagonist must make the choice on screen.")

    def ancestors(beat):
        pending = [beat["because"], *beat.get("also_because", [])]
        seen = set()
        while pending:
            index = pending.pop()
            if index and index not in seen:
                seen.add(index)
                parent = beats[index - 1]
                pending.extend([parent["because"], *parent.get("also_because", [])])
        return {beats[index - 1]["role"] for index in seen}

    for b in beats:
        chain = ancestors(b)
        if b["role"] == "choice" and "clue" not in chain:
            raise ValueError("Connect each choice to earlier on-screen evidence by its because chain.")
        if (
            b["role"] == "choice"
            and "also_because" in b
            and story["seconds"] >= 45
            and "attempt" not in chain
        ):
            raise ValueError("Connect the decision to both a failed attempt and evidence of the exception.")
        if b["role"] == "outcome" and "choice" not in chain:
            raise ValueError("The ending must be caused by the protagonist’s decision.")
    if len({b["witness"] for b in beats}) < 4:
        raise ValueError("Show four named people doing consequential things.")
    if not all(story[k].strip() for k in ("rule", "loophole", "cost")):
        raise ValueError("State the rule, observable exception and the cost.")


def tokens(text):
    return re.findall(r"[^\W_]+(?:'[^\W_]+)*", text.lower().replace("’", "'"))


def phrase_starts(line, sync):
    words = tokens(line)
    previous = -1
    previous_fraction = 0
    indices = []
    for mark in sync:
        phrase = tokens(mark["words"])
        matches = [i for i in range(len(words)) if phrase and words[i : i + len(phrase)] == phrase]
        if len(matches) != 1 or matches[0] <= previous or not previous_fraction < mark["at"] < 1:
            raise ValueError(f"Use distinct ordered spoken phrases as sync anchors: {mark['words']}")
        previous = matches[0]
        previous_fraction = mark["at"]
        indices.append(previous)
    return indices


def dialogue_ranges(line, cues, actors):
    words = tokens(line)
    used = set()
    for cue in cues:
        phrase = tokens(cue["words"])
        starts = [i for i in range(len(words)) if phrase and words[i : i + len(phrase)] == phrase]
        if cue["actor"] not in actors or len(starts) != 1:
            raise ValueError("Dialogue needs a visible speaker and a unique verbatim phrase from the line.")
        indices = range(starts[0], starts[0] + len(phrase))
        if used.intersection(indices):
            raise ValueError("Two speakers cannot own the same spoken words.")
        used.update(indices)
        yield cue["actor"], indices


def interval(x):
    if not 0 <= x["start"] < x["end"] <= 1:
        raise ValueError("Use increasing cue fractions between zero and one.")


def vector(v, n):
    if len(v) != n or any(not math.isfinite(a) or abs(a) > 100 for a in v):
        raise ValueError(f"Expected a finite {n}-component stage position.")


def check_direction(d, story, partial=False):
    cast = unique(d["looks"], "looks")
    places = unique(d["places"], "places")
    props = unique(d["props"], "props")
    if cast != {a["id"] for a in story["cast"]} or cast & props or len(places) < 2:
        raise ValueError("Match looks to the cast, give props unique IDs and build at least two locations.")
    if len(d["shots"]) != len(story["beats"]):
        raise ValueError("Supply one blocking setup per spoken beat.")
    for x in d["looks"]:
        if not 0.68 <= x["height"] <= 1.35:
            raise ValueError("Character height scale is .68–1.35.")
    prop_by_place = {key: set() for key in places}
    for x in d["props"]:
        if x["place"] not in places or not 0.05 <= x["scale"] <= 8:
            raise ValueError("Invalid prop location or scale.")
        if x["kind"] == "custom" and not 1 <= len(x["parts"]) <= 40:
            raise ValueError("A new prop or landmark needs 1–40 local primitive parts.")
        if x["kind"] != "custom" and x["parts"]:
            raise ValueError("Only custom props take primitive parts.")
        for piece in x["parts"]:
            vector(piece["at"], 3)
            vector(piece["size"], 3)
            if (
                len(piece["rotation"]) != 3
                or not all(math.isfinite(v) for v in piece["rotation"])
                or min(piece["size"]) <= 0
            ):
                raise ValueError("Give every custom part three rotation angles and positive dimensions.")
        vector(x["at"], 3)
        prop_by_place[x["place"]].add(x["id"])
    shown = set()
    for n, (s, b) in enumerate(zip(d["shots"], story["beats"]), 1):
        phrase_starts(b["line"], s["sync"])
        actors = unique(s["actors"], f"beat {n} actors")
        if any(c["actor"] not in actors for c in story.get("introductions", []) if c["beat"] == n):
            raise ValueError(f"Beat {n} must stage the cast member introduced here.")
        list(dialogue_ranges(b["line"], s.get("dialogue", []), actors))
        if s["transition"] == "continuous":
            if n == 1 or d["shots"][n - 2]["place"] != s["place"]:
                raise ValueError(f"Beat {n} needs a cutaway or ellipsis.")
            prior = {a["id"]: a["to"] for a in d["shots"][n - 2]["actors"]}
            if any(a["id"] in prior and math.dist(a["at"], prior[a["id"]]) > 0.025 for a in s["actors"]):
                raise ValueError(f"Beat {n} teleports a recurring actor across a continuous cut.")
        if s["place"] not in places or not actors <= cast or b["witness"] not in actors:
            raise ValueError(f"Beat {n} must stage the named participant in a known set.")
        shown |= actors
        local = prop_by_place[s["place"]]
        for a in s["actors"]:
            vector(a["at"], 2)
            vector(a["to"], 2)
            interval(a)
            if a["look_at"] and a["look_at"] not in (actors | local) - {a["id"]}:
                raise ValueError(f"Beat {n} needs a visible eyeline target or an empty look_at.")
            for c in a["cues"]:
                interval(c)
        if any(not 0 <= fx["at"] < 1 for fx in s["sounds"]):
            raise ValueError("Sound cues must fall within the beat.")
        if any(
            accent["focus"] not in actors | local or not 0 <= accent["at"] < 1
            for accent in s.get("accents", [])
        ):
            raise ValueError(f"Beat {n} needs an onstage target and time for each visual accent.")
        last = {}
        for e in s["events"]:
            vector(e["to"], 3)
            interval(e)
            if e["id"] not in local or e["start"] < last.get(e["id"], 0):
                raise ValueError(f"Invalid or overlapping prop cues in beat {n}.")
            if e["anchor"] and (
                e["anchor"].count("@") != 1
                or e["anchor"].split("@")[0] not in actors
                or e["anchor"].split("@")[-1] not in ("wrist1", "wrist-1", "spine", "head")
            ):
                raise ValueError(
                    f"Beat {n} has an unknown attachment. Use actor@wrist1, actor@wrist-1 or actor@spine."
                )
            last[e["id"]] = e["end"]
        cams = s["cameras"]
        if not cams or cams[0]["start"] != 0:
            raise ValueError(f"Beat {n} needs a camera from its first frame.")
        for i, c in enumerate(cams):
            if not c["focus"] or not set(c["focus"]) <= actors | local or not 1.1 <= c["size"] <= 14:
                raise ValueError(f"Camera {n} needs onstage targets and a 1.1–14 unit horizontal field.")
            if not 0 <= c["start"] < 1 or (i and c["start"] <= cams[i - 1]["start"]):
                raise ValueError(f"Beat {n} camera cuts must increase.")
    if not partial and (shown != cast or max((len(s["actors"]) for s in d["shots"]), default=0) < 4):
        raise ValueError("Put the ensemble together for at least one public demonstration.")


STORY_REVIEW = obj(verdict=enum("pass revise"), problem=S, correction=S)


TREATMENT = obj(
    lead_goal=S,
    other_person=S,
    other_goal=S,
    interference=S,
    everyday_object=S,
    first_read=S,
    second_read=S,
    price=S,
    public_change=S,
    joke_setup=S,
    joke_return=S,
)


def check_treatment(treatment):
    if any(not value.strip() for value in treatment.values()):
        raise ValueError("Give every treatment beat a concrete, filmable detail.")
    for a, b in [("lead_goal", "other_goal"), ("first_read", "second_read"), ("joke_setup", "joke_return")]:
        if tokens(treatment[a]) == tokens(treatment[b]):
            raise ValueError(f"The treatment repeats {a} for {b}.")


def screenplay(job, prompt, seconds):
    # Authored plans and resumes are already directed. Fresh model drafts get an independent editorial read.
    if (job / "story.json").is_file():
        return p.stage(job, "story", STORY, prompt, check_story)
    treatment = p.stage(
        job,
        "treatment",
        TREATMENT,
        prompt + " Before scripting, pitch two people who need incompatible outcomes from the same law. "
        "Give the supporting person a good reason to act. Plant one specific object in everyday use. "
        "Show how the lead's first intervention changes someone else's options, how the object later "
        "changes meaning, and what the lead gives up. Design a second use for an opening sight gag.",
        check_treatment,
    )
    prompt += "\nStage this chain of events in the spoken story and images: " + json.dumps(treatment)
    draft = p.stage(job, "story-draft", STORY, prompt, check_story, {"seconds": seconds})
    rubric = """Read the spoken lines as a first-time viewer. Find the early personal hook and public
demonstration, a second person's countermove, what the lead misunderstood, a planted physical detail,
and the later event which changes its meaning. Could the viewer predict the solution given the evidence?
Check the cost to each party and the second use of the joke. Quote or identify the weakest specific
beat and propose a filmable repair. Flag disconnected scenes, padding and a surprise rule at the end."""
    for revision in range(3):
        note = p.stage(
            job, f"story-edit-{revision}", STORY_REVIEW, rubric + "\n" + json.dumps(draft), lambda _: None
        )
        if note["verdict"] == "pass":
            p.save(job / "story.json", draft)
            return draft
        if revision < 2:
            draft = p.stage(
                job,
                f"story-rewrite-{revision + 1}",
                STORY,
                prompt + "\nDraft: " + json.dumps(draft) + "\nEdit: " + json.dumps(note),
                check_story,
                {"seconds": seconds},
            )
    raise ValueError("Story still needs editorial work: " + note["correction"])


def plan(job, idea, seconds, names=None, prop_id=None, prop_model=None):
    prompt = f"""Write an original {seconds}-second first-person animated social fable. Premise: {idea or "Invent a fresh town."}
Use about {round(seconds * 2.45)} spoken words. Give each beat 1–2 short spoken sentences.
In the first two sentences combine the public rule with a personal contradiction or immediate mishap. Start inside the impossible rule. Show a public example and a ridiculous, logical civic custom; give
at least four distinct people jobs, wants and actions. Give the protagonist a specific personal goal, a failed
ordinary attempt, an observable counterexample, and a costly decision that uses that evidence. Resolve
the goal on screen. End on a changed version of an earlier joke. An extra rule announced at the climax
is cheating. Keep what is counted, who knows it, and prop ownership consistent. For a named character whose relationship is hard to infer, an optional introductions entry can flash a short role caption keyed to unique spoken words. Use an empty list when the scene already explains the role. Use all functions
{ROLES}. because is a one-based earlier beat, or zero for an independent setup. witness is the ID
of the visible actor carrying the beat, the lead for choice. Use also_because for other earlier causes. The final decision should combine a failed approach with independently planted evidence. Encode causal effects in visible."""
    if names:
        prompt += (
            "\nRequested casting: "
            + json.dumps(names)
            + ". The lead and the first listed supporting role use those recurring actors."
        )
    if prop_id:
        prompt += f"\nMake {prop_id} a recurring physical clue." + (
            " Its appearance is " + json.dumps(prop_model) if prop_model else ""
        )
    story = screenplay(job, prompt, seconds)
    direction_prompt = f"""Direct this story in a vertical block-built world. Return reusable kit, cast, props and blocking.
Stage the public rule, failed attempt, counterexample and cost as visible changes. For a reveal, sync its authored timing fraction to a unique short spoken phrase. Use the opening 12 seconds for an image of the mechanism, one public example and a personal stake.
Cut when information changes: aim around 1–2 seconds in rapid passages, then hold longer for a difficult
choice or a joke. Compose foreground evidence, the acting pair and background work at different depths.
Set place.life to shoppers, workers, audience or quiet. Set place.light to daylight, late_sun or night according to the emotional turn. Fairground has market awnings, back lanes and a
Ferris wheel; glasshouse has greenhouse arches, seedling beds and a water tower. Use saturated accents
for plot objects. Practical raincloud drops rain below its base (stage near z=3.5); bouquet supports
CLOSED, OPEN and CLAP; cistern supports EMPTY, HALF and FULL. Use dialogue entries only for verbatim lines spoken by a visible character; leave voice-over unassigned. Set cue.play to accent for a single
native-speed action, cycle for repeating work, sustain to hold a pose. Camera move hold locks the frame,
follow tracks the target, arc orbits, punch closes in quickly and reveal opens out. Use brief splash, dust, petals or glint accents at physical contacts and discoveries. Attach each to an onstage focus ID. Reserve them for events a viewer should notice. All timings follow anchors. Use multiple cuts during long beats,
e.g. wide proof, insert, delayed reaction. A supporting actor should continue a different task while someone speaks.
Use the same coordinates across cuts in one place. Set look_at to a visible actor or prop ID, or empty for a neutral gaze. Actors face -Y at 0 degrees. X is screen right. Floor Z=0.
Actors are 2.5 units tall. Typical X range -3 to 3, Y range -1 to 3. Actor at/to are [x,y].
Keep coupled objects near the hands; animate handoffs and place evidence in camera focus. A prop at/to is [x,y,z],
its base. Event anchor is empty for world space or actor@wrist1 / actor@wrist-1 / actor@spine / actor@head; to becomes a local offset. Prop positions, yaw and display text persist between visits; events assign absolute position and yaw.
A hatch opens with event text OPEN and closes with CLOSED. Use a mark prop as an invisible, fixed camera target at its exact coordinates. The board has at most two centered lines, separated by a newline; use terse, large labels. Kit adds architecture. Invent landmarks or physical mechanisms with custom props (parts use local at, size, rotation in degrees, color). Use empty parts for stock props. Do not force a city elevator story onto another premise. The kit adds scenery,
not plot objects. Camera auto-centers on listed actor/prop IDs, size is horizontal visible world width
(2 portrait, 4 two-shot, 8 establishing). angle is degrees from straight ahead; elevation degrees above target;
drift is modest horizontal orbit in degrees. All starts/ends are beat fractions. Face and camera angles use degrees.
Give recurring people distinct silhouettes and use actions with purposeful timing. Match looks and witness IDs exactly.
Story: {json.dumps(story, ensure_ascii=False)}"""
    if prop_id:
        direction_prompt += f"\nInclude a prop with the exact ID {prop_id} in the world."
        if prop_model:
            direction_prompt += " Its saved visual model is " + json.dumps(prop_model)
    if (job / "direction.json").is_file():
        return story, p.stage(
            job, "direction", DIRECTION, direction_prompt, lambda d: check_direction(d, story)
        )
    # Keep long stories within a single CLI response budget. Each block resumes independently.
    catalog_schema = obj(looks=arr(LOOK), places=arr(PLACE), props=arr(PROP))

    def validate_catalog(catalog):
        if prop_id and not any(x["id"] == prop_id for x in catalog["props"]):
            raise ValueError(f"Include the named prop {prop_id}.")
        if prop_model:
            next(x for x in catalog["props"] if x["id"] == prop_id).update(prop_model)
        check_direction(dict(**catalog, shots=[]), dict(story, beats=[]), partial=True)

    catalog = p.stage(
        job,
        "world",
        catalog_schema,
        direction_prompt + " First design the entire episode cast and physical world.",
        validate_catalog,
    )
    design = dict(**catalog, shots=[])
    for first in range(0, len(story["beats"]), 3):
        stop = min(first + 3, len(story["beats"]))
        before = {
            item["id"]: dict(to=item["at"], text=item["text"], anchor="", spin=0)
            for item in catalog["props"]
        }
        for shot in design["shots"]:
            for event in shot["events"]:
                before[event["id"]] = {k: event[k] for k in ("to", "text", "anchor", "spin")}
        history = design["shots"][-1:] or []
        unseen = sorted(
            {a["id"] for a in catalog["looks"]} - {a["id"] for sh in design["shots"] for a in sh["actors"]}
        )

        def validate_block(block):
            if len(block["shots"]) != stop - first:
                raise ValueError(f"Supply exactly {stop - first} setups in this block.")
            trial = dict(catalog, shots=design["shots"] + block["shots"])
            check_direction(
                trial, dict(story, beats=story["beats"][:stop]), partial=stop < len(story["beats"])
            )

        blocking = f"""Direct ONLY beats {first + 1} through {stop}, one setup per beat. Use at least one
public scene with four co-present people. Include every cast member during the episode.
Use a continuous transition for adjacent setups that preserve marks, cutaway for a change of place,
ellipsis when time or blocking advances between cuts. First setup is a cutaway.
Harbor has a water gap at -1.25 < x < 1.25. Bridge and story mechanisms are props.
Available catalog: {json.dumps(catalog)}. Last setup: {json.dumps(history)}.
Prop state before this block: {json.dumps(before)}. Cast yet to appear: {json.dumps(unseen)}."""
        block = p.stage(
            job,
            f"blocking-{first + 1:03d}",
            obj(shots=arr(SHOT)),
            direction_prompt + "\n" + blocking,
            validate_block,
        )
        design["shots"].extend(block["shots"])
    check_direction(design, story)
    p.save(job / "direction.json", design)
    return story, design
