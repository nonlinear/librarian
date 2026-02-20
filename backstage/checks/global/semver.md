# Semantic Versioning

**For AI-assisted projects:**

| Type      | Version Change  | Breaking? |
| --------- | --------------- | --------- |
| **Patch** | v0.2.0 → v0.2.1 | No        |
| **Minor** | v0.2.x → v0.3.0 | No        |
| **Major** | v0.x → v1.0     | Yes       |

**Examples:**

- **Patch:** Bug fixes, typos, minor corrections
  - `fix: correct typo in metadata.json`
  - `fix: handle edge case in script`

- **Minor:** New features, backward compatible
  - `feat: add new capability`
  - `feat: improve existing feature`

- **Major:** Breaking changes, architecture changes
  - `feat!: migrate to new format (BREAKING)`
  - `refactor!: change folder structure`

## Auto-Renumbering (backstage-start)

**Policy enforces version continuity:**

1. **Read last stable version** from CHANGELOG.md
2. **Renumber ROADMAP epics** starting at +1 from CHANGELOG
3. **Detect branch type** from epic content (major/minor/patch)
4. **Rename branch** if type changed (e.g., `v1.0.0` → `v2.0.0`)

**Branch naming convention:**

- `vX.0.0` → Major (breaking changes)
- `v0.Y.0` → Minor (new features)
- `v0.0.Z` → Patch (bug fixes)

**Philosophy:**

- **ROADMAP = promises** (can change, can reorder, can renumber)
- **CHANGELOG = immutable** (versions frozen, no edits after merge)
- **Branch names follow version type** (explicit intent)

**When backstage-start runs:**

- Compares ROADMAP versions vs CHANGELOG stable
- Renumbers gaps (v0.1.0, v0.3.0 → v0.1.0, v0.2.0)
- Warns if active branch version conflicts with ROADMAP
- Suggests branch rename if type changed
