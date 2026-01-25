---
category: workspace
---

Preview a file in Hugo's Simple Browser:

- Only works if file is in `content/` folder
- If user mentions a specific file from `content/`, use that file instead of the currently focused file
- First, split editor to the right using `workbench.action.splitEditorRight` command
- Then open Simple Browser at `http://localhost:1313/{path}` where `{path}` is the file path without `content/` prefix and without file extension (`.md` or `.html`)
- Always add trailing `/` to the URL

Use `run_vscode_command` for splitting and `open_simple_browser` tool for opening the preview.
