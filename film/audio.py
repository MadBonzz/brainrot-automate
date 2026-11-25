"""Local narration, pacing, captions, and a procedurally synthesized score."""
from array import array
import base64
import hashlib
import inspect
import json
from functools import lru_cache
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import subprocess
import tempfile
import sys
import wave

RATE = 24000
HERE = Path(__file__).resolve().parent

def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)

def read_wave(path):
    with wave.open(str(path), 'rb') as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, RATE):
            raise ValueError('Expected 24 kHz mono PCM narration.')
        data = array('h')
        data.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder != 'little':
        data.byteswap()
    return data

def write_wave(path, data):
    if sys.byteorder != 'little':
        data = data[:]
        data.byteswap()
    with wave.open(str(path), 'wb') as w:
        w.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        w.writeframes(data.tobytes())

@lru_cache(maxsize=1)
def voice_settings(ffmpeg):
    """Resolve a reproducible voice. An unidentified OS default stays local to the job."""
    voice = os.environ.get('SHORTFILM_VOICE', '').strip()
    backend = 'sapi' if os.name == 'nt' else 'say' if sys.platform == 'darwin' else 'flite'
    if backend == 'flite':
        voice = 'slt'
    if backend == 'sapi' and not voice:
        cmd = ('Add-Type -AssemblyName System.Speech; '
               '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
               '[Console]::OutputEncoding = [Text.Encoding]::UTF8; [Console]::Write($s.Voice.Name); $s.Dispose()')
        probe = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand',
                                base64.b64encode(cmd.encode('utf-16-le')).decode('ascii')],
                               capture_output=True, encoding='utf-8-sig', errors='replace')
        if probe.returncode == 0:
            voice = probe.stdout.strip()
    identity = [backend, voice, platform.node(), platform.version(), RATE, os.stat(ffmpeg).st_mtime_ns,
                inspect.getsource(synthesize), (HERE/'narrate.ps1').read_text(encoding='utf8')]
    return voice, hashlib.sha256(json.dumps(identity).encode()).hexdigest()


def synthesize(text, directory, ffmpeg, voice):
    src, wav, marks = (directory/name for name in ('line.txt', 'voice.wav', 'marks.tsv'))
    src.write_text(text, encoding='utf8')
    if os.name == 'nt':
        env = dict(os.environ, FILM_LINE_FILE=str(src), FILM_WAVE_FILE=str(wav), FILM_MARK_FILE=str(marks), FILM_VOICE=voice)
        script = (HERE/'narrate.ps1').read_text(encoding='utf8').encode('utf-16-le')
        run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', base64.b64encode(script).decode('ascii')], env=env)
    elif sys.platform == 'darwin':
        spoken = directory/'narration.aiff'
        flags = ['-v', voice] if voice else []
        run(['/usr/bin/say', *flags, '-f', str(src), '-o', str(spoken)])
        run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(spoken),
             '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le', str(wav)])
        spoken.unlink()
    else:
        run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'flite=textfile=line.txt:voice=slt',
             '-af', 'atempo=1.06', '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le', 'voice.wav'], cwd=directory)
    if not read_wave(wav):
        raise RuntimeError('TTS returned an empty audio file.')


def narration(text, work, ffmpeg, assets=None):
    voice, profile = voice_settings(ffmpeg)
    digest = hashlib.sha256((profile+text).encode()).hexdigest()
    local = work/'voice'/digest
    # A previous release stored its default voice per job. Preserve that recording on resume.
    old_backend = 'macos-say' if sys.platform == 'darwin' else os.name
    old = work/'voice'/hashlib.sha256((old_backend+'-v2-'+text).encode()).hexdigest()[:18]
    if not os.environ.get('SHORTFILM_VOICE') and (old/'complete').is_file() and (old/'voice.wav').is_file():
        local = old
    if not (local/'complete').is_file():
        shared = assets/'voice'/digest if assets and voice else local
        if not (shared/'complete').is_file():
            shared.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=shared.parent) as temp:
                draft = Path(temp)/'line'
                draft.mkdir()
                synthesize(text, draft, ffmpeg, voice)
                (draft/'complete').touch()
                try:
                    draft.rename(shared)
                except OSError:
                    if not (shared/'complete').is_file():
                        raise
        if shared != local:
            local.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=local.parent) as temp:
                draft = Path(temp)/'line'
                shutil.copytree(shared, draft)
                draft.rename(local)
    data = read_wave(local/'voice.wav')
    marks = local/'marks.tsv'
    tokens = list(re.finditer(r'\S+', text))
    duration = len(data)/RATE
    # The macOS and Linux backends provide sound only. Weighted spacing estimates word starts within this exact line.
    weights = [max(2, len(t.group())**.65)+(2.1 if t.group().endswith((',', '.', '!', '?')) else 0) for t in tokens]
    pos = 0
    starts = []
    for weight in weights:
        starts.append(.04+(max(.01, duration-.14))*pos/sum(weights))
        pos += weight
    if marks.exists():
        mapping = {}
        for line in marks.read_text(encoding='utf-8-sig').splitlines():
            p, n, seconds=line.split('\t')
            mapping[int(p)]=float(seconds)
        for i, t in enumerate(tokens):
            a = len(text[:t.start()].encode('utf-16-le'))//2
            b = a+len(t.group().encode('utf-16-le'))//2
            values = [v for k, v in mapping.items() if a <= k<b]
            if values:
                starts[i]=min(values)
    for i in range(len(starts)):
        starts[i]=min(max(starts[i], starts[i-1] if i else 0), duration)
    return data, [(t.group(), s) for t, s in zip(tokens, starts)]

