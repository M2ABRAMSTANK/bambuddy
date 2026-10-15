"""Health reset and settings autosave behavior for AI bed checks."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def reset_health_registry():
    from backend.app.services import bedcheck_ai

    bedcheck_ai.reset_health_state()
    yield
    bedcheck_ai.reset_health_state()


class TestBedcheckAiHealthRoute:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_route_empty_before_any_check(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/bedcheck-ai/health")
        assert response.status_code == 200
        assert response.json() == {"printers": {}}

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_route_reflects_recorded_outcome(self, async_client: AsyncClient):
        """The route is a thin read of bedcheck_ai.get_health() -- populate the
        module-level registry directly (check_bed_ai()'s own recording is
        covered at the unit level in test_ai_bed_check.py) and confirm the
        route serializes it as-is."""
        from backend.app.services import bedcheck_ai

        bedcheck_ai._record_outcome(42, "degraded", None, "json_object")
        try:
            response = await async_client.get("/api/v1/bedcheck-ai/health")
            assert response.status_code == 200
            body = response.json()
            assert body["printers"]["42"]["outcome"] == "degraded"
            assert body["printers"]["42"]["request_mode"] == "json_object"
        finally:
            bedcheck_ai._last_outcome.pop(42, None)


class TestBedcheckAiSettingsWarmupHook:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_saving_bedcheck_ai_api_key_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        from backend.app.services import bedcheck_ai

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        response = await async_client.put("/api/v1/settings/", json={"bedcheck_ai_api_key": "new-key"})
        assert response.status_code == 200

        # The hook is fire-and-forget (asyncio.create_task) -- yield control
        # back to the loop so the scheduled task actually runs before we
        # assert on it.
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_saving_bedcheck_backend_ai_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        from backend.app.services import bedcheck_ai

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        response = await async_client.put("/api/v1/settings/", json={"bedcheck_backend": "ai"})
        assert response.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_saving_bedcheck_backend_opencv_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        """Switching TO opencv is not an AI-connection change -- must not fire."""
        from backend.app.services import bedcheck_ai

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        response = await async_client.put("/api/v1/settings/", json={"bedcheck_backend": "opencv"})
        assert response.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_saving_unrelated_setting_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        from backend.app.services import bedcheck_ai

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        response = await async_client.put("/api/v1/settings/", json={"auto_archive": True})
        assert response.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resaving_identical_values_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        """The settings UI auto-saves the whole bedcheck block on a debounce,
        so a key being *present* in the payload says nothing about whether it
        changed. Warming on presence alone fires a full vision-model request
        on every debounced save -- including the ones that change nothing."""
        from backend.app.services import bedcheck_ai

        payload = {
            "bedcheck_ai_base_url": "http://192.168.1.20:11434/v1",
            "bedcheck_ai_model": "qwen2.5vl:7b",
            "bedcheck_ai_api_key": "",
        }
        first = await async_client.put("/api/v1/settings/", json=payload)
        assert first.status_code == 200

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        second = await async_client.put("/api/v1/settings/", json=payload)
        assert second.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_changing_the_model_does_not_trigger_warmup(self, async_client: AsyncClient, monkeypatch):
        """Typing a model name must not send requests on autosave pauses."""
        from backend.app.services import bedcheck_ai

        await async_client.put("/api/v1/settings/", json={"bedcheck_ai_model": "qwen2.5vl:7b"})

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        response = await async_client.put("/api/v1/settings/", json={"bedcheck_ai_model": "llava:13b"})
        assert response.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.assert_not_awaited()


class TestBedcheckAiSettingsHealthReset:
    """Changing the connection settings points the check at a different
    backend, so the recorded outcomes describe something nobody is calling any
    more -- and the armed notification cooldown would swallow the NEW
    backend's first genuine failure for up to an hour."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_changing_base_url_clears_health_and_cooldown(self, async_client: AsyncClient, monkeypatch):
        from backend.app.services import bedcheck_ai

        monkeypatch.setattr(bedcheck_ai, "warmup", AsyncMock())
        bedcheck_ai._record_outcome(77, "unavailable", "connection failed", "json_schema")
        bedcheck_ai._last_unavailable_notified_at[77] = 1.0
        try:
            response = await async_client.put(
                "/api/v1/settings/", json={"bedcheck_ai_base_url": "http://192.168.1.99:11434/v1"}
            )
            assert response.status_code == 200
            assert bedcheck_ai.get_health() == {}
            assert bedcheck_ai._last_unavailable_notified_at == {}

            health = await async_client.get("/api/v1/bedcheck-ai/health")
            assert health.json() == {"printers": {}}
        finally:
            bedcheck_ai._last_outcome.pop(77, None)
            bedcheck_ai._last_unavailable_notified_at.pop(77, None)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_unrelated_setting_leaves_health_alone(self, async_client: AsyncClient):
        """Scoped to the bedcheck keys only -- every other setting in the app
        goes through this same endpoint."""
        from backend.app.services import bedcheck_ai

        bedcheck_ai._record_outcome(78, "ok", None, "json_schema")
        try:
            response = await async_client.put("/api/v1/settings/", json={"auto_archive": True})
            assert response.status_code == 200
            assert bedcheck_ai.get_health()[78]["outcome"] == "ok"
        finally:
            bedcheck_ai._last_outcome.pop(78, None)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_flipping_backend_from_ai_to_opencv_clears_health_without_warming(
        self, async_client: AsyncClient, monkeypatch
    ):
        """Item 5b: the reset above is gated on `bedcheck_ai_changed` (ANY of
        base_url/model/api_key/backend actually changing), not on
        `bedcheck_ai_warmup_needed` -- so switching the backend AWAY from
        'ai' must still drop the stale health entry even though there is
        correctly no reason to warm a vision model nobody is about to call."""
        from backend.app.services import bedcheck_ai

        warmup_mock = AsyncMock()
        monkeypatch.setattr(bedcheck_ai, "warmup", warmup_mock)

        # Establish backend='ai' as the stored value so the follow-up PUT to
        # 'opencv' below is a real transition, not a no-op re-save.
        first = await async_client.put("/api/v1/settings/", json={"bedcheck_backend": "ai"})
        assert first.status_code == 200
        for _ in range(5):
            await asyncio.sleep(0)
        warmup_mock.reset_mock()

        bedcheck_ai._record_outcome(81, "unavailable", "connection failed", "json_schema")
        bedcheck_ai._last_unavailable_notified_at[81] = 1.0
        try:
            response = await async_client.put("/api/v1/settings/", json={"bedcheck_backend": "opencv"})
            assert response.status_code == 200

            assert bedcheck_ai.get_health() == {}
            assert bedcheck_ai._last_unavailable_notified_at == {}

            for _ in range(5):
                await asyncio.sleep(0)
            warmup_mock.assert_not_awaited()
        finally:
            bedcheck_ai._last_outcome.pop(81, None)
            bedcheck_ai._last_unavailable_notified_at.pop(81, None)


