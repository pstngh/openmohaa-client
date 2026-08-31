#!/usr/bin/env python3
"""Source-level contracts for client render-resource caching."""

from pathlib import Path
import unittest


CGAME = Path(__file__).resolve().parents[1]
BEAM = (CGAME / "cg_beam.cpp").read_text()
DRAWTOOLS = (CGAME / "cg_drawtools.cpp").read_text()
ENTS = (CGAME / "cg_ents.c").read_text()
MAIN = (CGAME / "cg_main.c").read_text()
MODELANIM = (CGAME / "cg_modelanim.c").read_text()


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


class FrameResourceCacheTests(unittest.TestCase):
    def test_configstring_image_shaders_are_lazy_and_invalidated(self):
        clear = function_block(MAIN, "static void CG_ClearImageShaderCache")
        lookup = function_block(MAIN, "qhandle_t CG_GetImageShader")
        process = function_block(MAIN, "void CG_ProcessConfigString")

        self.assertIn("memset(cgs.image_precache, -1", clear)
        self.assertIn("cgs.image_precache[index] == -1", lookup)
        self.assertEqual(lookup.count("R_RegisterShader"), 1)
        self.assertIn("num >= CS_IMAGES", process)
        self.assertIn("cgs.image_precache[num - CS_IMAGES] = -1;", process)

    def test_packet_effects_reuse_configstring_shader_handles(self):
        decal = function_block(ENTS, "void CG_Decal")
        multibeam = function_block(BEAM, "void CG_MultiBeam(centity_t *cent)")
        rope = function_block(BEAM, "void CG_Rope")

        for block in (decal, multibeam, rope):
            self.assertIn("CG_GetImageShader", block)
            self.assertNotIn("R_RegisterShader", block)

    def test_beam_updates_only_register_changed_shaders(self):
        lookup = function_block(BEAM, "static qhandle_t CG_GetCachedBeamShader")
        create = function_block(BEAM, "void CG_CreateBeam")

        self.assertIn("R_GetShaderName(beam->beamshader)", lookup)
        self.assertIn("Q_stricmp", lookup)
        self.assertEqual(lookup.count("R_RegisterShader"), 1)
        self.assertGreaterEqual(create.count("CG_GetCachedBeamShader"), 2)
        self.assertNotIn("R_RegisterShader", create)

    def test_hud_shaders_follow_lazy_or_cvar_aware_cache_paths(self):
        disconnect = function_block(DRAWTOOLS, "void CG_DrawDisconnect")
        server_lag = function_block(DRAWTOOLS, "static void CG_DrawServerLag")
        player_team = function_block(DRAWTOOLS, "void CG_DrawPlayerTeam")
        instant_message = function_block(DRAWTOOLS, "void CG_DrawInstantMessageMenu")
        crosshair = function_block(DRAWTOOLS, "void CG_DrawCrosshair")
        crosshair_lookup = function_block(DRAWTOOLS, "static qhandle_t CG_GetCrosshairShader")

        for block in (disconnect, server_lag, player_team):
            self.assertIn("CG_Get", block)
            self.assertNotIn("R_RegisterShader", block)

        self.assertIn("instantMessageShaders[shaderIndex]", instant_message)
        self.assertIn("crosshair->modificationCount", crosshair_lookup)
        self.assertNotIn("R_RegisterShaderNoMip", crosshair)

    def test_team_icon_models_and_identity_axis_skip_frame_work(self):
        player_icon = function_block(MODELANIM, "void CG_PlayerTeamIcon")

        self.assertIn("CG_GetCachedIconModel", player_icon)
        self.assertNotIn("R_RegisterModel", player_icon)
        self.assertIn("AxisClear(iconEnt.axis);", player_icon)
        self.assertNotIn("AnglesToAxis(vTmp", player_icon)


if __name__ == "__main__":
    unittest.main()
