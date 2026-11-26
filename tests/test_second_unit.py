"""Check exact frame edits and keep the underlying stage take reusable."""

import copy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from film import character_props, vistas


class SecondUnitTests(unittest.TestCase):
    def test_alternate_cameras_do_not_change_the_stage_key(self):
        stage = dict(cameras=[dict(start=0, focus=["runner"]), dict(start=0.6, focus=["dial"])])
        authored = copy.deepcopy(stage)
        authored["cameras"][0]["vista"] = "desert_queue"
        authored["cameras"][1]["reactions"] = [dict(actor="runner", action="recoil")]
        clean, cutaways = vistas.extract(authored, 3, 150)
        self.assertEqual(clean, stage)
        self.assertEqual([q["kind"] for q in cutaways], ["desert_queue", "reaction"])
        self.assertEqual(cutaways[0]["stop"], 89)
        self.assertGreater(cutaways[1]["start"], 89)
        self.assertEqual(cutaways[1]["stop"], 150)
        self.assertIn("reactions", authored["cameras"][1])

    def test_detail_requires_readable_type_and_a_short_angle_keeps_the_original(self):
        with self.assertRaisesRegex(ValueError, "inscription"):
            vistas.extract(dict(cameras=[dict(start=0, vista="paper_detail")]), 1, 90)
        _, views = vistas.extract(
            dict(cameras=[dict(start=0, reactions=[dict(actor="kid", action="point")])]), 1, 26
        )
        self.assertEqual(views, [])

    def test_articulated_face_follows_prop_and_keeps_cues_and_selective_color(self):
        prop = dict(
            id="stranger",
            place="door",
            kind="stalker",
            face_model="fixed_grin",
            color="cream",
            scale=2,
            at=[1, 2, 0],
            parts=[],
            text="",
        )
        event = dict(id="stranger", start=0.1, end=0.7, to=[2, 3, 1], spin=35, anchor="", text="")
        shot = dict(
            place="door",
            events=[event],
            selective_color=["stranger"],
            cameras=[dict(focus=["stranger"], size=2)],
        )
        direction = dict(looks=[], props=[prop], shots=[shot])
        expanded = character_props.expand(direction)
        figure, mask = expanded["props"]
        self.assertEqual(figure["kind"], "stalker")
        self.assertEqual(mask["at"], [1, 2, 4.94])
        after = expanded["shots"][0]
        self.assertEqual(after["events"][-1]["to"], [2, 3, 5.94])
        self.assertEqual(after["events"][-1]["spin"], 35)
        self.assertIn(mask["id"], after["selective_color"])
        self.assertEqual(after["cameras"][0]["focus"], [mask["id"]])
        self.assertEqual(len(direction["props"]), 1)
        prop["face_model"] = "plain"
        clean = character_props.expand(direction)
        self.assertNotIn("face_model", clean["props"][0])
        self.assertEqual(clean["shots"], [shot])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg needed")
    def test_frame_boundaries_of_adjacent_inserts(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for name, frames in (("red", 60), ("blue", 12), ("lime", 16)):
                subprocess.run(
                    [
                        "ffmpeg",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        f"color={name}:s=32x64:r=30",
                        "-frames:v",
                        str(frames),
                        "-pix_fmt",
                        "yuv420p",
                        "-c:v",
                        "libx264",
                        "-threads",
                        "1",
                        str(out / (name + ".mp4")),
                    ],
                    check=True,
                )
            views = [
                dict(start=7, stop=19, output=str(out / "blue.mp4")),
                dict(start=19, stop=35, output=str(out / "lime.mp4")),
            ]
            result = vistas.cut(out / "red.mp4", views, 60, out, "ffmpeg", 30, "ffprobe", 32, 64)
            raw = subprocess.check_output(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(result),
                    "-vf",
                    "scale=1:1",
                    "-pix_fmt",
                    "rgb24",
                    "-f",
                    "rawvideo",
                    "-threads",
                    "1",
                    "-",
                ]
            )
            self.assertEqual(len(raw), 180)
            channels = [raw[i : i + 3].index(max(raw[i : i + 3])) for i in range(0, len(raw), 3)]
            self.assertEqual(channels, [0] * 7 + [2] * 12 + [1] * 16 + [0] * 25)
