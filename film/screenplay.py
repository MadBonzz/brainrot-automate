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


def voice_line(text):
    return " ".join(re.findall(r"[\w']+", text.casefold()))


def check(lines):
    if not lines:
        raise ValueError("A screenplay needs at least one spoken event.")
    ids = set()
    sentences = set()
    spoken = set()
    for line in lines:
        if line["id"] in ids or not line["id"] or not line["evidence"].strip():
            raise ValueError("Give each line a unique ID and a visible event to review.")
        ids.add(line["id"])
        words = voice_line(line["say"])
        if not words or words in spoken:
            raise ValueError(f"Empty or repeated spoken line at {line['id']}")
        spoken.add(words)
        for sentence in re.split(r"(?<=[.!?])\s+", line["say"]):
            key = voice_line(sentence)
            if len(key.split()) < 5:
                continue
            if key in sentences:
                raise ValueError(f"Repeated sentence at {line['id']}: {sentence}")
            sentences.add(key)
        if not line.get("shots"):
            raise ValueError(f"Missing picture for {line['id']}")


def native_source(selection, timeline, quality):
    index = selection["beat"]
    if not isinstance(index, int) or not 1 <= index <= len(timeline["shots"]):
        raise ValueError(f"Take {index} does not exist")
    take = timeline["shots"][index - 1]
    clip = Path(take["clip"])
    if not clip.is_file():
        clip = quality / "shots" / clip.name if clip.parent.name == "shots" else quality / "location-views" / clip.name
    if not clip.is_file():
        raise FileNotFoundError(f"Render the original plan before editing its take {selection['beat']}.")
    return clip, take["frames"]


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
    fps, width, height = (timeline[k] for k in ("fps","width","height"))
    if fps != FPS:
        raise ValueError("Screenplays currently use a 30-frame editing timeline")
    speech = array("h")
    captions, manifest, cuts = [], [], []
    frame = 0
    recipe = {k:timeline[k] for k in ("looks","places","assets","width","height","fps")}
    from .screening import dialogue_check, movie_hash, review_page
    with tempfile.TemporaryDirectory(dir=output) as temp:
        staging = Path(temp)
        for line in spec["lines"]:
            raw, marks = audio.narration(line["say"], output, ffmpeg, assets)
            start = len(speech)
            lead = round(audio.RATE * line.get("lead",.10))
            tail = round(audio.RATE * line.get("tail",.24))
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
                if len(group)>=5 or re.search(r"[.!?]$",word):
                    chunks.append(" ".join(group));group=[]
            if group:chunks.append(" ".join(group))
            word = 0
            for chunk in chunks:
                begin = marks[min(word,len(marks)-1)][1]
                word += len(chunk.split())
                end = marks[word][1] if word<len(marks) else len(raw)/audio.RATE
                when = (start+lead)/audio.RATE
                captions.append((when+begin,when+end,chunk,False))
            spans = line["shots"]
            weights = [s.get("weight",1) for s in spans]
            if any(w<=0 for w in weights):
                raise ValueError(f"Picture durations must be positive at {line['id']}")
            offset = 0
            for j,selection in enumerate(spans):
                stop = round(frames*sum(weights[:j+1])/sum(weights))
                length = stop-offset
                if length < 2:
                    raise ValueError(f"Camera at {line['id']} is too short")
                if "take" in selection:
                    path = (plan_file.parent / selection["take"]).resolve()
                    if not path.is_relative_to(plan_file.parent.resolve()) or path.suffix != ".json":
                        raise ValueError("A staged take must be a JSON file inside the screenplay folder")
                    scene = json.loads(path.read_text(encoding="utf8"))
                    scale = (length-1)/max(1,scene["frames"]-1)
                    for obj in scene["tracks"]:
                        for key in obj["keys"]:key[0]*=scale
                    for cam in scene["cameras"]:
                        cam["at"]*=scale
                        for key in cam["keys"]:key[0]*=scale
                    for item in scene.get("holds",[]):
                        for key in item["anchors"]:key[0]*=scale
                    scene.update(frames=length);scene.pop("proof",None);scene.pop("output",None)
                    digest = hashlib.sha256()
                    for module in ("stage_take.py","animate.py","world_art.py","story_objects.py","story_sets.py"):
                        digest.update((HERE/module).read_bytes())
                    identity=[scene,digest.hexdigest(),width,height,fps,timeline["looks"],{
                        k:v["sha256"] for k,v in timeline["assets"].items()},
                        recipe["places"].get(scene.get("place")),subprocess.check_output([blender,"--version"]).splitlines()[0].decode()]
                    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:20]
                    clip=output/"shots"/(key+".mp4")
                    if not ensemble_review.correct_clip(clip,probe,width,height,fps,length):
                        shot=dict(scene,output=str(clip))
                        job=staging/"take.json";planning.save(job,dict(plan=recipe,shots=[shot]))
                        with (output/"stage.log").open("a") as log:
                            subprocess.run([blender,"-b","-t","2","--factory-startup","--python-exit-code","1","--python",str(HERE/"stage_take.py"),"--",str(job)],stdout=log,stderr=subprocess.STDOUT,check=True)
                else:
                    clip,native_frames=native_source(selection,picture,quality)
                    source=clip
                    a,b=selection.get("range",[0,1])
                    if not 0<=a<b<=1:
                        raise ValueError(f"Invalid take interval at {line['id']}")
                    first=min(native_frames-1,round(a*native_frames));last=min(native_frames,max(first+1,round(b*native_frames)))
                    # Retain the selected action while borrowing the handles on either side
                    # before slowing motion to fill a long sentence.
                    wanted = min(native_frames, max(last-first, math.ceil(length * .86)))
                    first = max(0, min(native_frames-wanted, first-(wanted-(last-first))//2))
                    last = first + wanted
                    # The director can choose an exact before/contact/after interval. The edit never loops an action.
                    key=hashlib.sha256(repr((str(source),source.stat().st_size,source.stat().st_mtime_ns,first,last,length)).encode()).hexdigest()[:20]
                    clip=output/"shots"/(key+".mp4")
                    if not ensemble_review.correct_clip(clip,probe,width,height,fps,length):
                        dest=staging/"cut.mp4"
                        filters=f"trim=start_frame={first}:end_frame={last},setpts=(PTS-STARTPTS)*{length}/{last-first},fps={fps},tpad=stop_mode=clone:stop_duration=0.15,trim=end_frame={length},setsar=1"
                        subprocess.run([ffmpeg,"-nostdin","-v","error","-y","-threads","1","-i",str(source),"-an","-filter_threads","1","-vf",filters,"-frames:v",str(length),"-c:v","libx264","-threads","2","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",str(dest)],check=True)
                        dest.replace(clip)
                if not ensemble_review.correct_clip(clip,probe,width,height,fps,length):
                    raise ValueError(f"Incorrect frame count for {line['id']} camera {j+1}")
                cuts.append(clip.relative_to(output).as_posix())
                offset=stop
            manifest.append(dict(id=line["id"],start=start_frame/fps,end=frame/fps,
                                 speech_start=(start+lead)/audio.RATE,speech_end=(start+lead+len(raw))/audio.RATE,
                                 say=line["say"],evidence=line["evidence"]))
        audio.write_wave(staging/"dialogue.wav",speech)
        audio.make_captions(staging/"lines.ass",captions,style="phrases")
        # The input order is the authored story order. The final file contains one new dialogue stream.
        (output/"screenplay-clips.txt").write_text("".join("file "+s+"\n" for s in cuts),encoding="utf8")
        dest=staging/"picture.mp4"
        subprocess.run([ffmpeg,"-nostdin","-v","error","-y","-f","concat","-safe","1","-i",str(output/"screenplay-clips.txt"),"-i","dialogue.wav","-map","0:v:0","-map","1:a:0","-filter_threads","2","-vf",f"settb=1/{fps},setpts=N,ass=lines.ass","-r",str(fps),"-fps_mode","cfr","-frames:v",str(frame),"-threads","3","-c:v","libx264","-preset","veryfast","-crf","18","-c:a","aac","-b:a","128k","-movflags","+faststart",str(dest)],cwd=staging,check=True)
        if not ensemble_review.correct_clip(dest,probe,width,height,fps,frame):
            actual=ensemble_review.video_info(dest,probe)[0]
            raise ValueError(f"Expected {frame} frames at {fps} fps, got {actual}")
        subprocess.run([ffmpeg,"-v","error","-xerror","-threads","1","-i",str(dest),"-f","null","-"],check=True)
        checks = dialogue_check(dest, manifest, ffmpeg, assets)
        movie_digest = movie_hash(dest)
        dest.replace(output/"movie.mp4")
    data = dict(title=spec["title"],frames=frame,fps=fps,lines=manifest,sha256=movie_digest)
    planning.save(output/"screening.json",data)
    planning.save(output/"audio-checks.json",dict(sha256=movie_digest,dialogue=checks))
    review_page(output/"movie.mp4",data)
    return output/"movie.mp4"


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screenplay",type=Path)
    parser.add_argument("quality_folder",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--assets",type=Path)
    args=parser.parse_args()
    print(render(args.screenplay.resolve(),args.quality_folder.resolve(),args.output.resolve(),args.assets),flush=True)