@pytest.mark.asyncio
async def test_discovered_shape_survives_cache_loss(async_client, monkeypatch):
    import json

    import httpx
    from sqlalchemy import select

    from backend.app.models.settings import Settings
    from backend.app.services import bedcheck_ai

    bedcheck_ai._shape_cache.clear()
    url = "http://192.168.1.20:11434/v1"
    cfg = {"bedcheck_ai_base_url": url, "bedcheck_ai_model": "local-model", "bedcheck_ai_api_key": "secret"}
    assert (await async_client.put("/api/v1/settings/", json=cfg)).status_code == 200
    shapes = []

    async def post(base_url, model, api_key, messages, timeout, shape):
        shapes.append(dict(shape))
        if shape["token_param"] == "max_tokens" or shape["response_mode"] == "json_schema":
            param = "max_tokens" if shape["token_param"] == "max_tokens" else "response_format"
            request = httpx.Request("POST", url + "/chat/completions")
            response = httpx.Response(400, request=request, json={"error": {"param": param}})
            raise httpx.HTTPStatusError("unsupported", request=request, response=response)
        return json.dumps({"is_empty": True, "confidence": 0.9, "reason": "bare"})

    monkeypatch.setattr(bedcheck_ai, "_post_chat", post)
    try:
        response = await async_client.post(
            "/api/v1/bedcheck-ai/test-connection", json={"base_url": url + "/", "model": " local-model "}
        )
        assert response.json()["ok"] is True
        assert len(shapes) == 3
        async with bedcheck_ai.async_session() as db:
            rows = (await db.execute(select(Settings).where(Settings.key.like("bedcheck_ai_shape_%")))).scalars().all()
            assert len(rows) == 1
            assert "secret" not in rows[0].key + rows[0].value

        bedcheck_ai._shape_cache.clear()  # A new process has no cached entries.
        loaded = await bedcheck_ai.load_ai_settings()
        restored = bedcheck_ai._get_shape(**loaded)
        assert restored == {"token_param": "max_completion_tokens", "response_mode": "json_object"}
        result = await bedcheck_ai.check_bed_ai(42, bedcheck_ai._synthetic_test_frame(), "chamber")
        assert result.outcome == "degraded"
        assert shapes[-1] == restored

        # A key rotation must not inherit a different credential's discovery.
        bedcheck_ai._shape_cache.clear()
        await async_client.put("/api/v1/settings/", json={"bedcheck_ai_api_key": "rotated"})
        loaded = await bedcheck_ai.load_ai_settings()
        assert bedcheck_ai._get_shape(**loaded) == bedcheck_ai._DEFAULT_SHAPE
    finally:
        bedcheck_ai._shape_cache.clear()
        bedcheck_ai.reset_health_state()


