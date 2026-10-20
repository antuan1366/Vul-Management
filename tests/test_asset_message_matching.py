import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.asset_message_matching import (  # noqa: E402
    _normalize,
    _term_variants,
    match_message_to_assets,
)


class AssetMessageMatchingTests(unittest.TestCase):
    def test_separator_normalization_supports_vendor_and_model_mentions(self):
        index = [
            {
                "asset_id": 12,
                "asset_type": "equipment",
                "asset_type_label": "Equipment",
                "asset_name": "Edge Firewall",
                "terms": {
                    "fortinet": ["Vendor / Brand"],
                    "fortigate 100f": ["Model"],
                },
            }
        ]

        result = match_message_to_assets(
            "Fortinet advisory: FortiGate-100F is mentioned in this report.",
            index,
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["asset_match_count"], 1)
        self.assertEqual(result["asset_matches"][0]["asset_name"], "Edge Firewall")
        self.assertEqual(
            {item["term"] for item in result["asset_matches"][0]["matched_terms"]},
            {"fortinet", "fortigate 100f"},
        )

    def test_matching_respects_word_boundaries(self):
        index = [
            {
                "asset_id": 1,
                "asset_type": "application",
                "asset_type_label": "Application",
                "asset_name": "Microsoft SQL Server",
                "terms": {"microsoft": ["Vendor / Brand"]},
            }
        ]

        self.assertFalse(match_message_to_assets("microsofthost is down", index)["matched"])
        self.assertTrue(match_message_to_assets("Microsoft released a security update", index)["matched"])

    def test_generic_inventory_values_do_not_become_keywords(self):
        self.assertEqual(_term_variants("Production"), [])
        self.assertEqual(_term_variants("High"), [])
        self.assertIn("fortinet", _term_variants("Fortinet"))
        self.assertIn("hp", _term_variants("HP"))

    def test_underscores_and_punctuation_normalize_consistently(self):
        self.assertEqual(_normalize("edge_switch-1"), "edge switch 1")
        self.assertEqual(_normalize("FortiGate/100F"), "fortigate 100f")


if __name__ == "__main__":
    unittest.main()
