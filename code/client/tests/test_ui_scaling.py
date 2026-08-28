#!/usr/bin/env python3
"""Behavioral contracts for compass-safe message box layout."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
CLIENT_UI = ROOT / "code" / "client" / "cl_ui.cpp"


def automatic_scale(width, height):
    if width > 1920 and height > 1080:
        return height / 1080.0
    return 1.0


def message_box_layout(width, height, compass_cvar):
    scale = automatic_scale(width, height)
    compass_scale = height / 480.0 * compass_cvar
    compass_right = 128.0 * compass_scale
    compass_bottom = 128.0 * compass_scale

    dm_x = min(max(compass_right, 0.0), width)
    dm_width = max(width - dm_x - 192.0 * scale, 0.0)
    dm_height = min(120.0 * scale, height)

    gm_x = min(20.0 * scale, width)
    gm_y = min(max(compass_bottom, dm_height, 0.0), height)
    gm_height = min(128.0 * scale, height - gm_y)

    return {
        "compass_right": compass_right,
        "compass_bottom": compass_bottom,
        "dm": (dm_x, 0.0, dm_width, dm_height),
        "gm": (gm_x, gm_y, width - gm_x, gm_height),
    }


class UIScalingTests(unittest.TestCase):
    def test_legacy_640x480_layout_is_preserved(self):
        layout = message_box_layout(640, 480, 0.75)
        self.assertEqual(layout["dm"], (96.0, 0.0, 352.0, 120.0))
        self.assertEqual(layout["gm"], (20.0, 120.0, 620.0, 128.0))

    def test_message_boxes_clear_compass_and_stay_on_screen(self):
        for width, height in (
            (640, 480),
            (1280, 1024),
            (1920, 1080),
            (3440, 1440),
            (3840, 2160),
        ):
            for compass_cvar in (0.55, 0.75):
                with self.subTest(
                    resolution=(width, height), compass_cvar=compass_cvar
                ):
                    layout = message_box_layout(width, height, compass_cvar)
                    dm_x, dm_y, dm_width, dm_height = layout["dm"]
                    gm_x, gm_y, gm_width, gm_height = layout["gm"]

                    self.assertGreaterEqual(dm_x, layout["compass_right"])
                    self.assertGreaterEqual(
                        gm_y, max(layout["compass_bottom"], dm_y + dm_height)
                    )
                    self.assertGreaterEqual(dm_width, 0.0)
                    self.assertGreaterEqual(gm_height, 0.0)
                    self.assertLessEqual(dm_x + dm_width, width)
                    self.assertLessEqual(gm_x + gm_width, width)
                    self.assertLessEqual(gm_y + gm_height, height)

    def test_client_uses_cached_layout_without_per_frame_math(self):
        source = CLIENT_UI.read_text()
        self.assertIn("cachedGMBoxRectangle", source)
        self.assertIn("cachedDMBoxRectangle", source)
        self.assertIn("UI_UpdateMessageBoxLayout", source)
        self.assertIn("return cachedGMBoxRectangle.pos.y;", source)
        self.assertNotIn("getScreenWidth", source)


if __name__ == "__main__":
    unittest.main()
