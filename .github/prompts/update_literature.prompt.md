# Update Literature Prompt

When triggered, this prompt will:

1. Run the following command in the background:
   /opt/homebrew/bin/python3.11 /Users/nfrota/Documents/literature/scripts/update_literature.py

2. Wait for the process to finish.
3. Return a concise report listing any newly indexed books, or "No new books to index" if nothing was added.
4. Also include the total cost of the operation (even if zero).


If any .epub files are corrupted or unreadable, list them at the end of the report under a section "Ignored EPUBs (corrupted or invalid):". These files should be skipped automatically so the operation continues for all other books. This helps you identify and remove or fix problematic files without breaking the indexing process.

Always ensure that a single bad .epub never interrupts the indexing of the rest.
