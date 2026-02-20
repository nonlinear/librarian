# Commit Style

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
feat: add new capability
fix: resolve undefined error
docs: update ROADMAP with v0.3 epic
refactor: consolidate folder structure
```

## Typo Checking

**Run during backstage-start workflow:**

**Easy to detect typos:** Fix automatically

- Common misspellings (e.g., "runing" → "running", "inform" → "informs")
- Missing plurals/verb agreement
- Obvious grammatical errors

**Voice choice:** Keep as-is

- Intentional informal language
- Project-specific terminology
- Stylistic decisions

**Unknown/uncertain typos:** Present to user with context

- Show quoted text with surrounding context
- Include file link with line number
- Let user decide whether to fix

**Example output:**

```
Possible typo in [README.md](README.md#L42):
> "...allows you to be in your zone while AI ensure best practices..."
Did you mean "ensures"?
```

## Commit Rigor: Main vs Branch

**Philosophy:** Main is protected, branches are for experimentation.

### Main Branch (Maximum Rigor)

**🚨 MANDATORY: Run backstage-start before EVERY commit to main**

**Why:**
- Main = production-ready, vetted, stable
- CHANGELOG must match reality
- Checksums validate integrity
- Other developers/AI depend on it

**What backstage-start validates:**
- All HEALTH checks pass
- ROADMAP matches git diff
- Documentation synced
- No broken references
- Navigation blocks current

**No exceptions.** If you committed to main without backstage-start, you broke process.

**Allowed commits to main (still require backstage-start):**
- ✅ Epic completion (ROADMAP → CHANGELOG)
- ✅ Hotfixes (fix:)
- ✅ Documentation grooming (docs:)
- ✅ Dependency updates (chore:)

### Epic Branches (Soft Requirements)

**⚠️ RECOMMENDED but not enforced: backstage-start helps but doesn't block**

**Philosophy:** Branches are sandboxes for experimentation and work-in-progress.

**Soft checks:**
- Can commit with failing tests (document in commit message)
- Can have incomplete documentation
- Can experiment freely
- Must document known issues in epic-notes/

**Commit message format when checks fail:**

```
wip: implemented feature X

⚠️ Known issues:
- Test Y fails: reason
- Plan: how to fix before merge

See epic-notes/vX.Y.Z/MAIN.md for details
```

**Before merging branch → main:**
- ✅ Run backstage-start
- ✅ All checks must pass
- ✅ Epic notes reviewed
- ✅ ROADMAP → CHANGELOG (if complete)

### Documentation-Only Changes

**Special case:** ROADMAP/POLICY/epic-notes grooming

**Can merge to main from branch without backstage-start IF:**
- ✅ Changes are pure documentation (no code)
- ✅ Non-actionable (grooming, not implementation)
- ✅ Files: ROADMAP.md, epic-notes/, gap/, POLICY.md only

**Why this exception:**
- Planning/grooming happens continuously
- Documentation doesn't break code
- Main should have latest groomed state
- Avoids blocking idea capture with process overhead

**Workflow:**

```bash
# On branch: groom ROADMAP, create epic-notes
git checkout -b grooming/v1.4.0-planning
# Edit ROADMAP.md, create epic-notes/v1.4.0/
git add ROADMAP.md epic-notes/
git commit -m "docs: add v1.4.0 epic - reader integration planning"
git checkout main
git merge grooming/v1.4.0-planning --no-ff
git push origin main
```

**Still recommended (but not required):**
- Quick sanity check: navigation blocks intact?
- Links resolve correctly?
- Mermaid diagram valid?

### Summary: When to Run backstage-start

| Commit Target | Type                      | backstage-start Required? |
| ------------- | ------------------------- | ------------------------- |
| **Main**      | Code changes              | ✅ **MANDATORY**          |
| **Main**      | Epic completion           | ✅ **MANDATORY**          |
| **Main**      | Doc grooming (from branch)| ⚠️ **RECOMMENDED**        |
| **Branch**    | Work in progress          | 📝 **OPTIONAL**           |
| **Branch**    | Experimentation           | 📝 **OPTIONAL**           |
| **Branch**    | Before merge to main      | ✅ **MANDATORY**          |

**Key principle:** Main is sacred. Branches are sandboxes.
