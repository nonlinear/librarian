# FF-CITATION-003 — Evidence Presentation Contract

**Status:** ✅ Created  
**Date:** 2026-07-30  
**Replaces:** FF-CITATION-002 (absorbed)  

## Hypothesis

O Reader não precisa "editar" o EPUB. Ele precisa apontar para uma evidência no livro.

O mecanismo atual (`Range.surroundContents()` → `<mark>`) modifica o DOM do EPUB. Isso:
1. Falha quando o range cruza elementos (P1)
2. É destrutivo — não pode ser desfeito sem recarregar
3. Viola o princípio de que Reader é proof layer, não editor

A alternativa: **CSS Custom Highlight API** — zero modificação no DOM.

## Contract

### Flow

```mermaid
flowchart TD
    1️⃣[parseHash → href + start + end] --> 2️⃣{rendition.display(href)}
    2️⃣ -->|ok| 3️⃣[getIframeDoc]
    3️⃣ --> 4️⃣{locateRange}
    4️⃣ -->|found start| 5️⃣[create Range]
    5️⃣ --> 6️⃣{CSS Highlight API available?}
    6️⃣ -->|yes| 7️⃣[HighlightRegistry.add(range)]
    7️⃣ --> 8️⃣[scrollIntoView + log]
    6️⃣ -->|no| 9️⃣[fallback: scrollIntoView + CSS outline]
    8️⃣ --> 🔟[done]
    9️⃣ --> 🔟
    4️⃣ -->|not found| 1️⃣1️⃣[next page → retry]
    1️⃣1️⃣ -->|≤ maxPages| 3️⃣
    1️⃣1️⃣ -->|> maxPages| 1️⃣2️⃣[FAIL: not found]
```

### Node Details

**1️⃣ parseHash** — extrai href, start text, end text do locator. Se end vazio, range = single point.

**2️⃣ rendition.display** — navega ao capítulo alvo via href.

**4️⃣ locateRange** — busca `startText` no DOM. Se `endText` existe, busca também. Cria Range entre os dois.

**6️⃣ CSS Highlight API** — registra range no `HighlightRegistry` com nome `citation-highlight`. Estilo definido via `::highlight(citation-highlight)`. DOM permanece intacto.

**9️⃣ Fallback** — sem surroundContents. Apenas scrollIntoView + outline CSS no container do startNode.

### Severity Levels

| Level | Requirement | Acceptable |
|-------|-------------|-----------|
| **P0** | Correct book | 100% |
| **P1** | Correct chapter/location | 100% |
| **P2** | Cited text visible in viewport | 100% |
| **P3** | Cited text highlighted | ≥95% with acceptable fallback |
| **P4** | Viewport centered on highlight | Measured, not absolute |

### Success Criteria

1. All 12 stress-test links: P0-P2 = 100%
2. Links #1-#12: P3 ≥ 10/12 (83% minimum, target 95%)
3. When `CSS.Highlight` unavailable: graceful degradation to scrollIntoView
4. No DOM mutation except CSS outline fallback
5. No `surroundContents()` calls
6. `::highlight(citation-highlight)` style defined and applied

### API Reference

```javascript
// New highlight mechanism
const highlight = new Highlight(range);
CSS.highlights.set("citation-highlight", highlight);

// Style (injected into iframe head)
const style = doc.createElement("style");
style.textContent = `
  ::highlight(citation-highlight) {
    background-color: #fff2a8;
    color: inherit;
  }
`;
doc.head.appendChild(style);
```

### Test Protocol

**Setup:**
1. Open each link in browser
2. Open DevTools console (F12)
3. Check console for `[reader]` prefixed logs

**Per link, verify:**
```
[✓] rendition.display OK
[✓] locateRange startText found
[✓] CSS Highlight API applied
[✓] scrolled to highlight
```

**Per link, check (manual):**
- Texto citado visível na viewport (P2)
- Fundo amarelo no texto (P3)
- Scroll centralizado (P4 — visual estimate)

### Reference
- [CSS Custom Highlight API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/CSS_Custom_Highlight_API)
- [CSS.Highlights spec](https://www.w3.org/TR/css-highlight-api-1/)
- Browser support: Chrome 105+, Safari 17.2+, Firefox 130+
