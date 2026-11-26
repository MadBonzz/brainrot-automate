"""Story and blocking contracts shared by the writer, director and renderer."""

import json
import math
import re
from . import planning as p
from . import assets, blocking, vistas
from .props import CATALOG
from .story_objects import KINDS as STORY_PROPS

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
STORY["properties"]["framing"] = dict(enum("portrait native"), readOnly=True)
STORY["properties"]["caption_style"] = dict(enum("spoken phrases"), readOnly=True)
STORY["properties"]["introductions"] = arr(obj(beat=I, actor=S, words=S, label=S))
STORY["properties"]["beats"]["items"]["properties"]["also_because"] = arr(I)
STORY["properties"]["beats"]["items"]["properties"]["edit_frames"] = dict(I, readOnly=True)
STORY["properties"]["beats"]["items"]["properties"]["pickup"] = dict(S, readOnly=True)
V = arr(N)
LOOK = obj(
    id=S,
    coat=p.COLOR,
    skin=enum("amber umber rose bronze"),
    hair=p.COLOR,
    hat=enum("none cap beret bun crown visor curls helmet bow veil"),
    uniform=enum("jacket apron sash satchel tunic bandleader gown dress"),
    badge=S,
    height=N,
)
LOOK["properties"]["form"] = enum("human paper rock scissors")
PLACE = obj(
    id=S,
    kit=enum(
        "arcade depot theater garden harbor boathouse fairground glasshouse bedroom vault classroom market aisle lockup belfry canyon grove dreamcourt rooftops corridor skyport undercity meadow duskfield"
    ),
    sign=S,
    trim=p.COLOR,
    wall=p.COLOR,
)
PART = obj(shape=enum("box sphere cylinder cone ring sail"), at=V, size=V, rotation=V, color=p.COLOR)
PROP_KINDS = (
    "raincloud bouquet cistern cake clock radio lantern signal mark custom lamp drum mirror hatch board scoreboard skytype door parcel trophy trumpet goose bench stand "
    + " ".join([*CATALOG, *STORY_PROPS])
)
PROP = obj(id=S, kind=enum(PROP_KINDS), place=S, at=V, scale=N, color=p.COLOR, text=S, parts=arr(PART))
PROP["properties"]["face_model"] = enum("plain creased fixed_grin")
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
ACTOR["properties"]["travel"] = obj(kind=enum("as_blocked enter exit"), side=enum("left right front back"), distance=N)
ACTOR["properties"]["travel"]["properties"]["coverage"] = enum("authored follow")
ACTOR["properties"]["gaze"] = arr(obj(at=N, focus=S))
ACTOR["properties"]["lift"] = V
ACTOR["properties"]["pitch"] = V
ACTOR["properties"]["pose"] = enum("live frozen")
EVENT = obj(id=S, anchor=S, to=V, text=S, spin=N, start=N, end=N)
CAM = obj(start=N, focus=arr(S), size=N, angle=N, elevation=N, drift=N)
# These keys may be absent in saved plans. Fresh model output supplies them explicitly.
PLACE["properties"]["finish"] = enum("flat textured")
PLACE["properties"]["grade"] = enum("natural moonlight lamplight sunset neon dream")
PLACE["properties"]["light"] = enum("daylight late_sun night")
PLACE["properties"]["life"] = enum("quiet shoppers workers audience")
CAM["properties"]["move"] = enum("hold follow arc punch reveal")
CAM["properties"]["vista"] = enum("stage " + " ".join(vistas.KINDS))
CAM["properties"]["vista_text"] = S
CAM["properties"]["reactions"] = arr(obj(actor=S, action=p.PERFORMANCE))
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
SHOT["properties"]["stage_clock"] = dict(N, readOnly=True)
SHOT["properties"]["accents"] = arr(obj(kind=enum("splash petals dust glint"), focus=S, at=N))
SHOT["properties"]["selective_color"] = arr(S)
SHOT["properties"]["atmosphere"] = obj(
    kind=enum("none fog sunpatch eclipse flicker blackout dawn"), start=N, end=N
)
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
    minimum_cast = 1 if "source_cut" in story else 4
    if not minimum_cast <= len(cast) <= 10 or story["lead"] not in cast:
        raise ValueError(f"Give {minimum_cast}–10 people distinct jobs and wants and identify the lead.")
    locked = [b["edit_frames"] for b in beats if "edit_frames" in b]
    if any("pickup" in b and (not isinstance(b["pickup"], str) or not b["pickup"].strip()) for b in beats):
        raise ValueError("A dialogue pickup needs a spoken line.")
    budget = story["seconds"] * 30
    if (
        any(type(v) is not int or v < 3 for v in locked)
        or sum(locked) + 3 * (len(beats) - len(locked)) > budget
    ):
        raise ValueError("Locked takes exceed the edit duration or have fewer than three frames.")
    if len(locked) == len(beats) and sum(locked) != budget:
        raise ValueError("Fully locked takes must add up to the edit duration.")
    for card in story.get("introductions", []):
        if (
            card["actor"] not in cast
            or not 1 <= card["beat"] <= len(beats)
            or not 0 < len(card["label"]) <= 28
        ):
            raise ValueError("A cast introduction needs a known actor, beat, and label of 1–28 characters.")
        phrase_starts(beats[card["beat"] - 1]["line"], [dict(at=0.5, words=card["words"])])
    if "source_cut" in story:
        # An existing story can end in a trap or a failed choice. Preserve its authored beat order.
        source = story["source_cut"]
        if not isinstance(source, str) or not source.strip() or len(beats) < 2:
            raise ValueError("An adaptation needs a named source and at least two beats.")
        for n, b in enumerate(beats):
            if (
                b["witness"] not in cast
                or not b["line"].strip()
                or not b["visible"].strip()
                or not 0 <= b["because"] <= n
            ):
                raise ValueError(f"Invalid adapted beat {n + 1}.")
        return
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
    d = blocking.expand(d)
    cast = unique(d["looks"], "looks")
    places = unique(d["places"], "places")
    props = unique(d["props"], "props")
    if (
        cast != {a["id"] for a in story["cast"]}
        or cast & props
        or len(places) < (1 if "source_cut" in story else 2)
    ):
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
        if x.get("face_model", "plain") != "plain" and x["kind"] != "stalker":
            raise ValueError("The creased and fixed-grin faces fit the articulated stalker practical.")
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
            for axis in ("lift", "pitch"):
                if axis in a:
                    vector(a[axis], 2)
            if a["look_at"] and a["look_at"] not in (actors | local) - {a["id"]}:
                raise ValueError(f"Beat {n} needs a visible eyeline target or an empty look_at.")
            prior_gaze = -1
            for glance in a.get("gaze", []):
                if (
                    glance["focus"] not in (actors | local) - {a["id"]}
                    or not prior_gaze < glance["at"] < 1
                    or glance["at"] < 0
                ):
                    raise ValueError(f"Beat {n} contains an invalid gaze change.")
                prior_gaze = glance["at"]
            for c in a["cues"]:
                interval(c)
        if any(not 0 <= fx["at"] < 1 for fx in s["sounds"]):
            raise ValueError("Sound cues must fall within the beat.")
        if any(
            accent["focus"] not in actors | local or not 0 <= accent["at"] < 1
            for accent in s.get("accents", [])
        ):
            raise ValueError(f"Beat {n} needs an onstage target and time for each visual accent.")
        if not set(s.get("selective_color", [])) <= actors | local:
            raise ValueError("Color isolation needs a visible subject.")
        if "atmosphere" in s and s["atmosphere"]["kind"] != "none":
            interval(s["atmosphere"])
        if "stage_clock" in s and (not math.isfinite(s["stage_clock"]) or s["stage_clock"] < 0):
            raise ValueError("A reused take needs a finite, nonnegative stage clock.")
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
            replies = c.get("reactions", [])
            if len(replies) > 1 or (
                replies
                and (
                    c.get("vista", "stage") != "stage"
                    or not any(
                        a["id"] == replies[0]["actor"] and a.get("pose") != "frozen" for a in s["actors"]
                    )
                    or replies[0]["action"] not in p.MOTIONS
                )
            ):
                raise ValueError(f"Camera in beat {n} needs a single onstage reaction and a known action.")
            if c.get("vista", "stage") not in ["stage", *vistas.KINDS]:
                raise ValueError(f"Unknown location view in beat {n}.")
            if not c["focus"] or not set(c["focus"]) <= actors | local or not 1.1 <= c["size"] <= 14:
                raise ValueError(f"Camera {n} needs onstage targets and a 1.1–14 unit horizontal field.")
            if not 0 <= c["start"] < 1 or (i and c["start"] <= cams[i - 1]["start"]):
                raise ValueError(f"Beat {n} camera cuts must increase.")
    if not partial and (
        shown != cast
        or ("source_cut" not in story and max((len(s["actors"]) for s in d["shots"]), default=0) < 4)
    ):
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


