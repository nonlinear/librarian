# FF-RENDERER-001 — Evidence Presentation Contract

## Why

O sistema deve separar retrieval de presentation.
Evidence é um objeto semântico. Renderer é uma projeção.
Mudanças no formato de saída (Markdown → HTML → card → Slack)
não devem exigir mudanças no motor de busca.

## Given

Um conjunto de Evidence[] válido:

```json
{
  "evidence_id": "ev_001",
  "source": {
    "book_id": "book_001",
    "book_title": "Example Book"
  },
  "text": "Knowledge fragment...",
  "score": 0.91,
  "citation": {
    "target": {
      "url": "/reader/book_001#locator=abc"
    }
  }
}
```

## When

```
EvidenceRenderer.render(evidence_list)
```

## Then

O resultado deve ser uma representação humana:

```json
{
  "type": "evidence_list",
  "items": [
    {
      "title": "Example Book",
      "snippet": "Knowledge fragment...",
      "score_display": "91%",
      "citation_url": "/reader/book_001#locator=abc"
    }
  ]
}
```

### Não pode conter

- chunk_id
- FAISS internals
- embedding
- índice vetorial
- path físico do livro
- evidence_id
- href do locator (cru)

### Deve conter

- title (book title humano)
- snippet (texto chunk, cortado em ~120 chars)
- score_display (porcentagem formatada)
- citation_url (link verificável pro Reader)

## Architectural capability protected

Evidence can evolve independently from presentation.

## Owner

Contract Hardening

## Depends on

FF-CITATION-002
