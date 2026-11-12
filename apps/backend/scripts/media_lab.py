"""Owned F14 evaluation origin, runtime and corpus lifecycle."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from threading import Event

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.factories.media import generate_corpus, prepare_media_instance, serve_media
from tests.factories.runtime import FoundationInstance


def prepare(directory: Path) -> None:
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    generate_corpus()
    origin_file = directory / "origin.json"
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve", "--output", str(directory)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 10
    while not origin_file.exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("media origin unavailable")
        time.sleep(0.05)
    source = json.loads(origin_file.read_text())
    root = Path(__file__).resolve().parents[3]
    instance = prepare_media_instance(root, directory, source["origin"])
    manifest = dict(
        root=str(root),
        private_file=str(instance.private_file),
        source=source,
        port=instance.config.web_port,
    )
    file = directory / "manifest.json"
    file.write_text(json.dumps(manifest))
    file.chmod(0o600)
    result = instance.command("./scripts/init.sh", "--disposable", timeout=120)
    (directory / "init.txt").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("media eval init failed: inspect private init.txt")
    seeded = instance.shell(
        "from tests.factories.media import seed_media_cases; import json; print('CASES='+json.dumps(seed_media_cases("
        + repr(source["origin"])
        + ")))"
    )
    if seeded.returncode:
        raise RuntimeError(seeded.stderr)
    cases = json.loads(
        next(
            line.removeprefix("CASES=")
            for line in seeded.stdout.splitlines()
            if line.startswith("CASES=")
        )
    )
    manifest["cases"] = cases
    file.write_text(json.dumps(manifest))
    print(f"Ready: http://127.0.0.1:{instance.config.web_port}; manifest={file}")


def serve(directory: Path) -> None:
    with serve_media() as (origin, _):
        (directory / "origin.json").write_text(
            json.dumps(dict(origin=origin, pid=os.getpid(), created=psutil.Process().create_time()))
        )
        Event().wait()


def inspect(file: Path) -> None:
    data = json.loads(file.read_text())
    instance = FoundationInstance(Path(data["root"]), Path(data["private_file"]))
    result = instance.shell(
        "from tests.factories.media import inspect_media_cases; import json; print(json.dumps(inspect_media_cases(),default=str))"
    )
    print(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stderr)


def stop(file: Path) -> None:
    data = json.loads(file.read_text())
    instance = FoundationInstance(Path(data["root"]), Path(data["private_file"]))
    result = instance.command("./scripts/stop.sh", "--clean", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    source = data["source"]
    try:
        process = psutil.Process(source["pid"])
    except psutil.NoSuchProcess:
        return
    if (
        process.create_time() != source["created"]
        or str(Path(__file__).resolve()) not in process.cmdline()
    ):
        raise RuntimeError("origin owner mismatch")
    process.send_signal(signal.SIGTERM)
    print("Owned media runtime and origin stopped; private corpus retained.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare", "inspect", "stop", "serve"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.operation == "prepare":
        prepare(args.output)
    elif args.operation == "serve":
        serve(args.output)
    elif args.operation == "inspect":
        inspect(args.manifest)
    else:
        stop(args.manifest)


if __name__ == "__main__":
    main()
