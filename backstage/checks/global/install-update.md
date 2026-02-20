# Backstage Installation & Updates

**Backstage is AI-driven - no install scripts.**

## Initial Install

**Clone templates from GitHub:**

```bash
# Create backstage folder
mkdir -p backstage/global

# Download templates
for file in ROADMAP CHANGELOG POLICY HEALTH; do
  curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/templates/${file}-template.md" \
    -o "backstage/${file}.md"
done

# Download global files
curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/backstage/global/POLICY.md" \
  -o "backstage/global/POLICY.md"
curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/backstage/global/HEALTH.md" \
  -o "backstage/global/HEALTH.md"
```

**OR: Clone entire repo and copy backstage/ folder**

## Framework Updates

**Pull latest global files:**

```bash
# Update global POLICY/HEALTH
curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/backstage/global/POLICY.md" \
  -o "backstage/global/POLICY.md"
curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/backstage/global/HEALTH.md" \
  -o "backstage/global/HEALTH.md"

# Update prompts (if using OpenClaw)
curl -fsSL "https://raw.githubusercontent.com/nonlinear/backstage/main/.github/prompts/backstage-start.prompt.md" \
  -o ".github/prompts/backstage-start.prompt.md"
# ... repeat for other prompts
```

**What stays unchanged:**
- `backstage/ROADMAP.md` (your epics)
- `backstage/CHANGELOG.md` (your history)  
- `backstage/POLICY.md` (your rules)
- `backstage/HEALTH.md` (your tests)

**Why no install script:** Backstage = files + AI protocol. Just copy files, AI reads POLICY and executes.
