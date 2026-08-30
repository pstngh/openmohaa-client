#!/usr/bin/env python3
"""Behavioral contracts for transition-driven multiplayer HUD work."""

from pathlib import Path
import unittest


CGAME = Path(__file__).resolve().parents[1]
DRAWTOOLS = (CGAME / "cg_drawtools.cpp").read_text()
MAIN = (CGAME / "cg_main.c").read_text()
SERVER_COMMANDS = (CGAME / "cg_servercmds.c").read_text()

UNINITIALIZED = 0
HIDDEN = 1
NORMAL = 2
FUSE = 3
FUSE_WET = 4

HUD_NAMES = {
    NORMAL: "hud_stopwatch",
    FUSE: "hud_fuse",
    FUSE_WET: "hud_fuse_wet",
}


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


def transition_stopwatch_hud(current, desired):
    commands = []
    if current == desired:
        return desired, commands

    if current == UNINITIALIZED:
        commands.extend(f"ui_removehud {name}" for name in HUD_NAMES.values())
    elif current in HUD_NAMES:
        commands.append(f"ui_removehud {HUD_NAMES[current]}")

    if desired in HUD_NAMES:
        commands.append(f"ui_addhud {HUD_NAMES[desired]}")

    return desired, commands


class HudFrameWorkTests(unittest.TestCase):
    def test_unchanged_stopwatch_states_issue_no_commands(self):
        state, commands = transition_stopwatch_hud(UNINITIALIZED, HIDDEN)
        self.assertEqual(len(commands), 3)

        state, commands = transition_stopwatch_hud(state, HIDDEN)
        self.assertEqual(commands, [])

        state, commands = transition_stopwatch_hud(state, NORMAL)
        self.assertEqual(commands, ["ui_addhud hud_stopwatch"])

        state, commands = transition_stopwatch_hud(state, NORMAL)
        self.assertEqual(commands, [])

    def test_stopwatch_type_transitions_replace_only_the_active_hud(self):
        state, commands = transition_stopwatch_hud(NORMAL, FUSE)
        self.assertEqual(
            commands,
            ["ui_removehud hud_stopwatch", "ui_addhud hud_fuse"],
        )

        state, commands = transition_stopwatch_hud(state, FUSE_WET)
        self.assertEqual(
            commands,
            ["ui_removehud hud_fuse", "ui_addhud hud_fuse_wet"],
        )

        state, commands = transition_stopwatch_hud(state, HIDDEN)
        self.assertEqual(commands, ["ui_removehud hud_fuse_wet"])

    def test_stopwatch_draw_path_keeps_smooth_values_without_ui_commands(self):
        draw = function_block(DRAWTOOLS, "void CG_DrawStopwatch()")
        transition = function_block(
            DRAWTOOLS, "static void CG_SetStopwatchHudState"
        )
        shutdown = function_block(MAIN, "void CG_Shutdown(void)")

        self.assertIn('cgi.Cvar_Set("ui_stopwatch"', draw)
        self.assertIn("CG_SetStopwatchHudState(desiredState);", draw)
        self.assertNotIn("Cmd_Execute", draw)
        self.assertIn("cg.stopwatchHudState == desiredState", transition)
        self.assertLess(
            transition.index("return;"),
            transition.index("CG_ExecuteStopwatchHudCommand"),
        )
        self.assertIn("CG_ClearStopwatchHud();", shutdown)

    def test_objective_draw_path_uses_the_event_updated_cache(self):
        draw = function_block(DRAWTOOLS, "void CG_DrawObjectives()")
        process = function_block(MAIN, "void CG_ProcessConfigString")
        modified = function_block(
            SERVER_COMMANDS, "static void CG_ConfigStringModified"
        )

        self.assertIn("cg.ObjectivesCurrentIndex", draw)
        self.assertNotIn("CG_ProcessConfigString", draw)
        self.assertNotIn("CG_ConfigString(CS_CURRENT_OBJECTIVE)", draw)
        self.assertIn("num >= CS_OBJECTIVES", process)
        self.assertIn("objective->flags", process)
        self.assertIn("objective->text", process)
        self.assertIn("CG_ProcessConfigString(num, modelOnly);", modified)

    def test_objective_cache_is_populated_on_load_and_restart(self):
        received = function_block(MAIN, "void CG_GameStateReceived(void)")
        restarted = function_block(MAIN, "void CG_ServerRestarted(void)")
        prep = function_block(MAIN, "void CG_PrepRefresh(void)")
        refresh = function_block(DRAWTOOLS, "void CG_RefreshObjectives()")

        self.assertLess(
            received.index("CG_InitializeObjectives();"),
            received.index("CG_PrepRefresh();"),
        )
        self.assertIn("CG_ProcessConfigString(i, qfalse);", prep)
        self.assertIn("CG_ProcessConfigString(CS_CURRENT_OBJECTIVE, qfalse);", refresh)
        self.assertIn("CS_OBJECTIVES + MAX_OBJECTIVES", refresh)
        self.assertLess(
            restarted.index("CG_InitializeObjectives();"),
            restarted.index("CG_RefreshObjectives();"),
        )


if __name__ == "__main__":
    unittest.main()
