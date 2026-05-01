import pytest
from backend.llm.gateway import JSONParseError, _extract_json


def test_extract_json_strip_fence():
    raw = '```json\n{"a": 1}\n```'
    assert _extract_json(raw) == {"a": 1}


def test_extract_invalid():
    with pytest.raises(JSONParseError):
        _extract_json("not json")
