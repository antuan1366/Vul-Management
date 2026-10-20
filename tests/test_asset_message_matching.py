import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import Base  # noqa: E402
from app.models.asset_field import AssetFieldDefinition, AssetFieldValue  # noqa: E402
from app.models.equipment import Equipment  # noqa: E402
from app.services.asset_message_matching import (  # noqa: E402
    _normalize,
    _term_variants,
    build_asset_match_index,
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

    def test_ipv4_is_preserved_as_a_single_match_phrase(self):
        self.assertIn("192 168 1 10", _term_variants("192.168.1.10"))
        index = [
            {
                "asset_id": 4,
                "asset_type": "equipment",
                "asset_type_label": "Equipment",
                "asset_name": "Core Router",
                "terms": {"192 168 1 10": ["IP Address"]},
            }
        ]
        self.assertTrue(match_message_to_assets("Alert for 192.168.1.10", index)["matched"])

    def test_builds_match_index_from_asset_records_and_custom_values(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                asset = Equipment(
                    name="Payment Gateway",
                    device_type="Firewall",
                    vendor="Fortinet",
                    model="FortiGate-100F",
                )
                db.add(asset)
                db.flush()

                field = AssetFieldDefinition(
                    asset_type="equipment",
                    field_key="service_owner",
                    label="Service Owner",
                    field_type="text",
                    required=False,
                    visible=True,
                    system_field=False,
                    editable=True,
                    deletable=True,
                )
                db.add(field)
                db.flush()
                db.add(
                    AssetFieldValue(
                        asset_type="equipment",
                        asset_id=asset.id,
                        field_id=field.id,
                        value="Payment Platform",
                    )
                )
                db.commit()

                index = build_asset_match_index(db)
                result = match_message_to_assets(
                    "Fortinet FortiGate 100F advisory mentions the Payment Platform",
                    index,
                )

                self.assertTrue(result["matched"])
                self.assertEqual(result["asset_match_count"], 1)
                matched_asset = result["asset_matches"][0]
                self.assertEqual(matched_asset["asset_name"], "Payment Gateway")
                self.assertIn(
                    "Vendor / Brand",
                    [
                        field_name
                        for term in matched_asset["matched_terms"]
                        for field_name in term["fields"]
                    ],
                )
                self.assertIn(
                    "Service Owner",
                    [
                        field_name
                        for term in matched_asset["matched_terms"]
                        for field_name in term["fields"]
                    ],
                )
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
