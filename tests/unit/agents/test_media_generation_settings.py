"""Tests for encrypted multi-provider media-generation settings."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from octop.infra.agents.settings.media_generation import (
    DEFAULT_PROVIDER_ID,
    MediaGenerationSettingsStore,
    MediaProviderUpdate,
    verify_media_credentials,
)
from octop.infra.connectors.crypto import encrypt_credentials
from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.repos.secrets import SecretRepo
from octop.infra.db.repos.settings import SettingsRepo


@pytest.fixture
def store(
    tmp_path: Path,
) -> tuple[MediaGenerationSettingsStore, SettingsRepo, SecretRepo]:
    db = SqlitePool(tmp_path / "octop.db")
    run_migrations(db)
    settings = SettingsRepo(db)
    secrets = SecretRepo(db)
    return (
        MediaGenerationSettingsStore(
            settings_repo=settings,
            secret_repo=secrets,
        ),
        settings,
        secrets,
    )


def _provider(
    provider_id: str,
    provider: str,
    *,
    api_key: str | None = None,
    image_enabled: bool = True,
    video_enabled: bool = True,
) -> MediaProviderUpdate:
    defaults = {
        "volcengine": (
            "https://ark.cn-beijing.volces.com/api/v3",
            "seedream-test",
            "seedance-test",
        ),
        "dashscope": (
            "https://dashscope.aliyuncs.com/api/v1",
            "wan-image-test",
            "wan-video-test",
        ),
    }
    base_url, image_model, video_model = defaults[provider]
    return MediaProviderUpdate(
        id=provider_id,
        provider=provider,  # type: ignore[arg-type]
        display_name=provider_id,
        enabled=True,
        base_url=base_url,
        image_enabled=image_enabled,
        video_enabled=video_enabled,
        image_model=image_model,
        video_model=video_model,
        api_key=api_key,
    )


def test_media_generation_settings_encrypt_keys_and_build_routes(
    store: tuple[MediaGenerationSettingsStore, SettingsRepo, SecretRepo],
) -> None:
    media, settings, secrets = store
    view = media.save(
        enabled=True,
        providers=[
            _provider(
                "ark-image",
                "volcengine",
                api_key="ark-secret-test",
                video_enabled=False,
            ),
            _provider(
                "wan-video",
                "dashscope",
                api_key="dashscope-secret-test",
                image_enabled=False,
            ),
        ],
        default_image_provider="ark-image",
        default_video_provider="wan-video",
    )

    assert view.configured is True
    assert [item.api_key_set for item in view.providers] == [True, True]
    assert media.api_key("ark-image") == "ark-secret-test"
    assert media.api_key("wan-video") == "dashscope-secret-test"
    raw = secrets.get("media_generation_credentials_v2")
    assert raw is not None
    assert b"ark-secret-test" not in raw
    assert b"dashscope-secret-test" not in raw
    assert "secret-test" not in (settings.get("media_generation_config_v2") or "")

    config = media.harness_config()
    assert config is not None
    assert config.default_image_provider == "ark-image"
    assert config.default_video_provider == "wan-video"
    assert [item.id for item in config.providers] == ["ark-image", "wan-video"]
    assert [item.provider for item in config.providers] == ["volcengine", "dashscope"]


def test_legacy_ark_settings_are_exposed_as_default_provider(
    store: tuple[MediaGenerationSettingsStore, SettingsRepo, SecretRepo],
) -> None:
    media, settings, secrets = store
    settings.set("media_generation_enabled", "true")
    settings.set("media_generation_image_enabled", "true")
    settings.set("media_generation_video_enabled", "false")
    settings.set("media_generation_image_model", "legacy-seedream")
    secrets.get_or_create(
        "media_generation_credentials",
        lambda: encrypt_credentials(secrets, {"api_key": "legacy-ark-key"}),
    )

    view = media.load()

    assert view.enabled is True
    assert view.default_image_provider == DEFAULT_PROVIDER_ID
    assert view.default_video_provider is None
    assert len(view.providers) == 1
    assert view.providers[0].provider == "volcengine"
    assert view.providers[0].image_model == "legacy-seedream"
    assert view.providers[0].api_key_set is True
    assert media.api_key(DEFAULT_PROVIDER_ID) == "legacy-ark-key"


def test_disabled_media_generation_does_not_build_harness_config(
    store: tuple[MediaGenerationSettingsStore, SettingsRepo, SecretRepo],
) -> None:
    media, _, _ = store
    media.save(
        enabled=False,
        providers=[_provider("ark-main", "volcengine")],
        default_image_provider="ark-main",
        default_video_provider="ark-main",
    )

    assert media.harness_config() is None


@pytest.mark.parametrize(
    ("provider", "base_url", "expected_url"),
    [
        (
            "volcengine",
            "https://ark.cn-beijing.volces.com/api/v3",
            "https://ark.cn-beijing.volces.com/ping",
        ),
        (
            "dashscope",
            "https://dashscope.aliyuncs.com/api/v1",
            "https://dashscope.aliyuncs.com/api/v1/models?page_no=1&page_size=1",
        ),
        (
            "minimax",
            "https://api.minimax.cn",
            "https://api.minimax.cn/v1/models",
        ),
    ],
)
@pytest.mark.asyncio
async def test_verify_media_credentials_uses_provider_probe(
    provider: str,
    base_url: str,
    expected_url: str,
) -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await verify_media_credentials(
            provider,  # type: ignore[arg-type]
            "provider-test-key",
            base_url=base_url,
            client=client,
        )

    assert result == {"ok": True}
    assert seen == {
        "url": expected_url,
        "auth": "Bearer provider-test-key",
    }


# ---------------------------------------------------------------------------
# 回归：只做单一模态的供应商（如 OpenAI 兼容中转站）
#
# 这类预设的 video_models 是空元组。原实现直接取 [0]，保存设置时抛
# IndexError → PUT /admin/media-generation 返回 500，前端表现为「点保存没反应」。
# ---------------------------------------------------------------------------


def test_provider_preset_defaults_tolerate_missing_modality() -> None:
    from octop.infra.agents.settings.media_generation import MEDIA_PROVIDER_PRESETS

    preset = MEDIA_PROVIDER_PRESETS["openai"]
    assert preset.video_models == ()
    # 取值必须是空串而不是抛 IndexError
    assert preset.default_video_model == ""
    assert preset.default_image_model == "gpt-image-1"

    # 反向：只做视频的预设也不该在取图像默认值时炸掉
    from octop.infra.agents.settings.media_generation import MediaProviderPreset

    video_only = MediaProviderPreset(
        provider="minimax",
        display_name="video only",
        base_url="https://example.invalid",
        image_models=(),
        video_models=("some-video-model",),
    )
    assert video_only.default_image_model == ""
    assert video_only.default_video_model == "some-video-model"


def test_saving_image_only_provider_round_trips(
    store: tuple[MediaGenerationSettingsStore, SettingsRepo, SecretRepo],
) -> None:
    media, _settings, _secrets = store
    view = media.save(
        enabled=True,
        providers=[
            MediaProviderUpdate(
                id="relay-image",
                provider="openai",
                display_name="OpenAI 兼容中转站",
                enabled=True,
                base_url="https://relay.example.com/v1",
                image_enabled=True,
                video_enabled=False,
                image_model="gpt-image-2.5",
                # 前端在未渲染视频字段时传的就是空串
                video_model="",
                api_key="relay-secret-test",
            )
        ],
        default_image_provider="relay-image",
        default_video_provider=None,
    )

    assert view.configured is True
    saved = next(item for item in view.providers if item.id == "relay-image")
    assert saved.image_model == "gpt-image-2.5"
    assert saved.video_enabled is False
    assert saved.video_model == ""

    # 再次 load() 不能炸（500 就出在这一步）
    reloaded = media.load()
    assert [item.id for item in reloaded.providers] == ["relay-image"]

    config = media.harness_config()
    assert config is not None
    provider = next(item for item in config.providers if item.id == "relay-image")
    assert provider.provider == "openai"
    assert provider.video_enabled is False
