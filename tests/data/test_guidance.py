import json
import tempfile
import unittest
from pathlib import Path

from app.contracts.models import DataKind
from app.contracts.services import GuidanceUnavailableError
from app.guidance import (
    JsonGuidanceService,
    SCENARIO_ID,
    GuidanceDataError,
    get_crop_guidance,
    load_guidance,
    validate_evidence_ids,
    validate_guidance,
)


class GuidanceTests(unittest.TestCase):
    def test_default_guidance_is_explicit_fixture_without_sources(self):
        guidance = load_guidance()

        self.assertEqual(guidance["scenarioId"], SCENARIO_ID)
        self.assertEqual(guidance["dataKind"], "fixture")
        self.assertIsNone(guidance["reviewedAt"])
        self.assertEqual(len(guidance["sources"]), 3)
        self.assertTrue(all(source["url"] is None for source in guidance["sources"]))
        self.assertLessEqual(len(guidance["cards"]), 3)
        source_ids = {source["id"] for source in guidance["sources"]}
        self.assertTrue(all(card["evidenceIds"][0] in source_ids for card in guidance["cards"]))
        self.assertTrue(all("실제 재배" in card["caution"] for card in guidance["cards"]))

    def test_get_crop_guidance_rejects_unknown_scenario(self):
        with self.assertRaises(GuidanceDataError):
            get_crop_guidance("another-scenario")

    def test_fixture_evidence_ids_are_validated_against_cards(self):
        guidance = load_guidance()

        self.assertEqual(
            validate_evidence_ids(guidance, ["fixture-evidence-01"]),
            ["fixture-evidence-01"],
        )

    def test_unregistered_evidence_id_is_rejected(self):
        guidance = load_guidance()

        with self.assertRaisesRegex(GuidanceDataError, "unregistered evidence id"):
            validate_evidence_ids(guidance, ["fixture-evidence-unknown"])

    def test_empty_fixture_guidance_is_valid_and_has_no_valid_evidence(self):
        empty_guidance = {
            "scenarioId": SCENARIO_ID,
            "dataKind": "fixture",
            "reviewedAt": None,
            "sources": [],
            "cards": [],
        }

        validate_guidance(empty_guidance)
        self.assertEqual(validate_evidence_ids(empty_guidance, []), [])
        with self.assertRaisesRegex(GuidanceDataError, "unregistered evidence id"):
            validate_evidence_ids(empty_guidance, ["fixture-missing"])

    def test_reviewed_static_requires_registered_source_evidence(self):
        reviewed_guidance = {
            "scenarioId": SCENARIO_ID,
            "dataKind": "reviewed_static",
            "reviewedAt": "2026-11-05",
            "sources": [
                {
                    "id": "source-01",
                    "title": "Verified source",
                    "url": "https://example.org/source",
                    "publishedAt": None,
                    "scope": "Applicable scope",
                }
            ],
            "cards": [
                {
                    "id": "card-01",
                    "title": "Verified card",
                    "reason": "Supported by the source.",
                    "caution": "Use only within the stated scope.",
                    "evidenceIds": ["source-01"],
                }
            ],
        }

        validate_guidance(reviewed_guidance)
        self.assertEqual(validate_evidence_ids(reviewed_guidance, ["source-01"]), ["source-01"])

        reviewed_guidance["cards"][0]["evidenceIds"] = ["source-missing"]
        with self.assertRaisesRegex(GuidanceDataError, "unregistered source id"):
            validate_guidance(reviewed_guidance)

    def test_fixture_cannot_attach_a_source_record_or_review_date(self):
        guidance = {
            "scenarioId": SCENARIO_ID,
            "dataKind": "fixture",
            "reviewedAt": "2026-11-05",
            "sources": [],
            "cards": [],
        }

        with self.assertRaisesRegex(GuidanceDataError, "must not claim a reviewedAt date"):
            validate_guidance(guidance)

        guidance["reviewedAt"] = None
        guidance["sources"] = [
            {
                "id": "fake-source",
                "title": "Fake source",
                "url": "https://example.org/fake",
                "publishedAt": None,
                "scope": "Not a real citation",
            }
        ]
        with self.assertRaisesRegex(GuidanceDataError, "must not claim an external URL"):
            validate_guidance(guidance)

    def test_json_guidance_service_adapts_data_to_shared_contract(self):
        import asyncio

        guidance = asyncio.run(JsonGuidanceService().get_guidance(SCENARIO_ID))

        self.assertEqual(guidance.data_kind, DataKind.FIXTURE)
        self.assertEqual(guidance.scenario_id, SCENARIO_ID)
        self.assertEqual(len(guidance.cards), 3)
        self.assertTrue(all(source.url is None for source in guidance.sources))

    def test_json_guidance_service_surfaces_unavailable_scenario(self):
        import asyncio

        with self.assertRaises(GuidanceUnavailableError):
            asyncio.run(JsonGuidanceService().get_guidance("unknown"))

    def test_guidance_rejects_more_than_three_cards(self):
        guidance = load_guidance()
        guidance["cards"] *= 2

        with self.assertRaisesRegex(GuidanceDataError, "at most 3 cards"):
            validate_guidance(guidance)

    def test_dates_must_use_iso_calendar_format(self):
        guidance = {
            "scenarioId": SCENARIO_ID,
            "dataKind": "reviewed_static",
            "reviewedAt": "20261105",
            "sources": [
                {
                    "id": "source-01",
                    "title": "Verified source",
                    "url": "https://example.org/source",
                    "publishedAt": None,
                    "scope": "Applicable scope",
                }
            ],
            "cards": [],
        }

        with self.assertRaisesRegex(GuidanceDataError, "ISO reviewedAt date"):
            validate_guidance(guidance)

    def test_invalid_source_url_is_rejected(self):
        guidance = {
            "scenarioId": SCENARIO_ID,
            "dataKind": "reviewed_static",
            "reviewedAt": "2026-11-05",
            "sources": [
                {
                    "id": "source-01",
                    "title": "Verified source",
                    "url": "https://user:password@example.org/source",
                    "publishedAt": None,
                    "scope": "Applicable scope",
                }
            ],
            "cards": [],
        }

        with self.assertRaisesRegex(GuidanceDataError, "absolute HTTP\\(S\\) URL"):
            validate_guidance(guidance)

    def test_evidence_validation_rejects_non_object_guidance(self):
        with self.assertRaisesRegex(GuidanceDataError, "guidance must be an object"):
            validate_evidence_ids(None, [])

    def test_loader_surfaces_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(GuidanceDataError, "unable to load guidance data"):
                load_guidance(path)


if __name__ == "__main__":
    unittest.main()
