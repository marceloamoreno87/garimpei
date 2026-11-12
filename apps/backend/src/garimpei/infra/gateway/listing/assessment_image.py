"""Independent bounded PNG input. The F14 original remains immutable and pinned."""

import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from garimpei.domain.inference.errors import InferenceError


def assessment_derivative(raw: bytes) -> bytes:
    if len(raw) > 20 * 1024**2:
        raise InferenceError("capacity_limit")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            return _png(raw)
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise InferenceError("invalid_image_content") from None


def _png(raw: bytes) -> bytes:
    with Image.open(BytesIO(raw), formats=("JPEG", "PNG", "WEBP")) as image:
        if image.width * image.height > 40_000_000 or getattr(image, "n_frames", 1) != 1:
            raise InferenceError("capacity_limit")
        image.load()
        oriented = ImageOps.exif_transpose(image)
        oriented.thumbnail((512, 512), Image.Resampling.LANCZOS)
        rgb = _opaque(oriented)
        output = BytesIO()
        rgb.save(output, "PNG")
        return output.getvalue()


def _opaque(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        frame = Image.new("RGBA", image.size, "white")
        frame.alpha_composite(image.convert("RGBA"))
        return frame.convert("RGB")
    return image.convert("RGB")