def saved_story_schema(saved):
    return (
        dict(STORY, properties={**STORY["properties"], "source_cut": S}) if "source_cut" in saved else STORY
    )


def screenplay(job, prompt, seconds):
    # Authored plans and resumes are already directed. Fresh model drafts get an independent editorial read.
    if (job / "story.json").is_file():
        saved = json.loads((job / "story.json").read_text(encoding="utf8"))
        return p.stage(job, "story", saved_story_schema(saved), prompt, check_story)
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
Use finish textured for patterned street surfaces and architecture. Choose grade natural, moonlight, lamplight, sunset, neon or dream to suit the light source. Choose a specific kit such as market, bedroom, lockup, grove, belfry, skyport or canyon. Stage handheld items at the wrist. Give creatures and large machinery their own low or profile view. An actor can change gaze during the shot with gaze entries (at, focus), rise/fall with lift [startZ,endZ], or lean with pitch [startDegrees,endDegrees]. For a limited-color world, selective_color lists the IDs that retain color. Use an empty list for natural full color, normal human form and live pose for ordinary people, [0,0] for unused lift and pitch, and atmosphere kind none in clear scenes. Choose scoreboard for a ranked list and skytype for floating command text. Atmosphere supports fog, sunpatch, eclipse, flicker, blackout and dawn across start/end fractions.
When people run, cross a threshold, queue for a turn, rush to help, or back out of danger, show the distance they cover. Give them different departure times. A hand gesture alone cannot get someone to a door. For a staged entrance or exit, set at and to to the same contact mark and specify travel.kind enter or exit, its side and distance. The director keeps the arrival point and finds a lane past the cast. Use as_blocked when the actor is still or has explicit at/to. Use travel.coverage follow when the crossing is the new information. Use authored when another visible clue takes precedence. Time travel in seconds worth of the beat, before a handoff or after the decision. Hold still on purpose when silence or immobility is the rule.
Actors are 2.5 units tall. Typical X range -3 to 3, Y range -1 to 3. Actor at/to are [x,y].
A stalker practical can have face_model creased or fixed_grin when its expression is evidence. Use plain for other props. Normally use vista stage, empty vista_text and empty reactions. When a longer camera shows a cause, its reactions array may name one onstage actor and a matching performance action for a separately filmed reverse angle near its end. Preserve silence or intentional stillness when the rule needs it. A torch_detail camera sweeps a handheld light across the staged subject in an otherwise dark room. Reserve it for an actual light search and aim it at the object the character needs to find. For paper_detail or phone_detail, supply the clue in vista_text, up to 72 characters. A dedicated location view can replace a camera when geography itself is evidence. Use desert_queue for a queue that crosses the landscape, balloon_fleet for homes above the clouds, cell_tower for stacked prison tiers, or flooded_gym for a submerged basketball court. Only choose a view when its subject appears in the story. It replaces everything seen from that camera, so use stage for performances and clues carried by a person.
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
            item["id"]: dict(to=item["at"], text=item["text"], anchor="", spin=0) for item in catalog["props"]
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
