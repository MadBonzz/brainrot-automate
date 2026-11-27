from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from film import screenplay, screening


class ReviewTests(unittest.TestCase):
    def test_repeated_sentence_inside_distinct_lines(self):
        common = "The same door shut in front of us."
        lines = [dict(id=str(i),say=s,evidence="The lock moves.",shots=[{"beat":1}])
                 for i,s in enumerate([common+" Where now?", "We waited. "+common])]
        with self.assertRaisesRegex(ValueError,"Repeated sentence"):
            screenplay.check(lines)

    def test_wrong_take_cannot_select_last_by_accident(self):
        with self.assertRaisesRegex(ValueError,"does not exist"):
            screenplay.native_source({"beat":0},{"shots":[{"frames":7}]},Path("."))

    def test_review_belongs_to_the_export(self):
        with TemporaryDirectory() as temp:
            movie=Path(temp)/"movie.mp4"
            movie.write_bytes(b"different film")
            screening.review_page(movie,{"title":"Rank","lines":[]})
            page=(movie.parent/"screening.html").read_text()
            self.assertIn(screening.movie_hash(movie),page)
            self.assertIn("Unreviewed",page)
