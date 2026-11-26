"""Regression checks for editorial holds, shot reuse and reference coverage."""

import copy
import unittest

from film import ensemble, ensemble_movie, planning
from tools import compare_cuts, coverage_plan


class CoverageTests(unittest.TestCase):
    def sheet(self):
        return dict(
            title="The Late Train",
            source="A study scene",
            seconds=15,
            rule="The dial counts riders.",
            turn="There is one unseen passenger.",
            ending="The dial returns to one.",
            palette=["navy", "teal"],
            cast=[["conductor", "driver", "Find the last passenger."]],
            looks=[["teal", "amber", "brown", "cap", "tunic", 1]],
            anchors={"2": [{"at": 0.5, "words": "empty seat"}]},
            coverage=[
                [
                    "skyport",
                    "0:high_knee_march",
                    "clock:gold@0,1,0",
                    "0:P0:3:hold:0:7 0.5:A0:2:follow:15:4",
                    "The dial shows two.",
                ],
                [
                    "bedroom/night/quiet/fog/mono=P0",
                    "0:-@1,0,.5,-70",
                    "watch:gold@0,1,0",
                    "0:A0:2:hold:0:6 0.5:P0:2:hold:-8:9",
                    "One empty seat. One tick.",
                ],
            ],
        )

    def test_coverage_resolves_movement_freeze_and_gaze(self):
        story, direction = coverage_plan.compile_sheet(self.sheet())
        self.assertEqual(story["source_cut"], "A study scene")
        first, last = direction["shots"]
        self.assertEqual(first["actors"][0]["cues"][0]["play"], "cycle")
        self.assertEqual(last["actors"][0]["pose"], "frozen")
        self.assertEqual(last["actors"][0]["pitch"], [-70, -70])
        self.assertEqual(last["selective_color"], [last["cameras"][-1]["focus"][0]])
        self.assertEqual(last["sync"][0]["words"], "empty seat")

    def test_schema_keeps_frame_locks_out_of_generated_json(self):
        raw = planning.provider_schema(ensemble.STORY)
        self.assertNotIn("edit_frames", raw["properties"]["beats"]["items"]["properties"])
        self.assertNotIn("stage_clock", planning.provider_schema(ensemble.SHOT)["properties"])
        story, _ = coverage_plan.compile_sheet(self.sheet())
        story["beats"][0]["edit_frames"] = 500
        with self.assertRaisesRegex(ValueError, "Locked takes"):
            ensemble.check_story(story)
        lengths = ensemble_movie.timings([24000, 38000, 20000], 12, 30, [89, None, 61])
        self.assertEqual(lengths, [89, 210, 61])

    def test_camera_marks_are_visible_and_in_range(self):
        sheet = self.sheet()
        sheet["coverage"][0][3] = "0:P9:3:hold:0:8"
        with self.assertRaisesRegex(ValueError, "missing coverage"):
            coverage_plan.compile_sheet(sheet)
        sheet = self.sheet()
        sheet["coverage"][0][1] = "-1:look"
        with self.assertRaisesRegex(ValueError, "unknown actor"):
            coverage_plan.compile_sheet(sheet)

    def test_gaze_and_atmosphere_follow_voice(self):
        _, d = coverage_plan.compile_sheet(self.sheet())
        shot = copy.deepcopy(d["shots"][1])
        shot["actors"][0]["gaze"] = [dict(at=0.5, focus="p2-1")]
        shot["atmosphere"] = dict(kind="fog", start=0.5, end=0.8)
        res = ensemble_movie.synchronized(
            shot,
            "One empty seat. One tick.",
            [("One", 0), ("empty", 1), ("seat.", 1.5), ("One", 2), ("tick.", 3)],
            1,
            4,
        )
        self.assertEqual(res["cameras"][1]["start"], 0.25)
        self.assertEqual(res["actors"][0]["gaze"][0]["at"], 0.25)
        self.assertEqual(res["atmosphere"]["start"], 0.25)

    def test_rapid_change_measure_ignores_sustained_frames(self):
        changes = [0] * 63
        changes[7] = 0.35
        changes[31] = 0.4
        result = compare_cuts.change_summary(changes, 64)
        self.assertEqual(result["large_changes"], 2)
        self.assertEqual(result["median_gap_between_large_changes"], 3)
        self.assertEqual(result["median_other_pixel_change_percent"], 0)
