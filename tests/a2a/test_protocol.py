"""Tests for A2A protocol message types and parsing."""

import pytest

from open_notebook.a2a.protocol import (
    A2AAgentCard,
    A2AAgentSkill,
    A2AArtifact,
    A2AMessage,
    A2APart,
    A2ARequest,
    A2AResponse,
    A2ATask,
    A2ATaskStatus,
    make_error,
    make_response,
    parse_request,
)


# ---------------------------------------------------------------------------
# A2APart
# ---------------------------------------------------------------------------


class TestA2APart:
    def test_text_part(self):
        p = A2APart(type="text", text="hello")
        d = p.to_dict()
        assert d["type"] == "text"
        assert d["text"] == "hello"
        assert "data" not in d

    def test_data_part(self):
        p = A2APart(type="data", data={"k": 1})
        d = p.to_dict()
        assert d["data"] == {"k": 1}
        assert "text" not in d

    def test_roundtrip(self):
        p = A2APart(type="text", text="hi", data=None)
        d = p.to_dict()
        p2 = A2APart.from_dict(d)
        assert p2.type == "text"
        assert p2.text == "hi"


# ---------------------------------------------------------------------------
# A2AMessage
# ---------------------------------------------------------------------------


class TestA2AMessage:
    def test_message_with_parts(self):
        msg = A2AMessage(role="user", parts=[A2APart(type="text", text="hi")])
        d = msg.to_dict()
        assert d["role"] == "user"
        assert len(d["parts"]) == 1

    def test_empty_message(self):
        msg = A2AMessage()
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["parts"] == []

    def test_roundtrip(self):
        msg = A2AMessage(role="agent", parts=[A2APart(type="text", text="ok")])
        d = msg.to_dict()
        msg2 = A2AMessage.from_dict(d)
        assert msg2.role == "agent"
        assert msg2.parts[0].text == "ok"


# ---------------------------------------------------------------------------
# A2ATaskStatus
# ---------------------------------------------------------------------------


class TestA2ATaskStatus:
    def test_default(self):
        s = A2ATaskStatus()
        assert s.state == "submitted"
        assert s.message is None

    def test_with_message(self):
        m = A2AMessage(role="agent", parts=[A2APart(type="text", text="done")])
        s = A2ATaskStatus(state="completed", message=m)
        d = s.to_dict()
        assert d["state"] == "completed"
        assert d["message"]["parts"][0]["text"] == "done"


# ---------------------------------------------------------------------------
# A2AArtifact
# ---------------------------------------------------------------------------


class TestA2AArtifact:
    def test_empty_artifact(self):
        a = A2AArtifact()
        assert a.parts == []

    def test_roundtrip(self):
        a = A2AArtifact(parts=[A2APart(type="data", data={"x": 1})])
        d = a.to_dict()
        a2 = A2AArtifact.from_dict(d)
        assert a2.parts[0].data == {"x": 1}


# ---------------------------------------------------------------------------
# A2ATask
# ---------------------------------------------------------------------------


class TestA2ATask:
    def test_auto_id(self):
        t = A2ATask()
        assert t.id  # non-empty UUID

    def test_to_dict_roundtrip(self):
        t = A2ATask(
            sessionId="sess1",
            status=A2ATaskStatus(state="completed"),
            artifacts=[A2AArtifact(parts=[A2APart(type="data", data={"v": 42})])],
        )
        d = t.to_dict()
        t2 = A2ATask.from_dict(d)
        assert t2.sessionId == "sess1"
        assert t2.status.state == "completed"
        assert t2.artifacts[0].parts[0].data["v"] == 42


# ---------------------------------------------------------------------------
# JSON-RPC parsing
# ---------------------------------------------------------------------------


class TestParseRequest:
    def test_valid_request(self):
        raw = {"jsonrpc": "2.0", "method": "tasks/send", "id": "1", "params": {"x": 1}}
        req = parse_request(raw)
        assert req.jsonrpc == "2.0"
        assert req.method == "tasks/send"
        assert req.id == "1"
        assert req.params == {"x": 1}

    def test_missing_jsonrpc(self):
        with pytest.raises(ValueError, match="jsonrpc"):
            parse_request({"method": "test", "id": "1"})

    def test_missing_method(self):
        with pytest.raises(ValueError, match="method"):
            parse_request({"jsonrpc": "2.0", "id": "1"})

    def test_missing_id(self):
        with pytest.raises(ValueError, match="id"):
            parse_request({"jsonrpc": "2.0", "method": "test"})

    def test_default_params(self):
        req = parse_request({"jsonrpc": "2.0", "method": "test", "id": "42"})
        assert req.params == {}


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


class TestMakeResponse:
    def test_success(self):
        req = A2ARequest(method="test", id="1")
        resp = make_response(req, {"status": "ok"})
        d = resp.to_dict()
        assert d["jsonrpc"] == "2.0"
        assert d["id"] == "1"
        assert d["result"]["status"] == "ok"
        assert "error" not in d

    def test_error(self):
        req = A2ARequest(method="test", id="2")
        resp = make_error(req, -32600, "Bad request")
        d = resp.to_dict()
        assert d["error"]["code"] == -32600
        assert d["error"]["message"] == "Bad request"
        assert "result" not in d

    def test_error_with_data(self):
        req = A2ARequest(method="test", id="3")
        resp = make_error(req, -32600, "Bad", data={"detail": "x"})
        assert resp.to_dict()["error"]["data"] == {"detail": "x"}


# ---------------------------------------------------------------------------
# Agent Card types
# ---------------------------------------------------------------------------


class TestAgentSkill:
    def test_to_dict(self):
        s = A2AAgentSkill(id="q", name="Query", description="Search", tags=["search"])
        d = s.to_dict()
        assert d["id"] == "q"
        assert d["tags"] == ["search"]


class TestAgentCard:
    def test_to_dict(self):
        card = A2AAgentCard(
            name="Exo",
            description="test",
            url="http://localhost",
            capabilities={"streaming": True},
            skills=[A2AAgentSkill(id="q", name="Query")],
        )
        d = card.to_dict()
        assert d["name"] == "Exo"
        assert len(d["skills"]) == 1
