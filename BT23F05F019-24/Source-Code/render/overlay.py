"""Draw findings onto the screenshot.

Boxes arrive normalised to 0-BBOX_SCALE and are scaled to the original image's
pixel dimensions here, which is why nothing upstream needs to know the true size.

Each box is numbered so the findings table beside the image can be read against
it without colour being the only channel carrying meaning.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from config import BBOX_SCALE

# Severity palette. Numbers on the boxes carry the same information, so the
# colours are a secondary cue rather than the only one.
SEVERITY_COLOUR = {
    "high": (215, 38, 61),
    "medium": (232, 163, 61),
    "low": (74, 123, 167),
}
_FALLBACK_COLOUR = (120, 120, 120)

_FONT_CANDIDATES = [
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
    "Arial Bold.ttf",
    "LiberationSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _to_pixels(bbox: list[int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    w, h = size
    x1, y1, x2, y2 = (v / BBOX_SCALE for v in bbox[:4])
    # Models occasionally emit inverted or out-of-range boxes; clamp and order.
    left, right = sorted((x1 * w, x2 * w))
    top, bottom = sorted((y1 * h, y2 * h))
    left, right = max(0, left), min(w, right)
    top, bottom = max(0, top), min(h, bottom)
    # Guarantee a visible box even if the model returned a degenerate one.
    if right - left < 2:
        right = min(w, left + 2)
    if bottom - top < 2:
        bottom = min(h, top + 2)
    return int(left), int(top), int(right), int(bottom)


def annotate(image: Image.Image, findings: list) -> Image.Image:
    """Return a copy of `image` with every finding boxed and numbered."""
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)

    # Scale line and label weight with image size so a 2000px screenshot and a
    # 600px one both look deliberate.
    scale = max(canvas.size) / 1200
    width = max(2, round(3 * scale))
    font_size = max(13, round(18 * scale))
    font = _font(font_size)
    pad = max(3, round(5 * scale))

    for i, f in enumerate(findings, start=1):
        colour = SEVERITY_COLOUR.get(f.severity, _FALLBACK_COLOUR)
        left, top, right, bottom = _to_pixels(f.bbox, canvas.size)
        draw.rectangle([left, top, right, bottom], outline=colour, width=width)

        label = f"{i}. {f.pattern.replace('_', ' ')}"
        tl, tt, tr, tb = draw.textbbox((0, 0), label, font=font)
        tw, th = tr - tl, tb - tt

        # Prefer the tag above the box; drop it inside when there is no room.
        tag_top = top - th - 2 * pad
        if tag_top < 0:
            tag_top = top
        tag_left = min(left, canvas.width - tw - 2 * pad)
        tag_left = max(0, tag_left)

        draw.rectangle(
            [tag_left, tag_top, tag_left + tw + 2 * pad, tag_top + th + 2 * pad],
            fill=colour,
        )
        draw.text((tag_left + pad, tag_top + pad), label, fill=(255, 255, 255), font=font)

    return canvas
