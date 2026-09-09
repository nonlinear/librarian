"""EvidenceRenderer — projection layer.

Transforms Evidence dicts into PresentationModel.
Safe for consumption by humans and agents.
"""
from typing import List, Dict, Any

from .models import PresentationModel, PresentationItem


class EvidenceRenderer:
    """Renders Evidence objects into human-safe presentation.
    
    Responsibilities:
      - title humano (book title ou citation label)
      - snippet (texto chunk, cortado em ~120 chars)
      - score_display (porcentagem tipo "91%")
      - citation_url (link verificável pro Reader)
    
    Não faz:
      - markdown / HTML / voz
      - ranking / reordenação
      - LLM reasoning
      - retrieval
    """

    @staticmethod
    def render(evidence_list: List[Dict[str, Any]]) -> PresentationModel:
        """Render Evidence[] dicts → PresentationModel."""
        return PresentationModel(
            type="evidence_list",
            items=[EvidenceRenderer._render_item(e) for e in evidence_list],
        )

    @staticmethod
    def _render_item(ev: Dict[str, Any]) -> PresentationItem:
        """Render single Evidence dict → PresentationItem."""
        # Extract citation label (has format "Book Title — snippet")
        citation = ev.get("citation", {})
        label = citation.get("label", "") if isinstance(citation, dict) else ""

        # title = first part before " —"
        title = label.split(" —")[0].strip() if " —" in label else (label or "Unknown")

        # snippet = first 120 chars of text
        text = ev.get("text", "") or ""
        snippet = text.strip()[:120]

        # score_display = percentage
        score = ev.get("score", 0) or 0
        score_display = f"{score:.0%}"

        # citation_url = from citation.target.url (V1) or citation.url (V0 fallback)
        citation_url = ""
        if isinstance(citation, dict):
            target = citation.get("target", {})
            citation_url = target.get("url", "") if isinstance(target, dict) else citation.get("url", "")

        return PresentationItem(
            title=title,
            snippet=snippet,
            score_display=score_display,
            citation_url=citation_url,
        )
