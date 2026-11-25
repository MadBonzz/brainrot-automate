# Shortfilm

Generate an original, narrated, vertical block-animation short with a ChatGPT subscription and local tools. You can start with an idea or a blank prompt. The output is an H.264 MP4 with AAC narration, word captions, original synthesized background music, and sound effects.

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

Each command creates a **new** movie. With no premise, Codex invents the story. The default target is about 45 seconds. For pacing closer to the reference Shorts, use `--seconds 155`. Actual duration is determined by the narration and directed pauses. The default final render is 1080 × 1920 at 24 fps.

The path is printed at the end, typically `movies/<job>/final/movie.mp4`. A job also contains its request, story, direction, voice files, reusable shot clips, captions, and timeline. The two creative calls produce and validate structured JSON. A malformed plan can trigger a repair call. Blender and FFmpeg render locally.

## Reuse a character across episodes

Give a character an ID the first time you cast them. Use that ID again in either role.

```powershell
uv run movie.py --idea "The station clock counts backwards." --lead mira --witness jo
uv run movie.py --idea "The last train arrives on the roof." --lead jo --witness mira
uv run movie.py --list-cast
```

On first appearance Blender saves the character's block model, colors, and joint hierarchy to `assets/characters/<id>.blend` in the extracted project. Later episodes load that file, so Mira keeps her appearance even when the new direction suggests another coat. Each shot applies its own movement and expression to a fresh copy. The planner also receives the explicitly assigned character IDs. A witness gets a file when they appear on screen.

Without flags, the renderer picks an ID from the role and coat, such as `lead-rust`, and saves or reuses it automatically. The built-in generator has two base looks with coat variations. A new ID saves a separate character and can start with the same look as another. To customize a recurring actor, open its file in Blender. Keep the `Character` collection and the tagged joints and facial controls. Put any new accessories in that collection and parent them to the appropriate body part. The renderer uses object colors.

The movie's `cast.json` records the character files used. `--resume` remembers casting and checks for model edits before reusing a shot. To share a cast between project copies, use the same `--cast-dir "path/to/characters"` when starting each movie. To move a cast between computers, copy the folder containing the `.blend` files.

## Reuse animation, sets, props, and sound

Reuse is on by default. Keep the `assets/` folder when updating the scripts. Use `--asset-dir "path/to/assets"` to share the entire collection between project copies. Each episode records its Blender asset paths and hashes in `assets.json`.

| Asset | How it is reused |
|---|---|
| Character animation | The director selects a motion by name for either actor. On first use the renderer turns its pose curves into native Blender Actions and saves them in `assets/motions/`. Future shots attach the same Actions to the corresponding joints. Each actor gets their own start time and placement. Walk cycles repeat. One-time gestures hold their ending pose. |
| Sets | Each of the four sets has one editable Blender file in `assets/sets/`. Shots load the chosen set and add the episode's sign. |
| Props | Stock props reuse the same geometry across colors and labels. Custom props reuse matching geometry. Give a clue a name with `--prop-id station-clock` to bring its complete design back in another story. The runner fills in a known prop automatically. `--list-props` shows saved names. |
| Cameras and visual cues | Six framing presets live in `film/presets/cameras.json`. Camera pushes, facial expressions, and prop reveals use shared rendering code. The episode supplies the framing, timing and rotation. |
| Audio | Effects and looping music beds are saved as WAV files. An identical narration line can reuse its WAV and word marks on the same machine and voice configuration. Windows detects the voice, Linux uses SLT, and macOS can share lines between jobs when `SHORTFILM_VOICE` names an installed voice. With the macOS system default, voice reuse stays within the job. Captions, fades and the mix follow the new timeline. |
| Rendered shots | Matching visuals and timing reuse a completed clip across episodes. The signature includes the visible actors, motion and geometry files, camera, cue frame, shot duration, renderer version and resolution. Changing an action refreshes the shots that use it. Music or caption edits can reuse the visual clip when the timing matches. |

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

A late narration cue can extend the shot so the new performance has at least 70% of its authored duration to play. The longer of the lead and witness movements determines the minimum. The original eight presets keep their previous timing.

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

Preview is 360 × 640 at 12 fps. The preview-to-final command reuses the same generated script, direction, and voice. A resume at the same quality also reuses matching completed shot clips. To change one shot, edit the job's `direction.json` and resume. A text edit that changes a cue word also requires adjusting that shot's anchor. The included example, *One Minute Back*, contains a saved six-shot story and direction. Demo mode skips the CLI so you can check local rendering on its own.

## What actually gets generated

- **Story and direction.** Two Codex CLI calls by default. The first writes the complete narration. The second chooses the set, framing, actions, cue words, pauses, palette, prop, music mood, and effects. The semantic validator checks the shot count, actor visibility for witness close-ups, and whether the cue word occurs in the actual line.
- **Cast and scenery.** Blender loads the cast, set, clue and movement files selected for the shot. The director can design a custom clue from geometry. Clock hands and prop rotations persist across cuts.
- **Audio and captions.** Windows renders voice to WAV through its installed speech voice and uses reported word positions when available. On Linux, an FFmpeg build with `flite` and the SLT voice is required. The macOS and Linux backends estimate individual word timings within each synthesized line. Caption placement moves higher for clue close-ups. Sound and prop changes use the same cue word. Music and foley are synthesized locally; the voice is a basic system voice.
- **Rendering.** Tested here with Blender 4.3.2 and FFmpeg on Linux. Blender's Workbench renderer renders the frames of each shot, encodes a clip, and releases those PNGs. FFmpeg needs libx264, AAC, and libass support. On Linux the Blender build also needs a working headless graphics context. `blender.log` records failures. Blender, FFmpeg, and speech synthesis are local execution steps. Movie production does not require Roblox Studio, a Roblox account, an asset download, or an upload to YouTube.

The built-in rigs and four sets give the films a consistent block-animation style. Bespoke hand contacts, lip-sync, and elaborate new locations may require extending the rigs or renderer.

## Later, switch the LLM

Implement the same `generate(prompt, schema, job) -> dict` interface in `film/planning.py` against your local model. The story and direction schemas, semantic validation, speech, animation, and export remain reusable. No local model server is used by the included version.

Official CLI references: [non-interactive mode](https://developers.openai.com/codex/noninteractive/) and [ChatGPT sign-in](https://developers.openai.com/codex/auth/).
