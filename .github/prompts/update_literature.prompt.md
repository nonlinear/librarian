# Update Literature Prompt

When triggered, this prompt will:

1. Run the following command in the background:
   /opt/homebrew/bin/python3.11 /Users/nfrota/Documents/literature/scripts/update_literature.py

2. Wait for the process to finish.
3. Return a concise report listing any newly indexed books, or "No new books to index" if nothing was added.
4. Also include the total cost of the operation (even if zero).

Use this to keep your literature index up to date with minimal manual effort.
