# Contributing Guide

> 🤖 This file defines the git workflow for feature development. Reusable across projects.

> 🤖
>
> [CHANGELOG](../engine/docs/CHANGELOG.md) - What we did
> [ROADMAP](../engine/docs/ROADMAP.md) - What we wanna do
> [CONTRIBUTING](.github/CONTRIBUTING.md) - How we do it
> [CHECKS](../engine/docs/CHECKS.md) - What we accept
>
> [/whatsup](prompts/whatsup.prompt.md) - The prompt that keeps us sane
>
> 🤖

## Branch Strategy

**One branch per epic:**

```
main (stable releases only)
  ↓
v0.3-delta-indexing (feature branch)
v0.4-provider-integration (feature branch)
v0.5-automation (feature branch)
```

### Branch Naming

**Format:** `v{major}.{minor}-{epic-name}`

**Examples:**

- `v0.3-delta-indexing`
- `v0.4-provider-integration`
- `v1.0-breaking-changes`

### Workflow

1. **Create branch from main:**

   ```bash
   git checkout main
   git pull origin main
   git checkout -b v0.3-delta-indexing
   ```

2. **Link branch in ROADMAP.md:**

   ```markdown
   ## Epic v0.3: Delta Indexing 🔶 (IN PROGRESS)

   **Branch:** `v0.3-delta-indexing`
   ```

3. **Work on feature with regular commits:**

   ```bash
   git add .
   git commit -m "feat: implement change detection"
   git push origin v0.3-delta-indexing
   ```

4. **Stay current - rebase from main regularly:**

   ```bash
   git checkout main
   git pull origin main
   git checkout v0.3-delta-indexing
   git rebase main
   git push --force-with-lease origin v0.3-delta-indexing
   ```

   **Why rebase?**
   - Keeps linear history
   - Easier to review
   - Cleaner when merging back to main

   **When to rebase?**
   - Daily if main is active
   - Before creating PR
   - After major main updates

5. **Before merging - use `/whatsup`:**

   ```bash
   # Run pre-commit workflow (does steps 6-7 automatically)
   # See .github/prompts/whatsup.prompt.md
   ```

   **The `/whatsup` workflow will:**
   - ✅ Run all CHECKS (see engine/docs/CHECKS.md)
   - ✅ Update ROADMAP (mark completed checkboxes)
   - ✅ Move epic to CHANGELOG (if complete)
   - ✅ Bump version number (semantic versioning)
   - ✅ Generate commit message

6. **Merge to main when epic complete:**

   ```bash
   git checkout main
   git pull origin main
   git merge v0.3-delta-indexing --no-ff

   # Tag the release
   git tag v0.3.0 -m "Epic v0.3: Delta Indexing complete"

   git push origin main
   git push origin v0.3.0
   ```

7. **Delete feature branch (recommended):**

   ```bash
   # Local
   git branch -d v0.3-delta-indexing

   # Remote (optional - keeps history clean)
   git push origin --delete v0.3-delta-indexing
   ```

   **Branch deletion policy:**
   - ✅ **DO delete** after successful merge (keeps branch list clean)
   - ✅ Git history preserved via tags
   - ✅ Can recreate from tag if needed: `git checkout -b v0.3-delta-indexing v0.3.0`
   - ❌ **DON'T delete** if you plan to make hotfixes on that version

8. **Announce release:**
   - Update [README.md](../README.md) status section (links to new CHANGELOG entry)
   - Post in [Signal group](https://signal.group/#CjQKIKD7zJjxP9sryI9vE5ATQZVqYsWGN_3yYURA5giGogh3EhAWfvK2Fw_kaFtt-MQ6Jlp8)
   - Tweet/share if public release

---

## Semantic Versioning

**For AI-assisted projects:**

| Type      | Version Change  | Requires Reindex? | Breaking? |
| --------- | --------------- | ----------------- | --------- |
| **Patch** | v0.2.0 → v0.2.1 | No                | No        |
| **Minor** | v0.2.x → v0.3.0 | Optional          | No        |
| **Major** | v0.x → v1.0     | Yes               | Yes       |

**Examples:**

- **Patch:** Bug fixes, typos, minor corrections
  - `fix: correct typo in metadata.json`
  - `fix: handle edge case in indexer`

- **Minor:** New features, backward compatible
  - `feat: add delta indexing support`
  - `feat: PDF support`

- **Major:** Breaking changes, architecture changes
  - `feat!: migrate to new storage format (BREAKING)`
  - `refactor!: change folder structure (requires reindex)`

---

## Rebase vs Merge

**Use rebase for:**

- ✅ Keeping feature branch current with main
- ✅ Cleaning up local history before pushing
- ✅ Maintaining linear git history

**Use merge for:**

- ✅ Integrating completed features into main
- ✅ Preserving complete feature development history
- ✅ Creating clear version boundaries

**Never rebase:**

- ❌ Public/shared branches after others have pulled
- ❌ Main branch itself
- ❌ After a branch has been merged

**Rebase conflicts?**

```bash
# During rebase, if conflicts occur:
git status                    # See conflicting files
# Fix conflicts in editor
git add <resolved-files>
git rebase --continue

# If rebase gets messy:
git rebase --abort           # Start over
```

---

## Commit Messages

**Format:**

```
<type>: <subject>

[optional body]
[optional footer]
```

**Types:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code restructuring (no feature change)
- `test:` Adding tests
- `chore:` Maintenance (dependencies, build, etc.)

**Examples:**

```
feat: add delta indexing for books
fix: resolve STORAGE_DIR undefined error
docs: update ROADMAP with v0.3 epic
refactor: consolidate storage to books/ only
```

---

## Pre-Commit Workflow

**ALWAYS run before merging to main:**

1. **Use `/whatsup` prompt** (see [.github/prompts/whatsup.prompt.md](prompts/whatsup.prompt.md))
2. **Check CHECKS.md** for stability requirements (location in [README](/README.md))
3. **Update ROADMAP** - mark completed checkboxes
4. **Move to CHANGELOG** - if epic complete
5. **Run all tests** - ensure nothing broke

---

## Questions?

- 📖 See [ROADMAP.md](../engine/docs/ROADMAP.md) for current epics
- 📜 See [CHANGELOG.md](../engine/docs/CHANGELOG.md) for completed features
- ✅ See [CHECKS.md](../engine/docs/CHECKS.md) for stability requirements
- 🔄 Use [/whatsup](prompts/whatsup.prompt.md) before every commit

---

**Last updated:** 2026-01-20
**Version:** 1.0 (Initial workflow definition)
