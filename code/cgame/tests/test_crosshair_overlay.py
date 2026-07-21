#!/usr/bin/env python3
"""Source contracts for the crosshair overlay's visibility and teammate cue."""

from pathlib import Path
import unittest


CGAME = Path(__file__).resolve().parents[1]
DRAWTOOLS = (CGAME / "cg_drawtools.cpp").read_text()


def function_block(source, signature):
    start = source.index(signature)
    opening_brace = source.index("{", start)
    depth = 0

    for index in range(opening_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    raise ValueError(f"unterminated function: {signature}")


class CrosshairOverlayTests(unittest.TestCase):
    def test_mounted_guns_keep_the_overlay(self):
        overlay = function_block(DRAWTOOLS, "void CG_DrawCrosshairOverlay()")

        # Turrets view through a zoomed camera, yet the stock crosshair stays up.
        self.assertIn("CF_CAMERA_ANGLES_TURRETMODE", overlay)
        self.assertIn("(cg.snap->ps.pm_flags & PMF_CAMERA_VIEW) && !onTurret", overlay)
        self.assertIn("(cg.snap->ps.stats[STAT_INZOOM] && !onTurret)", overlay)
        self.assertNotIn("PMF_CAMERA_VIEW | PMF_SPECTATING", overlay)

    def test_overlay_and_stock_crosshair_share_the_teammate_cue(self):
        overlay = function_block(DRAWTOOLS, "void CG_DrawCrosshairOverlay()")
        stock = function_block(DRAWTOOLS, "void CG_DrawCrosshair()")
        teammate = function_block(DRAWTOOLS, "static qhandle_t CG_GetFriendCrosshairShader()")

        self.assertIn("cg_crosshair_friend", teammate)
        for block in (overlay, stock):
            self.assertIn("CG_GetFriendCrosshairShader()", block)
            self.assertIn("CG_DrawStockCrosshair(", block)
        self.assertLess(
            overlay.index("CG_GetFriendCrosshairShader()"),
            overlay.index("cgi.R_DrawBox"),
        )


if __name__ == "__main__":
    unittest.main()
