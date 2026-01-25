# Summarize Recent Changes (List Only, with GitHub Links)

You WILL analyze the git history for the entire repository.

You MUST:

- By default, list only commits made by other users (exclude the current user).
- If the user explicitly requests, list only the current user's commits (use "You updated...", "You reverted...", etc.).
- Group changes by day, but ONLY list days where changes actually occurred (e.g., "3 days ago", "7 days ago").
- For each commit, include:
  - The author’s name
  - A brief summary of the commit message
  - The main files or features affected
  - For each file or feature, show the diff link on the object itself: verb [object](https://github.com/[owner]/[repo]/commit/[commit-hash]#diff-[file-sha])
- At the end, add a "Last month" section with a very brief, high-level summary of overall changes (not every detail, just a general interpretation).
- If there were no significant changes from other users in the last month, output: "No significant changes from other users."

You MUST output only the list. Do NOT include any explanation, commentary, or extra text.

Example output:
3 days ago:
Alice updated the [README](https://github.com/owner/repo/commit/abc123#diff-xyz789).

7 days ago:
Bob added new tests for [`dataService.ts`](https://github.com/owner/repo/commit/def456#diff-uvw123).

Last month:
Major improvements to authentication, several bug fixes, and new features added to the dashboard.
