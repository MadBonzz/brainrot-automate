"""Read spoken token onsets from the Linux Flite voice used by FFmpeg."""

import ctypes
import ctypes.util
from functools import lru_cache
import sys


@lru_cache(maxsize=1)
def engine():
    ptr, string = ctypes.c_void_p, ctypes.c_char_p
    libpath = ctypes.util.find_library("flite")
    vpath = ctypes.util.find_library("flite_cmu_us_slt")
    if not libpath or not vpath:
        return None
    lib, voices = ctypes.CDLL(libpath), ctypes.CDLL(vpath)

    def bind(lib, name, args, result):
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
        return fn

    bind(lib, "flite_init", [], ctypes.c_int)()
    voice = bind(voices, "register_cmu_us_slt", [string], ptr)(None)
    if not voice:
        return None
    return (
        lib,
        voices,
        voice,
        bind(lib, "flite_synth_text", [string, ptr], ptr),
        bind(lib, "utt_relation", [ptr, string], ptr),
        bind(lib, "relation_head", [ptr], ptr),
        bind(lib, "item_next", [ptr], ptr),
        bind(lib, "ffeature_float", [ptr, string], ctypes.c_float),
        bind(lib, "delete_utterance", [ptr], None),
    )


def onsets(text, marks, duration):
    if not sys.platform.startswith("linux"):
        return marks
    try:
        api = engine()
    except (OSError, AttributeError):
        return marks
    if api is None:
        return marks
    _, _, voice, synth, relation, head, advance, feature, release = api
    utterance = synth(text.encode("utf8"), voice)
    if not utterance:
        return marks
    try:
        tokens = relation(utterance, b"Token")
        token = head(tokens) if tokens else None
        measured = []
        while token:
            start = feature(token, b"daughter1.R:SylStructure.daughter1.daughter1.R:Segment.p.end") / 1.06
            end = feature(token, b"daughtern.R:SylStructure.daughtern.daughtern.end") / 1.06
            if end <= start or (measured and start < measured[-1]):
                return marks
            measured.append(start)
            token = advance(token)
        if len(measured) != len(marks) or not measured or abs(end - duration) > max(0.65, 0.07 * duration):
            return marks
        return [(word, t) for (word, _), t in zip(marks, measured)]
    finally:
        release(utterance)
