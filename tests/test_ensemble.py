"""Contract regressions for block generation, editorial causality, prop ownership and timing."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from film import ensemble, ensemble_movie, planning

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    folder = ROOT / "example" / name
    return tuple(json.loads((folder / (k + ".json")).read_text()) for k in ("story", "direction"))


class EpisodeTests(unittest.TestCase):
    def test_both_saved_worlds(self):
        for name in ("floor-ten", "bell-bay"):
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
        replies = [
            without_seconds,
            dict(verdict="revise", problem="Tighten the ending.", correction="Keep the callback."),
            without_seconds,
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
