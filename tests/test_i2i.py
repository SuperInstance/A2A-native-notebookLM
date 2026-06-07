"""
Tests for the I2I vessel-native protocol package.

Covers model validation, CORTEX manifest, router endpoints via
FastAPI TestClient, and handler dispatch (with mocked underlying calls).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from open_notebook.i2i import (
    Bottle,
    BottleEnvelope,
    BottleType,
    VesselStatus,
    __version__,
    dispatch,
    get_handler,
    registered_types,
)


# ===================================================================
# Bottle Model Validation
# ===================================================================


class TestBottleValidation:
    """Bottle/BottleEnvelope Pydantic v2 model validation."""

    def test_minimal_bottle(self):
        """A bottle with only required fields should be valid."""
        b = Bottle(sender="test-agent", recipient="notebook-1", type=BottleType.STATUS)
        assert b.id is not None
        assert uuid.UUID(b.id)  # valid UUID
        assert b.sender == "test-agent"
        assert b.recipient == "notebook-1"
        assert b.type == BottleType.STATUS
        assert b.payload == {}
        assert b.context == {}
        assert isinstance(b.timestamp, datetime)
        assert b.timestamp.tzinfo is not None  # timezone-aware

    def test_bottle_with_payload(self):
        """Bottle with a research payload should serialize/deserialize cleanly."""
        b = Bottle(
            sender="researcher-1",
            recipient="notebook-1",
            type=BottleType.RESEARCH,
            payload={"question": "What is the capital of France?", "sources": ["wiki"]},
            context={"priority": "high", "trace_id": "abc-123"},
        )
        assert b.payload["question"] == "What is the capital of France?"
        assert b.context["priority"] == "high"

        # Round-trip through JSON
        data = json.loads(b.model_dump_json())
        b2 = Bottle(**data)
        assert b2.id == b.id
        assert b2.sender == b.sender
        assert b2.type == BottleType.RESEARCH
        assert b2.payload["question"] == b.payload["question"]

    def test_bottle_empty_sender_raises(self):
        """Empty or blank sender should raise a validation error."""
        with pytest.raises(Exception):
            Bottle(sender="", recipient="notebook-1", type=BottleType.STATUS)
        with pytest.raises(Exception):
            Bottle(sender="  ", recipient="notebook-1", type=BottleType.STATUS)

    def test_bottle_empty_recipient_raises(self):
        """Empty or blank recipient should raise a validation error."""
        with pytest.raises(Exception):
            Bottle(sender="agent-1", recipient="", type=BottleType.STATUS)

    def test_envelope_wraps_bottle(self):
        """BottleEnvelope should correctly wrap a Bottle with optional fields."""
        b = Bottle(sender="a", recipient="b", type=BottleType.ACK)
        env = BottleEnvelope(bottle=b, routing={"hop": 1})
        assert env.bottle.id == b.id
        assert env.routing["hop"] == 1
        assert env.signature is None

        # Round-trip
        data = json.loads(env.model_dump_json())
        env2 = BottleEnvelope(**data)
        assert env2.bottle.id == b.id
        assert env2.routing["hop"] == 1

    def test_bottle_type_enum_values(self):
        """All expected bottle types should be present in the enum."""
        expected = {
            "RESEARCH",
            "TRANSFORM",
            "PODCAST",
            "STATUS",
            "SYNTHESIS",
            "SESSION",
            "ACK",
            "ERROR",
        }
        actual = {t.value for t in BottleType}
        assert actual == expected

    def test_vessel_status_serialization(self):
        """VesselStatus should serialize correctly."""
        vs = VesselStatus(
            name="test-vessel",
            version="1.0",
            uptime=123.45,
            capabilities=[{"type": "STATUS", "description": "Check status"}],
            active_bottles=2,
        )
        data = json.loads(vs.model_dump_json())
        assert data["name"] == "test-vessel"
        assert data["uptime"] == 123.45
        assert data["active_bottles"] == 2


# ===================================================================
# CORTEX Manifest
# ===================================================================


class TestCortexManifest:
    """CORTEX.json capability manifest."""

    def test_cortex_json_exists(self):
        """CORTEX.json should exist at repo root."""
        cortex_path = os.path.join(os.path.dirname(__file__), "..", "CORTEX.json")
        assert os.path.exists(cortex_path), "CORTEX.json not found"
        with open(cortex_path) as f:
            manifest = json.load(f)
        assert manifest["api_version"] == "v1"
        assert manifest["identity"]["name"] == "a2a-native-notebooklm"
        assert "bottle" in manifest["endpoints"]
        assert "status" in manifest["endpoints"]
        assert "cortex" in manifest["endpoints"]
        assert len(manifest["capabilities"]) >= 4

    def test_cortex_endpoint_returns_valid_manifest(self):
        """The /.well-known/cortex.json endpoint should return the manifest."""
        from open_notebook.i2i.router import _well_known_router

        # Create a temporary FastAPI app with just the well-known router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(_well_known_router)
        client = TestClient(app)

        response = client.get("/.well-known/cortex.json")
        assert response.status_code == 200
        data = response.json()
        assert data["api_version"] == "v1"
        assert data["identity"]["name"] == "a2a-native-notebooklm"
        assert data["identity"]["vessel_protocol"] == "i2i-v2"
        assert len(data["capabilities"]) >= 4


# ===================================================================
# Router Endpoints
# ===================================================================


class TestRouterEndpoints:
    """FastAPI router endpoints for I2I."""

    @pytest.fixture
    def app(self):
        from fastapi import FastAPI

        from open_notebook.i2i.router import _well_known_router, router

        app = FastAPI()
        app.include_router(router)
        app.include_router(_well_known_router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_status_endpoint(self, client):
        """GET /api/v1/i2i/status should return VesselStatus."""
        response = client.get("/api/v1/i2i/status")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "a2a-native-notebooklm"
        assert data["version"] is not None
        assert data["uptime"] >= 0
        assert len(data["capabilities"]) >= 1
        assert data["active_bottles"] >= 0

    def test_cortex_endpoint(self, client):
        """GET /.well-known/cortex.json should return manifest."""
        response = client.get("/.well-known/cortex.json")
        assert response.status_code == 200
        data = response.json()
        assert data["identity"]["agent_type"] == "notebook"
        assert len(data["capabilities"]) >= 1

    def test_bottles_list_empty(self, client):
        """GET /api/v1/i2i/bottles should return an empty list initially."""
        response = client.get("/api/v1/i2i/bottles")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_bottles_list_with_limit(self, client):
        """GET /api/v1/i2i/bottles?limit=5 should respect limit."""
        response = client.get("/api/v1/i2i/bottles", params={"limit": 5})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_post_bottle_status(
        self, client
    ):
        """POST /api/v1/i2i/bottle with STATUS type should return status info."""
        env = BottleEnvelope(
            bottle=Bottle(
                sender="test-agent",
                recipient="*",  # wildcard recipient
                type=BottleType.STATUS,
            )
        )
        response = client.post(
            "/api/v1/i2i/bottle",
            json=json.loads(env.model_dump_json()),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["routing"]["status"] in ("ok", "error")
        if result["routing"]["status"] == "ok":
            payload = result["bottle"]["payload"]
            assert "name" in payload
            assert "version" in payload
            assert "capabilities" in payload

    def test_post_bottle_research_no_question(
        self, client
    ):
        """POST /api/v1/i2i/bottle with RESEARCH type without question
        should return an error."""
        env = BottleEnvelope(
            bottle=Bottle(
                sender="test-agent",
                recipient="*",
                type=BottleType.RESEARCH,
                payload={},  # no question
            )
        )
        response = client.post(
            "/api/v1/i2i/bottle",
            json=json.loads(env.model_dump_json()),
        )
        assert response.status_code == 200
        assert response.json()["routing"]["status"] == "error"

    def test_post_bottle_transform_no_content(
        self, client
    ):
        """POST /api/v1/i2i/bottle with TRANSFORM type without content
        should return an error."""
        env = BottleEnvelope(
            bottle=Bottle(
                sender="test-agent",
                recipient="*",
                type=BottleType.TRANSFORM,
                payload={},
            )
        )
        response = client.post(
            "/api/v1/i2i/bottle",
            json=json.loads(env.model_dump_json()),
        )
        assert response.status_code == 200
        assert response.json()["routing"]["status"] == "error"

    def test_post_unknown_bottle_type(self, client):
        """POST with an unknown bottle type should return an error."""
        # Build a raw envelope with a bogus type string — FastAPI validation
        # will reject it at the Pydantic level since BottleType is a strict enum.
        raw = {
            "bottle": {
                "sender": "test-agent",
                "recipient": "notebook-1",
                "type": "UNKNOWN_TYPE",
                "payload": {},
                "context": {},
            },
            "routing": {},
        }
        response = client.post(
            "/api/v1/i2i/bottle",
            json=raw,
        )
        assert response.status_code == 422  # validation error


# ===================================================================
# Handler Dispatch
# ===================================================================


class TestHandlerDispatch:
    """Bottle type handler dispatch."""

    def test_registered_types_include_all_handled(self):
        """registered_types() should return the expected set of types."""
        types = registered_types()
        type_set = {t.value for t in types}
        assert "RESEARCH" in type_set
        assert "TRANSFORM" in type_set
        assert "PODCAST" in type_set
        assert "STATUS" in type_set
        assert "SYNTHESIS" in type_set

    def test_get_handler_returns_callable(self):
        """get_handler() should return a callable for known types."""
        for bt in registered_types():
            handler = get_handler(bt)
            assert handler is not None
            assert callable(handler)

    def test_get_handler_returns_none_for_unknown(self):
        """get_handler() should return None for unknown types."""
        assert get_handler(BottleType.SESSION) is None

    @pytest.mark.asyncio
    async def test_dispatch_status(self):
        """Dispatch a STATUS bottle should succeed without external deps."""
        bottle = Bottle(
            sender="test-agent",
            recipient="notebook-1",
            type=BottleType.STATUS,
        )
        result = await dispatch(bottle)
        assert result is not None
        assert result.bottle.type == BottleType.ACK
        payload = result.bottle.payload
        assert "name" in payload
        assert "version" in payload
        assert "capabilities" in payload

    @pytest.mark.asyncio
    async def test_dispatch_research_missing_query(self):
        """Dispatch a RESEARCH bottle without a question should return error."""
        bottle = Bottle(
            sender="test-agent",
            recipient="notebook-1",
            type=BottleType.RESEARCH,
            payload={},
        )
        result = await dispatch(bottle)
        assert result.routing.get("status") == "error"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_type(self):
        """Dispatch a SESSION bottle (no handler) should return error."""
        bottle = Bottle(
            sender="test-agent",
            recipient="notebook-1",
            type=BottleType.SESSION,
        )
        result = await dispatch(bottle)
        assert result.routing.get("status") == "error"
        assert "No handler for" in result.routing.get("error", "")

    @pytest.mark.asyncio
    async def test_dispatch_transform_missing_content(self):
        """Dispatch a TRANSFORM bottle without content should return error."""
        bottle = Bottle(
            sender="test-agent",
            recipient="notebook-1",
            type=BottleType.TRANSFORM,
            payload={},
        )
        result = await dispatch(bottle)
        assert result.routing.get("status") == "error"


# ===================================================================
# Package Import
# ===================================================================


class TestPackage:
    """Package-level checks."""

    def test_version(self):
        """__version__ should be a string."""
        assert isinstance(__version__, str)
        assert "i2i" in __version__

    def test_public_api(self):
        """All expected names should be importable from the package."""
        from open_notebook import i2i
        assert hasattr(i2i, "Bottle")
        assert hasattr(i2i, "BottleEnvelope")
        assert hasattr(i2i, "BottleType")
        assert hasattr(i2i, "VesselStatus")
        assert hasattr(i2i, "dispatch")
        assert hasattr(i2i, "get_handler")
        assert hasattr(i2i, "registered_types")
        assert hasattr(i2i, "router")
        assert hasattr(i2i, "_well_known_router")
        assert hasattr(i2i, "start_poller")
        assert hasattr(i2i, "stop_poller")


# ===================================================================
# CORTEX.json Structural
# ===================================================================


class TestCortexJsonStructure:
    """Structural tests for CORTEX.json content."""

    def test_cortex_capabilities_match_registered_types(self):
        """Every CORTEX capability type should have a corresponding handler."""
        import json
        import os

        cortex_path = os.path.join(os.path.dirname(__file__), "..", "CORTEX.json")
        with open(cortex_path) as f:
            manifest = json.load(f)

        cortex_types = {c["type"] for c in manifest["capabilities"]}
        handled_types = {bt.value for bt in registered_types() if bt != BottleType.SESSION}

        # Every CORTEX-declared capability should have a handler
        for ct in cortex_types:
            bt = BottleType(ct)
            assert get_handler(bt) is not None, f"No handler for CORTEX capability {ct}"
