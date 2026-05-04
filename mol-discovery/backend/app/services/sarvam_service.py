"""
Sarvam AI Translation Service
==============================
Uses the official `sarvamai` Python library.
Wraps translation with:
  - Scientific glossary pre-processing (prevents mistranslation of domain terms)
  - lru_cache for repeated phrases (zero extra API calls for same text)
  - Graceful fallback: returns original text if API key is missing or call fails

Set SARVAM_API_KEY in backend/.env to enable live translation.
Without a key the service returns the glossary-processed text as-is (still
useful for demo — scientific terms are already in Kannada from the glossary).
"""
import logging
import os
from functools import lru_cache
from typing import Optional

log = logging.getLogger(__name__)

SARVAM_API_KEY: Optional[str] = os.getenv("SARVAM_API_KEY") or None

# Lazy-initialised client — only created when a key is present
_client = None


def _get_client():
    global _client
    if _client is None:
        if not SARVAM_API_KEY:
            return None
        try:
            from sarvamai import SarvamAI
            _client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
            log.info("Sarvam AI client initialised.")
        except ImportError:
            log.warning("sarvamai package not installed. Run: pip install sarvamai")
        except Exception as exc:
            log.warning("Sarvam AI client init failed: %s", exc)
    return _client


# ---------------------------------------------------------------------------
# Core (uncached) translate — called by the cached wrapper below
# ---------------------------------------------------------------------------

def _translate_raw(text: str, target_lang: str = "kn-IN") -> str:
    """
    Call Sarvam translate API.
    Returns original text on any failure so the UI never breaks.
    """
    client = _get_client()
    if client is None:
        log.debug("No Sarvam client — returning text as-is.")
        return text

    try:
        response = client.text.translate(
            input=text,
            source_language_code="en-IN",
            target_language_code=target_lang,
            model="mayura:v1",          # 12-language model; swap to sarvam-translate:v1 for 22
        )
        return response.translated_text
    except Exception as exc:
        log.error("Sarvam translate error: %s", exc)
        return text                     # graceful fallback


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1000)
def translate_text_cached(text: str, target_lang: str = "kn-IN") -> str:
    """
    Translate with in-process LRU cache (1 000 entries).
    Identical inputs never hit the network twice in the same process lifetime.
    """
    return _translate_raw(text, target_lang)


def translate_text(text: str, target_lang: str = "kn-IN") -> str:
    """Uncached translate — use translate_text_cached for repeated phrases."""
    return _translate_raw(text, target_lang)


def translate_with_glossary(
    text: str,
    target_lang: str = "kn-IN",
    use_cache: bool = True,
) -> str:
    """
    Full pipeline:
      1. Apply scientific glossary  (replaces domain terms before API call)
      2. Translate via Sarvam       (or return glossary-processed text if no key)
      3. Cache result

    This is the recommended entry-point for all dynamic content translation.
    """
    if not text or not text.strip():
        return text

    # Step 1 — glossary
    from app.services.glossary import get_glossary_service
    glossary = get_glossary_service()
    processed = glossary.apply_glossary(text, source_lang="en", target_lang="kn")

    # Step 2+3 — translate (cached)
    if use_cache:
        return translate_text_cached(processed, target_lang)
    return translate_text(processed, target_lang)


def is_configured() -> bool:
    """Return True if a Sarvam API key is present."""
    return bool(SARVAM_API_KEY)
