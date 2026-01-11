# Recommend Chatmode

Review the current conversation and identify where the user is having problems.

Always index all files in `.github/chatmodes/` using direct filesystem access, ignoring `.gitignore` and git tracking.
List all available chatmodes in `.github/chatmodes/`.

Output ONLY the most relevant chatmodes for the current issues, using this format:

"Based on our conversation, I'd suggest to switch to:

- **AGENT1**: helps more with XYZ
- **AGENT2**: useful for ZYZ"

Do not add any other explanation or context. Remove the `.chatmode.md` suffix from agent names and display them in bold.
