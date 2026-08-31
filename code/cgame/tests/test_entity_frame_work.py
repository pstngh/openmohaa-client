#!/usr/bin/env python3
"""Behavioral contracts for the packet-entity frame traversal."""

from pathlib import Path
import re
import unittest


CGAME = Path(__file__).resolve().parents[1]
ENTS = (CGAME / "cg_ents.c").read_text()
MODELANIM = (CGAME / "cg_modelanim.c").read_text()

ENTITY_NONE = 1023
MULTIBEAM = 9


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


def traverse_entities(snapshot):
    entities = {entity["number"]: entity for entity in snapshot}
    present = set(entities)
    processed = set()
    added = []
    multibeams = []

    for entity in snapshot:
        if entity["type"] == MULTIBEAM:
            multibeams.append(entity["number"])

    for entity in snapshot:
        child = entity["number"]
        parent = entity["parent"]

        while parent != ENTITY_NONE and parent in present and parent not in processed:
            processed.add(parent)
            added.append(parent)
            parent = entities[parent]["parent"]

        if child not in processed:
            processed.add(child)
            added.append(child)

    return added, multibeams


class EntityFrameWorkTests(unittest.TestCase):
    def test_parent_order_and_deferred_multibeams_are_preserved(self):
        snapshot = [
            {"number": 2, "parent": 1, "type": 0},
            {"number": 1, "parent": ENTITY_NONE, "type": 0},
            {"number": 7, "parent": ENTITY_NONE, "type": MULTIBEAM},
            {"number": 4, "parent": ENTITY_NONE, "type": 0},
            {"number": 9, "parent": ENTITY_NONE, "type": MULTIBEAM},
        ]

        added, multibeams = traverse_entities(snapshot)

        self.assertEqual(added, [1, 2, 7, 4, 9])
        self.assertEqual(multibeams, [7, 9])

    def test_entity_state_uses_generation_markers_instead_of_full_clear(self):
        add_packet_entities = function_block(ENTS, "void CG_AddPacketEntities(void)")

        self.assertNotIn("processed[MAX_ENTITIES]", add_packet_entities)
        self.assertNotIn("num < MAX_ENTITIES", add_packet_entities)
        self.assertIn("entityFrameMarker += 2;", add_packet_entities)
        self.assertIn("entityFrameState[parent] == presentMarker", add_packet_entities)
        self.assertIn("entityFrameState[child] = processedMarker", add_packet_entities)

    def test_multibeams_are_collected_during_the_presence_pass(self):
        add_packet_entities = function_block(ENTS, "void CG_AddPacketEntities(void)")

        self.assertEqual(add_packet_entities.count("cg.snap->numEntities"), 2)
        self.assertIn("multibeams[numMultibeams++] = child;", add_packet_entities)
        self.assertIn("num < numMultibeams", add_packet_entities)
        self.assertIn("CG_MultiBeam(&cg_entities[multibeams[num]])", add_packet_entities)

    def test_discarded_model_lookups_are_removed(self):
        get_origin = function_block(ENTS, "void CG_GetOrigin")

        self.assertNotIn("R_Model_GetHandle", get_origin)
        self.assertIsNone(
            re.search(r"^\s*cgi\.R_Model_GetHandle\(model\.hModel\);\s*$", MODELANIM, re.MULTILINE)
        )


if __name__ == "__main__":
    unittest.main()
