"""Controlled media corpus and isolated PostgreSQL cases; never seeds a personal database."""

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from threading import Thread
from typing import cast
from uuid import uuid4

from PIL import Image, ImageDraw

from tests.factories.runtime import FoundationInstance, prepare_instance

CORPUS = Path(__file__).parents[1] / "fixtures/listing/media"


def generate_corpus() -> dict[str, dict[str, object]]:
    CORPUS.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict[str, object]] = {}
    for filename, size, color, format in (
        ("primary-small.jpg", (320, 240), "#2f584c", "JPEG"),
        ("primary-large.jpg", (1280, 960), "#2f584c", "JPEG"),
        ("additional.png", (1000, 800), "#b3683d", "PNG"),
        ("other.png", (900, 900), "#3a4d7e", "PNG"),
    ):
        image = Image.new("RGB", size, color)
        ImageDraw.Draw(image).rectangle(
            (size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4),
            outline="white",
            width=max(1, size[0] // 100),
        )
        output = BytesIO()
        image.save(output, format)
        data = output.getvalue()
        (CORPUS / filename).write_bytes(data)
        result[filename] = dict(
            sha256=hashlib.sha256(data).hexdigest(), width=size[0], height=size[1], bytes=len(data)
        )
    (CORPUS / "invalid.bin").write_bytes(b"<html>not an image</html>")
    (CORPUS / "cases.json").write_text(
        json.dumps(
            dict(
                files=result,
                cases=[
                    "A",
                    "B",
                    "SEM",
                    "DESCONHECIDA",
                    "PENDENTE",
                    "FALHA",
                    "T",
                    "P",
                    "TP",
                    "C",
                    "LEGADO",
                ],
            ),
            indent=2,
        )
        + "\n"
    )
    return result


@contextmanager
def serve_media() -> Iterator[tuple[str, list[dict[str, str]]]]:
    requests: list[dict[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(dict(self.headers))
            path = CORPUS / self.path.lstrip("/")
            if self.path == "/expired":
                self.send_response(410)
                self.end_headers()
                return
            if self.path == "/retry":
                self.send_response(503)
                self.send_header("Retry-After", "172800")
                self.end_headers()
                return
            if not path.is_file() or path.parent != CORPUS:
                self.send_response(404)
                self.end_headers()
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg" if path.suffix == ".jpg" else "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def prepare_media_instance(root: Path, directory: Path, origin: str) -> FoundationInstance:
    instance = prepare_instance(root, directory, "media_" + uuid4().hex[:10])
    with instance.private_file.open("a") as output:
        output.write(
            f"GARIMPEI_MEDIA_ROOT={directory / 'media'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MIN_FREE_BYTES=1048576\nGARIMPEI_MEDIA_MAX_FILE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
        )
    return instance


def seed_media_cases(origin: str) -> dict[str, dict[str, str]]:
    from django.utils.timezone import now

    from garimpei.config.env import load_media_settings
    from garimpei.domain.listing.listing import Evidence
    from garimpei.domain.media.media import Manifest, Photo, Variant
    from garimpei.infra.persistence.listing_models import (
        CollectionCycle,
        CollectionState,
        Listing,
        ListingObservation,
    )
    from garimpei.infra.repository.listing.mapper import encode_evidence
    from garimpei.infra.repository.media.captures import create_capture
    from tests.factories.monitoring import require_disposable

    require_disposable()
    state = CollectionState.objects.create(configuration_id=uuid4(), source="media_fixture")
    cycle = CollectionCycle.objects.create(state=state, scope_key="media", revision=1)
    result = {}
    for index, name in enumerate(
        ("A", "B", "SEM", "DESCONHECIDA", "PENDENTE", "FALHA", "T", "P", "TP", "C", "LEGADO"), 1
    ):
        row = Listing.objects.create(
            source="media_fixture",
            external_id=str(index),
            canonical_url=f"https://www.facebook.com/marketplace/item/{index}/",
            first_seen_at=now(),
            origin="initial_load",
        )
        evidence = Evidence(
            title="Anúncio de mídia " + name, description="Produto usado. Funciona bem."
        )
        observation = ListingObservation.objects.create(
            listing=row,
            cycle=cycle,
            ordinal=1,
            observed_at=now(),
            evidence=encode_evidence(evidence),
            coverage={},
        )
        row.latest = observation
        row.ordinal = 1
        row.save()
        photos: tuple[Photo, ...] = (
            Photo(
                "primary",
                (
                    Variant(origin + "/primary-small.jpg", 320, 240),
                    Variant(origin + "/primary-large.jpg", 1280, 960),
                ),
                True,
            ),
            Photo("additional", (Variant(origin + "/additional.png", 1000, 800),)),
        )
        if name == "B":
            photos = (Photo("other", (Variant(origin + "/other.png", 900, 900),), True),)
        if name == "FALHA":
            photos = (Photo("failure", (Variant(origin + "/retry"),), True),)
        manifest = (
            Manifest("none", (), True, "", 0)
            if name == "SEM"
            else Manifest()
            if name in {"DESCONHECIDA", "LEGADO"}
            else Manifest("present", photos, True, "", len(photos))
        )
        capture = create_capture(observation, manifest, load_media_settings().policy, now())
        result[name] = dict(
            listing=str(row.id), observation=str(observation.id), capture=str(capture.id)
        )
    return result


def inspect_media_cases() -> dict[str, object]:
    from garimpei.domain.media.media import MediaFile
    from garimpei.infra.persistence.media_models import MediaAsset, MediaJob
    from garimpei.main import build_media_store

    assets = list(
        MediaAsset.objects.values("id", "sha256", "width", "height", "state", "thumbnail_state")
    )
    for row in MediaAsset.objects.filter(state="available"):
        assert (
            hashlib.sha256(
                build_media_store().read(
                    MediaFile(row.id, row.key, row.mime, row.sha256, row.byte_count)
                )
            ).hexdigest()
            == row.sha256
        )
    return dict(
        assets=cast(list[object], assets),
        jobs=list(MediaJob.objects.values("state", "kind", "attempts", "reason")),
    )
