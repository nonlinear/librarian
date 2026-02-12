# Epic v0.20.0: Usage Analytics

**Status:** 🟡 Ready (Not Started)
**Branch:** v0.20.0 (not created yet)
**Created:** 2026-02-11

---

## Goal

Build analytics on top of `usage.jsonl` to rank topics, detect patterns, and identify gaps.

**User story:**
> "I want to know which topics I use most, which queries succeed/fail, and see patterns in my research behavior."

---

## Context

**Current state:**
- ✅ `usage.jsonl` logs every query (timestamp, query, topic, exit_code)
- ✅ `analyze-usage.py` exists but only shows basic stats
- ❌ No topic ranking
- ❌ No success rate analysis
- ❌ No pattern detection

**Data we have:**
```json
{"timestamp": "2026-02-11T22:45:00", "query": "servitors", "topic": "magick_chaos", "exit_code": 0}
{"timestamp": "2026-02-11T22:50:00", "query": "Apple notes async", "topic": "ai_theory", "exit_code": 0}
```

**What we can learn:**
1. **Topic popularity:** Which topics get queried most?
2. **Success rate:** Which topics/queries find results? (`exit_code 0` = success)
3. **Recency:** When was each topic last used?
4. **Query patterns:** Common phrases, multi-word vs single-word searches
5. **Session correlation:** Which topics appear together in same timeframe?

---

## Tasks

### Phase 1: Topic Ranking (Core Feature)

- [ ] **Design CLI flags:**
  - `--rank-topics` → Show topics by usage volume
  - `--rank-by-success` → Show topics by success rate
  - `--rank-by-recency` → Show topics by last used
  - `--top N` → Limit results (default: 10)

- [ ] **Implement ranking logic:**
  - Count queries per topic
  - Calculate success rate (successes / total queries)
  - Find last timestamp per topic
  - Sort by chosen metric

- [ ] **Output formats:**
  - **Human-readable (default):**
    ```
    Top Topics by Volume:
    1. magick_chaos (45 queries, 89% success, last: 2 days ago)
    2. ai_theory (32 queries, 94% success, last: today)
    3. anarchy_david_graeber (28 queries, 75% success, last: 1 week ago)
    ```
  - **JSON (for programmatic use):**
    ```json
    {
      "topics": [
        {"id": "magick_chaos", "count": 45, "success_rate": 0.89, "last_used": "2026-02-09T14:30:00"},
        ...
      ]
    }
    ```

### Phase 2: Query Pattern Detection

- [ ] **Common queries per topic:**
  - Extract most frequent search terms
  - Group similar queries (fuzzy matching?)
  - Identify multi-word vs single-word patterns

- [ ] **Example output:**
  ```
  Top Queries in magick_chaos:
  1. "servitors" (12 times)
  2. "sigils chaos magick" (8 times)
  3. "Phil Hine" (5 times)
  ```

### Phase 3: Time-Based Analysis (Future)

- [ ] **Trends over time:**
  - Queries per week/month
  - Topic popularity shifts
  - Seasonal patterns?

- [ ] **Session correlation:**
  - Which topics appear together within 1-hour window?
  - "Users who search X also search Y"

### Phase 4: Integration

- [ ] **Add to research.py help:**
  - Show top 5 topics when user runs `research.py --help`
  - Suggest topics based on common queries

- [ ] **Add to SKILL.md:**
  - Document analytics commands
  - Example usage patterns

### Phase 5: Quick Similarity Scan (Future - Smart Topic Selection)

- [ ] **`--quick-scan` flag:**
  - Run query against ALL topics (top-k 1 only)
  - Return similarity scores WITHOUT full results
  - User sees: "ai_prompt_engineering: 96%, ai_theory: 0.3%, ..."
  - **Then** user decides which topics to fully query

- [ ] **Auto-filter by threshold:**
  - `--auto-scan --threshold 75` → only search topics >75% similarity
  - Directed (manual topic selection) vs intelligent (auto-discovery)

- [ ] **Use case:**
  - User has vague query, doesn't know which topic fits
  - Quick scan shows relevance across library
  - More exploration, less guessing

**Why future:** Need stable ranking first. Quick scan = optimization on top.

---

## Implementation Notes

**File location:** `~/Documents/librarian/analyze-usage.py` (already exists)

**Current code:**
```python
# analyze-usage.py already parses usage.jsonl
# Add new functions for ranking, pattern detection
```

**Dependencies:**
- ✅ Python 3 (stdlib only - json, collections, datetime)
- ✅ usage.jsonl (already logging)

**Performance:**
- JSONL = fast append (low write cost)
- Analytics = read entire file (acceptable for <10k queries)
- Future: If file grows large, add sampling or pagination

---

## Success Criteria

**Minimum viable (Phase 1):**
- ✅ Can rank topics by volume, success rate, recency
- ✅ Output readable markdown table
- ✅ Fast execution (<1s for 1000 queries)

**Nice to have (Phase 2+):**
- ✅ Query pattern detection
- ✅ JSON output for automation
- ✅ Integration with research.py help

**Future enhancements (Phase 3+):**
- Topic correlation ("chaos-magick + anarchy" co-occur?)
- Time-based trends (usage over weeks/months)
- Predictive analytics (which queries likely to succeed?)

---

## Questions to Resolve

**Q1: Should we cache rankings?**
- **Pro:** Faster repeat calls (no re-parsing JSONL)
- **Con:** Cache invalidation complexity
- **Decision:** START WITHOUT CACHE (simple > fast for now)

**Q2: What counts as "success"?**
- **Option A:** `exit_code == 0` (command succeeded)
- **Option B:** `exit_code == 0 AND results > 0` (found content)
- **Decision:** START WITH OPTION A (simpler), add B later if needed

**Q3: How to handle topics with few queries?**
- Topic with 1 query, 100% success vs topic with 100 queries, 80% success
- **Decision:** Add `--min-queries N` filter (ignore topics with <N queries)

**Q4: Should we track query duration?**
- Useful for detecting slow topics (large indexes? complex queries?)
- **Decision:** DEFER to future epic (needs code changes in research.py)

---

## Related Epics

- **v0.15.0 Skill Protocol:** Analytics could inform skill triggers (suggest popular topics)
- **v1.2.0 User Testing:** Analytics show what real users search for
- **v1.3.0 Better Feedback:** Failed queries + analytics = identify gaps in library

---

## Notes

**Why this matters:**
- **Self-knowledge:** Know which parts of library are most valuable
- **Gap detection:** Topics with high failure rate = need more books or better indexing
- **Workflow optimization:** Automate common queries (shortcuts for top 10?)
- **Usage-driven development:** Build features based on real usage patterns

**Low metabolic cost:**
- No external dependencies (Python stdlib)
- No database (JSONL = simple append log)
- Fast analysis (1000 queries in <1s)

**Nicholas's insight:** "será que dá?" = YES, it's already structured for this! 🏴

---

## Next Steps

1. Review this epic (approve scope)
2. Create branch `v0.20.0`
3. Implement Phase 1 (topic ranking)
4. Test with real usage.jsonl data
5. Document in SKILL.md
6. Merge when stable

---

**Created:** 2026-02-11 by Claw
**Status:** Ready for Nicholas approval
