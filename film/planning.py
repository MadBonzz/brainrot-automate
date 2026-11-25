"""The single provider boundary. All creative decisions go through generate()."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def arr(items):
    return {"type": "array", "items": items}


def choices(values):
    return {"type": "string", "enum": values.split()}


PRESETS = Path(__file__).resolve().parent / "presets"
MOTIONS = json.loads((PRESETS/"motions.json").read_text(encoding="utf8"))
CAMERAS = json.loads((PRESETS/"cameras.json").read_text(encoding="utf8"))

S = {"type": "string"}
N = {"type": "number"}
I = {"type": "integer"}
COLOR = choices("navy teal mint gold rust red cream charcoal lavender blue brown")
STORY = obj(title=S, rule=S, planted_clue=S, payoff=S, beats=arr(S))
PIECE = obj(shape=choices("box sphere cylinder cone"), x=N, y=N, z=N, width=N, depth=N, height=N, color=COLOR)
PROP = obj(kind=choices("clock signal radio lantern custom"), label=S, color=COLOR, parts=arr(PIECE))
PERFORMANCE = choices(" ".join(MOTIONS))
SHOT = obj(beat=I, set=choices("station archive rooftop hallway"), camera=choices(" ".join(CAMERAS)),
           lead=PERFORMANCE, witness=choices("absent "+" ".join(MOTIONS)),
           face=choices("calm worried startled happy"), prop=choices("still pulse turn vanish appear"),
           turn_degrees=N, anchor=S, effect=choices("none knock bell static click rumble"), hold_ms=I)
DESIGN = obj(lead_coat=COLOR, witness_coat=COLOR, location_sign=S, prop=PROP,
             score=choices("suspense wonder quiet"), shots=arr(SHOT))


def save(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf8")
    tmp.replace(path)


def check(value, schema, field="result"):
    typ = schema["type"]
    good = {"string": isinstance(value, str), "number": type(value) in (int, float),
            "integer": type(value) is int, "array": isinstance(value, list), "object": isinstance(value, dict)}
    if not good[typ] or ("enum" in schema and value not in schema["enum"]):
        raise ValueError(f"Invalid {field}: {value!r}")
    if typ == "object":
        if set(value) != set(schema["properties"]):
            raise ValueError(f"Wrong fields at {field}")
        for key, child in schema["properties"].items():
            check(value[key], child, f"{field}.{key}")
    if typ == "array":
        for i, item in enumerate(value):
            check(item, schema["items"], f"{field}[{i}]")


def generate(prompt, schema, job):
    """Swap this function for a local model when desired. Return parsed JSON."""
    exe = shutil.which("codex")
    if not exe:
        raise RuntimeError("Install @openai/codex and run codex login in this terminal.")
    with tempfile.TemporaryDirectory(dir=job) as temp:
        work = Path(temp).resolve()
        fmt, result = work / "schema.json", work / "result.json"
        save(fmt, schema)
        cmd = [exe, "exec", "-c", 'model_provider="openai"', "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--output-schema",
               str(fmt), "-o", str(result), "-"]
        env = os.environ.copy()
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY"):
            env.pop(key, None)
        status = subprocess.run([exe, "login", "status"], env=env, capture_output=True, encoding="utf8", errors="replace")
        if status.returncode or not re.search(r"logged in (?:using|with) chatgpt", status.stdout + status.stderr, re.I):
            raise RuntimeError("Run codex login and choose Sign in with ChatGPT before generating a movie.")
        # On Windows npm may provide codex.cmd. All user-authored text travels via stdin.
        proc = subprocess.run(cmd, input=prompt, encoding="utf8", errors="replace",
                              cwd=work, env=env, capture_output=True)
        if proc.returncode or not result.exists():
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            raise RuntimeError("Codex generation failed. Check codex login status and your plan limits.\n"
                               + "\n".join(detail[-8:]))
        return json.loads(result.read_text(encoding="utf-8-sig"))


def story_checks(value):
    if not 3 <= len(value["beats"]) <= 60 or any(not line.strip() for line in value["beats"]):
        raise ValueError("The story needs 3–60 nonempty narration beats.")


def design_checks(value, story):
    expected = list(range(1, len(story["beats"])+1))
    if [s["beat"] for s in value["shots"]] != expected:
        raise ValueError(f"Return exactly one shot per beat, numbered {expected}.")
    def words(text):
        return re.findall(r"[^\W_]+(?:'[^\W_]+)*", text.casefold().replace("’", "'"))
    for shot, line in zip(value["shots"], story["beats"]):
        if len(words(shot["anchor"])) != 1 or words(shot["anchor"])[0] not in words(line):
            raise ValueError(f"Shot {shot['beat']} needs an anchor word from this line: {line}")
        if abs(shot["turn_degrees"]) > 720:
            raise ValueError("Use a rotation within two full turns.")
        if not 0 <= shot["hold_ms"] <= 2000:
            raise ValueError("hold_ms must be 0–2000")
        if shot["camera"] == "witness" and shot["witness"] == "absent":
            raise ValueError("A witness camera needs a visible witness.")
    prop = value["prop"]
    if len(prop["parts"])>30 or (prop["kind"] == "custom" and not prop["parts"]):
        raise ValueError("Custom props require 1–30 primitive parts.")


def stage(job, name, schema, prompt, validate, fixed=None):
    fixed = fixed or {}
    generated_schema = obj(**{k:v for k, v in schema['properties'].items() if k not in fixed}) if fixed else schema
    target = job / (name + ".json")
    if target.exists():
        value = json.loads(target.read_text(encoding="utf8"))
        if isinstance(value, dict):
            value.update(fixed)
        check(value, schema)
        validate(value)
        return value
    for attempt in range(2):
        try:
            value = generate(prompt, generated_schema, job)
            if isinstance(value, dict):
                value.update(fixed)
            check(value, schema)
            validate(value)
        except ValueError as exc:
            if attempt:
                raise
            prompt += "\nYour previous response failed validation. Fix this: "+str(exc)
            continue
        save(target, value)
        return value


def plan(job, premise, seconds, characters=None, prop_id=None, saved_prop=None):
    style = ("Write original first-person speculative fiction for a vertical block-character short. "
             "Open with a concrete impossible rule; plant a visible clue; let a character test it; "
             "finish with a visual payoff that changes what the clue means. Conversational, economical. "
             "The camera can show one recurring physical clue, up to two people, and station, rooftop, "
             "archive or hallway sets. A clue may also be designed from simple geometry. No brand names. ")
    n = max(4, min(36, round(seconds / 4.2)))
    cast_note = ''
    if characters:
        cast_note = ('Use these recurring characters in the assigned roles: '+json.dumps(characters)+
                     '. A returning actor keeps their appearance. Avoid plot points that require a particular wardrobe. ')
    if prop_id:
        cast_note += f'The recurring clue is called {prop_id}. '
    if saved_prop:
        cast_note += ('This clue already exists. Stage the story around the following prop. '
                      'Its design will be inserted automatically. '+json.dumps(saved_prop)+' ')
    prompt = (style+cast_note+f"Premise: {premise or 'Invent your own fresh premise.'} Aim for {round(seconds*2.3)} spoken words "
            f"across roughly {n} narration beats. Each beat is 1–2 short spoken sentences and one "
            "distinct picture. No stage directions in the beats. Return only the structured result.")
    story = stage(job, "story", STORY, prompt, story_checks)
    prompt = (cast_note+"Direct this story shot by shot as a fully animated 3D short. Return only the structured result. "
            "Use one shot per beat numbered from 1, preserving the order. Choose the exact ONE spoken word that "
            "triggers each cue. The rig action, clue change and sound start at that word. Pick wide for geography, "
            "face or witness for reactions, clue to reveal details, shoulder for the lead facing the clue. "
            "Use purposeful variety. Keep wardrobe and place continuous. A shot’s prop state is its own staging: "
            "still = present, appear/vanish change on cue, turn rotates by signed turn_degrees (use 0 for other cues), pulse changes size. Rotation persists across cuts. For custom props provide "
            "1–30 blocks, cones, upright cylinders or ellipsoids in local coordinates. x horizontal, y depth, z up. "
            "Fit within x ±0.8, y ±0.5, z 0–1.4; dimensions positive. Otherwise use empty parts. "
            "The clue label is fixed and legible, 12 characters maximum, scene sign 20 maximum. "
            "hold_ms is 0–2000 ms after each narrated line; reserve longer pauses for reveals. "
            "Use music mood quiet, wonder, or suspense and occasional purposeful effects. Story:\n"+json.dumps(story))
    design = stage(job, "direction", DESIGN, prompt, lambda d:design_checks(d, story),
                   {'prop':saved_prop} if saved_prop else None)
    return story, design
