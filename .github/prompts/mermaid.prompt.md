# Mermaid Syntax: Do & Don't

**Do:**

- Use only alphanumeric IDs for nodes (A, B, C, node1, etc.)
- Use valid node shapes: (Text), [Text], {Text}, ([Text])
- Use plain text in node labels (avoid special characters)
- Keep node labels short and clear

**Don't:**

- Don't use special characters in node IDs (no spaces, dashes, punctuation, etc.)
- Don't use double quotes (") inside node labels
- Don't mix different bracket types together (e.g., {([Text])})
- Don't use emojis or symbols in node IDs or labels
- Don't use reserved Mermaid keywords as node IDs

**Examples of invalid node IDs/labels:**

- `A-1` (dash not allowed)
- `A B` (space not allowed)
- `A!` (punctuation not allowed)
- `A("Click here")` (double quotes not allowed)

# Mermaid Syntax Tips (AI Assistant)

When generating Mermaid diagrams, always follow these rules to avoid common parse errors:

1. **Node Syntax**: Use only valid node shapes:
   - Round: `(Text)`
   - Square: `[Text]`
   - Diamond: `{Text}`
   - Subroutine: `([Text])`
   - Do NOT mix different bracket types together (e.g., `{([Text])}` is invalid).
2. **No Quotes in Node Labels**: Avoid using double quotes (`"`) inside node labels. Use plain text or single quotes if needed.
3. **No Special Characters in Node IDs**: Use simple alphanumeric IDs (A, B, C, etc.).
4. **Example (Valid):**
   ```mermaid
   flowchart TD
     A(User clicks file search) --> B{Reader has path extension?}
     B -- No --> C[Open file, ignoring search]
     B -- Yes --> D{Is string found in file?}
     D -- No --> C
     D -- Yes, one entry --> E[Open file at search point, highlighted]
     D -- Yes, multiple entries --> F[Open file with search modal and results to choose]
   ```
5. **Example (Also Valid):**
   ```mermaid
   flowchart TD
     A([User clicks ...]) --> B{...}
   ```
   (This is a subroutine node and is valid.)

If you encounter Mermaid parse errors, check por bracket misuse, double quotes in node labels, or invalid node syntax.
