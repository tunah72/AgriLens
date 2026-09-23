import json
from copy import deepcopy
from pathlib import Path

import pytest

from backend.app.knowledge import KnowledgeBase
from backend.app.knowledge.knowledge_base import REQUIRED_LABELS

ROOT_DIR = Path(__file__).resolve().parents[1]
CLASS_NAMES_PATH = ROOT_DIR / "models" / "class_names.json"
KNOWLEDGE_DB_PATH = ROOT_DIR / "backend" / "app" / "knowledge" / "diseases.json"


def _valid_payload():
    return json.loads(KNOWLEDGE_DB_PATH.read_text(encoding="utf-8"))


def _write_payload(tmp_path, payload):
    db_path = tmp_path / "diseases.json"
    db_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(db_path)


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def test_knowledge_base_labels_match_model_class_names():
    class_names = set(json.loads(CLASS_NAMES_PATH.read_text(encoding="utf-8")))
    knowledge_base = KnowledgeBase()

    labels = {item["label"] for item in knowledge_base.list_diseases()}

    assert labels == class_names


def test_knowledge_base_has_no_placeholder_text():
    knowledge_base = KnowledgeBase()
    all_diseases = [knowledge_base.get_disease_info(item["label"]) for item in knowledge_base.list_diseases()]

    for text in _walk_strings(all_diseases):
        assert "TODO" not in text.upper()


def test_get_disease_info_returns_full_known_disease():
    knowledge_base = KnowledgeBase()

    disease = knowledge_base.get_disease_info("BrownSpot")

    assert disease is not None
    assert disease["label"] == "BrownSpot"
    assert disease["crop"] == "rice"
    assert disease["name_vi"]
    assert disease["treatments"]
    assert disease["prevention"]
    assert disease["sources"]


def test_get_disease_info_returns_none_for_unknown_label():
    knowledge_base = KnowledgeBase()

    assert knowledge_base.get_disease_info("InvalidLabel") is None


def test_get_disease_info_returns_deep_copy():
    knowledge_base = KnowledgeBase()

    disease = knowledge_base.get_disease_info("BrownSpot")
    assert disease is not None
    disease["treatments"].append("mutated")

    fresh_disease = knowledge_base.get_disease_info("BrownSpot")
    assert fresh_disease is not None
    assert "mutated" not in fresh_disease["treatments"]


def test_format_recommendation_includes_low_confidence_warning():
    knowledge_base = KnowledgeBase()

    recommendation = knowledge_base.format_recommendation("LeafBlast", 0.55)

    assert recommendation["label"] == "LeafBlast"
    assert recommendation["confidence"] == 0.55
    assert "Low confidence" in recommendation["confidence_note"]
    assert recommendation["advisory"]


def test_format_recommendation_uses_regular_note_at_confidence_threshold():
    knowledge_base = KnowledgeBase()

    recommendation = knowledge_base.format_recommendation("LeafBlast", 0.6)

    assert recommendation["confidence"] == 0.6
    assert "Low confidence" not in recommendation["confidence_note"]


@pytest.mark.parametrize("confidence", [-0.01, 1.01, "0.8"])
def test_format_recommendation_rejects_invalid_confidence(confidence):
    knowledge_base = KnowledgeBase()

    with pytest.raises(ValueError, match="confidence"):
        knowledge_base.format_recommendation("LeafBlast", confidence)


@pytest.mark.parametrize(
    ("mutate_payload", "message"),
    [
        (lambda payload: payload.pop("diseases"), "diseases"),
        (lambda payload: payload["diseases"].pop("Healthy"), "missing labels"),
        (
            lambda payload: payload["diseases"].__setitem__("Unexpected", deepcopy(payload["diseases"]["Healthy"])),
            "unsupported labels",
        ),
        (lambda payload: payload["diseases"]["Healthy"].pop("sources"), "missing fields"),
        (lambda payload: payload["diseases"]["Healthy"].__setitem__("severity", "urgent"), "invalid severity"),
        (lambda payload: payload["diseases"]["Healthy"].__setitem__("treatments", []), "empty field"),
        (lambda payload: payload["diseases"]["Healthy"].__setitem__("description", "TODO"), "placeholder"),
        (lambda payload: payload["diseases"]["Healthy"].__setitem__("symptoms", "green"), "list of strings"),
        (
            lambda payload: payload["diseases"]["Healthy"].__setitem__(
                "sources", [{"title": "Broken", "url": "ftp://bad"}]
            ),
            "source URL",
        ),
    ],
)
def test_knowledge_base_rejects_invalid_database_payload(tmp_path, mutate_payload, message):
    payload = _valid_payload()
    mutate_payload(payload)

    with pytest.raises(ValueError, match=message):
        KnowledgeBase(_write_payload(tmp_path, payload))


def test_required_labels_stay_in_sync_with_model_class_names():
    class_names = set(json.loads(CLASS_NAMES_PATH.read_text(encoding="utf-8")))

    assert REQUIRED_LABELS == class_names


def test_format_recommendation_falls_back_for_unknown_label():
    knowledge_base = KnowledgeBase()

    recommendation = knowledge_base.format_recommendation("InvalidLabel", 0.8)

    assert recommendation["label"] == "InvalidLabel"
    assert recommendation["name_vi"] == "Chưa có dữ liệu khuyến nghị"
    assert recommendation["treatments"]
    assert recommendation["advisory"]
