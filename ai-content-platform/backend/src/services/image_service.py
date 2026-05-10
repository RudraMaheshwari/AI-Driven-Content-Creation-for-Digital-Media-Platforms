"""Image generation.

Two backends, selected by `IMAGE_PROVIDER`:

- ``pollinations`` (default) — free public endpoint at image.pollinations.ai,
  Flux/SD-backed, no API key required. Good for unblocked development.
- ``gemini`` — Gemini's native image-output model (e.g. ``gemini-2.5-flash-image``).
  Requires a billed Google API key; the free tier returns 429 with ``limit: 0``.

In mock mode (``CONTENT_MOCK=true``) we draw a deterministic placeholder so the
UI/API can be developed offline.
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx
from PIL import Image, ImageDraw, ImageFont

from src.config.settings import settings
from src.utils.exceptions import GenerationError, ModelUnavailableError
from src.utils.ids import new_id
from src.utils.logger import get_logger

logger = get_logger("image")


@dataclass
class ImageResult:
    path: Path
    url: str
    provider: str
    mock: bool


class ImageService:
    """Generates an illustrative image to accompany the produced content."""

    def __init__(self) -> None:
        self._gemini_client = None
        self.base_path: Path = settings.image_storage_path
        self.base_url: str = settings.public_image_base_url.rstrip("/")

    # ---------- public ----------

    def generate(
        self,
        prompt: str,
        *,
        record_id: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> ImageResult:
        record_id = record_id or new_id("img")
        w = width or settings.image_width
        h = height or settings.image_height
        if settings.content_mock:
            return self._save_mock(prompt, record_id, w, h)

        provider = (settings.image_provider or "pollinations").lower()
        if provider == "gemini":
            return self._save_gemini(prompt, record_id)
        if provider == "pollinations":
            return self._save_pollinations(prompt, record_id, w, h)
        raise ModelUnavailableError(
            f"unknown IMAGE_PROVIDER={provider!r} (expected 'pollinations' or 'gemini')",
        )

    # ---------- pollinations ----------

    # Quality-booster suffix appended to every Pollinations prompt so
    # the diffusion model produces a clean composition with no gibberish
    # typography (Flux/SD render letters as garbled glyphs).
    _POLLINATIONS_QUALITY_TAIL = (
        " | high quality, professional photography, magazine quality, "
        "sharp focus, high detail, balanced colour grading, clean composition"
    )
    _POLLINATIONS_NEGATIVE = (
        "text, letters, words, typography, captions, signage, watermarks, "
        "logos, blurry, low quality, distorted, deformed, malformed text"
    )

    def _save_pollinations(
        self, prompt: str, record_id: str, width: int, height: int
    ) -> ImageResult:
        full_prompt = prompt + self._POLLINATIONS_QUALITY_TAIL
        encoded = quote(full_prompt, safe="")
        encoded_negative = quote(self._POLLINATIONS_NEGATIVE, safe="")
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={width}"
            f"&height={height}"
            f"&model={settings.image_pollinations_model}"
            f"&nologo=true"
            f"&enhance=true"
            f"&negative_prompt={encoded_negative}"
        )
        logger.info(f"calling pollinations model={settings.image_pollinations_model}")
        try:
            response = httpx.get(url, timeout=120.0, follow_redirects=True)
            response.raise_for_status()
        except Exception as exc:
            raise GenerationError(f"pollinations request failed: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise GenerationError(
                f"pollinations returned non-image response (content-type={content_type})"
            )

        path = self.base_path / f"{record_id}.png"
        path.write_bytes(response.content)
        logger.info(f"saved image record_id={record_id} bytes={len(response.content)} via=pollinations")
        return ImageResult(
            path=path,
            url=f"{self.base_url}/{path.name}",
            provider="pollinations",
            mock=False,
        )

    # ---------- gemini ----------

    def _get_gemini(self):
        if self._gemini_client is not None:
            return self._gemini_client
        if not settings.google_api_key:
            raise ModelUnavailableError(
                "GOOGLE_API_KEY is not set; cannot use Gemini image provider.",
            )
        try:
            from google import genai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ModelUnavailableError(
                "google-genai SDK not installed. Run `pip install google-genai`.",
            ) from exc
        logger.info(f"initializing Gemini image client model={settings.image_model_id}")
        self._gemini_client = genai.Client(api_key=settings.google_api_key)
        return self._gemini_client

    def _save_gemini(self, prompt: str, record_id: str) -> ImageResult:
        client = self._get_gemini()
        try:
            response = client.models.generate_content(
                model=settings.image_model_id,
                contents=prompt,
            )
        except Exception as exc:
            raise GenerationError(f"gemini image request failed: {exc}") from exc

        image_bytes = self._extract_gemini_bytes(response)
        if image_bytes is None:
            raise GenerationError("gemini image response had no inline image data")

        path = self.base_path / f"{record_id}.png"
        path.write_bytes(image_bytes)
        logger.info(f"saved image record_id={record_id} bytes={len(image_bytes)} via=gemini")
        return ImageResult(
            path=path,
            url=f"{self.base_url}/{path.name}",
            provider="gemini",
            mock=False,
        )

    @staticmethod
    def _extract_gemini_bytes(response) -> bytes | None:
        try:
            candidates = getattr(response, "candidates", None) or []
            for cand in candidates:
                content = getattr(cand, "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    inline = getattr(part, "inline_data", None)
                    if inline is None:
                        continue
                    mime = getattr(inline, "mime_type", "") or ""
                    data = getattr(inline, "data", None)
                    if data and mime.startswith("image/"):
                        return data
        except Exception as exc:  # pragma: no cover
            logger.warning(f"failed to parse Gemini image response: {exc}")
        return None

    # ---------- mock ----------

    def _save_mock(self, prompt: str, record_id: str, width: int, height: int) -> ImageResult:
        digest = hashlib.md5(prompt.encode()).digest()
        r, g, b = digest[0], digest[1], digest[2]
        r2, g2, b2 = digest[3], digest[4], digest[5]

        img = Image.new("RGB", (width, height), (r, g, b))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        max_r = max(width, height) // 2
        for i, radius in enumerate(range(max_r, 0, -20)):
            t = i / max(1, max_r // 20)
            color = (
                int(r + (r2 - r) * t) & 0xFF,
                int(g + (g2 - g) * t) & 0xFF,
                int(b + (b2 - b) * t) & 0xFF,
            )
            draw.rectangle(
                (cx - radius, cy - radius, cx + radius, cy + radius),
                outline=color,
                width=4,
            )
        try:
            font = ImageFont.load_default()
            label = "MOCK IMAGE"
            draw.text((20, height - 28), label, fill=(255, 255, 255), font=font)
            snippet = (prompt[:80] + "…") if len(prompt) > 80 else prompt
            draw.text((20, 20), snippet, fill=(255, 255, 255), font=font)
        except Exception:  # pragma: no cover
            pass

        path = self.base_path / f"{record_id}.png"
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        path.write_bytes(buf.getvalue())
        return ImageResult(
            path=path,
            url=f"{self.base_url}/{path.name}",
            provider="mock",
            mock=True,
        )


_service: ImageService | None = None


def get_image_service() -> ImageService:
    global _service
    if _service is None:
        _service = ImageService()
    return _service
