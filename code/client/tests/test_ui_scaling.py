#!/usr/bin/env python3
"""Behavioral contracts for compass-safe layout and cached HUD scaling."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
CLIENT_UI = ROOT / "code" / "client" / "cl_ui.cpp"
CLIENT_MAIN = ROOT / "code" / "client" / "cl_main.cpp"
UI_WIDGET = ROOT / "code" / "uilib" / "uiwidget.cpp"
UI_WIDGET_HEADER = ROOT / "code" / "uilib" / "uiwidget.h"


def automatic_scale(width, height):
    if width > 1920 and height > 1080:
        return height / 1080.0
    return 1.0


def message_box_layout(width, height, compass_cvar, ui_scale=1.0):
    ui_scale = min(max(ui_scale, 0.5), 2.0)
    scale = automatic_scale(width, height) * ui_scale
    compass_scale = height / 480.0 * compass_cvar * ui_scale
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
                for ui_scale in (0.5, 0.8, 1.0, 1.25, 2.0):
                    with self.subTest(
                        resolution=(width, height),
                        compass_cvar=compass_cvar,
                        ui_scale=ui_scale,
                    ):
                        layout = message_box_layout(
                            width, height, compass_cvar, ui_scale
                        )
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

    def test_ui_scale_changes_hud_geometry_once(self):
        baseline = message_box_layout(1920, 1080, 0.75, 1.0)

        for ui_scale in (0.5, 0.8, 1.25, 2.0):
            with self.subTest(ui_scale=ui_scale):
                layout = message_box_layout(1920, 1080, 0.75, ui_scale)
                self.assertAlmostEqual(
                    layout["compass_right"],
                    baseline["compass_right"] * ui_scale,
                )
                self.assertAlmostEqual(
                    layout["dm"][3], baseline["dm"][3] * ui_scale
                )
                self.assertAlmostEqual(
                    layout["gm"][0], baseline["gm"][0] * ui_scale
                )

    def test_ui_scale_is_clamped(self):
        self.assertEqual(
            message_box_layout(1920, 1080, 0.75, 0.1),
            message_box_layout(1920, 1080, 0.75, 0.5),
        )
        self.assertEqual(
            message_box_layout(1920, 1080, 0.75, 4.0),
            message_box_layout(1920, 1080, 0.75, 2.0),
        )

    def test_client_uses_cached_layout_without_per_frame_math(self):
        source = CLIENT_UI.read_text()
        self.assertIn("cachedGMBoxRectangle", source)
        self.assertIn("cachedDMBoxRectangle", source)
        self.assertIn("UI_UpdateMessageBoxLayout", source)
        self.assertIn("return cachedGMBoxRectangle.pos.y;", source)
        self.assertNotIn("getScreenWidth", source)

    def test_ui_scale_is_latched_and_not_polled_per_frame(self):
        source = CLIENT_UI.read_text()
        update_start = source.index("void UI_Update(void)")
        update_end = source.index(
            "void UI_MultiplayerMenuWidgetsUpdate(void)", update_start
        )
        update_body = source[update_start:update_end]

        self.assertIn(
            'Cvar_Get("ui_scale", "1", CVAR_ARCHIVE | CVAR_LATCH)', source
        )
        self.assertIn("Cvar_CheckRange(ui_scale, 0.5f, 2.0f, qfalse);", source)
        self.assertNotIn("ui_scale", update_body)
        self.assertNotIn("modificationCount", source)

    def test_hud_widgets_cache_scale_during_realign(self):
        source = UI_WIDGET.read_text()
        header = UI_WIDGET_HEADER.read_text()

        self.assertIn("#define WF_HUD_SCALE", header)
        self.assertIn("VectorScale2D(out, uid.hudScale, out);", source)
        self.assertIn("m_bVirtual = true;", source)

        getter_start = source.index("const vec2_t& UIWidget::getVirtualScale() const")
        getter_end = source.index(
            "const vec2_t& UIWidget::getHighResScale() const", getter_start
        )
        self.assertNotIn("WF_HUD_SCALE", source[getter_start:getter_end])

    def test_cgame_receives_new_scale_after_resolution_reflow(self):
        source = CLIENT_MAIN.read_text()
        start = source.index("qboolean CL_SetVidMode( int mode )")
        end = source.index("void CL_SetFullscreen", start)
        body = source[start:end]

        self.assertLess(
            body.index("UI_ResolutionChange();"),
            body.index("cge->CG_GetRendererConfig();"),
        )


if __name__ == "__main__":
    unittest.main()
