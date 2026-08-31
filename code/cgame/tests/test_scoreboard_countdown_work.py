#!/usr/bin/env python3
"""Behavioral contracts for change-driven scoreboard and countdown work."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CGAME = ROOT / "cgame"
CLIENT = ROOT / "client"

CONSOLE_COMMANDS = (CGAME / "cg_consolecmds.c").read_text()
DRAWTOOLS = (CGAME / "cg_drawtools.cpp").read_text()
UI = (CLIENT / "cl_ui.cpp").read_text()


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


def scores_down(show_scores, request_time, now):
    requests = 0
    shows = 0

    if request_time + 2000 < now:
        request_time = now
        requests += 1
    if not show_scores:
        show_scores = True
        shows += 1

    return show_scores, request_time, requests, shows


def update_scoreboard_visibility(requested, menu_active, dirty, previous_menu_active):
    if not dirty and previous_menu_active == menu_active:
        return dirty, previous_menu_active, []

    action = "show" if requested and not menu_active else "hide"
    return False, menu_active, [action]


class ScoreboardCountdownWorkTests(unittest.TestCase):
    def test_held_scoreboard_shows_once_but_keeps_two_second_requests(self):
        show_scores = False
        request_time = 0
        requests = 0
        shows = 0

        for now in (100, 1000, 2000, 2001, 3000, 4001, 4002):
            show_scores, request_time, new_requests, new_shows = scores_down(
                show_scores, request_time, now
            )
            requests += new_requests
            shows += new_shows

        self.assertEqual(shows, 1)
        self.assertEqual(requests, 2)

    def test_cgame_score_path_only_touches_ui_on_visibility_transition(self):
        scores = function_block(CONSOLE_COMMANDS, "void CG_ScoresDown_f")

        self.assertEqual(scores.count("UI_ShowScoreBoard"), 1)
        self.assertEqual(scores.count('SendClientCommand("score")'), 1)
        self.assertLess(scores.index("if (!cg.showScores)"), scores.index("UI_ShowScoreBoard"))

    def test_scoreboard_ui_work_only_runs_when_state_changes(self):
        dirty, menu_active, actions = update_scoreboard_visibility(True, False, True, False)
        self.assertEqual(actions, ["show"])

        dirty, menu_active, actions = update_scoreboard_visibility(True, False, dirty, menu_active)
        self.assertEqual(actions, [])

        dirty, menu_active, actions = update_scoreboard_visibility(True, True, dirty, menu_active)
        self.assertEqual(actions, ["hide"])

        dirty, menu_active, actions = update_scoreboard_visibility(True, True, dirty, menu_active)
        self.assertEqual(actions, [])

        dirty, menu_active, actions = update_scoreboard_visibility(True, False, dirty, menu_active)
        self.assertEqual(actions, ["show"])

    def test_ui_helper_returns_before_hierarchy_work_on_unchanged_frames(self):
        update = function_block(UI, "static void UI_UpdateScoreboardVisibility")
        ui_frame = function_block(UI, "void UI_Update(void)")
        show = function_block(UI, "void UI_ShowScoreboard_f")
        hide = function_block(UI, "void UI_HideScoreboard_f")

        self.assertLess(update.index("return;"), update.index("menuManager.FindMenu"))
        self.assertLess(update.index("return;"), update.index("ForceShow"))
        self.assertEqual(ui_frame.count("UI_UpdateScoreboardVisibility();"), 2)
        self.assertIn("scoreboard_requested        = qtrue;", show)
        self.assertIn("scoreboard_requested        = qfalse;", hide)
        self.assertNotIn("ForceShow", show)
        self.assertNotIn("ForceHide", hide)

    def test_countdown_formats_only_when_displayed_second_changes(self):
        countdown = function_block(DRAWTOOLS, "void CG_UpdateCountdown()")
        cache_check = countdown.index("cg.countdownDisplayState == desiredState")
        localization = countdown.index("LV_ConvertString")

        self.assertLess(cache_check, localization)
        self.assertIn("cg.countdownSeconds == secondsLeft", countdown)
        self.assertIn("cg.countdownModificationCount == ui_timemessage->modificationCount", countdown)
        self.assertEqual(countdown.count("LV_ConvertString"), 1)
        self.assertEqual(countdown.count('Cvar_Set("ui_timemessage"'), 1)


if __name__ == "__main__":
    unittest.main()
