# Shortfilm

Generate an original, narrated, vertical block-animation short with a ChatGPT subscription and local tools. You can start with an idea or a blank prompt. The output is an H.264 MP4 with AAC narration, phrase captions, synthesized music and timed sound effects.

## Windows setup

Install Blender, FFmpeg, and the official Codex CLI. Node/npm and uv are assumed available. In PowerShell:

```powershell
winget install --id BlenderFoundation.Blender -e --source winget
winget install --id Gyan.FFmpeg -e --source winget
npm install -g @openai/codex
codex login
codex login status
```

Choose **Sign in with ChatGPT**. The pipeline checks the saved authentication mode and invokes the OpenAI provider. Subscription usage limits apply. No OpenAI API key or paid voice service is needed. Reopen the terminal if a newly installed executable is missing from PATH. The runner also searches Blender's standard Windows installation folder. Windows PowerShell 5.1 supplies the System.Speech synthesizer. The Python program uses the standard library.

## macOS setup

With Homebrew installed, run:

```bash
brew install uv ffmpeg-full
brew install --cask blender codex
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
codex login
```

Use the full FFmpeg formula for its libass caption filter. It is keg-only. To reuse the PATH setting in new terminals, add that export line to your shell profile. macOS provides the narrator through its built-in `say` command. The runner also finds Blender in the system and user Applications folders.

From the extracted folder, run `uv run movie.py --demo --quality preview` to check your local installation, or `uv run movie.py` to generate a new story. A native Mac render has not been verified.

## Generate a movie

Open a terminal in the folder containing `movie.py`.

```powershell
uv run movie.py
uv run movie.py --idea "Every mirror in a railway station is one train ahead." --seconds 90
```

Each command creates a fresh episode. The default length is 45 seconds. The writer first develops competing motives, an everyday object, two readings of the same evidence and a returning joke. It then drafts a first-person story with a public rule, a failed attempt, an observable exception and a consequential choice. A separate editor checks the logic and humor and rereads revisions. A decision can have multiple earlier causes. The director defines the cast and physical world once, then blocks three beats per call with the prior character marks and prop state. The runner checkpoints each response. Final output is 1080 × 1920 at 30 fps.

**Render the three included two-minute films** with these commands. They use the same directing and rendering path as generated plans and can run offline after installation.

```powershell
uv run movie.py --demo --quality review
uv run movie.py --from-plan example/floor-ten --quality review
uv run movie.py --from-plan example/bell-bay --quality review
```

The default demo, *The Last Clap at Our Wedding*, puts eight named residents at a fair and a nursery. Its raincloud, spring-loaded bouquet and wheeled tank carry the story from the opening accident to the last gag. The [timecoded reference study](docs/shorts-reference-study.md) records the 13 films examined and how they informed this episode.

*Taking Separate Lifts* casts nine people in a municipal lift, a freight depot and a rooftop orchestra. *The Quietest Drum in Bell Bay* casts seven in a harbor where paired lanterns form temporary bridges. Each folder contains the spoken script, the cast's motives, the causal links between beats, and the complete camera and performance direction.

To review compositions before a long render, append `--storyboard`. The runner samples the middle of every camera shot and writes contact sheets and individual frames. The accompanying blocking review reports edit timing, camera treatments and sustained overlaps between actors. Edit the saved job and use `--resume <job-folder>` to render it. Each completed ensemble movie includes a `render-review.json` with the decoded frame count, audio and video duration checks and repeated-frame measurements from the raw animation clips.

## Reuse a character across episodes

Give a character an ID the first time you cast them. Use that ID again in either role.

```powershell
uv run movie.py --idea "The station clock counts backwards." --lead mira --witness jo
uv run movie.py --idea "The last train arrives on the roof." --lead jo --witness mira
uv run movie.py --list-cast
```

On first appearance Blender saves each named model under `assets/characters/`. The lead flag binds the protagonist. The witness flag binds the first supporting cast member in the story's cast list. Other roles also get persistent model files. Auto-generated IDs include the character name and appearance hash. The badge and height belong to this episode's costume. Existing named models keep their appearance when cast in a different role.

The job's `cast.json` records the resolved paths and hashes. Use `--cast-dir` to share characters between project copies, or `--asset-dir` to share the whole collection. When customizing a Blender model, preserve the Character collection and tagged joints.

## How a scene is directed

