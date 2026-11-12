"""Only application boundary that reads or exports process configuration."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, urlsplit

from garimpei.domain.navigation.policy import NavigationPolicy


class ConfigurationError(ValueError):
    """Safe public diagnostic: secret values must never be interpolated."""


@dataclass(frozen=True)
class RuntimeConfig:
    root: Path
    environment: str
    instance: str
    environment_id: str
    django_secret: str = field(repr=False)
    postgres_password: str = field(repr=False)
    waha_key: str = field(repr=False)
    web_port: int
    pg_port: int
    waha_port: int
    startup_timeout: int
    shutdown_timeout: int
    log_level: str
    run_id: str
    ai_port: int = 11434

    @property
    def directory(self) -> Path:
        return self.root / ".runtime" / self.environment_id

    @property
    def database(self) -> str:
        return "garimpei_" + self.environment_id

    @property
    def test_database(self) -> str:
        return "garimpei_test_" + hashlib.sha256(self.environment_id.encode()).hexdigest()[:16]

    @property
    def database_url(self) -> str:
        password = quote(self.postgres_password, safe="")
        return f"postgresql://garimpei:{password}@127.0.0.1:{self.pg_port}/{self.database}"


def _values(explicit: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    filename = explicit.get("GARIMPEI_ENV_FILE")
    if filename:
        try:
            lines = Path(filename).read_text().splitlines()
        except OSError:
            raise ConfigurationError("GARIMPEI_ENV_FILE: expected readable private file") from None
        result = dict(
            _parse_line(line)
            for line in lines
            if line.strip() and not line.lstrip().startswith("#")
        )
    return result | dict(explicit)


def _parse_line(line: str) -> tuple[str, str]:
    key, separator, value = line.partition("=")
    if not separator or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key.strip()):
        raise ConfigurationError("GARIMPEI_ENV_FILE: expected KEY=value data")
    return key.strip(), value.strip().strip("\"'")


def _integer(values: Mapping[str, str], key: str, default: int, low: int, high: int) -> int:
    raw = values.get(key, str(default))
    if not raw.isdecimal() or not low <= int(raw) <= high:
        raise ConfigurationError(f"{key}: {raw!r}; expected integer {low}..{high}")
    return int(raw)


def _secret(values: Mapping[str, str], key: str, required: bool) -> str:
    value = values.get(key, "")
    if required and (
        not value.strip() or value.lower() in {"changeme", "change-me", "placeholder"}
    ):
        raise ConfigurationError(f"{key}: expected nonempty private secret, not a placeholder")
    return value


def _default_instance(root: Path) -> str:
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True
    )
    name = branch.stdout.strip() if branch.returncode == 0 else "checkout"
    digest = hashlib.sha256(f"{root}:{name}".encode()).hexdigest()[:10]
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:20] or "checkout"
    return f"{normalized}_{digest}"


def _reserve_port(stack: ExitStack, preferred: int) -> int:
    # Avoid the Windows/WSL ephemeral range, which may be reserved on the host.
    for candidate in range(preferred, preferred + 100):
        probe = stack.enter_context(socket.socket())
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", candidate))
            return candidate
        except OSError:
            continue
    raise ConfigurationError("Ports: expected available loopback ports")


def _ports(values: Mapping[str, str], directory: Path) -> tuple[int, int, int]:
    manifest = directory / "manifest.json"
    saved = json.loads(manifest.read_text()).get("ports", {}) if manifest.exists() else {}
    with ExitStack() as stack:
        seed = 10000 + int(hashlib.sha256(str(directory).encode()).hexdigest()[:6], 16) % 15000
        defaults = [
            saved.get(key) or _reserve_port(stack, seed + index * 100)
            for index, key in enumerate(("web", "pg", "waha"))
        ]
    result = tuple(
        _integer(values, key, default, 1024, 65535)
        for key, default in zip(
            ("GARIMPEI_WEB_PORT", "GARIMPEI_PG_PORT", "GARIMPEI_WAHA_PORT"), defaults, strict=True
        )
    )
    if len(set(result)) != 3:
        raise ConfigurationError("GARIMPEI_*_PORT: expected three distinct ports")
    return result[0], result[1], result[2]


def load_config(
    environ: Mapping[str, str] | None = None,
    *,
    root: Path | None = None,
    require_secrets: bool = True,
) -> RuntimeConfig:
    values = _values(os.environ if environ is None else environ)
    root = (root or Path(__file__).resolve().parents[5]).resolve()
    environment = values.get("GARIMPEI_ENV", "dev")
    if environment not in {"dev", "eval"}:
        raise ConfigurationError(f"GARIMPEI_ENV: {environment!r}; expected dev or eval")
    instance = values.get(
        "GARIMPEI_INSTANCE", "" if environment == "eval" else _default_instance(root)
    )
    if not re.fullmatch(r"[a-z0-9_]{1,40}", instance):
        raise ConfigurationError(f"GARIMPEI_INSTANCE: {instance!r}; expected [a-z0-9_]{{1,40}}")
    identity = f"{environment}_{instance}"
    django_secret = _secret(values, "DJANGO_SECRET_KEY", require_secrets)
    password = _secret(values, "POSTGRES_PASSWORD", require_secrets)
    waha_key = _secret(values, "WAHA_API_KEY", require_secrets)
    ports = _ports(values, root / ".runtime" / identity)
    level = values.get("LOG_LEVEL", "INFO")
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError(
            f"LOG_LEVEL: {level!r}; expected DEBUG/INFO/WARNING/ERROR/CRITICAL"
        )
    config = RuntimeConfig(
        root,
        environment,
        instance,
        identity,
        django_secret,
        password,
        waha_key,
        *ports,
        _integer(values, "GARIMPEI_STARTUP_TIMEOUT_SECONDS", 60, 1, 300),
        _integer(values, "GARIMPEI_SHUTDOWN_TIMEOUT_SECONDS", 30, 1, 120),
        level,
        values.get("GARIMPEI_RUN_ID", ""),
        _ai_port(values, root / ".runtime" / identity, ports),
    )
    override = values.get("DATABASE_URL")
    if override and urlsplit(override) != urlsplit(config.database_url):
        raise ConfigurationError(
            "DATABASE_URL: expected the owned loopback database and configured credentials"
        )
    return config


def process_environment(config: RuntimeConfig, run_id: str) -> dict[str, str]:
    values = _values(os.environ)
    values.update(
        {
            "GARIMPEI_ENV": config.environment,
            "GARIMPEI_INSTANCE": config.instance,
            "GARIMPEI_RUN_ID": run_id,
            "GARIMPEI_ENVIRONMENT_ID": config.environment_id,
            "GARIMPEI_CHECKOUT": str(config.root),
            "GARIMPEI_WEB_PORT": str(config.web_port),
            "GARIMPEI_PG_PORT": str(config.pg_port),
            "GARIMPEI_WAHA_PORT": str(config.waha_port),
            "GARIMPEI_AI_PORT": str(config.ai_port),
            "GARIMPEI_DB_NAME": config.database,
            "DJANGO_SECRET_KEY": config.django_secret,
            "POSTGRES_PASSWORD": config.postgres_password,
            "WAHA_API_KEY": config.waha_key,
            "DJANGO_SETTINGS_MODULE": "garimpei.config.settings",
        }
    )
    return values


def configure_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "garimpei.config.settings")
    if os.environ["DJANGO_SETTINGS_MODULE"] == "garimpei.config.test_settings":
        return
    config = load_config()
    manifest = config.directory / "manifest.json"
    current = json.loads(manifest.read_text()) if manifest.exists() else {}
    activate_environment(config, config.run_id or str(current.get("run_id", "")))


def activate_environment(config: RuntimeConfig, run_id: str) -> None:
    os.environ.update(process_environment(config, run_id))


def logging_context() -> tuple[str, str]:
    return os.environ.get("GARIMPEI_ENVIRONMENT_ID", "quality"), os.environ.get(
        "GARIMPEI_RUN_ID", "quality"
    )


@dataclass(frozen=True)
class ListingSettings:
    fixture_url: str | None
    fixture_clock: Path | None
    facebook_state: Path | None
    cadence_ms: int
    interval: int
    timeout: int
    lease: int
    max_pages: int
    retry_base: int
    retry_max: int
    facebook_profile: Path | None = None


def load_listing_settings(
    *, facebook_state: Path | None = None, facebook_profile: Path | None = None
) -> ListingSettings:
    values = _values(os.environ)
    fixture_url = values.get("GARIMPEI_LISTING_FIXTURE_URL")
    clock = values.get("GARIMPEI_LISTING_FIXTURE_CLOCK")
    if fixture_url or clock:
        parsed = urlsplit(fixture_url or "")
        if (
            values.get("GARIMPEI_ENV") != "eval"
            or parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.port is None
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ConfigurationError(
                "Listing fixture requires an eval instance and a loopback HTTP origin"
            )
    state = values.get("GARIMPEI_FACEBOOK_STATE_FILE")
    state_path = facebook_state or (Path(state).expanduser().resolve() if state else None)
    if state_path is not None and (
        not state_path.is_file()
        or state_path.stat().st_mode & 0o077
        or state_path.is_relative_to(Path(__file__).resolve().parents[5])
    ):
        raise ConfigurationError(
            "GARIMPEI_FACEBOOK_STATE_FILE: expected an external private file with mode 0600"
        )
    live = state_path is not None or facebook_profile is not None
    timeout = _integer(values, "GARIMPEI_LISTING_TIMEOUT", 20 if live else 5, 1, 60)
    retry_base = _integer(values, "GARIMPEI_LISTING_RETRY_BASE", 15, 1, 3600)
    return ListingSettings(
        fixture_url.rstrip("/") if fixture_url else None,
        Path(clock) if clock else None,
        state_path,
        _integer(values, "GARIMPEI_FACEBOOK_CADENCE_MS", 1200, 500, 10000),
        _integer(values, "GARIMPEI_LISTING_INTERVAL", 60 if live else 300, 1, 86400),
        timeout,
        _integer(values, "GARIMPEI_LISTING_LEASE", 60, timeout + 2, 3600),
        _integer(values, "GARIMPEI_LISTING_MAX_PAGES", 100 if live else 5, 1, 100),
        retry_base,
        _integer(
            values,
            "GARIMPEI_LISTING_RETRY_MAX",
            max(300 if live else 900, retry_base),
            retry_base,
            86400,
        ),
        facebook_profile,
    )


def load_valuation_fixture() -> str | None:
    values = _values(os.environ)
    url = values.get("GARIMPEI_VALUATION_FIXTURE_URL")
    if url is None:
        return None
    parsed = urlsplit(url)
    if (
        values.get("GARIMPEI_ENV") != "eval"
        or parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigurationError(
            "GARIMPEI_VALUATION_FIXTURE_URL: expected eval loopback HTTP origin"
        )
    return url.rstrip("/")


@dataclass(frozen=True)
class ExplorationSettings:
    interval: int
    retention: int


def load_exploration_settings() -> ExplorationSettings:
    values = _values(os.environ)
    return ExplorationSettings(
        _integer(values, "GARIMPEI_EXPLORATION_INTERVAL_SECONDS", 10, 2, 300),
        _integer(values, "GARIMPEI_EXPLORATION_RETENTION_SECONDS", 86400, 60, 604800),
    )


def load_catalog_fixture() -> Path | None:
    values = _values(os.environ)
    raw = values.get("GARIMPEI_CATALOG_FIXTURE")
    if raw is None:
        return None
    path = Path(raw).resolve()
    if values.get("GARIMPEI_ENV") != "eval" or not path.is_file():
        raise ConfigurationError("Catalog fixture requires an eval instance and an existing file")
    return path


@dataclass(frozen=True)
class AlertSettings:
    enabled: bool
    url: str
    key: str = field(repr=False)
    session: str = field(repr=False)
    recipient: str = field(repr=False)
    account: str = field(repr=False)
    tick: int
    timeout: int
    lease: int
    retry_base: int
    retry_max: int
    window: int
    history_pages: int


def load_alert_settings() -> AlertSettings:
    values = _values(os.environ)
    enabled = values.get("GARIMPEI_ALERTS_ENABLED", "false")
    if enabled not in {"true", "false"}:
        raise ConfigurationError("GARIMPEI_ALERTS_ENABLED: expected true or false")
    recipient = values.get("GARIMPEI_WAHA_RECIPIENT", "")
    if recipient and not re.fullmatch(
        r"(?:[0-9]{1,20}@(?:c\.us|lid)|[0-9]+(?:-[0-9]+)?@g\.us)", recipient
    ):
        raise ConfigurationError(
            "GARIMPEI_WAHA_RECIPIENT: expected canonical direct or group chat ID"
        )
    fixture = values.get("GARIMPEI_ALERT_FIXTURE_URL")
    if fixture:
        parsed = urlsplit(fixture)
        if (
            values.get("GARIMPEI_ENV") != "eval"
            or parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or not parsed.port
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ConfigurationError("Alert fixture requires eval and loopback HTTP origin")
    timeout = _integer(values, "GARIMPEI_ALERT_TIMEOUT", 10, 1, 60)
    base = _integer(values, "GARIMPEI_ALERT_RETRY_BASE", 15, 1, 3600)
    return AlertSettings(
        enabled == "true",
        fixture.rstrip("/") if fixture else f"http://127.0.0.1:{load_config().waha_port}",
        values.get("WAHA_API_KEY", ""),
        values.get("GARIMPEI_WAHA_SESSION", ""),
        recipient,
        values.get("GARIMPEI_WAHA_ACCOUNT", ""),
        _integer(values, "GARIMPEI_ALERT_TICK", 5, 1, 60),
        timeout,
        _integer(values, "GARIMPEI_ALERT_LEASE", 60, timeout + 2, 3600),
        base,
        _integer(values, "GARIMPEI_ALERT_RETRY_MAX", max(base, 300), base, 86400),
        _integer(values, "GARIMPEI_ALERT_WINDOW", 86400, 60, 604800),
        _integer(values, "GARIMPEI_ALERT_HISTORY_PAGES", 10, 1, 100),
    )


@dataclass(frozen=True)
class IntegrationPrivateSettings:
    directory: Path


def load_integration_private_settings() -> IntegrationPrivateSettings:
    values = _values(os.environ)
    config = load_config(require_secrets=False)
    raw = values.get("GARIMPEI_INTEGRATION_PRIVATE_DIR")
    directory = (
        Path(raw).expanduser().resolve()
        if raw
        else (Path.home() / ".local/share/garimpei/integrations" / config.environment_id).resolve()
    )
    if directory.is_relative_to(config.root):
        raise ConfigurationError(
            "GARIMPEI_INTEGRATION_PRIVATE_DIR: expected private directory outside checkout"
        )
    return IntegrationPrivateSettings(directory)


def load_facebook_browser_origin() -> tuple[str, bool]:
    values = _values(os.environ)
    fixture = values.get("GARIMPEI_FACEBOOK_BROWSER_FIXTURE_URL")
    if not fixture:
        return "https://www.facebook.com", False
    parsed = urlsplit(fixture)
    if (
        values.get("GARIMPEI_ENV") != "eval"
        or parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigurationError("Facebook browser fixture requires eval and loopback HTTP origin")
    return fixture.rstrip("/"), True


def _ai_port(values: Mapping[str, str], directory: Path, ports: tuple[int, int, int]) -> int:
    manifest = directory / "manifest.json"
    saved = json.loads(manifest.read_text()).get("ports", {}) if manifest.exists() else {}
    seed = 10000 + int(hashlib.sha256(str(directory).encode()).hexdigest()[:6], 16) % 15000
    with ExitStack() as stack:
        default = saved.get("ai") or _reserve_port(stack, seed + 300)
    value = _integer(values, "GARIMPEI_AI_PORT", default, 1024, 65535)
    if value in ports:
        raise ConfigurationError("GARIMPEI_AI_PORT: expected distinct owned loopback port")
    return value


@dataclass(frozen=True)
class InferenceSettings:
    service_enabled: bool
    endpoint: str
    directory: Path
    model_lock: Path
    tokenizer: Path
    gpu_lock: Path
    owner: str
    queue_limit: int = 100
    disk_limit: int = 1073741824
    timeout: int = 180
    idle_seconds: int = 300
    lease_seconds: int = 240
    attempts: int = 3
    text_tokens: int = 2048
    context_tokens: int = 4096
    output_tokens: int = 512
    photo_manifest: Path | None = None


def load_inference_settings() -> InferenceSettings:
    values = _values(os.environ)
    config = load_config(require_secrets=False)
    enabled = values.get("GARIMPEI_AI_SERVICE_ENABLED", "false")
    if enabled not in {"true", "false"}:
        raise ConfigurationError("GARIMPEI_AI_SERVICE_ENABLED: expected true or false")
    folder = config.directory / "inference"
    return InferenceSettings(
        enabled == "true",
        f"http://127.0.0.1:{config.ai_port}",
        folder,
        config.root / "docs/F19-inferencia-multimodal-local-em-docker/model-lock.json",
        folder / "tokenizer.json",
        Path.home() / ".local/share/garimpei/gpu-owner.json",
        f"{config.root}:{config.environment_id}",
        _integer(values, "GARIMPEI_AI_QUEUE_LIMIT", 100, 1, 100),
        _integer(values, "GARIMPEI_AI_DISK_LIMIT", 1073741824, 1048576, 1073741824),
        _integer(values, "GARIMPEI_AI_TIMEOUT", 180, 1, 180),
        _integer(values, "GARIMPEI_AI_IDLE_SECONDS", 300, 1, 300),
        _integer(values, "GARIMPEI_AI_LEASE_SECONDS", 240, 240, 240),
        photo_manifest=Path(values["GARIMPEI_AI_PHOTO_MANIFEST"]).expanduser().resolve()
        if values.get("GARIMPEI_AI_PHOTO_MANIFEST")
        else None,
    )


def load_navigation_policy() -> NavigationPolicy:
    values = _values(os.environ)
    try:
        return NavigationPolicy(
            slice_seconds=_integer(values, "GARIMPEI_NAV_SLICE_SECONDS", 120, 1, 10000),
            slice_pages=_integer(values, "GARIMPEI_NAV_SLICE_PAGES", 2, 1, 10000),
            slice_details=_integer(values, "GARIMPEI_NAV_SLICE_DETAILS", 10, 1, 10000),
            cycle_pages=_integer(values, "GARIMPEI_NAV_CYCLE_PAGES", 100, 1, 10000),
            cycle_terms=_integer(values, "GARIMPEI_NAV_CYCLE_TERMS", 3, 1, 3),
            pending_details=_integer(values, "GARIMPEI_NAV_PENDING_DETAILS", 500, 1, 10000),
            suggestion_seconds=_integer(values, "GARIMPEI_NAV_SUGGESTION_SECONDS", 45, 1, 10000),
            suggestion_pages=_integer(values, "GARIMPEI_NAV_SUGGESTION_PAGES", 1, 1, 10000),
            suggestion_details=_integer(values, "GARIMPEI_NAV_SUGGESTION_DETAILS", 1, 1, 10000),
            suggestion_interval=_integer(values, "GARIMPEI_NAV_SUGGESTION_INTERVAL", 300, 1, 10000),
            suggestion_limit=_integer(values, "GARIMPEI_NAV_SUGGESTION_LIMIT", 100, 1, 10000),
            evidence_limit=_integer(values, "GARIMPEI_NAV_EVIDENCE_LIMIT", 10, 1, 10000),
            margin=_integer(values, "GARIMPEI_NAV_MARGIN", 5, 1, 10000),
        )
    except ConfigurationError:
        raise
    except ValueError as error:
        raise ConfigurationError(f"GARIMPEI_NAV_*: {error}") from None


@dataclass(frozen=True)
class OperationsSettings:
    backup_dir: Path
    enabled: bool
    environment_id: str
    recovery_file: Path
    recovery_evidence_url: str | None = None


def load_operations_settings() -> OperationsSettings:
    values = _values(os.environ)
    config = load_config(require_secrets=False)
    directory = (
        Path(
            values.get(
                "GARIMPEI_BACKUP_DIR",
                str(Path.home() / ".local/share/garimpei/backups" / config.environment_id),
            )
        )
        .expanduser()
        .resolve()
    )
    if directory.is_relative_to(config.root):
        raise ConfigurationError("GARIMPEI_BACKUP_DIR: expected private directory outside checkout")
    flag = values.get("GARIMPEI_OPERATIONS_ENABLED", "false")
    if flag not in {"true", "false"}:
        raise ConfigurationError("GARIMPEI_OPERATIONS_ENABLED: expected true or false")
    evidence = values.get("GARIMPEI_RECOVERY_EVIDENCE_FIXTURE_URL")
    if evidence:
        _validate_recovery_origin(evidence, config.environment)
    return OperationsSettings(
        directory,
        flag == "true",
        config.environment_id,
        config.directory / "recovery-barrier.json",
        evidence,
    )


@dataclass(frozen=True)
class MediaSettings:
    root: Path
    policy: MediaPolicy
    environment_id: str
    eval_origin: str | None = None


def load_media_settings(environ: Mapping[str, str] | None = None) -> MediaSettings:
    from garimpei.domain.media.policy import MediaPolicy

    values = _values(os.environ if environ is None else environ)
    config = load_config(values, require_secrets=False)
    default = Path.home() / ".local/share/garimpei/media" / config.environment_id
    root = Path(values.get("GARIMPEI_MEDIA_ROOT", str(default))).expanduser().resolve()
    if root == config.root or config.root in root.parents:
        raise ConfigurationError("GARIMPEI_MEDIA_ROOT: expected private directory outside checkout")
    raw = values.get("GARIMPEI_MEDIA_BUDGET_BYTES", "")
    budget = int(raw) if raw.isdecimal() and 0 < int(raw) <= 1024**5 else None
    origin = values.get("GARIMPEI_MEDIA_EVAL_ORIGIN")
    if origin:
        parsed = urlsplit(origin)
        if (
            config.environment != "eval"
            or parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or not parsed.port
            or parsed.path not in {"", "/"}
        ):
            raise ConfigurationError(
                "GARIMPEI_MEDIA_EVAL_ORIGIN: expected explicit eval loopback origin"
            )
        origin = origin.rstrip("/")
    policy = MediaPolicy(
        budget,
        _integer(values, "GARIMPEI_MEDIA_MAX_PHOTOS", 12, 1, 100),
        _integer(values, "GARIMPEI_MEDIA_MAX_FILE_BYTES", 20 * 1024**2, 1024, 20 * 1024**2),
        _integer(values, "GARIMPEI_MEDIA_MAX_PIXELS", 40_000_000, 1, 40_000_000),
        _integer(values, "GARIMPEI_MEDIA_THUMB_EDGE", 640, 16, 640),
        _integer(values, "GARIMPEI_MEDIA_TIMEOUT_SECONDS", 20, 1, 20),
        _integer(values, "GARIMPEI_MEDIA_MIN_FREE_BYTES", 256 * 1024**2, 0, 1024**4),
        _integer(values, "GARIMPEI_MEDIA_LEASE_SECONDS", 60, 30, 600),
    )
    return MediaSettings(root, policy, config.environment_id, origin)


from garimpei.domain.media.policy import MediaPolicy  # noqa: E402


def _validate_recovery_origin(value: str, environment: str) -> None:
    parsed = urlsplit(value)
    if (
        environment != "eval"
        or parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ConfigurationError(
            "Recovery evidence fixture requires owned eval and explicit loopback origin"
        )


def load_assessment_enabled() -> bool:
    values = _values(os.environ)
    raw = values.get("GARIMPEI_ASSESSMENT_ENABLED", "false")
    if raw not in {"true", "false"}:
        raise ConfigurationError("GARIMPEI_ASSESSMENT_ENABLED: expected true or false")
    return raw == "true"