@pytest.mark.asyncio
async def test_printer_override_change_resets_only_its_health(async_client, db_session):
    from backend.app.models.printer import Printer
    from backend.app.services import bedcheck_ai

    printer = Printer(
        name="Test",
        serial_number="REVIEWTEST",
        ip_address="192.168.1.10",
        access_code="12345678",
        bedcheck_backend_override="ai",
        is_active=False,
    )
    db_session.add(printer)
    await db_session.commit()
    await db_session.refresh(printer)
    bedcheck_ai._record_outcome(printer.id, "unavailable", "timeout", "json_schema")
    bedcheck_ai._last_unavailable_notified_at[printer.id] = 1.0
    bedcheck_ai._record_outcome(999, "ok", None, "json_schema")
    try:
        response = await async_client.patch(
            f"/api/v1/printers/{printer.id}", json={"bedcheck_backend_override": "opencv"}
        )
        assert response.status_code == 200
        assert printer.id not in bedcheck_ai.get_health()
        assert printer.id not in bedcheck_ai._last_unavailable_notified_at
        assert bedcheck_ai.get_health()[999]["outcome"] == "ok"
    finally:
        bedcheck_ai.reset_health_state()


@pytest.mark.asyncio
async def test_concurrent_discovery_saves_share_one_persisted_row(tmp_path, monkeypatch):
    import json

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from backend.app.models.settings import Settings
    from backend.app.services import bedcheck_ai

    # A file-backed disposable DB gives concurrent sessions independent
    # connections, matching production SQLite rather than a shared in-memory one.
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'discovery.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(bedcheck_ai, "async_session", sessions)
    key = bedcheck_ai._shape_cache_key("http://192.168.1.20/v1", "local-model", "key")
    shape = {"token_param": "max_completion_tokens", "response_mode": "json_object"}
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Settings.__table__.create)
        await asyncio.gather(*(bedcheck_ai._save_shape(key, shape) for _ in range(10)))
        async with sessions() as db:
            rows = (await db.execute(select(Settings))).scalars().all()
            assert len(rows) == 1
            assert json.loads(rows[0].value) == shape

        await bedcheck_ai._save_shape(key, bedcheck_ai._DEFAULT_SHAPE)
        async with sessions() as db:
            rows = (await db.execute(select(Settings))).scalars().all()
            assert len(rows) == 1
            assert json.loads(rows[0].value) == bedcheck_ai._DEFAULT_SHAPE
    finally:
        await engine.dispose()
