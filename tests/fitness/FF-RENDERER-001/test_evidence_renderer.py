"""
FF-RENDERER-001: Evidence Projection

Why:
    O sistema deve separar retrieval de presentation.
    Evidence é um objeto semântico. Renderer é uma projeção.
    Mudanças no formato de saída não devem exigir mudanças no motor de busca.

Given:
    Evidence[] válido vindo de /v1/search (ou construído manualmente)

When:
    Renderer.render(evidence_list)

Then:
    A saída deve conter fonte humana, target.url, snippet e score.
    Não deve expor chunk_id, FAISS metadata, JSON interno ou locator fields crus.

Architectural capability protected:
    Evidence can evolve independently from presentation.
"""
import sys
import os

# Import EvidenceRenderer from flagship/renderer/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from flagship.renderer.evidence_renderer import EvidenceRenderer

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def test_evidence_renderer_contract():
    print("\n=== FF-RENDERER-001: Evidence Projection ===\n")

    # Given: Evidence[] (simulated — como /v1/search retornaria)
    evidence_list = [
        {
            "evidence_id": "ev_ch_test123",
            "source": {"book_id": "book_test", "chunk_id": "ch_test123"},
            "text": "A good design is actually a lot harder to notice than a poor design.",
            "locator": {
                "href": "chapter01.xhtml",
                "text_range": {"start": "A good design is actually", "end": "than a poor design."},
                "cfi": None,
            },
            "citation": {
                "label": "The Design of Everyday Things — Don Norman",
                "target": {"url": "/reader/book_test#locator=abc123"}
            },
            "score": 0.91,
        },
        {
            "evidence_id": "ev_ch_test456",
            "source": {"book_id": "book_test", "chunk_id": "ch_test456"},
            "text": "Clustering is the process of grouping similar items.",
            "locator": {
                "href": "chapter02.xhtml",
                "text_range": {"start": "Clustering is the process", "end": "grouping similar items."},
                "cfi": None,
            },
            "citation": {
                "label": "Design Patterns — Gamma et al",
                "target": {"url": "/reader/book_test#locator=def456"}
            },
            "score": 0.85,
        },
    ]

    # When: Renderer processes evidence list
    try:
        output = EvidenceRenderer.render(evidence_list)
    except Exception as e:
        check("Renderer exists and runs", False, f"Renderer not implemented: {e}")
        print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
        return False

    # Then: output deve ser PresentationModel
    check("output is PresentationModel",
          hasattr(output, "type") and hasattr(output, "items"),
          f"got {type(output).__name__}")
    check("output.type is evidence_list",
          output.type == "evidence_list",
          f"got {output.type}")
    check("output has same number of items",
          len(output.items) == len(evidence_list),
          f"got {len(output.items)}, expected {len(evidence_list)}")

    # Check first item
    item = output.items[0]
    check("item has title",
          bool(item.title),
          f"empty title")
    check("item.title contains book title",
          "The Design of Everyday Things" in item.title or "Don Norman" in item.title,
          f"got '{item.title}'")
    check("item has snippet",
          bool(item.snippet),
          f"empty snippet")
    check("item.snippet contains text",
          "good design" in item.snippet.lower(),
          f"got '{item.snippet}'")
    check("item has score_display",
          bool(item.score_display),
          f"empty score")
    check("item.score_display is formatted as percentage",
          "91%" in item.score_display,
          f"got '{item.score_display}'")
    check("item has citation_url",
          bool(item.citation_url),
          f"empty citation_url")
    check("item.citation_url contains reader path",
          "reader/book_test#locator=" in item.citation_url.lower(),
          f"got '{item.citation_url}'")

    # Check second item
    item2 = output.items[1]
    check("item2.title is different",
          "Design Patterns" in item2.title,
          f"got '{item2.title}'")
    check("item2.score is 85%",
          "85%" in item2.score_display,
          f"got '{item2.score_display}'")

    # Serialize to dict and verify no internals leak
    out_dict = output.model_dump()
    out_str = str(out_dict)
    check("output does NOT expose chunk_id",
          "ch_test123" not in out_str and "ch_test456" not in out_str,
          "chunk_id leaked")
    check("output does NOT expose evidence_id",
          "ev_ch_" not in out_str,
          "evidence_id leaked")
    check("output does NOT expose FAISS metadata",
          "faiss" not in out_str.lower(),
          "FAISS metadata leaked")
    check("output does NOT expose raw href",
          "chapter01.xhtml" not in out_str,
          "raw href leaked")

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    return FAIL == 0


if __name__ == "__main__":
    success = test_evidence_renderer_contract()
    sys.exit(0 if success else 1)
