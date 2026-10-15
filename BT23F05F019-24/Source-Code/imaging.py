"""Image preparation for model calls.

Screenshots of real checkout pages are often very tall, which matters twice: the
API downscales anything over MAX_IMAGE_EDGE anyway, and tall thin images waste
tokens. We downscale here so the behaviour is explicit and the overlay maths has
a single source of truth for dimensions.
"""

from __future__ import annotations

import base64
import io

from PIL import Image

from config import MAX_IMAGE_EDGE


def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    # Screenshots arrive as RGBA or palette images often enough to matter.
    return img.convert("RGB")


def downscale(img: Image.Image, max_edge: int = MAX_IMAGE_EDGE) -> Image.Image:
    longest = max(img.size)
    if longest <= max_edge:
        return img
    ratio = max_edge / longest
    new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    return img.resize(new_size, Image.LANCZOS)


def to_image_block(img: Image.Image) -> dict:
    """Encode a PIL image as an Anthropic image content block."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.standard_b64encode(buf.getvalue()).decode("ascii"),
        },
    }


def prepare(data: bytes) -> tuple[dict, Image.Image]:
    """Raw screenshot bytes -> (image content block, original full-size image).

    The original is returned unscaled because overlays are drawn on it; bounding
    boxes are normalised, so the two never need to agree on pixel dimensions.
    """
    original = load_image(data)
    return to_image_block(downscale(original)), original
