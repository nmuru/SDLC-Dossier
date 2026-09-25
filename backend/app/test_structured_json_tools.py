from pathlib import Path
import json

from .structured_json_tools import _decode_pointer, _resolve, _preview_structure, _truncate_serialized


def test_json_pointer_resolves_nested_taxonomy():
    value = {"facts": {"us-gaap": {"Revenues": {"units": {"USD": [1, 2]}}}}}
    assert _resolve(value, "/facts/us-gaap/Revenues/units/USD") == [1, 2]


def test_structure_inspection_is_bounded():
    value = {"a": 1, "b": 2, "c": 3}
    result = _preview_structure(value, 2)
    assert result["key_count"] == 3
    assert result["truncated"] is True



def test_pointer_rejects_non_pointer_syntax():
    try:
        _decode_pointer("facts/us-gaap/Revenues")
    except ValueError as exc:
        assert "JSON Pointer" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_large_direct_read_is_bounded():
    text, truncated = _truncate_serialized({"values": ["x"] * 100}, 1000)
    assert truncated is True
    assert text.endswith("[truncated]")
