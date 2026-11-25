"""Resolve the reusable assets used by an episode and build only missing files."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from .planning import save


def character_id(value):
    name = value.lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', name) or re.fullmatch(
            r'con|prn|aux|nul|com[1-9]|lpt[1-9]', name):
        raise ValueError('Use a character ID of 1–64 letters, digits, hyphens or underscores, '
                         'starting with a letter or digit. Windows device names are reserved.')
    return name


@contextmanager
def creation_lock(directory):
    # Serialize first creation only. The OS releases the lock if the process exits.
    with (directory/'.asset-lock').open('a+b') as lock:
        if lock.seek(0, 2) == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def ensure_models(job, lock_dir, entries, blender_command):
    def missing():
        return [entry for entry in entries if not Path(entry['path']).is_file()]
    created = set()
    if missing():
        lock_dir.mkdir(parents=True, exist_ok=True)
        with creation_lock(lock_dir):
            pending = missing()
            if pending:
                request = job/'build-assets.json'
                save(request, pending)
                subprocess.run([*blender_command, '--build-assets', str(request)], check=True)
                created = {entry['path'] for entry in pending}
    total = len({entry['path'] for entry in entries})
    print(f'  {len(created)} Blender assets built, {total-len(created)} reused', flush=True)
    return {entry['id']:dict(path=entry['path'], sha256=hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest())
            for entry in entries}


def prepare(job, root, cast_dir, names, design, blender_command, motions):
    roles = ['lead']
    if any(shot['witness'] != 'absent' for shot in design['shots']):
        roles.append('witness')
    characters = {}
    for role in roles:
        coat = design[role+'_coat']
        name = character_id(names.get(role) or f'{role}-{coat}')
        characters[role] = dict(id=name, kind='character', path=str(cast_dir/(name+'.blend')), coat=coat, role=role)
    models = ensure_models(job, cast_dir, list(characters.values()), blender_command)
    cast = {role:dict(id=entry['id'], **models[entry['id']]) for role, entry in characters.items()}
    save(job/'cast.json', cast)
    for role, entry in cast.items():
        print(f"  {role.capitalize()} uses {entry['id']}.blend", flush=True)

    entries = []
    def asset(category, name, filename, **settings):
        entry = dict(id=category+'/'+name, kind=category, name=name, path=str(root/category/(filename+'.blend')), **settings)
        entries.append(entry)
    for name in sorted({shot['set'] for shot in design['shots']}):
        asset('sets', name, name)
    actions = {shot[role] for shot in design['shots'] for role in roles} - {'absent'}
    for name in sorted(actions):
        recipe = motions[name]
        asset('motions', name, name+'-'+digest(recipe)[:12], recipe=recipe)
    prop = design['prop']
    geometry = dict(kind=prop['kind'], parts=prop['parts'] if prop['kind']=='custom' else [])
    asset('props', 'clue', prop['kind']+'-'+digest(geometry)[:16], geometry=geometry)
    result = ensure_models(job, root, entries, blender_command)
    library = dict(cast=cast, models=result)
    save(job/'assets.json', library)
    return library
