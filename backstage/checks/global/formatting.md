# Formatting Standard

All backstage files (CHECKS, ROADMAP, CHANGELOG, POLICY) must be both **human-readable** (clear, prompt-like, easy to follow) and **machine-readable** (easy for scripts or AI to parse and execute).

**How to format tests and checklists:**

1. **Each test/check should be a short, copy-pasteable code block** (one-liner or small block), with a plain-text explanation and pass/fail criteria immediately after.
2. **No large, monolithic scripts**—keep each check atomic and self-contained.
3. **No markdown formatting or prose inside code blocks.**
4. **All explanations, expected output, and pass criteria must be outside code blocks.**
5. **Backstage files should be easy for both humans and automation to read, extract, and run.**

_Example:_

```bash
python3.11 -c "import llama_index.core; import sentence_transformers"
```

Expected: No error, prints nothing.
Pass: ✅ Dependencies OK
