"""Publish a reusable file only after its contents have been written."""
from pathlib import Path
import shutil
import tempfile


def copy_file(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        draft = Path(staging)/destination.name
        shutil.copyfile(source, draft)
        draft.replace(destination)


def restore_shot(spec):
    folder = Path(spec['folder'])
    clip, done, shared = folder/'clip.mp4', folder/'complete', Path(spec['shared_clip'])
    if done.is_file() and clip.is_file():
        if not shared.is_file():
            copy_file(clip, shared)
        return True
    if shared.is_file():
        copy_file(shared, clip)
        done.write_text(str(spec['frames']))
        return True
    return False
