# Reader Comparison

Evaluating EPUB/PDF readers for deep-linking integration.

## Criteria

1. **Deep-linking support** — Paragraph/page/chapter URLs
2. **URL scheme** — Custom protocol (kavita://, calibre://)
3. **API access** — Programmatic book/position mapping
4. **Search capability** — Can find text in books
5. **Platform** — macOS, web, cross-platform
6. **Open source** — Customizability

---

## Option A: Kavita

**Current choice** — User already uses it

### Pros
- ✅ Already installed (http://192.168.1.152:5000)
- ✅ Web-based (works from any device)
- ✅ Library management built-in
- ✅ User familiar with it

### Cons
- ❌ **No search** (major limitation!)
- ❓ URL scheme unknown (needs research)
- ❓ Deep-linking support unknown
- ❓ API for position mapping?

### Research Needed
- [ ] Does Kavita support URL fragments? (`#page=42`, `#para=142`)
- [ ] API documentation for library/series/page IDs
- [ ] Can we map EPUB paragraph → Kavita position?

---

## Option B: Calibre

### Pros
- ✅ Powerful EPUB/PDF support
- ✅ Plugin ecosystem (could write custom deep-link plugin)
- ✅ Good search
- ✅ Open source

### Cons
- ❌ Desktop app (not web-based)
- ❓ URL scheme exists? (`calibre://`)
- ❓ Deep-linking to paragraph?

### Research Needed
- [ ] Calibre URL scheme capabilities
- [ ] Plugin API for deep-linking
- [ ] Community plugins for citation integration?

---

## Option C: Readium

Web-based open-source EPUB reader

### Pros
- ✅ Open source (fully customizable)
- ✅ Web-based
- ✅ Strong EPUB standards compliance

### Cons
- ❌ Requires self-hosting
- ❌ No built-in library management
- ❓ Deep-linking support?

---

## Option D: Apple Books

macOS/iOS native

### Pros
- ✅ Native integration
- ✅ URL scheme exists (`ibooks://`)
- ✅ Good search

### Cons
- ❌ macOS/iOS only
- ❌ Closed ecosystem
- ❓ Supports paragraph-level deep-links?

---

## Option E: Thorium Reader

Open-source desktop EPUB reader

### Pros
- ✅ Open source
- ✅ Modern, standards-compliant

### Cons
- ❌ Desktop app
- ❓ URL scheme?
- ❓ Deep-linking?

---

## Decision Framework

**Must-have:**
- Deep-linking to at least chapter level
- Works on macOS
- Doesn't break user's existing workflow

**Nice-to-have:**
- Paragraph-level granularity
- Search capability
- Cross-platform

**Decision:** TBD after research phase