| Component | What the director controls |
|---|---|
| World | Architecture, palette, signs, custom landmarks and reusable instruments, machines, buildings and practical props. Location kits cover a civic arcade, freight depot, rooftop theater, garden, coastal harbor, barbershop or boathouse, fairground and glasshouse. Each place can specify shoppers, an audience, workers or a quiet background, as well as daylight, late sun or night. |
| Ensemble | The actor's start and end marks, facing, eyeline, reaction, costume and one or more timed performances. Adjacent continuous setups must agree on the actors' marks. A cutaway or a time jump can establish new positions. |
| Motion | Walk cycles follow distance traveled. Bodies turn into the path and settle into the final facing. A shared pose library layers independently timed gestures over gait, breathing, eye blinks and head motion. Cues use native-speed accents, repeated cycles or held poses. On-screen dialogue drives mouth timing. Splashes, dust, petals and glints can mark a physical contact. |
| Props | Objects keep world positions, text and ownership across shots and returns to a location. Objects can transfer between hands, move into a chute or attach to an actor. Named models can be reused across episodes with `--prop-id`. |
| Camera | Multiple perspective cuts per spoken beat. Each can follow one actor, several subjects, a moving prop or a fixed point. Choose a locked hold, follow, orbit, punch-in or pullback. Close shots check foreground occlusion at three points. |
| Timing | Map a reveal to an exact spoken phrase. The director's camera, sound, gesture and mechanism cues follow the narration clock. A short cast label can appear on the first spoken mention when the viewer needs a relationship explained. Windows can supply word boundaries. Linux and macOS estimate word onsets within each recorded line. |
| Reuse | Shared character files, motion recipes, prop designs, voices, scores and rendered clips. The shot cache includes the state carried into the shot and the versions of the Blender code and visible assets. |

### Film a reference with a saved coverage sheet

A coverage sheet ties each spoken line to a location, actors, actions, working props and camera cuts. Compile it into the same plan format used by the ordinary movie command. Its `source` field identifies the original story and preserves its ending. A solo adaptation can keep a solo cast.

```bash
python tools/coverage_plan.py coverage.json plans/my-cut
python movie.py --from-plan plans/my-cut --quality review --storyboard
python movie.py --resume <job-folder> --quality review
python tools/compare_cuts.py reference.mp4 <job-folder>/review/movie.mp4
```

A coverage row has five strings in order. They specify the set, blocking, props, cameras and narration. For example, the camera string `0:P0:3:hold:0:8 0.48:A0:2:follow:15:5` opens on the first prop, then cuts to the first cast member. Each camera token gives the beat fraction, targets, horizontal field width, move, yaw and elevation. Use `A0+A1` for a two-shot or `W` for everyone onstage. A typical prop string is `key:gold@0,1,.8>hand0`. A movement such as `0:walk@-2,0>1,0` uses the cached walk and moves the actor through the set. A dash in the action field freezes the character, including the face.

The `anchors` object maps a one-based beat number to entries with `at` and `words`. At render time the narrator's timing moves camera cuts, gestures, gaze changes and effects together. For an edit that preserves an approved take, copy its frame count into the beat's `edit_frames` and its original animation clock (seconds) into the shot's `stage_clock`. The remaining setups share the remaining running time. The shot cache still checks the cast, set, props, staging, motion and renderer version.

Use `--prepare-only` with an ensemble plan to write narration, captions, the sound mix and the timed shot list without starting a picture render. Use the same job folder and quality when resuming. A location can specify `grade` as `natural`, `lamplight`, `moonlight`, `sunset`, `neon` or `dream`. Grading runs before captions. It reuses captured shots, and skips scenes that reserve color for named clues.

The comparison command decodes both local movies, samples their upper-center images eight times per second and reports large visual changes per minute. This measure responds to large in-shot movement as well as cuts. For an excerpt in a longer video, provide `--source-offset` in media seconds, `--source-seconds` in original seconds and `--source-rate` in media seconds per original second. Inspect faces, prop contacts, scale and the order of clues alongside the measurement.

### Reuse and review a prop

The director can choose 50 tabletop instruments, machines and miniatures alongside the four original props. A saved direction can select the compass with this prop entry.

```json
{"kind": "gimbal_compass", "label": "NORTH", "color": "rust", "parts": []}
```

A turn rotates the working part on models with an axle, such as the compass needle or the desk globe. Other models turn as a whole. The renderer seats the contact points on the tabletop, mounts the nameplate on the pedestal, and fits the clue close-up around the complete turn and pulse. A vanished prop stays hidden across cuts until an appear cue. A shot starting with a reveal can open on an empty pedestal.

This command reviews the machines in Blender and saves the rendered views.

```bash
blender -b --factory-startup --python-exit-code 1 --python tools/review_props.py -- --batch machines --out review/props/machines --render
```

Use `instruments`, `machines`, `miniatures`, or `legacy`. Add `--only tabletop_fan` to isolate one model in its batch. Omit `--render` for geometry, playback and camera checks only. The [prop review](docs/prop-review.md) lists the designs, their turn behavior, and the tests performed.

### Add a movement once

