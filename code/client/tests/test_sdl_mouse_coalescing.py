#!/usr/bin/env python3
"""Behavioral contracts for SDL relative mouse-motion coalescing."""

from pathlib import Path
import unittest


SDL_INPUT = Path(__file__).resolve().parents[2] / "sdl" / "sdl_input.c"


def coalesce(events):
    queued = []
    delta_x = 0
    delta_y = 0

    for event in events:
        if event[0] != "motion":
            if delta_x or delta_y:
                queued.append(("motion", delta_x, delta_y))
                delta_x = 0
                delta_y = 0
            queued.append(event)
            continue

        delta_x += event[1]
        delta_y += event[2]

    if delta_x or delta_y:
        queued.append(("motion", delta_x, delta_y))

    return queued


class SDLMouseCoalescingTests(unittest.TestCase):
    def test_consecutive_motion_packets_become_one_exact_delta(self):
        events = [
            ("motion", 3, -2),
            ("motion", -1, 5),
            ("motion", 4, -1),
        ]
        self.assertEqual(coalesce(events), [("motion", 6, 2)])

    def test_button_boundaries_preserve_motion_order(self):
        events = [
            ("motion", 2, 1),
            ("motion", 3, -1),
            ("button", "down"),
            ("motion", -4, 2),
            ("button", "up"),
        ]
        self.assertEqual(
            coalesce(events),
            [
                ("motion", 5, 0),
                ("button", "down"),
                ("motion", -4, 2),
                ("button", "up"),
            ],
        )

    def test_cancelled_motion_does_not_queue_empty_work(self):
        events = [("motion", 8, -3), ("motion", -8, 3)]
        self.assertEqual(coalesce(events), [])

    def test_sdl_path_accumulates_before_queueing(self):
        source = SDL_INPUT.read_text()
        self.assertIn("IN_FlushMouseMotion", source)
        self.assertIn("mouseMotionX += e.motion.xrel;", source)
        self.assertIn("mouseMotionY += e.motion.yrel;", source)
        self.assertNotIn(
            "Com_QueueEvent( in_eventTime, SE_MOUSE, e.motion.xrel, e.motion.yrel",
            source,
        )


if __name__ == "__main__":
    unittest.main()
