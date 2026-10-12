"""Central configuration and the shared Anthropic client.

Everything that affects a reported number lives here, so an evaluation run can be
reproduced from a single file. Do not scatter model names or temperatures through
the pipeline modules.
"""

from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

# --- Model configuration ----------------------------------------------------
# Sonnet is the default because evaluation sweeps re-run the whole dataset many
# times. Switch to an Opus model via DPA_MODEL when you want a capability
# comparison for the results section.
MODEL = os.getenv("DPA_MODEL", "claude-sonnet-5-5")

# Pinned at 0 so repeated runs over the same dataset are comparable. Changing
# this mid-experiment invalidates every number already collected.
TEMPERATURE = float(os.getenv("DPA_TEMPERATURE", "0"))

MAX_TOKENS = 4096

# Anthropic downscales images whose long edge exceeds ~1568px. Doing it
# ourselves keeps the coordinate maths predictable and the payload small.
MAX_IMAGE_EDGE = 1568

# Bounding boxes come back in a normalised 0-1000 space so the model never has
# to know the true pixel dimensions. render/overlay.py scales them back.
BBOX_SCALE = 1000

TAXONOMY_PATH = ROOT / "taxonomy" / "patterns.yaml"

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def get_client():
    """Return an LLM client (Groq or Anthropic)."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from groq import Groq
        return Groq(api_key=groq_key)

    ant_key = os.getenv("ANTHROPIC_API_KEY")
    if ant_key:
        return Anthropic(api_key=ant_key)

    raise RuntimeError(
        "Neither GROQ_API_KEY nor ANTHROPIC_API_KEY is set. Please check your .env file."
    )
