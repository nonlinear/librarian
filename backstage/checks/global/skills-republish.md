# Published Skills Republish Policy

**DESCRIPTION:** Published skills stay synced with ClawHub. Prevents stale distribution drift.  
**TYPE:** interpretive  
**SCOPE:** global

**Applies to:** Projects that contain published skills (ClawHub)

**Check:** Before merging to main, verify if any published skills were modified.

---

## Detection

1. Find all skills with `status: production` or `type: public` in frontmatter
2. Check if any skill files were modified (`git diff`)
3. If YES → skill MUST be republished

---

## When to Republish

**BEFORE merge to main:**
- Breaking changes (API, behavior, requirements)
- Version bump (major/minor)
- Critical fixes

**AFTER merge to main:**
- Documentation updates
- Non-breaking improvements
- Patch fixes

---

## How to Republish

```bash
# From skill directory
clawhub publish

# Or specify path
clawhub publish /path/to/skill
```

---

## Warning Signs (AI should alert)

- ❌ Modified skill has `status: production`
- ❌ Modified skill has `type: public`
- ❌ Git shows changes in `skills/*/SKILL.md` or `skills/*/*.sh`

**Message template:**
```
⚠️  Published skill modified: [skill-name]
Status: production
Action required: Republish BEFORE/AFTER merge to main
Command: cd skills/[name] && clawhub publish
```

---

## Future Automation

When this becomes `.sh` (automated):
- Parse frontmatter automatically
- Detect `git diff` on skill files
- Run `clawhub publish --dry-run` to verify
- Block merge if republish needed (configurable)
