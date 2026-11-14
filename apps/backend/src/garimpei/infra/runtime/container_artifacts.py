"""Explicit artifact preparation inside manage, never on a normal startup."""

import hashlib
import sys
import urllib.request
from pathlib import Path
from typing import cast

from garimpei.config.env import load_inference_settings
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import read_lock


def main(arguments: list[str]) -> int:
    settings = load_inference_settings()
    lock = read_lock(settings.model_lock)
    guard = HostGpuGuard(settings.gpu_lock, settings.owner)
    action = arguments[0] if arguments else ""
    if action == "reserve":
        return 0 if guard.reserve() else 1
    if action == "owned":
        return 0 if guard.owned() else 1
    if action == "release":
        guard.release()
        return 0
    if action in {"tokenizer", "build-tokenizer"}:
        metadata = cast(dict[str, str], lock["tokenizer"])
        url = metadata["url"]
        if not url.startswith(
            "https://huggingface.co/Qwen/Qwen3.5-4B/resolve/"
        ) or not url.endswith("/tokenizer.json"):
            raise ValueError("Tokenizer: expected pinned official model artifact")
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read(20000001)
        if len(raw) > 20000000 or hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
            raise ValueError("Tokenizer digest mismatch")
        destination = (
            Path("/app/artifacts/tokenizer.json")
            if action == "build-tokenizer"
            else settings.tokenizer
        )
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(raw)
        temporary.chmod(0o600)
        temporary.replace(destination)
        return 0
    if action == "layers":
        manifest = cast(dict[str, object], lock["manifest"])
        layers = [
            cast(dict[str, str], manifest["config"]),
            *cast(list[dict[str, str]], manifest["layers"]),
        ]
        for layer in layers:
            print(layer["digest"])
        return 0
    if action == "model":
        print(lock["model"])
        return 0
    if action == "image":
        print(lock["image"])
        return 0
    if action == "shutdown":
        from garimpei.config.env import configure_django, load_config

        configure_django()
        import django

        django.setup()
        from garimpei.infra.runtime.manifest import read_manifest, write_manifest
        from garimpei.infra.worker.probe_service import end_run

        config = load_config()
        end_run(config)
        current_manifest = read_manifest(config.directory)
        if current_manifest is not None:
            current_manifest["status"] = "stopped"
            write_manifest(config.directory, current_manifest)
        return 0
    if action == "diagnose":
        from garimpei.config.env import configure_django

        configure_django()
        import django

        django.setup()
        from garimpei.main import build_inference_gateway

        diagnostic = build_inference_gateway().diagnose()
        if diagnostic.get("reason") != "ready":
            raise ValueError(
                "Pinned local AI verification failed: " + str(diagnostic.get("reason"))
            )
        return 0
    if action == "recovered":
        from django.utils.timezone import now

        from garimpei.config.env import configure_django

        configure_django()
        import django

        django.setup()
        from garimpei.main import build_inference_repository

        # Only the host wrapper calls this after stop + inspect confirmed termination.
        repository = build_inference_repository()
        repository.recovered(True, now())
        return 0
    raise ValueError(
        "Artifact operation: expected reserve, owned, release, tokenizer, layers, model, image or recovered"
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
