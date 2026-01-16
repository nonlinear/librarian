# Copilot Instructions for the `notes` Repository

Welcome to the `notes` repository! This document provides essential guidelines for AI coding agents to be productive and aligned with the project's conventions. Please follow these instructions carefully to ensure consistency and maintainability.

## 🚨 DEBUG MODE

**When debugging or troubleshooting issues:**

1. **ALWAYS follow `.github/prompts/debug.prompt.md` instructions**
2. **STOP before making changes** - Think first, act second
3. **NO zigzagging** - One well-researched solution, not multiple attempts
4. **Research official docs** before proposing solutions
5. **Get user approval** before executing changes

**Triggers for Debug Mode:**

- User says "this is frustrating"
- Multiple failed attempts
- User asks to "debug" or "figure out why"
- Complex technical issues

## Project Overview

The `notes` repository is a collection of markdown files and related resources. It serves as a knowledge base for various topics, including AEM, AI tools, Docker, and more. The structure is flat, with most files located in the root directory, and a few subdirectories like `wiley/` for specific topics.

## Folder Structure and File Organization

| Folder        | Description                                                    | Shared?        |
| ------------- | -------------------------------------------------------------- | -------------- |
| `.github/`    | meta info                                                      | Other projects |
| `code/`       | technical notes                                                | Peach Debug    |
| `literature/` | reference materials                                            | No             |
| `personal/`   | Personal notes                                                 | No             |
| `rot/`        | Research, articles, PDFs (e.g., letterlocking, rot-01-content) | Yes, rot team  |
| `wiley/`      | Work related                                                   | No             |

## Repository Link

THis contains so many PII that we decided not to put it online.

### Markdown Formatting

- Use ordered lists for tasks and steps.
- Bold titles for emphasis.
- Maintain a consistent heading structure.

### Terminology

- Ensure terminology is consistent across all files.

### File Organization

- Place general documentation in the root directory.
- Use subdirectories for topic-specific files.

## Examples

### Markdown Formatting Example

```markdown
1. **Step One**: Description of step one.
2. **Step Two**: Description of step two.
```

### Terminology Replacement Example

Before:

```markdown
This feature is supported by ollama.
```

After:

```markdown
This feature is supported by gpt-oss.
```

## Dynamic Chatmode Indexing and Recommendations

To ensure chatmode guidance is always current:

- **Always index the contents of `.github/chatmodes/` at runtime.**
- For each chatmode file, extract the name and summary from its frontmatter or description.
- List and briefly describe all available chatmodes in the workspace.
- When prompted, analyze the current conversation and context to recommend the most suitable chatmode(s).
- Do not use a hardcoded list—changes to chatmode files (additions, removals, edits) are automatically reflected.

**Example prompt:**

> “Index all chatmodes in `.github/chatmodes/`, summarize their purpose and ideal use case, and recommend the best chatmode(s) for my current workflow based on recent conversation.”

## Terminal Command Execution (Always use run_in_terminal)

**Checklist for Home Assistant terminal operations:**

1. **Check if you are on Wi-Fi Verizon_7Y379B**
   - Only works at home.
2. **Check if local Syncthing is running**
   - Use: `ps aux | grep syncthing | grep -v grep`
3. **Edit Home Assistant files locally**
   - Example: configuration.yaml, automations.yaml, etc.
4. **Wait for Syncthing to sync changes to the server**
   - Confirm the folder is synced.
5. **Access the server via SSH if needed**
   - ssh nonlinear@192.168.1.152
6. **Restart Home Assistant to apply changes**
   - Use web interface, Portainer, or terminal.
7. **Quick references:**
   - Home Assistant address: http://192.168.1.152:8123
   - Access token: $HA_TOKEN
   - Always use `sudo` for admin commands
   - IP may change if server changes network
   - Always use the correct IP for API commands
   - Home Assistant is on [openmediavault](http://192.168.1.152/#/services/compose/files)
   - **Always execute terminal commands via “run_in_terminal” so the assistant detects the response automatically. Never copy/paste commands manually from chat. This applies to ALL terminal instructions, not just Home Assistant.**

---

## Terminal Command Execution

**ALWAYS use `run_in_terminal` tool for shell commands instead of suggesting them.**

When you need to execute a terminal command:

- ✅ **DO:** Use `run_in_terminal` to execute and capture output automatically
- ❌ **DON'T:** Suggest commands in code blocks for user to copy/paste
- ✅ **DO:** Read output and respond based on actual results
- ❌ **DON'T:** Assume command results without executing

**Example:**

```
User: "Is Docker running?"
Agent: [Uses run_in_terminal to check `docker ps`]
Agent: "Docker is running. Here are active containers: ..."
```

**Exceptions:** Only suggest commands (don't execute) when:

- User explicitly asks "what command should I run?"
- Command requires user interaction (password prompts, confirmations)
- Command has destructive side effects needing explicit user approval

## Skeptical mode

You are an expert who double checks things, you are skeptical and you do research. I am not always right. Neither are you, but we both strive for accuracy.
