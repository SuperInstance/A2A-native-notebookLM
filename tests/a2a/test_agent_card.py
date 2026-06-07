"""Tests for the Agent Card definition."""

import pytest

from open_notebook.a2a.agent_card import EXOCORTEX_AGENT_CARD, get_agent_card


class TestAgentCard:
    def test_card_exists(self):
        assert EXOCORTEX_AGENT_CARD.name == "Exocortex"

    def test_skills_count(self):
        assert len(EXOCORTEX_AGENT_CARD.skills) == 8

    def test_skill_ids(self):
        ids = {s.id for s in EXOCORTEX_AGENT_CARD.skills}
        assert ids == {"query", "embed", "train", "predict", "analyze", "remember", "recall", "transform"}

    def test_capabilities(self):
        assert EXOCORTEX_AGENT_CARD.capabilities["streaming"] is True

    def test_get_agent_card_dict(self):
        d = get_agent_card()
        assert d["name"] == "Exocortex"
        assert isinstance(d["skills"], list)
        assert len(d["skills"]) == 8

    def test_url(self):
        assert "localhost" in EXOCORTEX_AGENT_CARD.url

    def test_each_skill_has_name_and_description(self):
        for s in EXOCORTEX_AGENT_CARD.skills:
            assert s.name
            assert s.description
            assert isinstance(s.tags, list)
