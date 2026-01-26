# TEST: EPUB Anchor Support

**Purpose:** Test if `cweijan.epub-reader` VS Code extension supports navigation anchors and if pills work.

**Extension:** cweijan.epub-reader (installed, 5⭐, 68k downloads)

---

## Test EPUBs

Using existing EPUBs from library:

1. `books/anarchy/david graeber/Debt.epub`
2. `books/AI/theory/Superintelligence.epub`
3. `books/plants/Entangled Life.epub`

---

## Test Cases

### Test 1: Baseline (no anchor)

**Link:** [Debt.epub](../../books/anarchy/david%20graeber/Debt.epub)

**Expected:**

- ✅ Pill appears
- ✅ Extension opens book
- ⚠️ Opens at beginning/last position

**Result:** _(test and fill)_

---

### Test 2: Chapter anchor (#chapterX)

**Link:** [Debt.epub (chapter 3)](../../books/anarchy/david%20graeber/Debt.epub#chapter3)

**Expected:**

- ❓ Pill appears (critical test)
- ❓ Extension opens
- ❓ Jumps to chapter 3

**Result:** _(test and fill)_

---

### Test 3: Paragraph anchor (#paraX)

**Link:** [Debt.epub (para 30)](../../books/anarchy/david%20graeber/Debt.epub#para30)

**Expected:**

- ❓ Pill appears
- ❓ Extension opens
- ❓ Jumps to paragraph 30

**Result:** _(test and fill)_

---

### Test 4: XHTML file anchor (#chapterX.xhtml)

**Link:** [Superintelligence.epub (ch1.xhtml)](../../books/AI/theory/Superintelligence.epub#chapter1.xhtml)

**Expected:**

- ❓ Pill appears
- ❓ Extension opens
- ❓ Jumps to chapter file

**Result:** _(test and fill)_

---

### Test 5: CFI anchor (EPUB Canonical Fragment Identifier)

**Link:** [Entangled Life.epub (CFI)](<../../books/plants/Entangled%20Life.epub#epubcfi(/6/4[chapter01]!/4/2/8)>)

**Expected:**

- ❓ Pill appears
- ❓ Extension opens
- ❓ Jumps to CFI location

**Result:** _(test and fill)_

---

### Test 6: Simple numeric anchor (#30)

**Link:** [Debt.epub (page 30)](../../books/anarchy/david%20graeber/Debt.epub#30)

**Expected:**

- ❓ Pill appears
- ❓ Extension opens
- ❓ Navigation behavior

**Result:** _(test and fill)_

---

## Decision Tree

```
Test 1 (baseline) works?
├─ NO → Extension broken, find alternative
└─ YES → Continue

Test 2-6 (with anchors) - Does pill appear?
├─ NO → CRITICAL BLOCKER
│       Pills break with anchors
│       Cannot use granularity
│       Need workaround or different approach
└─ YES → Continue

Extension navigates to anchor?
├─ NO → Anchors ignored, but pills work
│       Still useful (pill validates file)
│       Granularity less effective
└─ YES → PERFECT
         Both pills and navigation work
```

---

## Alternative Anchor Formats (if needed)

If extension doesn't support standard formats, try:

### Test A: Query String Parameter

**Link:** [Debt.epub](books/anarchy/david%20graeber/Debt.epub?chapter=3)
**Result:** ❌ FAIL - No link rendered, no pill, nothing appears

### Test B: URL-Encoded Hash

**Link:** [Debt.epub](books/anarchy/david%20graeber/Debt.epub%23chapter3)
**Result:** ❌ FAIL - No link rendered, no pill, nothing appears

### Test C: Empty Fragment

**Link:** [Debt.epub](books/anarchy/david%20graeber/Debt.epub#)
**Result:** ✅ PILL WORKS - But provides no navigation value

### Test D: Double-Encoded Hash

**Link:** [Debt.epub](books/anarchy/david%20graeber/Debt.epub%2523chapter3)
**Result:** ❌ FAIL - No link rendered, no pill, nothing appears

**CONCLUSION:** VS Code pill validation is INCOMPATIBLE with URL fragments. Only empty `#` works, but it provides no navigation benefit. This is a **CRITICAL BLOCKER** for the epic's primary goal.

---

## Extension Capabilities Research

**Check extension docs:**

- Does it mention fragment/anchor support?
- What format does it expect?
- Any examples in marketplace page?

---

## Results Summary

_(Fill after testing)_

| Test      | Pill? | Opens? | Navigates? | Notes |
| --------- | ----- | ------ | ---------- | ----- |
| Baseline  |       |        |            |       |
| #chapter3 |       |        |            |       |
| #para30   |       |        |            |       |
| #ch.xhtml |       |        |            |       |
| #epubcfi  |       |        |            |       |
| #30       |       |        |            |       |

**Recommendation:** _(based on results)_
