---
category: Meta & Recommendations
---

# Recommend Tools

Analyze the current conversation and workflow to recommend the most relevant tools from `.github/` directories.

## Process

1. **Index all available tools** (ignoring `.gitignore` and git tracking):

   - Chatmodes in `.github/chatmodes/`
   - Prompts in `.github/prompts/`
   - Scripts in `.github/scripts/`

2. **Analyze current context**:

   - Review conversation history and identify user challenges
   - Detect repeating, boring, or error-prone tasks
   - Identify workflow friction points

3. **Generate recommendations** for:
   - **Chatmodes** - Specialized AI modes for specific workflows
   - **Prompts** - Task-specific prompt templates
   - **Scripts** - Automation scripts for common tasks
   - **Automations** - VS Code tasks, keybindings, extensions, integrations
   - **Learning** - Workflows, tools, and best practices to improve productivity

## Output Format

Show only strictly relevant recommendations. If nothing is truly useful, it's OK to return an empty list.

### Chatmodes

Based on our conversation, I'd suggest switching to:

- **Design Engineer**: helps with Figma-to-code workflows
- **Project Manager**: useful for planning and tracking

### Prompts

You might find these prompts helpful:

- **/literature**: search indexed books using RAG
- **/terminal**: terminal command assistance

### Scripts

Consider running:

- **sync_literature.py** - Update book database for RAG searches
- **sync_comics.py** - Organize comic library

### Automations & Learning

- 🧠 Learn advanced SCSS features for better modularity ([get started](https://sass-lang.com/guide))
- 🔎 Investigate extensions for live preview of Markdown and Hugo
- ✅ Add a task to run Hugo and open preview automatically
- ✅ Create keybindings to expand/shrink selection in JSON

## Guidelines

- Be concise and actionable
- Remove file extensions (`.chatmode.md`, `.prompt.md`, `.py`, etc.) from names
- Display chatmode and prompt names in bold
- Use emojis for automation categories: 🧠 Learn, 🔎 Investigate, ✅ Implement
- Only show recommendations when you're confident they're relevant and useful
- Tailor suggestions to current session and user habits
