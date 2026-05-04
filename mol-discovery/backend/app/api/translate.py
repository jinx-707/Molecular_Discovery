"""
Translation API
===============
GET  /api/translate            — translate a single string (query params)
POST /api/translate            — translate with full options (JSON body)
POST /api/translate/batch      — translate a list of strings (library wrapper)
POST /api/translate/page-batch — efficient batch for the "Translate Page" button
                                 (joins strings with separator → one Sarvam call)
GET  /api/translate/glossary   — browse the scientific glossary
GET  /api/translate/status     — check whether Sarvam key is configured
"""
import logging
import os
import re
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.sarvam_service import (
    translate_with_glossary,
    translate_text_cached,
    is_configured,
)
from app.services.glossary import get_glossary_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/translate", tags=["translation"])

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_URL = "https://api.sarvam.ai/translate"
SEP = " [||] "          # separator that survives Sarvam translation
LATIN = re.compile(r"[a-zA-Z]")


# ── Pydantic models ────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    target_lang: str = Field("kn-IN")
    apply_glossary: bool = Field(True)
    use_cache: bool = Field(True)


class TranslateResponse(BaseModel):
    original: str
    translated: str
    target_lang: str
    cached: bool = False


class BatchTranslateRequest(BaseModel):
    texts: List[str] = Field(..., max_length=100)
    target_lang: str = Field("kn-IN")
    apply_glossary: bool = Field(True)
    use_cache: bool = Field(True)


class BatchTranslateResponse(BaseModel):
    translations: List[TranslateResponse]
    total: int


class PageBatchRequest(BaseModel):
    """Sent by the frontend 'Translate Page' button."""
    texts: List[str] = Field(..., description="Visible text strings scraped from the page")
    source: str = Field("en-IN")
    target: str = Field("kn-IN")


class PageBatchResponse(BaseModel):
    translations: List[str]


class GlossaryTerm(BaseModel):
    english: str
    kannada: str


# ── Helpers ────────────────────────────────────────────────────────────────

async def _sarvam_call(text: str, source: str, target: str) -> str:
    """Single raw Sarvam REST call (used by page-batch)."""
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "input": text,
        "source_language_code": source,
        "target_language_code": target,
        "model": "mayura:v1",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(SARVAM_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["translated_text"]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=TranslateResponse)
async def translate_get(
    text: str = Query(..., description="Text to translate"),
    target: str = Query("kn-IN"),
):
    """GET /api/translate?text=catalyst&target=kn-IN"""
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        translated = translate_with_glossary(text, target_lang=target, use_cache=True)
        return TranslateResponse(original=text, translated=translated, target_lang=target)
    except Exception as exc:
        log.error("GET translate error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", response_model=TranslateResponse)
async def translate_post(req: TranslateRequest):
    """POST with full options — glossary → Sarvam → LRU cache."""
    try:
        if req.apply_glossary:
            translated = translate_with_glossary(req.text, req.target_lang, req.use_cache)
        elif req.use_cache:
            translated = translate_text_cached(req.text, req.target_lang)
        else:
            from app.services.sarvam_service import translate_text
            translated = translate_text(req.text, req.target_lang)
        return TranslateResponse(original=req.text, translated=translated, target_lang=req.target_lang)
    except Exception as exc:
        log.error("POST translate error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch", response_model=BatchTranslateResponse)
async def translate_batch(req: BatchTranslateRequest):
    """Translate a list of strings via the library wrapper (glossary + cache)."""
    results: List[TranslateResponse] = []
    for text in req.texts:
        try:
            translated = translate_with_glossary(text, req.target_lang, req.use_cache)
            results.append(TranslateResponse(original=text, translated=translated, target_lang=req.target_lang))
        except Exception as exc:
            log.error("Batch item failed: %s", exc)
            results.append(TranslateResponse(original=text, translated=text, target_lang=req.target_lang))
    return BatchTranslateResponse(translations=results, total=len(results))


@router.post("/page-batch", response_model=PageBatchResponse)
async def translate_page_batch(req: PageBatchRequest):
    """
    Efficient batch endpoint for the frontend 'Translate Page' button.

    Pipeline:
      1. Apply glossary to every string (free, instant — handles scientific terms).
      2. Strings that no longer contain Latin chars are done; skip API for them.
      3. Remaining strings are packed into chunks ≤ 1 900 chars joined by SEP,
         then sent as ONE Sarvam call per chunk.
      4. If the separator is mangled in the response, fall back to individual calls.
      5. Reassemble in original order and return.
    """
    if not req.texts:
        return PageBatchResponse(translations=[])

    glossary = get_glossary_service()

    # Step 1 — glossary pass
    processed = [
        glossary.apply_glossary(t, source_lang="en", target_lang="kn")
        for t in req.texts
    ]

    # Step 2 — no API key → glossary output is the best we can do
    if not SARVAM_API_KEY:
        return PageBatchResponse(translations=processed)

    # Step 3 — find strings that still need API translation
    needs_api: List[int] = [i for i, t in enumerate(processed) if LATIN.search(t)]
    if not needs_api:
        return PageBatchResponse(translations=processed)

    results = list(processed)

    # Step 4 — pack into ≤ 1 900-char chunks
    chunks: List[List[int]] = []
    cur_chunk: List[int] = []
    cur_len = 0

    for idx in needs_api:
        t = processed[idx]
        extra = len(t) + (len(SEP) if cur_chunk else 0)
        if cur_chunk and cur_len + extra > 1900:
            chunks.append(cur_chunk)
            cur_chunk, cur_len = [idx], len(t)
        else:
            cur_chunk.append(idx)
            cur_len += extra

    if cur_chunk:
        chunks.append(cur_chunk)

    # Step 5 — translate each chunk
    for chunk in chunks:
        combined = SEP.join(processed[i] for i in chunk)
        try:
            translated_combined = await _sarvam_call(combined, req.source, req.target)
            parts = translated_combined.split(SEP)
            if len(parts) == len(chunk):
                for k, idx in enumerate(chunk):
                    results[idx] = parts[k].strip()
            else:
                # Separator mangled — fall back to individual calls
                for idx in chunk:
                    try:
                        results[idx] = await _sarvam_call(processed[idx], req.source, req.target)
                    except Exception:
                        pass  # keep glossary text
        except Exception as exc:
            log.error("page-batch chunk failed: %s", exc)
            # keep glossary-processed text for this chunk

    return PageBatchResponse(translations=results)


@router.get("/glossary", response_model=List[GlossaryTerm])
def get_glossary(search: Optional[str] = Query(None)):
    """Browse the scientific glossary. Pass ?search=enzyme to filter."""
    terms = get_glossary_service().get_all_terms()
    if search:
        terms = {k: v for k, v in terms.items() if search.lower() in k.lower()}
    return [GlossaryTerm(english=k, kannada=v) for k, v in sorted(terms.items())]


@router.get("/status")
def translation_status():
    """Check whether the Sarvam API key is configured."""
    return {
        "sarvam_configured": is_configured(),
        "mode": "live" if is_configured() else "glossary-only (set SARVAM_API_KEY to enable live translation)",
    }