def stamp(s):
    cs = max(0, round(s*100))
    return f'{cs//360000}:{(cs//6000)%60:02}:{(cs//100)%60:02}.{cs%100:02}'

def make_captions(path, captions):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narration,Arial,69,&H00FFFFFF,&H000000FF,&H00171B22,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,95,95,300,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with path.open('w', encoding='utf-8-sig') as f:
        f.write(header)
        for a, b, t, top in captions:
            t = t.replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')
            if top:
                t = r'{\an8\pos(540,190)}'+t
            if t and b-a>.025:
                f.write(f'Dialogue: 0,{stamp(a)},{stamp(b)},Narration,,0,0,0,,{t}\n')

def effect(name):
    length = {'knock':.23, 'bell':1.35, 'static':.28, 'click':.09, 'rumble':.85}[name]
    rng = random.Random(16)
    out = array('h')
    for i in range(round(RATE*length)):
        t = i/RATE
        r = rng.uniform(-1, 1)
        if name == 'knock':
            v = (math.sin(2*math.pi*140*t)+.3*r)*math.exp(-26*t)
        elif name == 'bell':
            v = (math.sin(2*math.pi*784*t)+.3*math.sin(2*math.pi*1480*t))*math.exp(-3.6*t)
        elif name == 'click':
            v = r*math.exp(-105*t)
        elif name == 'rumble':
            v = math.sin(2*math.pi*(49*t+8*t*t))*math.sin(math.pi*t/length)**2
        else:
            v = r*math.sin(math.pi*t/length)**2
        out.append(round(5800*v))
    return out

def music_bed(mood):
    notes = {'quiet':(130.81, 196, 261.63), 'wonder':(146.83, 220, 369.99), 'suspense':(110, 164.81, 233.08)}[mood]
    count = RATE*4
    # Whole cycles in four seconds keep the loop continuous at the splice.
    cycles = [round(hz*4) for hz in notes]
    table = [math.sin(i*math.tau/4096) for i in range(4096)]
    return array('h', (round(235*sum(table[(i*n*4096//count)%4096] for n in cycles)) for i in range(count)))


def saved_sound(directory, name, make):
    if directory is None:
        return make(name)
    revision = hashlib.sha256((str(RATE)+inspect.getsource(make)).encode()).hexdigest()[:12]
    path = directory/f'{name}-{revision}.wav'
    if not path.is_file():
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as temp:
            draft = Path(temp)/path.name
            write_wave(draft, make(name))
            draft.replace(path)
    return read_wave(path)


def soundtrack(path, dialogue, effects, mood, assets=None):
    output = array('h')
    length = len(dialogue)
    bed = saved_sound(assets/'music' if assets else None, mood, music_bed)
    for i, v in enumerate(dialogue):
        fade = min(1, i/(RATE*.4), (length-i)/(RATE*.65))
        output.append(max(-32760, min(32760, round(v*.91+bed[i%len(bed)]*fade))))
    clips = {}
    for time, name in effects:
        if name not in clips:
            clips[name] = saved_sound(assets/'effects' if assets else None, name, effect)
        pos = round(time*RATE)
        clip = clips[name]
        for k in range(min(len(clip), length-pos)):
            output[pos+k]=max(-32760, min(32760, output[pos+k]+clip[k]))
    write_wave(path, output)
