"""
Tests for the A2A / I2I integration package.

Covers Bottle model creation/validation, CORTEXManifest loading,
VesselClient send/receive with temp directories, FastAPI router
endpoints via TestClient, and hook invocation patterns.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from open_notebook.a2a import (
    A2ACapability,
    Bottle,
    BottleEnvelope,
    BottleType,
    CORTEXManifest,
    VesselClient,
    after_ask,
    after_transformation,
    before_ask,
    before_transformation,
    setup_a2a_context,
)
from open_notebook.a2a.router import router as a2a_router


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def temp_vessel_dir() -> Generator[str, None, None]:
    """Create a temporary vessel directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["VESSEL_DIR"] = tmpdir
        yield tmpdir
        os.environ.pop("VESSEL_DIR", None)


@pytest.fixture
def vessel_client(temp_vessel_dir: str) -> VesselClient:
    """Return a VesselClient backed by a temp directory."""
    return VesselClient(vessel_dir=temp_vessel_dir)


@pytest.fixture
def sample_bottle() -> Bottle:
    """A basic task-type bottle for testing."""
    return Bottle(
        sender="test-agent",
        recipient="notebooklm",
        type="TASK",
        payload={"query": "What is the capital of France?"},
        context={"priority": "high"},
    )


@pytest.fixture
def sample_bottle_envelope(sample_bottle: Bottle) -> BottleEnvelope:
    """A BottleEnvelope wrapping sample_bottle."""
    return BottleEnvelope(
        bottle=sample_bottle,
        signature="test-sig-123",
        routing={"hop": 1, "ttl": 10},
    )


@pytest.fixture
def fastapi_app() -> FastAPI:
    """A FastAPI app with the A2A router mounted."""
    app = FastAPI()
    app.include_router(a2a_router)
    return app


@pytest.fixture
def client(fastapi_app: FastAPI) -> TestClient:
    """A FastAPI TestClient."""
    return TestClient(fastapi_app)


# ======================================================================
# Test: Bottle model creation and validation
# ======================================================================


class TestBottleModel:
    def test_create_minimal_bottle(self):
        """A bottle with just sender should work."""
        b = Bottle(sender="agent-a")
        assert b.sender == "agent-a"
        assert b.recipient == "broadcast"
        assert b.type == BottleType.TASK
        assert isinstance(b.id, str)
        assert b.id.startswith("bottle-")
        assert isinstance(b.timestamp, datetime)

    def test_create_full_bottle(self):
        """A bottle with all fields."""
        b = Bottle(
            id="custom-id",
            sender="agent-a",
            recipient="agent-b",
            type="CHECKPOINT",
            payload={"step": 3},
            context={"env": "prod"},
        )
        assert b.id == "custom-id"
        assert b.sender == "agent-a"
        assert b.recipient == "agent-b"
        assert b.type == BottleType.CHECKPOINT
        assert b.payload == {"step": 3}

    def test_bottle_serialization(self):
        """Bottle should serialize to JSON cleanly."""
        b = Bottle(sender="agent-a")
        data = b.model_dump(mode="json")
        assert data["sender"] == "agent-a"
        assert data["type"] == "TASK"
        assert isinstance(data["timestamp"], str)
        assert "T" in data["timestamp"]  # ISO-8601

    def test_bottle_deserialization(self):
        """Bottle should deserialize from a dict."""
        data = {
            "id": "bottle-test123",
            "sender": "agent-x",
            "recipient": "agent-y",
            "type": "DELIVERABLE",
            "payload": {"result": "done"},
            "timestamp": "2026-06-07T00:00:00+00:00",
        }
        b = Bottle.model_validate(data)
        assert b.id == "bottle-test123"
        assert b.sender == "agent-x"
        assert b.type == BottleType.DELIVERABLE
        assert b.payload["result"] == "done"

    def test_bottle_envelope(self, sample_bottle: Bottle):
        """BottleEnvelope wraps a bottle with signature and routing."""
        env = BottleEnvelope(
            bottle=sample_bottle,
            signature="abc123",
            routing={"hops": 0},
        )
        assert env.bottle.id == sample_bottle.id
        assert env.signature == "abc123"
        assert env.routing["hops"] == 0
        data = env.model_dump(mode="json")
        assert data["bottle"]["sender"] == "test-agent"
        assert data["signature"] == "abc123"

    def test_bottle_type_enum_values(self):
        """All bottle types should have correct string values."""
        assert BottleType.TASK.value == "TASK"
        assert BottleType.STATUS.value == "STATUS"
        assert BottleType.CHECKPOINT.value == "CHECKPOINT"
        assert BottleType.BLOCKER.value == "BLOCKER"
        assert BottleType.DELIVERABLE.value == "DELIVERABLE"
        assert BottleType.BOTTLE.value == "BOTTLE"
        assert BottleType.ACK.value == "ACK"
        assert BottleType.SYNTHESIS.value == "SYNTHESIS"
        assert BottleType.CHALLENGE.value == "CHALLENGE"
        assert BottleType.SESSION.value == "SESSION"


