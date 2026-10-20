import unittest

from airplay_trial_lab import (
    DENON_FEATURES,
    TECNOHEAD_FEATURES,
    WIIM_FEATURES,
    feature_diff,
    observation,
    option_plan,
    parse_features,
)


class TrialLabTests(unittest.TestCase):
    def test_feature_word_order_and_difference(self):
        self.assertEqual(parse_features(TECNOHEAD_FEATURES), 0x0005C340401C4A00)
        delta = feature_diff(TECNOHEAD_FEATURES, WIIM_FEATURES)
        self.assertEqual(delta["added"], [15, 16, 17, 22, 26])
        self.assertEqual(delta["removed"], [14, 50])
        self.assertEqual(feature_diff(WIIM_FEATURES, DENON_FEATURES)["added"], [59])

    def test_rejects_bad_feature_values(self):
        for value in ("0x123", "0x100000000,0", "garbage,0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_features(value)

    def test_combined_plan_is_one_zone_and_does_not_enable_vendor_mask(self):
        self.assertEqual(
            option_plan("M3", "pool"),
            {
                "apple_legacy_metadata_zone": "pool",
                "apple_feature_comparison_zone": "off",
                "apple_mediaremote_forward_zone": "pool",
            },
        )
        for zone in ("both", "wiim"):
            with self.subTest(zone=zone), self.assertRaises(ValueError):
                option_plan("M3", zone)

    def test_record_only_structured_outcome(self):
        states = {
            "discovered": True,
            "speaker_icon": False,
            "sender_metadata": True,
            "hk_access": False,
            "rc_event_open": False,
            "rc_ack": False,
            "home_art": False,
            "home_controls": False,
        }
        result = observation("M1", "pool", states)
        self.assertFalse(result["home_native_success"])
        self.assertEqual(result["options"]["apple_mediaremote_forward_zone"], "pool")
        with self.assertRaises(ValueError):
            observation("M1", "pool", {"title": "private"})


if __name__ == "__main__":
    unittest.main()