Run `uv run movie.py --list-actions` to see all 112 movements. The catalog includes eight basic motions and 104 multi-stage performances in six pose sheets under `film/presets/performances/`. A shot can use any one per actor, for example `"lead": "lift_a_crate", "witness": "double_take"`.

| Pose sheet | Examples |
|---|---|
| `gestures.json` | Cover the ears, wipe the brow, conduct a downbeat, bow and rise |
| `footwork.json` | Side-step and collect, pivot a quarter turn, cross a gap, jump and land |
| `pantomime.json` | Catch and cushion a parcel, turn a crank, fold a map, paddle a canoe |
| `signals.json` | Clap three times, make a time-out sign, sneeze into an elbow, signal a fork in the path |
| `rhythm.json` | Do a half-turn hop, a grapevine, a Charleston kick, or a tightrope weight shift |
| `daily_tasks.json` | Check a wristwatch, wring out a cloth, deal three cards, play air accordion |

Copy a similar entry to add a performance. The `frames` array gives the timing at 24 fps. Each row in `pose` contains one value per frame. Keys such as `elbow1.x` rotate the named joint in degrees. A leading `d` in the axis, such as `root.dz`, translates it in scene units. The sides `1` and `-1` refer to the model's positive and negative X sides. Start at zero and match the endpoints of loops. The director discovers the name automatically. Existing clips in `film/presets/motions.json` keep their original radians-based format.

For flat-floor moves, `ground` keeps the lowest sole in contact. Optional `plant` intervals such as `"1:8:17"` pin that shoe's center horizontally and keep its sole on the floor over the specified authored frames. `floor` prevents penetration while allowing airborne phases. The renderer upgrades the stock cast with spine, elbow, knee and wrist pivots when loading older character files. Saved originals retain their appearance. The foot solver uses both tagged stock shoes and assumes a flat floor. The pantomimes animate the character. A physical prop that must follow a hand requires staging for that scene.

In the legacy two-character renderer, a late narration cue can extend the shot so the new performance has at least 70% of its authored duration to play. The longer of the lead and witness movements determines the minimum. The original eight presets keep their previous timing.

### Review an animation batch without a story or model call

From the project root, run the following with Blender on your PATH. Choose any of the six pose sheet names in the table above, omitting the `.json` extension.

```bash
blender -b --factory-startup --python-exit-code 1 --python tools/review_motions.py -- --batch gestures --out review/gestures --render
```

The review notes cover the [first 54 performances](docs/motion-review.md) and the [next 50 performances](docs/motion-review-2.md). The command builds the saved Blender Actions, measures normal and late-cue playback at 12 and 24 fps, and writes per-motion results to `checks.json`. With `--render`, it also writes a labeled two-view MP4 for each movement and its source frames. FFmpeg with drawtext is needed for those MP4s. Omit `--render` for measurements only. Pass `--character path/to/actor.blend` to check an existing stock-compatible cast file. Optional hand landmarks specify target positions and tolerances in scene units. A pose sheet can also test hand spacing, forearm direction, separation of the feet, and sole clearance at a particular beat, including compressed playback.

## Use Codex as the only entry point

Start Codex in this folder and ask it to make a film. Or launch it non-interactively:

```powershell
codex exec --skip-git-repo-check --sandbox workspace-write "Make a 60-second original mystery short using this project's AGENTS.md. Invent the premise and render the final MP4."
```

This path has one outer Codex session author and direct the episode. It invokes the same renderer using `--from-plan`. Your local sandbox/application permissions apply. For unattended batch use, the Python entry point gives you a predictable sequence of structured CLI calls.

## Fast preview, resume, or render an existing plan

```powershell
uv run movie.py --quality preview --seconds 25
uv run movie.py --resume ".\movies\YOUR-JOB-FOLDER" --quality final
uv run movie.py --demo --quality preview
uv run movie.py --from-plan ".\example" --quality final
```

Ensemble preview renders at 432 × 768, review at 720 × 1280 and final at 1080 × 1920. All three render 30 distinct timeline samples per second. Exact repeats are measured before captions, including intentional stillness. The older *One Minute Back* plan is available via `--from-plan example`. Legacy plans and old jobs retain their original schema and render timing.

The renderer schedules the story's chosen duration, paces each line to fit, and mixes local narration, foley and music. The exported `movie.mp4` appears inside the job's quality folder. To repeat the delivery checks on an existing ensemble render, use `python -m film.ensemble_review <job/quality>`.

## Later, switch the LLM

Implement the same `generate(prompt, schema, job) -> dict` interface in `film/planning.py` against your local model. The story and direction schemas, semantic validation, speech, animation, and export remain reusable. No local model server is used by the included version.

Official CLI references: [non-interactive mode](https://developers.openai.com/codex/noninteractive/) and [ChatGPT sign-in](https://developers.openai.com/codex/auth/).
