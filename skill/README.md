# Librarian Skill

**OpenClaw conversational interface for semantic book search**

---

## ⚠️ CRITICAL: This is a Companion Skill

**This skill CANNOT run standalone.**

You **MUST** install the full [Librarian project](https://github.com/nonlinear/librarian) first.

**Do NOT use `clawhub install librarian` alone** — it won't work.

---

## Installation (CORRECT Way)

### Step 1: Clone Librarian (Parent Project)

```bash
cd ~/Documents
git clone https://github.com/nonlinear/librarian
cd librarian
```

### Step 2: Setup Librarian Engine

```bash
# Install dependencies
bash engine/scripts/setup.sh

# Add your books to books/ folder
# Index your library
python3 engine/scripts/index_library.py
```

### Step 3: Activate Skill in OpenClaw

**Option A: Symlink (Recommended)**
```bash
ln -s ~/Documents/librarian/skill ~/.openclaw/skills/librarian
```

**Option B: OpenClaw Symlink (if supported)**
```bash
# Only works AFTER step 1+2 are complete
clawhub link ~/Documents/librarian/skill
```

### Verify Installation

```bash
ls -la ~/.openclaw/skills/librarian
# Should point to ~/Documents/librarian/skill

# Test wrapper
~/.openclaw/skills/librarian/librarian.sh "test query" "topic" "magick_chaos" 3
# Should return JSON results
```

---

## Why Can't I Just Install the Skill?

**Companion skills depend on parent projects:**

```
librarian/                 ← You need ALL of this
├── engine/                ← Search engine (research.py)
├── books/                 ← Your library
└── skill/                 ← Conversational wrapper ONLY
    ├── librarian.sh       → Points to ../engine/
    └── librarian.py       → Points to ../engine/
```

**If you only install `skill/`:**
- Wrappers point to `../engine/` → **doesn't exist**
- No books to search → **no data**
- Skill breaks ❌

**You need the full project for this skill to work.**

---

## Usage

**Trigger patterns:**
- "pesquisa por X"
- "research for X"
- "can you check it against (topic/book)"
- "pergunta ao I Ching sobre Y"
- "what does Graeber say about debt?"

**Examples:**

```
User: "What does chaos magick say about sigils?"
Kin: [loads metadata → infers topic → searches → formats response with citations]

User: "Procura no Graeber sobre debt"
Kin: [searches Debt book → returns excerpts with page numbers]
```

**How it works:**
1. AI detects trigger pattern
2. Loads metadata (`.library-index.json`)
3. Infers scope (topic or book)
4. Calls wrapper → `../engine/scripts/research.py`
5. Formats results with citations

**See [SKILL.md](SKILL.md) for full protocol documentation.**

---

## What This Skill Does

- **Conversational layer** for librarian engine
- **Trigger detection** (natural language → search)
- **Scope inference** (which book/topic to search)
- **Hard stops** (honest failures > invented answers)
- **Citation formatting** (emoji markers, sources)

**What it does NOT do:**
- Indexing (done by librarian engine)
- Search logic (done by research.py in parent)
- Book storage (done by librarian/books/ in parent)

**This skill = protocol wrapper. Engine = heavy lifting.**

---

## Links

- **Librarian project**: [https://github.com/nonlinear/librarian](https://github.com/nonlinear/librarian)
- **OpenClaw**: [https://openclaw.ai](https://openclaw.ai)
- **Skill marketplace**: [https://clawhub.com](https://clawhub.com)

---

## Version

**v0.15.0** - Skill as Protocol (2026-02-21)

**Status:** Companion skill (requires librarian parent)

**Future:** v0.21.0 will generalize (standalone skill with embedded indexing)

---

## Troubleshooting

**Error: "ERROR_EXECUTION_FAILED" or "research.py not found"**
- ✅ Did you clone the full librarian project?
- ✅ Did you run `engine/scripts/setup.sh`?
- ✅ Is your symlink pointing to the right place?

**Check:**
```bash
readlink ~/.openclaw/skills/librarian
# Should show: /Users/YOU/Documents/librarian/skill

ls ~/Documents/librarian/engine/scripts/research.py
# Should exist
```

**Still broken?** Open an issue: https://github.com/nonlinear/librarian/issues
