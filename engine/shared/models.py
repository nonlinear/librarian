"""
Librarian domain models — single source of truth.

Loosely aligned with:
  - W3C Web Annotation Data Model (Evidence → Target → Selector)
  - FRBR (Work → Expression → Manifestation → Item)

Model hierarchy:

    Evidence
      ├── source         book_id + chunk_id (and later paper, website, conversation)
      ├── locator        Internal truth: where the text lives in the artifact
      └── citation       Navigable representation: how a human reaches it
"""

from pydantic import BaseModel
from typing import Optional


class TextRange(BaseModel):
    """Text anchor range: start → end.
    
    - start: first ~80 chars of the chunk
    - end: last ~80 chars of the chunk (V1 uses last line)
    
    The Reader uses both to create a DOM Range and apply <mark>.
    """
    start: str
    end: Optional[str] = None

    model_config = {"extra": "forbid"}


class Locator(BaseModel):
    """Internal truth: resource-level addressing.
    
    Immutable per artifact format. Stable across representations.
    
    - href: EPUB spine href (e.g. "text/ch03.xhtml")
    - text_range: character/text anchor within that resource
    - cfi: EPUB Canonical Fragment Identifier (null today)
    """
    href: str
    text_range: TextRange
    cfi: Optional[str] = None

    model_config = {"extra": "forbid"}


class CitationTarget(BaseModel):
    """Navigable representation: how a human reaches the evidence.
    
    Mutable across channels. A single locator can produce:
      - web reader URL
      - mobile deep link
      - Kindle send-to-kindle link
      - voice playback timestamp
    """
    label: str
    url: str

    model_config = {"extra": "forbid"}


class EvidenceSource(BaseModel):
    """Origin of the evidence.
    
    Today: {book_id, chunk_id}.
    Tomorrow: also {paper_id, website_url, conversation_id}.
    """
    book_id: str
    chunk_id: str

    model_config = {"extra": "forbid"}


class Evidence(BaseModel):
    """First-class evidence object.
    
    Created from a search result. Resolved by chunk_id.
    Contains everything needed to verify and navigate to the source.
    """
    evidence_id: str
    source: EvidenceSource
    locator: Locator
    citation: CitationTarget

    model_config = {"extra": "forbid"}
