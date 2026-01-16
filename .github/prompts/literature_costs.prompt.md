# Literature RAG Usage & Value

**Purpose:** Show how useful your indexed books are - frequency, recency, and value to your work. Costs are secondary (mostly free with Gemini).

---

## Usage Examples

```
Show me usage for anthropocene folder
```

```
How much am I using Seeing Like a State?
```

```
What's my literature ROI this month?
```

```
Which books are giving me the most value?
```

---

## Instructions for AI

When user asks about literature usage/value:

1. **Identify target:**

   - Folder name (e.g., "anthropocene", "urbanism")
   - Book name (e.g., "Seeing Like a State", "How forests think")
   - Time period (e.g., "this month", "January")

2. **Run analysis:**

   ```python
   python3 code/view_detailed_costs.py
   ```

   Then filter output for requested item.

3. **Format response with value context:**

   - **How often used:** queries/day, total queries
   - **How recently:** last used, days since added
   - **Impact:** How many times it helped answer questions
   - Embedding cost (usually $0 with Gemini)
   - **Usefulness assessment:** Is this book earning its place?

4. **Interpretation:**
   - **High use (3+ queries/day):** Essential resource, great value
   - **Medium use (1-2 queries/day):** Solid contributor
   - **Low use (<1 query/day):** Either niche/specialized or underutilized
   - **Never used:** Consider why - wrong keywords? Needs different questions?
   - Suggest ways to get more value from underused books

---

## Response Format

````
📚 **[Book/Folder Name]**

📊 Usage:
• XX queries total (X.X per day)
• Used XX times in past month
• Last used: X days ago
• Added: YYYY-MM-DD

💡 Value: [Essential/Solid/Niche/Underused]
   [Insight: e.g., "Heavily consulted - core reference"
    or "Rarely used - try asking about [related topic]"
    or "Just added - give it time"]

💰 Cost: $X.XX (mostly $0 with Gemini)

## Alternative Command

User can also run directly:

```bash
python3 code/view_detailed_costs.py
````
