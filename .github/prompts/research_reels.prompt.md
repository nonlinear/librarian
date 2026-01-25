# research_reels.prompt.md

Automatic suggestion of relevant reels based on your interests and current context.

## Instructions

- The system reads the file links/reels.md and suggests 3 to 5 reels related to the most frequent or relevant topics/tags in your context.
- Context may include: mental-health, AI, inspiration, recipes, etc.
- Suggestions are presented in the format:

```
- [TITLE](LINK) #tag1 #tag2 #tag3
```

## Example usage

1. The user asks for suggestions of reels about mental health.
2. The system reads links/reels.md, identifies posts with #mental-health, and suggests the most recent or diverse ones.
3. The system may vary suggestions according to the conversation context.

## Agent prompt:

Read the file links/reels.md and, considering the conversation context and requested topics/tags, suggest 3 to 5 relevant reels. Prioritize diversity of tags and relevance to the request.

---

Suggest now:
