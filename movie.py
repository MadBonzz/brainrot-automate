"""Create an original vertical film. Run 'uv run movie.py --help' for the flags."""
import argparse
from array import array
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time

from film import assets, audio, planning, storage, ensemble, ensemble_movie
from film.prop_timing import prop_end, next_state
from film.performances import motion_end

ROOT = Path(__file__).resolve().parent

def locate(name):
    exe = shutil.which(name)
    if not exe and sys.platform == 'darwin' and name == 'blender':
        for apps in (Path('/Applications'), Path.home()/'Applications'):
            candidate = apps/'Blender.app/Contents/MacOS/Blender'
            if os.access(candidate, os.X_OK):
                return str(candidate)
    if not exe and os.name == 'nt' and name == 'blender':
        base = Path(os.environ.get('ProgramFiles', 'C:/Program Files'))/'Blender Foundation'
        exe = next(iter(sorted(base.glob('Blender */blender.exe'), reverse=True)), None)
    if not exe:
        raise RuntimeError(f'{name} is missing. See the platform setup in README.md.')
    return str(exe)

def stage_message(label):
    print(label, flush=True)

def word(text):
    return ''.join(c for c in text.casefold() if c.isalnum() or c in "'’").replace('’', "'")

def render(job, story, design, quality, blender, ffmpeg, asset_root, cast_directory, names):
    width,height,fps={'preview':(360,640,12),'review':(720,1280,24),'final':(1080,1920,24)}[quality]
    target = job/quality
    target.mkdir(exist_ok=True)
    speech = array('h')
    captions = []
    effects = []
    shots = []
    offset = 0
    angle, visible = 0, design['shots'][0]['prop'] != 'appear'
    version = hashlib.sha256((ROOT/'film/animate.py').read_bytes()).hexdigest()
    command = [blender, '-b', '-t', str(min(6, os.cpu_count() or 2)), '-noaudio', '--factory-startup',
               '--python-exit-code', '1', '--python', str(ROOT/'film/animate.py'), '--']
    stage_message('Preparing characters, motion clips, sets and props…')
    library = assets.prepare(job, asset_root, cast_directory, names, design, command, planning.MOTIONS)
    actors, models = library['cast'], library['models']
    engine = subprocess.check_output([blender, '--version'], text=True, errors='replace').splitlines()[0]
    for i, (line, shot) in enumerate(zip(story['beats'], design['shots']), 1):
        raw, timed=audio.narration(line, job, ffmpeg, asset_root)
        stage_message(f'  Voice and timing {i}/{len(design["shots"])}')
        start = offset/fps
        seconds = len(raw)/audio.RATE
        anchor = word(shot['anchor'])
        position = next(t for w, t in timed if anchor in [word(x) for x in re.findall(r"[^\W_]+(?:['’][^\W_]+)*", w)])
        cue = 1+round(position*fps)
        count = max(cue+1, math.ceil((seconds+shot['hold_ms']/1000)*fps), 2)
        playback = [planning.MOTIONS[action] for action in (shot['lead'], shot['witness']) if action != 'absent']
        count = motion_end(cue, count, fps, playback)
        count = prop_end(cue, count, fps, shot['prop'])
        speech.extend(raw)
        samples = round((offset+count)*audio.RATE/fps)-len(speech)
        speech.extend(array('h', [0])*samples)
        if shot['effect'] != 'none':
            effects.append((start+position, shot['effect']))
        for k, (w, t) in enumerate(timed):
            until = timed[k+1][1] if k+1<len(timed) else seconds
            captions.append((start+t, start+until, w, planning.CAMERAS[shot['camera']].get('captions_top', False)))
        used = [actors['lead']['sha256'], models['motions/'+shot['lead']]['sha256'],
                models['sets/'+shot['set']]['sha256'], models['props/clue']['sha256']]
        if shot['witness'] != 'absent':
            used.extend([actors['witness']['sha256'], models['motions/'+shot['witness']]['sha256']])
        screen = {k:shot[k] for k in ('camera','face','lead','witness','prop','turn_degrees')}
        signature = assets.digest([version, engine, screen, count, cue, angle, visible, width, height, fps, used, playback,
                                   design['location_sign'], design['prop']['label'], design['prop']['color'], planning.CAMERAS[shot['camera']]])
        folder = target/'shots'/f'{i:03d}-{signature[:24]}'
        shared = asset_root/'shots'/(signature+'.mp4')
        shots.append(dict(shot=shot, cue=cue, frames=count, angle=angle, visible=visible, folder=str(folder), shared_clip=str(shared)))
        angle, visible = next_state(shot["prop"],angle,visible,shot["turn_degrees"])
        offset += count
    timeline = dict(ffmpeg=ffmpeg, width=width, height=height, fps=fps, design=design, shots=shots, cast=actors,
                    models=models, motions=planning.MOTIONS, cameras=planning.CAMERAS)
    planning.save(target/'timeline.json', timeline)
    audio.make_captions(target/'words.ass', captions)
    audio.soundtrack(target/'mix.wav', speech, effects, design['score'], asset_root)
    render_shots(target, shots, command, offset, width, height)
    for i, s in enumerate(shots):
        folder = Path(s['folder'])
        if not (folder/'complete').exists():
            raise RuntimeError('Incomplete render: '+str(folder))
        clip = folder/'clip.mp4'
        if not clip.is_file():
            raise RuntimeError('Missing finished clip: '+str(clip))
    # Generated relative names contain only digits and hex, even when the project path has spaces.
    entries = ['file '+(Path(s['folder'])/'clip.mp4').relative_to(target).as_posix() for s in shots]
    (target/'clips.txt').write_text('\n'.join(entries)+'\n', encoding='utf8')
    stage_message('Mixing the voice, music and foley, and burning captions.')
    audio.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '1', '-i', 'clips.txt',
        '-i', 'mix.wav', '-vf', 'ass=words.ass', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', 'movie.partial.mp4'], cwd=target)
    dest = target/'movie.mp4'
    (target/'movie.partial.mp4').replace(dest)
    stage_message(f'Finished: {dest}\nDuration: {offset/fps:.1f}s')
    return dest

def render_shots(target, shots, command, frames, width, height):
    logfile = target/'blender.log'
    ready = sum(storage.restore_shot(shot) for shot in shots)
    summary = f'Reused {ready}/{len(shots)} completed shot clips.'
    stage_message(summary)
    if ready == len(shots):
        logfile.write_text(summary+' No frames rendered.\n', encoding='utf8')
        return
    stage_message(f'Finishing {len(shots)} shots, {frames} timeline frames, {width} × {height}.')
    cmd = [*command, str(target/'timeline.json')]
    with logfile.open('w', encoding='utf8') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        last = -1
        try:
            while proc.poll() is None:
                done = sum((Path(s['folder'])/'complete').exists() for s in shots)
                if done != last:
                    stage_message(f'  Rendered shots {done}/{len(shots)}')
                    last = done
                time.sleep(.8)
        except BaseException:
            proc.terminate()
            proc.wait()
            raise
    if proc.returncode:
        raise RuntimeError('Blender failed. See '+str(logfile))

@contextmanager
def job_lock(job):
    with (job/'.run-lock').open('a+b') as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b'0')
            f.flush()
        f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as e:
            raise RuntimeError('Another process is working on this movie.') from e
        yield

def args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--idea', help='Optional premise. Codex invents one if omitted.')
    p.add_argument('--seconds', type=int, default=45, help='Approximate writing target, 12–180 seconds.')
    p.add_argument('--quality', choices=['preview', 'review', 'final'], default='final')
    group = p.add_mutually_exclusive_group()
    p.add_argument('--screenplay', type=Path, help='Cut a saved ensemble film to this spoken script and its staged takes.')
    group.add_argument('--demo', action='store_true', help='Render the included saved example without any model calls.')
    group.add_argument('--resume', type=Path, help='Reuse a prior job and valid completed stages.')
    group.add_argument('--from-plan', type=Path, help='Render a folder containing story.json and direction.json.')
    group.add_argument('--list-cast', action='store_true', help='List saved character IDs and exit.')
    group.add_argument('--list-prop-kinds', action='store_true', help='List built-in prop designs and the custom kind.')
    group.add_argument('--list-props', action='store_true', help='List named recurring props and exit.')
    group.add_argument('--list-actions', action='store_true', help='List the actions available to either character.')
    p.add_argument('--prop-id', type=assets.character_id, help='Save a clue design by name, or use that saved prop.')
    p.add_argument('--lead', type=assets.character_id, help='Use or create this named lead character.')
    p.add_argument('--witness', type=assets.character_id, help='Use or create this character when a witness appears.')
    p.add_argument('--asset-dir', type=Path, help='Folder shared by episodes for reusable assets (default: assets in this project).')
    p.add_argument('--cast-dir', type=Path, help='Shared character folder (default: assets/characters in this project).')
    p.add_argument('--prepare-only',action='store_true',help='Prepare the ensemble timeline, captions and soundtrack for an external Blender render.')
    p.add_argument('--storyboard',action='store_true',help='Render a contact sheet of every ensemble camera setup and stop before full-frame rendering.')
    p.add_argument('--out', type=Path, default=Path('movies'), help='Parent folder for new jobs.')
    return p.parse_args()

def main():
    a = args()
    if a.prepare_only and a.storyboard:
        raise ValueError('Choose either a camera storyboard or a prepared render timeline.')
    default_assets = ROOT/'assets'
    if a.list_actions:
        print('\n'.join(sorted(planning.MOTIONS)))
        return
    if a.list_prop_kinds:
        print('\n'.join(sorted(set(planning.PROP['properties']['kind']['enum']) | set(ensemble.PROP_KINDS.split()))))
        return
    if a.list_props:
        directory = ((a.asset_dir or default_assets)/'props/named').resolve()
        files={p.stem for folder in (directory,directory.with_name('ensemble-named')) for p in folder.glob('*.json')}
        print('\n'.join(sorted(files)) or '(no named props)')
        return
    if a.list_cast:
        directory = (a.cast_dir or ((a.asset_dir or default_assets)/'characters')).resolve()
        print(f'Cast folder: {directory}')
        print('\n'.join(sorted(p.stem for p in directory.glob('*.blend') if p.is_file())) or '(no saved characters)')
        return
    if not 12 <= a.seconds <= 180:
        raise ValueError('--seconds must be between 12 and 180.')
    if a.screenplay and (a.storyboard or a.prepare_only):
        raise ValueError('A screenplay edit needs rendered shot footage.')
    if a.idea and (a.resume or a.demo or a.from_plan):
        raise ValueError('Use --idea on a new generated movie.')
    blender, ffmpeg=locate('blender'), locate('ffmpeg')
    if a.resume:
        job = a.resume.resolve()
        if not (job/'request.json').is_file():
            raise ValueError('Use the job folder containing request.json.')
    else:
        job = (a.out/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3))).resolve()
        job.mkdir(parents=True)
    stage_message('Job: '+str(job))
    with job_lock(job):
        source = None
        if not a.resume:
            source = ((ROOT/'example' if a.prop_id else ROOT/'example'/'last-clap') if a.demo else a.from_plan)
            if source:
                for name in ['story', 'direction']:
                    shutil.copyfile(source/(name+'.json'), job/(name+'.json'))
            legacy = ('loophole' not in json.loads((job/'story.json').read_text(encoding='utf8'))
                      if source else False)
            planning.save(job/'request.json', dict(idea=a.idea, seconds=a.seconds, format=1 if legacy else 2))
        request = json.loads((job/'request.json').read_text(encoding='utf8'))
        names = dict(request.get('characters', {}))
        names.update({role:getattr(a, role) for role in ('lead', 'witness') if getattr(a, role)})
        asset_root = Path(a.asset_dir or request.get('asset_root') or default_assets).resolve()
        override = a.cast_dir or request.get('cast_override') or request.get('cast_directory')
        directory = Path(override or asset_root/'characters').resolve()
        prop_id = a.prop_id or request.get('prop_id')
        request.update(characters=names, asset_root=str(asset_root), cast_override=str(directory) if override else None, prop_id=prop_id)
        planning.save(job/'request.json', request)
        from film.screenplay import render as edit_screenplay, save_plan, available_footage
        script = a.screenplay
        if script is None and source and (source/'screenplay.json').is_file():
            script = source/'screenplay.json'
        if script is None and a.resume and (job/'screenplay'/'screenplay.json').is_file():
            script = job/'screenplay'/'screenplay.json'
        references = []
        if script is not None:
            script = script.resolve()
            if not script.is_file():
                raise FileNotFoundError(script)
            if request.get('format', 1) != 2:
                raise ValueError('A screenplay edit needs an ensemble cast and timeline.')
            script = save_plan(script, job/'screenplay')
            saved = json.loads(script.read_text(encoding='utf8'))
            references = [s for line in saved['lines'] for s in line['shots'] if 'beat' in s]
            if a.resume and not (a.storyboard or a.prepare_only) and available_footage(job/a.quality,references):
                movie = edit_screenplay(script, job/a.quality, job/a.quality/'screened', asset_root, ffmpeg, blender)
                stage_message(f'Picture and dialogue ready for review at {movie}')
                return
        stage_message('Preparing story and shot direction…')
        if request.get('format',1)==2:
            model_path,model=ensemble_movie.named_model(asset_root,prop_id) if prop_id else (None,None)
            story,design=ensemble.plan(job,request['idea'],request['seconds'],names,prop_id,model)
            if prop_id:
                ensemble_movie.bind_model(model_path,model,prop_id,design)
                planning.check(design,ensemble.DIRECTION)
                ensemble.check_direction(design,story)
                planning.save(job/'direction.json',design)
            print(story['title'],flush=True)
            prepare_assets_only = a.prepare_only or (script is not None and not references and not a.storyboard)
            ensemble_movie.render(job,story,design,a.quality,blender,ffmpeg,asset_root,directory,names,a.storyboard,prepare_assets_only)
            if script is not None and not (a.storyboard or a.prepare_only):
                movie = edit_screenplay(script, job/a.quality, job/a.quality/'screened', asset_root, ffmpeg, blender)
                stage_message(f'Picture and dialogue ready for review at {movie}')
            return
        if a.storyboard or a.prepare_only:raise ValueError('Preparing a timeline or storyboard takes an ensemble plan.')
        prop_path = asset_root/'props/named'/(assets.character_id(prop_id)+'.json') if prop_id else None
        saved_prop = json.loads(prop_path.read_text(encoding='utf8')) if prop_path and prop_path.is_file() else None
        story, design=planning.plan(job, request['idea'], request['seconds'], names, prop_id, saved_prop)
        if prop_path:
            prop_path.parent.mkdir(parents=True, exist_ok=True)
            with assets.creation_lock(prop_path.parent):
                if prop_path.is_file():
                    design['prop'] = json.loads(prop_path.read_text(encoding='utf8'))
                else:
                    planning.save(prop_path, design['prop'])
            planning.check(design, planning.DESIGN)
            planning.design_checks(design, story)
            planning.save(job/'direction.json', design)
        stage_message(story['title'])
        render(job, story, design, a.quality, blender, ffmpeg, asset_root, directory, names)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError, StopIteration) as e:
        print(f'Movie generation stopped: {e}', file=sys.stderr)
        sys.exit(1)
