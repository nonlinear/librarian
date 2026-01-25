Prompt instructions file:

- When suggesting or writing code that should be tested, always show the terminal command as run_in_terminal.
- The agent must run terminal commands directly, read the feedback/output, and use it to automatically fix errors or improve code.
- Do not just output code blocks—execute code in the terminal and iterate until the result is correct.
- When asking the user to test results, always show the terminal command as run_in_terminal if it’s a terminal action.
- The agent’s workflow: write code → run in terminal → read results → fix or improve as needed, until the task is solved.
