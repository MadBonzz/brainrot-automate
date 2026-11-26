"""Contract regressions for block generation, editorial causality, prop ownership and timing."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from film import ensemble, ensemble_movie, ensemble_review, planning, shot_rhythm

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    folder = ROOT / "example" / name
    return tuple(json.loads((folder / (k + ".json")).read_text()) for k in ("story", "direction"))


class EpisodeTests(unittest.TestCase):
    def test_both_saved_worlds(self):
        for name in ("floor-ten", "bell-bay", "last-clap"):
            story, d = example(name)
            planning.check(story, ensemble.STORY)
            planning.check(d, ensemble.DIRECTION)
            ensemble.check_story(story)
            ensemble.check_direction(d, story)
            self.assertEqual(story["seconds"], 120)

    def test_unearned_solution_and_teleport(self):
        story, d = example("floor-ten")
        choice = next(b for b in story["beats"] if b["role"] == "choice")
        choice["because"] = 1
        with self.assertRaisesRegex(ValueError, "evidence"):
            ensemble.check_story(story)
        d["shots"][1]["actors"][0]["at"][0] += 2
        with self.assertRaisesRegex(ValueError, "teleports"):
            ensemble.check_direction(d, story)

    def test_invisible_or_malformed_attachment(self):
        story, d = example("floor-ten")
        event = d["shots"][4]["events"][0]
        for anchor in ("kit@extra@wrist1", "ghost@wrist1", "kit@nonexistent"):
            event["anchor"] = anchor
            with self.assertRaisesRegex(ValueError, "attachment"):
                ensemble.check_direction(d, story)

    def test_overlapping_prop_events(self):
        story, d = example("floor-ten")
        e = d["shots"][0]["events"][0]
        d["shots"][0]["events"].append(deepcopy(e))
        with self.assertRaisesRegex(ValueError, "overlapping"):
            ensemble.check_direction(d, story)

    def test_phrase_anchor_moves_camera_object_and_foley_together(self):
        story, direction = example("floor-ten")
        shot = direction["shots"][5]
        line = story["beats"][5]["line"]
        words = line.split()
        marks = [(word, i * 0.2) for i, word in enumerate(words)]
        spoken = next(t for word, t in marks if word == "Twelve.")
        result = ensemble_movie.synchronized(shot, line, marks, 1, 4)
        self.assertAlmostEqual(result["events"][0]["end"], spoken / 4)
        self.assertGreater(result["sounds"][0]["at"], result["events"][0]["end"])
        self.assertLess(result["cameras"][1]["start"], shot["cameras"][1]["start"])
        with self.assertRaisesRegex(ValueError, "spoken phrases"):
            ensemble.phrase_starts("He went home and he slept.", [{"at": 0.4, "words": "he"}])

    def test_word_clock(self):
        result = ensemble_movie.timings([24000, 63500, 10000, 172000], 23, 30)
        self.assertEqual(sum(result), 690)
        self.assertTrue(all(b > a for a, b in zip(sorted(result), sorted(result)[1:])))

    def test_generated_blocks_revise_and_resume(self):
        story, d = example("bell-bay")
        without_seconds = {k: v for k, v in story.items() if k != "seconds"}
        treatment = {k: k.replace("_", " ") for k in ensemble.TREATMENT["properties"]}
        replies = [
            treatment,
            without_seconds,
            dict(verdict="revise", problem="Tighten the ending.", correction="Keep the callback."),
            without_seconds,
            dict(verdict="pass", problem="", correction=""),
            {k: v for k, v in d.items() if k != "shots"},
        ]
        replies += [dict(shots=d["shots"][n : n + 3]) for n in range(0, len(d["shots"]), 3)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(planning, "generate", side_effect=deepcopy(replies)) as provider:
                a, b = ensemble.plan(root, "A harbor with bridges of light", 120)
                self.assertEqual(provider.call_count, len(replies))
                self.assertEqual((a, b), (story, d))
            with patch.object(planning, "generate", side_effect=AssertionError("Unexpected model call")):
                (root / "direction.json").unlink()
                a, b = ensemble.plan(root, "resume", 120)
                self.assertEqual((a, b), (story, d))

    def test_native_time_and_camera(self):
        recipe = {"frames": 24}
        for window in (2, 8):
            self.assertAlmostEqual(shot_rhythm.performance_sample(0.5, window, recipe)[0], 12)
        self.assertEqual(shot_rhythm.performance_sample(2, 8, recipe)[1], 0)
        self.assertEqual(shot_rhythm.performance_sample(2, 8, recipe, "sustain"), (24, 1))
        self.assertAlmostEqual(
            shot_rhythm.performance_sample(0.4, 4, recipe, "cycle")[0],
            shot_rhythm.performance_sample(2.4, 4, recipe, "cycle")[0],
        )
        self.assertEqual(shot_rhythm.camera_width(3, 0.8, "hold"), 3)
        self.assertLess(shot_rhythm.camera_width(3, 0.25, "punch"), 2.5)

    def test_dialogue_and_branched_causality(self):
        story, d = example("last-clap")
        beat, shot = story["beats"][13], d["shots"][13]
        words = beat["line"].split()
        result = ensemble_movie.sync_dialogue(
            shot, beat["line"], [(w, i * 0.2) for i, w in enumerate(words)], 1, 6
        )
        speaking = [a["id"] for a in result["actors"] if a.get("syllables")]
        self.assertEqual(speaking, ["nell"])
        shot["dialogue"][0]["actor"] = "offscreen"
        with self.assertRaisesRegex(ValueError, "speaker"):
            ensemble.check_direction(d, story)
        story["beats"][5]["also_because"] = [6]
        with self.assertRaisesRegex(ValueError, "secondary causes"):
            ensemble.check_story(story)

    def test_overlap_report_and_cut_durations(self):
        _, d = example("last-clap")
        shot = deepcopy(d["shots"][0])
        a, b = shot["actors"][:2]
        b["at"], b["to"] = a["at"], a["to"]
        result = ensemble_review.directing_stats(
            dict(
                fps=30, looks={v["id"]: v for v in d["looks"]}, shots=[dict(shot=shot, frames=180, clock=0)]
            )
        )
        self.assertIn([a["id"], b["id"]], [v["actors"] for v in result["sustained_actor_overlaps"]])
        self.assertEqual(len(result["opening_15s_shot_starts"]), len(shot["cameras"]))

    def test_introductions_and_visual_accents_have_visible_targets(self):
        story, d = example("last-clap")
        story["introductions"][0]["words"] = "text that is not spoken"
        with self.assertRaisesRegex(ValueError, "spoken phrases"):
            ensemble.check_story(story)
        story, d = example("last-clap")
        d["shots"][0]["accents"][0]["focus"] = "in_another_town"
        with self.assertRaisesRegex(ValueError, "visual accent"):
            ensemble.check_direction(d, story)

    def test_stored_legacy_schema_and_strict_model_schema(self):
        camera = dict(start=0, focus=["pip"], size=2, angle=0, elevation=2, drift=0)
        planning.check(camera, ensemble.CAM)
        strict = planning.provider_schema(ensemble.CAM)
        self.assertIn("move", strict["required"])
        with self.assertRaises(ValueError):
            planning.check(camera, strict)
        with self.assertRaises(ValueError):
            planning.check(dict(camera, zoom="jump"), ensemble.CAM)

    def test_migrate_named_prop_and_keep_blocking(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "props" / "named"
            directory.mkdir(parents=True)
            old = dict(
                kind="custom",
                label="HOOP",
                color="red",
                parts=[dict(shape="box", x=0, y=0, z=1, width=2, depth=0.2, height=0.1, color="red")],
            )
            planning.save(directory / "hoop.json", old)
            path, model = ensemble_movie.named_model(root, "hoop")
            design = dict(props=[dict(id="hoop", at=[2, 3, 0], place="pier", scale=0.5)])
            ensemble_movie.bind_model(path, model, "hoop", design)
            p = design["props"][0]
            self.assertEqual((p["at"], p["scale"], p["parts"][0]["size"]), ([2, 3, 0], 0.5, [2, 0.2, 0.1]))
            self.assertEqual(ensemble_movie.named_model(root, "hoop")[1], model)


if __name__ == "__main__":
    unittest.main()
