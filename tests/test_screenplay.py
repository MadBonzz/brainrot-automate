from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from film import screenplay, screening


class ReviewTests(unittest.TestCase):
    def test_repeated_sentence_inside_distinct_lines(self):
        common = "The same door shut in front of us."
        lines = [
            dict(id=str(i), say=s, evidence="The lock moves.", shots=[{"beat": 1}])
            for i, s in enumerate([common + " Where now?", "We waited. " + common])
        ]
        with self.assertRaisesRegex(ValueError, "Repeated sentence"):
            screenplay.check(lines)

    def test_wrong_take_cannot_select_last_by_accident(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            screenplay.native_source({"beat": 0}, {"shots": [{"frames": 7}]}, Path("."))

    def test_shared_scenery_loaded_once_and_scoped_to_the_plan(self):
        import json

        with TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "bay.json").write_text(json.dumps({"objects": [{"id": "pier"}]}))
            (folder / "cut.json").write_text(
                json.dumps({"objects_from": "bay.json", "objects": [{"id": "actor"}]})
            )
            self.assertEqual(
                [o["id"] for o in screenplay.read_take(folder, "cut.json")["objects"]], ["pier", "actor"]
            )
            with self.assertRaisesRegex(ValueError, "inside the screenplay"):
                screenplay.read_take(folder, "../escape.json")

    def test_physical_action_hits_its_spoken_clause(self):
        scene = {"frames": 91, "speech_cues": [{"time": 1.5, "words": "the door shuts"}]}
        marks = [("Then", 0.1), ("the", 1.8), ("door", 1.95), ("shuts.", 2.2)]
        remap = screenplay.speech_time_map(scene, "Then the door shuts.", marks, 0.1, 0, 121, 30)
        self.assertAlmostEqual(remap(1.5), 1.9)
        self.assertEqual(remap(0), 0)
        self.assertEqual(remap(3), 4)

    def test_reference_file_survives_job_resume(self):
        import json

        with TemporaryDirectory() as temp:
            work = Path(temp)
            script = work / "screenplay.json"
            source = {
                "title": "Crossing",
                "lines": [
                    {
                        "id": "cross",
                        "say": "They cross.",
                        "evidence": "Both cross.",
                        "shots": [{"take": "cross.json"}],
                    }
                ],
            }
            script.write_text(json.dumps(source))
            (work / "cross.json").write_text(json.dumps({"objects_from": "set.json", "objects": []}))
            (work / "set.json").write_text(json.dumps({"objects": [{"id": "bridge"}]}))
            copy = screenplay.save_plan(script, work / "job")
            self.assertEqual(screenplay.read_take(copy.parent, "cross.json")["objects"], [{"id": "bridge"}])

    def test_review_belongs_to_the_export(self):
        with TemporaryDirectory() as temp:
            movie = Path(temp) / "movie.mp4"
            movie.write_bytes(b"different film")
            screening.review_page(movie, {"title": "Rank", "lines": []})
            page = (movie.parent / "screening.html").read_text()
            self.assertIn(screening.movie_hash(movie), page)
            self.assertIn("Unreviewed", page)
