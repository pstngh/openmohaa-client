#!/usr/bin/env python3
"""Source-level contract tests for passive client movement telemetry."""

import ast
import csv
import io
from pathlib import Path
import re
import unittest


CGAME = Path(__file__).resolve().parents[1]
SOURCE = (CGAME / "cg_client_telemetry.cpp").read_text()


def csv_header(file_name):
    marker = f"Append(\n        {file_name},"
    start = SOURCE.index(marker) + len(marker)
    end = SOURCE.index("\n    );", start)
    literals = re.findall(r'"(?:[^"\\]|\\.)*"', SOURCE[start:end])
    text = "".join(ast.literal_eval(literal) for literal in literals).rstrip("\n")
    return next(csv.reader(io.StringIO(text)))


class ClientTelemetryTests(unittest.TestCase):
    def test_frame_and_input_schemas_are_stable(self):
        frame = csv_header("frameFile")
        inputs = csv_header("inputFile")

        self.assertEqual(len(frame), 113)
        self.assertEqual(len(inputs), 20)
        for name in (
            "lean_left",
            "lean_right",
            "command_distance",
            "crosshair_distance",
            "target_entity",
            "target_confidence",
            "nearest_visible_enemy_distance",
        ):
            self.assertIn(name, frame)

    def test_lifecycle_hooks_are_small_and_explicit(self):
        main = (CGAME / "cg_main.c").read_text()
        view = (CGAME / "cg_view.c").read_text()

        self.assertEqual(main.count("CG_ClientTelemetryInit();"), 1)
        self.assertEqual(main.count("CG_ClientTelemetryShutdown();"), 1)
        self.assertEqual(view.count("CG_ClientTelemetryFrame();"), 1)
        self.assertLess(view.index("CG_PredictPlayerState();"), view.index("CG_ClientTelemetryFrame();"))
        self.assertLess(view.index("CG_CalcViewValues();"), view.index("CG_ClientTelemetryFrame();"))
        self.assertLess(view.index("CG_AddPacketEntities();"), view.index("CG_ClientTelemetryFrame();"))

    def test_disabled_path_does_no_recording_work(self):
        start = SOURCE.index('extern "C" void CG_ClientTelemetryFrame(void)')
        end = SOURCE.index('extern "C" void CG_ClientTelemetryShutdown(void)', start)
        frame_hook = SOURCE[start:end]

        self.assertIn("if (!clMoveLog || !clMoveLog->integer)", frame_hook)
        self.assertLess(frame_hook.index("return;"), frame_hook.index("ProcessInputTransitions();"))
        self.assertLess(frame_hook.index("return;"), frame_hook.index("WriteFrame();"))

    def test_recorder_is_local_and_omits_identity_data(self):
        self.assertIn("privacy=no_names_chat_or_network_addresses", SOURCE)
        for forbidden in ("cl_currentServerAddress", "CS_PLAYERS", "G_MoveLogChat", "SendClientCommand"):
            self.assertNotIn(forbidden, SOURCE)

    def test_automatic_session_names_are_unique_across_processes(self):
        self.assertIn("std::chrono::system_clock::now()", SOURCE)
        self.assertIn("for (unsigned int suffix = 2; OutputExists(fileStem); ++suffix)", SOURCE)
        self.assertIn("cgi.FS_ReadFile", SOURCE)
        self.assertIn('"client_telemetry/" + sessionId', SOURCE)


if __name__ == "__main__":
    unittest.main()
