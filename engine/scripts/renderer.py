"""
Response Renderer V1 (ADR-009).

Transforma claims + sources em Markdown formatado com links clicáveis.

O agente resolve evidence primeiro, depois chama /render com as URLs prontas.

POST /render
{
  "claims": [
    {
      "text": "Ihde argues X",
      "sources": [
        {"book_title": "...", "url": "https://...", "chunk_id": "ch_xxx"}
      ]
    }
  ]
}

Response:
{
  "markdown": "...\n\n---\n**Fontes**\n\n1 📖 [Book](url) {: target=\"librarian\" }",
  "sources": [...]
}

A camada de projeção de evidência (EvidenceRenderer) é consumida aqui como
módulo separado (engine/renderer/evidence_renderer.py) — preservada intacta;
este endpoint apenas a invoca.
"""
import os, json, sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Consume the EvidenceRenderer as a separate module (preserved architecture).
# Add {engine}/ to path so the evidence_renderer package resolves to engine/evidence_renderer.
_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))
from evidence_renderer.evidence_renderer import EvidenceRenderer

router = APIRouter()

TARGET = 'target="librarian"'


class SourceItem(BaseModel):
    book_title: str = Field(default="Unknown")
    url: str = Field(default="")
    chunk_id: str = Field(default="")


class ClaimItem(BaseModel):
    text: str = Field(..., min_length=1)
    sources: list[SourceItem] = Field(default_factory=list)


class RenderRequest(BaseModel):
    claims: list[ClaimItem] = Field(..., min_length=1)


class SourceResponse(BaseModel):
    index: int
    book_title: str
    url: str
    chunk_id: str


class RenderResponse(BaseModel):
    markdown: str
    sources: list[SourceResponse]


def render_response(claims: list[dict]) -> dict:
    """
    Render claims + sources into Markdown.

    Input:
      claims = [
        {
          "text": "claim text",
          "sources": [{"book_title": "...", "url": "...", "chunk_id": "..."}]
        }
      ]
    """
    all_sources = []
    source_map = {}  # url → index
    source_idx = 0

    for claim in claims:
        for src in claim.get("sources", []):
            url = src.get("url", "")
            if url and url not in source_map:
                source_idx += 1
                source_map[url] = source_idx
                all_sources.append({
                    "index": source_idx,
                    "book_title": src.get("book_title", "Unknown"),
                    "url": url,
                    "chunk_id": src.get("chunk_id", ""),
                })

    # Build markdown
    lines = []
    for claim in claims:
        text = claim.get("text", "")
        refs = []
        for src in claim.get("sources", []):
            idx = source_map.get(src.get("url", ""))
            if idx:
                refs.append(str(idx))
        if refs:
            # Superscript-style references: ¹ ² ³
            superscripts = " ".join(f"^{r}^" for r in refs)
            lines.append(f"{text} {superscripts}")
        else:
            lines.append(text)
        lines.append("")

    if all_sources:
        lines.append("---")
        lines.append("**Fontes**")
        lines.append("")
        for s in all_sources:
            idx = s["index"]
            lines.append(
                f"^{idx}^ 📖 [{s['book_title']}]({s['url']}) {{: {TARGET} }}"
            )

    return {
        "markdown": "\n".join(lines).strip(),
        "sources": all_sources,
    }


@router.post("/render", response_model=RenderResponse)
async def render_endpoint(req: RenderRequest):
    claims_dict = [
        {
            "text": c.text,
            "sources": [
                {"book_title": s.book_title, "url": s.url, "chunk_id": s.chunk_id}
                for s in c.sources
            ]
        }
        for c in req.claims
    ]
    return render_response(claims_dict)


@router.get("/render/health")
async def render_health():
    return {"status": "ok", "service": "response-renderer-v1"}


@router.post("/render/evidence")
async def render_evidence(req: dict):
    """Render Evidence[] dicts via EvidenceRenderer (separate module).

    Body: {"evidence": [ {text, score, citation:{...}}, ... ]}
    Returns a PresentationModel projection (human-safe).
    """
    evidence = req.get("evidence", [])
    presentation = EvidenceRenderer.render(evidence)
    return presentation.model_dump()


if __name__ == "__main__":
    # CLI demo
    demo = [
        {
            "text": "Technology mediates human perception of the world.",
            "sources": [{"book_title": "Technology and the Lifeworld", "url": "/reader/book123#href=ch3&t=technology mediates", "chunk_id": "ch_abc"}]
        },
        {
            "text": "Assemblages are wholes whose parts are not linked by relations of interiority.",
            "sources": [{"book_title": "New Philosophy of Society", "url": "/reader/book456#href=ch8&t=assemblages against", "chunk_id": "ch_def"}]
        },
    ]
    result = render_response(demo)
    print(result["markdown"])
