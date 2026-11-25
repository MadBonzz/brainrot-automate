"""Reusable tabletop props in scene units. Z is up and the audience faces +Y."""
from . import instruments, machines, miniatures

CATALOG = {fn.__name__: fn for group in (instruments, machines, miniatures) for fn in group.MODELS}


def geometry(prop):
    kind = prop['kind']
    if kind in CATALOG:
        model = CATALOG[kind]()
        return dict(kind=kind, pieces=model.pieces, pivot=model.pivot)
    return dict(kind=kind, parts=prop['parts'] if kind == 'custom' else [])
