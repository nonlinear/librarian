# v0.18.0 - Skill Validation & AI Testing

**Status:** 📋 Planned  
**Created:** 2026-02-20  
**Priority:** HIGH (validation of v0.15.0 work)

---

## Goal

End-to-end conversational testing of librarian skill protocol. Validate all 🟠 ORANGE nodes from v0.15.0 architecture.

---

## Context

**v0.15.0 Implementation Status (as of 2026-02-20):**
- 🟢 8/15 nodes GREEN (wrapper + Python working)
- 🟠 7/15 nodes ORANGE (conversational layer untested)
- 🔴 1/15 nodes RED (--book flag bug, Phase 2)

**Untested nodes (🟠):**
1. TRIGGER - Conversational activation
2. INFER - Scope inference (confidence >75%)
3. CLARIFY - Low confidence hard stop
4. FORMAT - Emoji citations + synthesis
5. RESPONSE - Final user output
6. BROKEN - System failure hard stop
7. EMPTY - No results hard stop

**Need:** Real AI session to test conversational flow.

---

## Tasks

### Phase 1: Trigger Testing

**Goal:** Validate skill activation patterns from SKILL.md

**Test cases:**
- [ ] "pesquisa sobre sigils" → activate
- [ ] "o que é caos magick?" → activate
- [ ] "procura no livro X sobre Y" → activate
- [ ] "search tarot meanings" → activate (English)
- [ ] "tell me about bitcoin" → do NOT activate (no trigger)
- [ ] "lembra disso" → do NOT activate (wrong skill)

**Success:** >90% trigger accuracy

---

### Phase 2: Scope Inference Testing

**Goal:** Validate INFER node (confidence >75%, correct scope type)

**Test cases:**
- [ ] "pesquisa chaos magick sobre sigils" → infer: topic "magick_chaos"
- [ ] "procura no livro Condensed Chaos" → infer: book "Condensed Chaos.epub"
- [ ] "o que Graeber fala sobre dívida?" → infer: book "Debt.epub" (from context)
- [ ] "tarot" (ambiguous) → confidence <75%, trigger CLARIFY
- [ ] "hexagrama 23" → infer: topic "magick_i_ching"

**Success:** >85% confidence on clear queries, <75% on ambiguous

---

### Phase 3: Hard Stop Testing

**Goal:** Validate CLARIFY, BROKEN, EMPTY hard stops

**Test cases:**

**CLARIFY (low confidence):**
- [ ] "pesquisa isso" (no context) → hard stop, ask clarification
- [ ] "tarot" (too vague) → hard stop, ask which topic/book

**BROKEN (system failure):**
- [ ] Delete books/ symlink → hard stop "system is broken"
- [ ] Remove Python deps → hard stop with install instructions

**EMPTY (no results):**
- [ ] Query nonsense in valid topic → return low-similarity results (unlikely to trigger)
- [ ] Query in empty topic → hard stop "no results found"

**Success:** All hard stops honest, actionable, helpful

---

### Phase 4: Format & Response Testing

**Goal:** Validate FORMAT and RESPONSE nodes

**Test cases:**
- [ ] Query returns 3 results → formatted with emojis 📕📍💬
- [ ] Citations include book title, location, text snippet
- [ ] Synthesis paragraph coherent and accurate
- [ ] Links to Kavita work (for EPUBs)
- [ ] No hallucination (only cite actual results)

**Success:** User-facing output helpful, readable, cites sources correctly

---

### Phase 5: Edge Cases

**Document unexpected behaviors discovered during testing:**
- [ ] Multi-word book titles
- [ ] Accented characters in queries
- [ ] Very long queries (>100 words)
- [ ] Rapid-fire queries (caching? rate limits?)
- [ ] Mixed language (Portuguese + English in same query)

---

### Phase 6: Regression Suite

**Create test log for future validation:**
- [ ] Record 20+ test queries with expected outputs
- [ ] Save in `skill/tests/regression.json`
- [ ] Document how to run regression suite
- [ ] Automate where possible (wrapper tests OK, AI tests manual)

---

## Success Criteria

**Protocol complete:**
- All 15 nodes 🟢 GREEN
- Diagram updated (no ORANGE/RED)
- SKILL.md accurate (reflects actual behavior)

**User experience:**
- Triggers reliable (>90% accuracy)
- Responses helpful (accurate, well-formatted)
- Hard stops honest (no fake answers)

**Documentation:**
- Edge cases documented
- Regression suite created
- SKILL.md examples verified

---

## Blocked By

**v0.15.0 Phase 2:**
- --book flag bug (Node BUILD 🔴 → 🟢)

**v0.15.0 Phase 3:**
- Frontmatter (deps, install, prereqs)
- Config file (library path)
- Pre-trigger flow

**Timeline:** Cannot start until v0.15.0 Phases 2-3 complete

---

## Notes

**Why separate epic:**
- v0.15.0 = implementation
- v0.18.0 = validation
- Different concerns, different timelines

**AI session testing:**
- Cannot automate (requires real conversation)
- Manual testing OK (record results)
- Regression suite for wrapper/Python (automatable)

**Integration with AGENTS.md:**
- Trigger patterns must match AGENTS.md skill triggers table
- Update AGENTS.md after validation (accurate patterns)

---

*Epic created: 2026-02-20 22:57 EST*
