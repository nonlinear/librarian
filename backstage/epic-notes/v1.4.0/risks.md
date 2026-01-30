# Risks & Mitigations

## Risk 1: Reading Interruption

**Problem:** User is on page 142. Clicks citation → Jumps to page 87. Loses reading position.

### Severity: HIGH
User experience disruption. Could make feature unusable.

### Mitigations

**Option A: Return Link**
- Citation opens book at target position
- Show floating "Return to page 142" button
- Clicking returns to previous position

**Option B: Modal/Overlay**
- Citation opens in overlay/popup
- Book position doesn't change
- User can choose to navigate or dismiss

**Option C: Warning**
- Before jumping: "This will navigate away from page 142. Continue?"
- User confirms navigation
- Simple but interrupts flow

**Option D: Dual-Link**
```markdown
[View citation](kavita://...#page=87) | [Continue reading](kavita://...#page=142)
```

**Recommendation:** Test Option A first (return link). Fallback to Option D if reader doesn't support history.

---

## Risk 2: Reader Offline/Unavailable

**Problem:** Kavita server not running, or book not in reader library.

### Severity: MEDIUM
Fallback needed, but not critical.

### Mitigations

**Solution: Hybrid Links**
```markdown
[Molecular Red](kavita://... || file://path)
```

- Try reader link first
- Fall back to file link if reader unavailable
- Always include file path as backup

---

## Risk 3: Granularity Mismatch

**Problem:** Citation says "Chapter 3, ¶4" but lands on wrong paragraph.

### Severity: MEDIUM
Confusing, reduces trust in system.

### Causes
- EPUB paragraph IDs inconsistent
- Chunking misaligns with paragraph boundaries
- Reader interprets position differently

### Mitigations

- Validate paragraph ID extraction across sample books
- Test deep-links with known positions
- Include searchable snippet (4 consecutive words) as verification
- User can search snippet if position wrong

---

## Risk 4: Kavita Limitations

**Problem:** Kavita may not support paragraph-level anchors.

### Severity: HIGH (if true)
Reduces granularity to page or chapter only.

### Mitigations

- Research Kavita URL scheme thoroughly
- Test with actual Kavita instance
- Fallback to page-level if paragraph not supported
- Consider alternative readers (Calibre, Readium)

**Decision Gate:** If Kavita can't do paragraph-level, evaluate alternatives before proceeding.

---

## Risk 5: Cross-Platform Compatibility

**Problem:** Deep-links work on macOS but not on mobile/web clients.

### Severity: LOW
Most research happens on desktop.

### Mitigations

- Document platform requirements
- Test across VS Code, Claude Desktop, terminal
- Provide file fallback for unsupported platforms

---

## Risk 6: URL Scheme Registration

**Problem:** `kavita://` protocol not registered on user's system.

### Severity: LOW
One-time setup issue.

### Mitigations

- Document protocol registration steps
- Provide setup script
- Graceful fallback to file links
