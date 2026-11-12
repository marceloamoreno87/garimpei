"""Bounded subprocess entrypoint: only derived bytes are re-encoded."""

import sys
from io import BytesIO

from PIL import Image, ImageOps


def main() -> None:
    image = ImageOps.exif_transpose(
        Image.open(BytesIO(sys.stdin.buffer.read(20 * 1024 * 1024 + 1)))
    )
    image.thumbnail((int(sys.argv[1]), int(sys.argv[1])))
    image.convert("RGB").save(sys.stdout.buffer, "WEBP", quality=85, exif=b"")


if __name__ == "__main__":
    main()
