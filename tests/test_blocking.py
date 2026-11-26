import unittest
from copy import deepcopy
from math import dist

from film import blocking


def actor(name, x, y):
    return dict(id=name, at=[x, y], to=[x, y], start=0.1, end=0.7)


class BlockingTests(unittest.TestCase):
    def test_entrance_keeps_contact_mark_and_clears_bystander(self):
        lead, other = actor("child", 0, 0), actor("guard", -1.05, 0)
        lead["travel"] = dict(kind="enter", side="left", distance=2.1)
        original = dict(actors=[lead, other])
        shot = blocking.resolve(original, dict(child=1, guard=1))
        mover = shot["actors"][0]
        self.assertEqual(mover["to"], [0, 0])
        self.assertNotEqual(mover["at"][1], 0)
        self.assertNotIn("travel", mover)
        self.assertEqual(original["actors"][0]["at"], [0, 0])
        for i in range(51):
            self.assertGreaterEqual(dist(blocking.position(mover, i / 50), other["at"]), 0.55)
        self.assertIs(shot, blocking.resolve(shot, dict(child=1, guard=1)))

    def test_exit_preserves_first_pose_and_as_blocked_preserves_old_take(self):
        old = dict(actors=[actor("child", 1, 1)])
        self.assertIs(blocking.resolve(old, dict(child=1)), old)
        change = deepcopy(old)
        change["actors"][0]["travel"] = dict(kind="exit", side="front", distance=1.2)
        out = blocking.resolve(change, dict(child=1))["actors"][0]
        self.assertEqual((out["at"], out["to"]), ([1, 1], [1.0, -0.2]))
        change["actors"][0]["travel"]["kind"] = "as_blocked"
        self.assertEqual(blocking.resolve(change, dict(child=1)), old)

    def test_follow_covers_the_travel_and_preserves_a_specialty_view(self):
        child = actor("child", 1, 1)
        child["travel"] = dict(kind="enter", side="right", distance=1.5, coverage="follow")
        cameras = [
            dict(start=0, focus=["town"], size=5, vista="desert_queue"),
            dict(start=0.25, focus=["town"], size=2, move="hold"),
            dict(start=0.8, focus=["door"], size=2, move="hold"),
        ]
        framed = blocking.resolve(dict(actors=[child], cameras=cameras), dict(child=1))
        self.assertEqual(framed["cameras"][0], cameras[0])
        self.assertEqual(framed["cameras"][1]["focus"], ["child"])
        self.assertEqual(framed["cameras"][1]["move"], "follow")
        self.assertEqual(framed["cameras"][2], cameras[2])

    def test_frozen_actor_cannot_walk_in(self):
        frozen = actor("statue", 1, 1)
        frozen.update(pose="frozen", travel=dict(kind="enter", side="right", distance=1.2))
        with self.assertRaisesRegex(ValueError, "live actor"):
            blocking.resolve(dict(actors=[frozen]), dict(statue=1))
