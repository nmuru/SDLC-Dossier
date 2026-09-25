from pathlib import Path
import json

from .financial_tools import _concept_candidates, _annual


def _facts():
    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "label": "Revenue",
                    "units": {
                        "USD": [
                            {"fy": 2024, "fp": "FY", "form": "10-K", "frame": "CY2024", "end": "2024-12-31", "filed": "2025-02-25", "val": 1000},
                            {"fy": 2024, "fp": "Q3", "form": "10-Q", "end": "2024-09-30", "filed": "2024-10-30", "val": 900},
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "label": "Net income",
                    "units": {
                        "USD": [
                            {"fy": 2024, "fp": "FY", "form": "10-K", "frame": "CY2024", "end": "2024-12-31", "filed": "2025-02-25", "val": 100}
                        ]
                    }
                }
            }
        }
    }


def test_concept_lookup_accepts_qualified_and_bare_names():
    facts = _facts()
    assert _concept_candidates(facts, "us-gaap.Revenues")[0][0] == "us-gaap.Revenues"
    assert _concept_candidates(facts, "Revenues")[0][0] == "us-gaap.Revenues"
    assert _concept_candidates(facts, "US-GAAP.REVENUES")[0][0] == "us-gaap.Revenues"


def test_concept_lookup_does_not_false_negative_existing_concept():
    facts = _facts()
    candidates = _concept_candidates(facts, "us-gaap.NetIncomeLoss")
    assert len(candidates) == 1
    assert candidates[0][1]["label"] == "Net income"


def test_annual_filter_excludes_quarterly_rows():
    rows = _facts()["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    selected = _annual(rows, {2024}, "10-K", True)
    assert len(selected) == 1
    assert selected[0]["val"] == 1000
