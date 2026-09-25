import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.agent_runner import _build_tools


class AgentToolConstructionTests(unittest.TestCase):
    def test_runtime_tools_are_not_registered_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = _build_tools("revenue-earnings-engine", root, root / "outputs")
            names = [tool.name for tool in tools]
            self.assertEqual(names.count("list_resources"), 1)
            self.assertEqual(names.count("read_resource"), 1)

    def test_financial_tools_are_present_when_companyfacts_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "companyfacts.json").write_text(
                json.dumps({
                    "cik": 1,
                    "entityName": "Example Corp",
                    "facts": {"us-gaap": {"Revenues": {"units": {"USD": [
                        {"fy": 2024, "fp": "FY", "form": "10-K", "end": "2024-12-31", "val": 100}
                    ]}}}}
                }),
                encoding="utf-8",
            )
            tools = _build_tools("revenue-earnings-engine", root, root / "outputs")
            names = [tool.name for tool in tools]
            self.assertIn("query_financial_facts", names)
            self.assertIn("query_financial_statement", names)


if __name__ == "__main__":
    unittest.main()
