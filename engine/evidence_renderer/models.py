"""Evidence renderer models — presentation layer.

PresentationModel: output limpo do renderer, sem leaks de implementação.
"""
from pydantic import BaseModel
from typing import Optional


class PresentationItem(BaseModel):
    """Single rendered evidence item — projeção humana."""
    title: str
    snippet: str
    score_display: str
    citation_url: str

    model_config = {"extra": "forbid"}


class PresentationModel(BaseModel):
    """Rendered evidence list."""
    type: str = "evidence_list"
    items: list[PresentationItem]

    model_config = {"extra": "forbid"}
