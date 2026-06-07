"""Tests for domain ↔ A2A payload converters."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from open_notebook.a2a.converters import (
    artifact_to_insight,
    batch_to_artifacts,
    chat_message_to_a2a,
    insight_to_artifact,
    notebook_to_artifact,
    note_to_artifact,
    source_to_artifact,
)
from open_notebook.a2a.protocol import A2AArtifact, A2APart


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_insight(**kw):
    defaults = dict(
        id="insight:1",
        insight_type="summary",
        content="Test insight content",
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _make_notebook(**kw):
    defaults = dict(
        id="notebook:1",
        name="Test NB",
        description="A test notebook",
        archived=False,
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _make_source(**kw):
    defaults = dict(
        id="source:1",
        title="Test Source",
        topics=["ml", "ai"],
        asset=None,
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _make_note(**kw):
    defaults = dict(
        id="note:1",
        title="Test Note",
        note_type="human",
        content="Some content",
        created=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# insight_to_artifact
# ---------------------------------------------------------------------------


class TestInsightToArtifact:
    def test_basic(self):
        ins = _make_insight()
        art = insight_to_artifact(ins)
        assert len(art.parts) == 1
        data = art.parts[0].data
        assert data["type"] == "summary"
        assert data["content"] == "Test insight content"

    def test_no_nulls(self):
        ins = _make_insight(updated=None)
        data = insight_to_artifact(ins).parts[0].data
        assert "updated" not in data

    def test_epoch_timestamps(self):
        ins = _make_insight()
        data = insight_to_artifact(ins).parts[0].data
        assert isinstance(data["created"], int)


# ---------------------------------------------------------------------------
# notebook_to_artifact
# ---------------------------------------------------------------------------


class TestNotebookToArtifact:
    def test_basic(self):
        nb = _make_notebook()
        data = notebook_to_artifact(nb).parts[0].data
        assert data["name"] == "Test NB"
        assert "desc" in data

    def test_strip_archived_false(self):
        nb = _make_notebook(archived=False)
        data = notebook_to_artifact(nb).parts[0].data
        assert data["archived"] is False


# ---------------------------------------------------------------------------
# source_to_artifact
# ---------------------------------------------------------------------------


class TestSourceToArtifact:
    def test_basic(self):
        src = _make_source()
        data = source_to_artifact(src).parts[0].data
        assert data["title"] == "Test Source"
        assert data["topics"] == ["ml", "ai"]

    def test_no_asset(self):
        src = _make_source(asset=None)
        data = source_to_artifact(src).parts[0].data
        assert "asset" not in data

    def test_with_asset(self):
        asset = SimpleNamespace(file_path="/tmp/f.txt", url=None)
        src = _make_source(asset=asset)
        data = source_to_artifact(src).parts[0].data
        assert data["asset"]["fp"] == "/tmp/f.txt"
        assert "url" not in data["asset"]


# ---------------------------------------------------------------------------
# note_to_artifact
# ---------------------------------------------------------------------------


class TestNoteToArtifact:
    def test_basic(self):
        note = _make_note()
        data = note_to_artifact(note).parts[0].data
        assert data["title"] == "Test Note"
        assert data["type"] == "human"

    def test_strip_null_updated(self):
        note = _make_note(updated=None)
        data = note_to_artifact(note).parts[0].data
        assert "updated" not in data


# ---------------------------------------------------------------------------
# chat_message_to_a2a
# ---------------------------------------------------------------------------


class TestChatMessageToA2A:
    def test_from_dict(self):
        msg = chat_message_to_a2a({"role": "user", "content": "hello"})
        assert msg.role == "user"
        assert msg.parts[0].text == "hello"

    def test_from_object(self):
        obj = SimpleNamespace(role="agent", content="world")
        msg = chat_message_to_a2a(obj)
        assert msg.role == "agent"
        assert msg.parts[0].text == "world"


# ---------------------------------------------------------------------------
# artifact_to_insight
# ---------------------------------------------------------------------------


class TestArtifactToInsight:
    def test_basic(self):
        art = A2AArtifact(parts=[A2APart(type="data", data={"insight_type": "summary", "content": "x"})])
        d = artifact_to_insight(art)
        assert d["insight_type"] == "summary"

    def test_no_data_part(self):
        art = A2AArtifact(parts=[A2APart(type="text", text="hello")])
        d = artifact_to_insight(art)
        assert d == {}


# ---------------------------------------------------------------------------
# batch_to_artifacts
# ---------------------------------------------------------------------------


class TestBatch:
    def test_batch(self):
        items = [_make_insight(id=f"i:{i}") for i in range(3)]
        arts = batch_to_artifacts(items, insight_to_artifact)
        assert len(arts) == 3

    def test_empty(self):
        assert batch_to_artifacts([], insight_to_artifact) == []
