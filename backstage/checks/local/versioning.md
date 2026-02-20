# Versioning - Librarian-Specific Rules

**Reindexing requirement by version type:**

| Type      | Version Change  | Requires Reindex? | Breaking? |
| --------- | --------------- | ----------------- | --------- |
| **Patch** | v0.2.0 → v0.2.1 | No                | No        |
| **Minor** | v0.2.x → v0.3.0 | Optional          | No        |
| **Major** | v0.x → v1.0     | Yes               | Yes       |

**Reindexing triggers:**
- ✅ **Requires reindex:** Schema changes, new embedding models, chunking algorithm changes
- ❌ **No reindex needed:** UI changes, prompt updates, MCP server improvements

**Why this matters:**
- Library can have 100+ books
- Reindexing = minutes to hours
- Patch releases shouldn't force reindex
