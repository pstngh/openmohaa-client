#!/usr/bin/env python3
"""Behavioral contracts for sound metadata and capped voice rollover."""

from dataclasses import dataclass
from pathlib import Path
import unittest


CLIENT = Path(__file__).resolve().parents[1]
SOUND_INFO = CLIENT / "snd_info.cpp"
OPENAL = CLIENT / "snd_openal_new.cpp"


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


@dataclass
class Channel:
    entity: int
    entity_channel: int
    start_time: int
    playing: bool = True


def make_room(channels, limit, incoming_entity, incoming_channel, listener_entity=0):
    if limit <= 0:
        return True, None

    remaining = limit
    replacement = None
    replacement_matches = False
    for index, channel in enumerate(channels):
        if not channel.playing:
            continue

        can_replace = (
            (channel.entity != listener_entity or incoming_entity == listener_entity)
            and channel.entity_channel <= incoming_channel
        )
        matches = (
            incoming_channel != 0
            and channel.entity == incoming_entity
            and channel.entity_channel == incoming_channel
        )
        if can_replace and (
            replacement is None
            or (matches and not replacement_matches)
            or (
                matches == replacement_matches
                and (
                    channel.entity_channel < channels[replacement].entity_channel
                    or (
                        channel.entity_channel
                        == channels[replacement].entity_channel
                        and channel.start_time < channels[replacement].start_time
                    )
                )
            )
        ):
            replacement = index
            replacement_matches = matches

        remaining -= 1
        if remaining == 0:
            return replacement is not None, replacement

    return True, None


class SoundConcurrencyTests(unittest.TestCase):
    def test_new_sound_rolls_over_oldest_voice_at_limit(self):
        channels = [Channel(entity=i + 1, entity_channel=6, start_time=100 + i) for i in range(10)]

        allowed, replacement = make_room(channels, 10, incoming_entity=20, incoming_channel=6)

        self.assertTrue(allowed)
        self.assertEqual(replacement, 0)

    def test_same_entity_channel_is_reused_before_an_unrelated_voice(self):
        channels = [
            Channel(entity=7, entity_channel=6, start_time=90),
            Channel(entity=3, entity_channel=6, start_time=110),
        ]

        allowed, replacement = make_room(channels, 2, incoming_entity=3, incoming_channel=6)

        self.assertTrue(allowed)
        self.assertEqual(replacement, 1)

    def test_remote_sound_never_replaces_listener_owned_voice(self):
        channels = [Channel(entity=0, entity_channel=6, start_time=100)]

        allowed, replacement = make_room(channels, 1, incoming_entity=4, incoming_channel=6)

        self.assertFalse(allowed)
        self.assertIsNone(replacement)

    def test_lower_priority_sound_does_not_replace_higher_priority_voice(self):
        channels = [Channel(entity=4, entity_channel=8, start_time=100)]

        allowed, replacement = make_room(channels, 1, incoming_entity=5, incoming_channel=6)

        self.assertFalse(allowed)
        self.assertIsNone(replacement)

    def test_unlimited_sound_does_not_scan_or_replace_channels(self):
        channels = [Channel(entity=1, entity_channel=6, start_time=100)]
        self.assertEqual(make_room(channels, 0, incoming_entity=2, incoming_channel=6), (True, None))

    def test_metadata_values_are_consumed_and_floats_stay_fractional(self):
        source = SOUND_INFO.read_text()
        self.assertNotIn("if (!tiki.TokenAvailable(qtrue))", source)
        self.assertIn("max_factor = atof(token);", source)
        self.assertIn("number_of_sfx_infos == MAX_SFX_INFOS", source)

    def test_openal_limit_rolls_over_instead_of_dropping_newest(self):
        source = OPENAL.read_text()
        self.assertIn("S_OPENAL_FindVoiceToReplace", source)
        self.assertIn("pReplacement->end_sample();", source)
        self.assertNotIn("S_OPENAL_ShouldPlay", source)

    def test_only_audible_sounds_roll_a_voice_over(self):
        source = OPENAL.read_text()
        find = function_block(source, "static qboolean S_OPENAL_FindVoiceToReplace")
        start = function_block(source, "void S_OPENAL_StartSound(")
        start_2d = start.index("S_OPENAL_Start2DSound(")
        rollover_3d = start.index("pReplacement->end_sample();", start_2d)

        # Searching must not stop anything.
        self.assertNotIn("end_sample", find)
        # 2D sounds always start.
        self.assertLess(start.index("pReplacement->end_sample();"), start_2d)
        # A 3D sound set up out of range never starts, so it must not replace a
        # voice. Ending the voice before picking a channel frees that channel.
        self.assertLess(start.index("S_OPENAL_ShouldStart(vOrigin"), rollover_3d)
        self.assertLess(rollover_3d, start.index("S_OPENAL_PickChannel3D"))


if __name__ == "__main__":
    unittest.main()