# ======================================================================
# Test: CORTEXManifest loading
# ======================================================================


class TestCORTEXManifest:
    def test_default_manifest(self):
        """CORTEXManifest should have sensible defaults."""
        m = CORTEXManifest()
        assert m.api_version == "v1"
        assert m.identity == {}
        assert m.capabilities == []
        assert m.endpoints == {}

    def test_manifest_from_dict(self):
        """CORTEXManifest should load from a dict."""
        data = {
            "api_version": "v1",
            "identity": {"name": "test-agent", "version": "1.0"},
            "capabilities": [
                {"name": "ping", "version": "1.0", "description": "Ping pong"}
            ],
            "endpoints": {"ping": "/api/ping"},
        }
        m = CORTEXManifest.model_validate(data)
        assert m.identity["name"] == "test-agent"
        assert len(m.capabilities) == 1
        assert m.capabilities[0].name == "ping"
        assert m.endpoints["ping"] == "/api/ping"

    def test_manifest_from_json_file(self, temp_vessel_dir: str):
        """CORTEXManifest should load from a JSON file."""
        manifest_path = Path(temp_vessel_dir) / "cortex.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "api_version": "v1",
                    "identity": {
                        "name": "file-agent",
                        "version": "2.0",
                    },
                    "capabilities": [],
                    "endpoints": {},
                }
            )
        )
        data = json.loads(manifest_path.read_text())
        m = CORTEXManifest.model_validate(data)
        assert m.identity["name"] == "file-agent"
        assert m.api_version == "v1"

    def test_a2a_capability_model(self):
        """A2ACapability should handle input/output schemas."""
        cap = A2ACapability(
            name="research",
            version="2.0",
            description="Deep research",
            input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        )
        assert cap.name == "research"
        assert cap.input_schema["properties"]["topic"]["type"] == "string"
        data = cap.model_dump(mode="json")
        assert data["input_schema"]["properties"]["topic"]["type"] == "string"

    def test_manifest_from_disk_cortex_json(self):
        """Load the actual CORTEX.json from project root."""
        cortex_path = (
            Path(__file__).parent.parent / "CORTEX.json"
        )
        if cortex_path.exists():
            data = json.loads(cortex_path.read_text())
            m = CORTEXManifest.model_validate(data)
            assert m.identity["name"] == "a2a-native-notebooklm"
            assert len(m.capabilities) >= 5
            assert "research" in [c.name for c in m.capabilities]
            assert "/.well-known/cortex.json" in m.endpoints.get("cortex", "")


# ======================================================================
# Test: VesselClient send/receive
# ======================================================================


