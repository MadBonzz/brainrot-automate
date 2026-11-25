"""Read the block-rig pose sheets. Artists work in degrees and 24-fps frames."""
import json
import math
from pathlib import Path

PRESETS = Path(__file__).with_name('presets')


def read_motions():
    motions = json.loads((PRESETS/'motions.json').read_text(encoding='utf8'))
    for sheet in sorted((PRESETS/'performances').glob('*.json')):
        for name, entry in json.loads(sheet.read_text(encoding='utf8')).items():
            if name in motions:
                raise ValueError(f'Duplicate motion {name} in {sheet.name}')
            frames = entry['frames']
            if len(frames) < 2 or frames[0] != 0 or any(b <= a for a,b in zip(frames,frames[1:])):
                raise ValueError(f'{name} needs increasing frames starting at zero')
            channels = {}
            for key, values in entry['pose'].items():
                joint, axis = key.split('.')
                translation = axis.startswith('d')
                axis = axis.removeprefix('d')
                if axis not in ('x','y','z') or len(values) != len(frames) or not all(math.isfinite(v) for v in values):
                    raise ValueError(f'Invalid pose row {name}/{key}')
                if values[0] != 0 or (entry.get('loop') and values[-1] != values[0]):
                    raise ValueError(f'{name}/{key} needs a neutral start and matching loop endpoints')
                field = ('delta_location.' if translation else 'delta_rotation_euler.')+axis
                curve = [[f, v if translation else math.radians(v)] for f,v in zip(frames,values)]
                channels.setdefault(joint,{})[field] = curve
            recipe = dict(frames=frames[-1], channels=channels, readable_frames=math.ceil(frames[-1]*.70))
            recipe.update({k:entry[k] for k in ('loop','ground','floor','plant') if k in entry})
            previous = -1
            for segment in recipe.get('plant', []):
                side, start, stop = map(int,segment.split(':'))
                if side not in (-1,1) or not previous < start <= stop <= frames[-1]:
                    raise ValueError(f'Invalid support interval {name}/{segment}')
                previous = stop
            motions[name] = recipe
    return motions


def motion_end(cue, proposed_end, fps, recipes):
    """Give a multi-beat gesture time to read even when dialogue cues it on the last word."""
    tail = max((r.get('readable_frames', 0) for r in recipes), default=0)
    return max(proposed_end, cue+math.ceil(tail*fps/24))
