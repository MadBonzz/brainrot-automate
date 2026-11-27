import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from film import visual_review


class VisualReviewTests(unittest.TestCase):
    def test_first_read_is_blind_and_incomplete_verdict_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            film = folder / "movie.mp4"
            film.write_bytes(b"encoded-film")
            cue = dict(id="handoff", start=0, end=2, say="I gave her my badge.", evidence="Both hands hold the badge.")
            (folder / "screening.json").write_text(json.dumps({"lines": [cue]}))

            def frames(movie, line, target, ffmpeg):
                path = target / "frames.jpg"
                path.write_bytes(b"frames")
                return path

            def observe(prompt, schema, job, images=()):
                if images:
                    self.assertNotIn(cue["say"], prompt)
                    self.assertTrue(images[0].is_file())
                    return {"observations": "Two people stand still.", "uncertain": "Their hands are hidden."}
                self.assertIn(cue["say"], prompt)
                self.assertIn("Their hands are hidden.", prompt)
                return {"lines": [], "story_issues": [], "priority_fixes": []}

            with patch.object(visual_review, "sheet", frames), patch.object(visual_review.planning, "generate", observe):
                with self.assertRaisesRegex(ValueError, "omitted"):
                    visual_review.review(film)
            self.assertFalse((folder / "model-visual-review.json").exists())