class TestVesselClient:
    def test_vessel_creates_dirs(self, temp_vessel_dir: str):
        """VesselClient should create incoming/outgoing dirs."""
        client = VesselClient(vessel_dir=temp_vessel_dir)
        assert (Path(temp_vessel_dir) / "incoming").exists()
        assert (Path(temp_vessel_dir) / "outgoing").exists()

    def test_send_bottle(self, vessel_client: VesselClient, sample_bottle: Bottle):
        """send_bottle should write a JSON file to outgoing."""
        result = vessel_client.send_bottle(sample_bottle)
        assert result is True

        out_dir = vessel_client._outgoing_dir()
        files = list(out_dir.iterdir())
        assert len(files) == 1
        data = json.loads(files[0].read_text())
        assert data["bottle"]["id"] == sample_bottle.id
        assert data["bottle"]["sender"] == "test-agent"

    def test_check_vessel_empty(self, vessel_client: VesselClient):
        """check_vessel should return empty list when no bottles."""
        envelopes = vessel_client.check_vessel()
        assert envelopes == []

    def test_check_vessel_with_bottles(
        self, vessel_client: VesselClient, sample_bottle: Bottle
    ):
        """check_vessel should return bottles from incoming dir."""
        # Manually place a bottle in incoming
        in_dir = vessel_client._incoming_dir()
        env = BottleEnvelope(bottle=sample_bottle)
        bottle_file = in_dir / f"TASK_{sample_bottle.id}.json"
        bottle_file.write_text(env.model_dump_json(indent=2))

        envelopes = vessel_client.check_vessel()
        assert len(envelopes) == 1
        assert envelopes[0].bottle.id == sample_bottle.id
        assert envelopes[0].bottle.sender == "test-agent"

    def test_mark_processed(
        self, vessel_client: VesselClient, sample_bottle: Bottle
    ):
        """mark_processed should remove the bottle file."""
        in_dir = vessel_client._incoming_dir()
        env = BottleEnvelope(bottle=sample_bottle)
        bottle_file = in_dir / f"TASK_{sample_bottle.id}.json"
        bottle_file.write_text(env.model_dump_json(indent=2))

        envelopes = vessel_client.check_vessel()
        assert len(envelopes) == 1

        vessel_client.mark_processed(envelopes[0])
        assert not bottle_file.exists()

    def test_send_and_check_roundtrip(
        self, vessel_client: VesselClient, sample_bottle: Bottle
    ):
        """Full round-trip: write to outgoing, move to incoming (simulated), read back."""
        # The vessel client writes to outgoing; in real usage, another agent
        # would pick it up and place it in our incoming. We simulate that.
        vessel_client.send_bottle(sample_bottle)
        out_dir = vessel_client._outgoing_dir()

        # Move the outgoing bottle to incoming
        for f in out_dir.iterdir():
            dest = vessel_client._incoming_dir() / f.name
            f.rename(dest)

        envelopes = vessel_client.check_vessel()
        assert len(envelopes) == 1
        assert envelopes[0].bottle.id == sample_bottle.id

    def test_process_bottle_task(self, vessel_client: VesselClient):
        """process_bottle should ACK a TASK bottle."""
        bottle = Bottle(sender="agent-a", recipient="notebooklm", type="TASK")
        reply = vessel_client.process_bottle(bottle, reply_vessel=vessel_client)
        assert reply is not None
        assert reply.type == BottleType.ACK
        assert reply.payload["original_bottle_id"] == bottle.id

    def test_process_bottle_ack(self, vessel_client: VesselClient):
        """process_bottle should return None for ACK bottles."""
        bottle = Bottle(sender="agent-a", recipient="agent-b", type="ACK")
        reply = vessel_client.process_bottle(bottle)
        assert reply is None

    def test_process_bottle_unknown(self, vessel_client: VesselClient):
        """process_bottle should CHALLENGE unknown types."""
        bottle = Bottle(sender="x", recipient="y", type="BOTTLE")
        reply = vessel_client.process_bottle(bottle, reply_vessel=vessel_client)
        assert reply is not None
        assert reply.type == BottleType.CHALLENGE
        assert "Unrecognized" in reply.payload["message"]

    @pytest.mark.asyncio
    async def test_discover_cortex_success(self):
        """discover_cortex should return manifest on 200."""
        manifest_data = {
            "api_version": "v1",
            "identity": {"name": "remote-agent", "version": "1.0"},
            "capabilities": [{"name": "ping", "version": "1.0", "description": "Ping"}],
            "endpoints": {"ping": "/api/ping"},
        }

        client = VesselClient()
        with patch.object(client, "_get_http_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = manifest_data
            mock_http.get.return_value = mock_response
            mock_get.return_value = mock_http

            manifest = await client.discover_cortex("http://localhost:8000")
            assert manifest is not None
            assert manifest.identity["name"] == "remote-agent"
            assert len(manifest.capabilities) == 1

    @pytest.mark.asyncio
    async def test_discover_cortex_failure(self):
        """discover_cortex should return None on HTTP error."""
        import httpx
        client = VesselClient()
        with patch.object(client, "_get_http_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get.side_effect = httpx.ConnectError("Connection refused")
            mock_get.return_value = mock_http

            manifest = await client.discover_cortex("http://localhost:1")
            assert manifest is None

    @pytest.mark.asyncio
    async def test_send_bottle_remote(self, sample_bottle: Bottle):
        """send_bottle_remote should POST to target URL."""
        client = VesselClient()
        with patch.object(client, "_get_http_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_http.post.return_value = mock_response
            mock_get.return_value = mock_http

            result = await client.send_bottle_remote(
                sample_bottle, "http://localhost:8000/api/v1/a2a/bottle"
            )
            assert result is True


# ======================================================================
# Test: Router endpoints
# ======================================================================


class TestRouter:
    def test_get_capabilities(self, client: TestClient):
        """GET /api/v1/a2a/capabilities should return the manifest."""
        resp = client.get("/api/v1/a2a/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_version"] == "v1"
        assert "identity" in data
        assert "capabilities" in data
        assert len(data["capabilities"]) >= 5

    def test_cortex_discovery(self, client: TestClient):
        """GET /.well-known/cortex.json should return the CORTEX manifest."""
        resp = client.get("/.well-known/cortex.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_version"] == "v1"
        assert data["identity"]["name"] == "a2a-native-notebooklm"
        assert "bottle" in data["endpoints"]

    def test_receive_bottle(self, client: TestClient):
        """POST /api/v1/a2a/bottle should accept a valid envelope."""
        envelope = {
            "bottle": {
                "sender": "test-agent",
                "recipient": "notebooklm",
                "type": "TASK",
                "payload": {"query": "Test question?"},
            }
        }
        resp = client.post("/api/v1/a2a/bottle", json=envelope)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "bottle_id" in data
        assert data["bottle_id"].startswith("bottle-")

    def test_receive_bottle_invalid(self, client: TestClient):
        """POST /api/v1/a2a/bottle with invalid body should 422."""
        resp = client.post("/api/v1/a2a/bottle", json={"bad": "data"})
        assert resp.status_code == 422

    def test_list_bottles_empty(self, client: TestClient):
        """GET /api/v1/a2a/bottles should return empty list initially."""
        resp = client.get("/api/v1/a2a/bottles")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_bottles_after_receive(self, fastapi_app: FastAPI):
        """GET /api/v1/a2a/bottles should list received bottles."""
        from fastapi.testclient import TestClient
        client = TestClient(fastapi_app)

        envelope = {
            "bottle": {
                "sender": "test-agent",
                "recipient": "notebooklm",
                "type": "TASK",
                "payload": {"query": "Hello"},
            }
        }
        client.post("/api/v1/a2a/bottle", json=envelope)

        resp = client.get(
            "/api/v1/a2a/bottles",
            params={"limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        senders = [d["bottle"]["sender"] for d in data]
        assert "test-agent" in senders

    def test_list_bottles_with_limit(self, fastapi_app: FastAPI):
        """GET /api/v1/a2a/bottles should respect limit param."""
        from fastapi.testclient import TestClient
        client = TestClient(fastapi_app)

        for i in range(3):
            env = {
                "bottle": {
                    "sender": f"agent-{i}",
                    "recipient": "notebooklm",
                    "type": "TASK",
                    "payload": {"query": f"Q{i}"},
                }
            }
            client.post("/api/v1/a2a/bottle", json=env)

        resp = client.get("/api/v1/a2a/bottles", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 2

    def test_cors_headers_on_cortex(self, client: TestClient):
        """cortex discovery endpoint should have CORS headers."""
        resp = client.get("/.well-known/cortex.json")
        assert resp.headers.get("access-control-allow-origin") == "*"


# ======================================================================
# Test: Hook invocation patterns
# ======================================================================


class TestHooks:
    @pytest.mark.asyncio
    async def test_before_ask_no_a2a_context(self):
        """before_ask should be a no-op without a2a_context."""
        state = {"question": "What is Python?"}
        result = await before_ask(state, a2a_context=None)
        assert result == state

    @pytest.mark.asyncio
    async def test_before_ask_with_pending_task(self):
        """before_ask should inject bottle question into state."""
        a2a_context = {
            "pending_task": {
                "id": "bottle-abc",
                "origin": "agent-x",
                "query": "What is the capital of France?",
            }
        }
        state = {"question": "Default question"}
        result = await before_ask(state, a2a_context=a2a_context)
        assert "[A2A Bottle Request]" in result["question"]
        assert "capital of France" in result["question"]
        assert result["_a2a_bottle_id"] == "bottle-abc"
        assert result["_a2a_origin"] == "agent-x"

    @pytest.mark.asyncio
    async def test_before_ask_no_pending_task(self):
        """before_ask should be a no-op if no pending task."""
        a2a_context = {"pending_task": None}
        state = {"question": "Hello"}
        result = await before_ask(state, a2a_context=a2a_context)
        assert result["question"] == "Hello"

    @pytest.mark.asyncio
    async def test_after_ask_no_bottle_id(self):
        """after_ask should be a no-op without bottle id."""
        state = {"final_answer": "Paris"}
        result = await after_ask(state, a2a_context={"emit_result": AsyncMock()})
        assert result == state

    @pytest.mark.asyncio
    async def test_after_ask_with_result(self):
        """after_ask should call emit_result when bottle id present."""
        emit_fn = AsyncMock()
        a2a_context = {"emit_result": emit_fn}
        state = {
            "_a2a_bottle_id": "bottle-abc",
            "_a2a_origin": "notebooklm",
            "final_answer": "Paris is the capital of France.",
        }
        result = await after_ask(state, a2a_context=a2a_context)
        emit_fn.assert_awaited_once_with(
            bottle_id="bottle-abc",
            result="Paris is the capital of France.",
            origin="notebooklm",
        )

    @pytest.mark.asyncio
    async def test_before_transformation_with_content(self):
        """before_transformation should inject bottle content."""
        a2a_context = {
            "pending_task": {
                "id": "bottle-xyz",
                "origin": "agent-y",
                "content": "Article about AI",
            }
        }
        state = {"input_text": "", "transformation": MagicMock()}
        state["transformation"].prompt = "Default prompt"
        result = await before_transformation(state, a2a_context=a2a_context)
        assert result["input_text"] == "Article about AI"
        assert result["_a2a_bottle_id"] == "bottle-xyz"

    @pytest.mark.asyncio
    async def test_before_transformation_no_context(self):
        """before_transformation should be a no-op without a2a_context."""
        state = {"input_text": "test"}
        result = await before_transformation(state, a2a_context=None)
        assert result["input_text"] == "test"

    @pytest.mark.asyncio
    async def test_after_transformation_with_result(self):
        """after_transformation should emit result for transformation."""
        emit_fn = AsyncMock()
        a2a_context = {"emit_result": emit_fn}
        state = {
            "_a2a_bottle_id": "bottle-123",
            "_a2a_origin": "notebooklm",
            "output": "Transformed output",
        }
        result = await after_transformation(state, a2a_context=a2a_context)
        emit_fn.assert_awaited_once_with(
            bottle_id="bottle-123",
            result="Transformed output",
            origin="notebooklm",
        )

    @pytest.mark.asyncio
    async def test_after_transformation_no_output(self):
        """after_transformation should skip emit if output is empty."""
        emit_fn = AsyncMock()
        state = {
            "_a2a_bottle_id": "bottle-123",
            "output": "",
        }
        result = await after_transformation(state, a2a_context={"emit_result": emit_fn})
        assert result == state
        emit_fn.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_setup_a2a_context_empty(self, temp_vessel_dir: str):
        """setup_a2a_context should return empty context with no bottles."""
        ctx = await setup_a2a_context(notebook_id="test-notebook")
        assert "pending_task" in ctx
        assert "emit_result" in ctx
        # No bottles in vessel, so no pending task
        assert ctx["pending_task"] is None

    @pytest.mark.asyncio
    async def test_setup_a2a_context_with_bottle(self, temp_vessel_dir: str):
        """setup_a2a_context should find pending tasks in vessel."""
        # Place a TASK bottle in incoming
        client = VesselClient(vessel_dir=temp_vessel_dir)
        task_bottle = Bottle(
            sender="remote-agent",
            recipient="test-notebook",
            type="TASK",
            payload={"query": "What's the weather?"},
        )
        # Write directly to incoming
        env = BottleEnvelope(bottle=task_bottle)
        in_file = client._incoming_dir() / f"TASK_{task_bottle.id}.json"
        in_file.write_text(env.model_dump_json(indent=2))

        ctx = await setup_a2a_context(notebook_id="test-notebook")
        assert ctx["pending_task"] is not None
        assert ctx["pending_task"]["id"] == task_bottle.id
        assert ctx["pending_task"]["origin"] == "remote-agent"
        assert ctx["pending_task"]["query"] == "What's the weather?"

    @pytest.mark.asyncio
    async def test_setup_a2a_context_emit_result(self, temp_vessel_dir: str):
        """emit_result from setup_a2a_context should write a deliverable bottle."""
        # Place a TASK bottle
        client = VesselClient(vessel_dir=temp_vessel_dir)
        task_bottle = Bottle(
            sender="remote",
            recipient="test-nb",
            type="TASK",
            payload={"query": "Test"},
        )
        env = BottleEnvelope(bottle=task_bottle)
        in_file = client._incoming_dir() / f"TASK_{task_bottle.id}.json"
        in_file.write_text(env.model_dump_json(indent=2))

        ctx = await setup_a2a_context(notebook_id="test-nb")
        emit = ctx["emit_result"]
        assert callable(emit)

        # Call emit
        await emit(bottle_id=task_bottle.id, result="Test result", origin="notebooklm")

        # Check outgoing for deliverable
        out_files = list(client._outgoing_dir().iterdir())
        assert len(out_files) >= 1
        data = json.loads(out_files[0].read_text())
        assert data["bottle"]["type"] == "DELIVERABLE"
        assert data["bottle"]["payload"]["result"] == "Test result"
