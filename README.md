# Librarian MCP

> A BYOB (Bring Your Own Books) local MCP so you can consult your library as you build your projects.

> All local (books, embedding models, database). Connect with your favorite AI provider and [ask away](#Usage)

---

| Possible uses               | Description                                                                                                                                                     |
| :-------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ⚖️&nbsp;**Compliance**      | Collect all compliance and regulation manuals to test a new idea the proper way                                                                                 |
| 🔧&nbsp;**Home&nbsp;fixes** | Move all your home devices and appliances' instruction manuals + warranties, ask troubleshooting questions                                                      |
| 🌱&nbsp;**Gardening**       | Permaculture, indigenous plant guides, water management books to redesign your garden with less trial-and-error                                                 |
| 🎸&nbsp;**New&nbsp;hobby**  | Wanna try a new hobby but have no idea of scope? Collect authoritative books in the field you wanna learn, and reduce your confusion by asking freely questions |
| 🎮&nbsp;**Game&nbsp;Dev**   | Design patterns, procedural generation, narrative theory—query mid-project to find exactly which book explained that algorithm                                  |
| 🌍&nbsp;**Academic**        | Anthropology, ethnography, linguistics—entire library indexed locally, works offline for weeks in remote locations                                              |
| 💼&nbsp;**Professional**    | Legal texts, industry whitepapers, case studies—cite exact sources during audits or client presentations                                                        |
| 💪&nbsp;**Fitness**         | Training programs, nutrition guides, sports science—get grounded advice without influence rabbit holes                                                          |

---

## Installation

1. **Clone this repo**
2. **[Install Python](https://www.python.org/downloads/)**: 3.11 or higher
3. **Run setup**: `bash ./engine/scripts/setup.sh`
   - Installs dependencies
   - Downloads embedding model: [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) (~130MB, 384-dim)
   - Saved in `engine/models/` (git-ignored)
4. **BYOB**: Bring Your Own Books
   - Create folders in `books/` (one per topic)
   - Add `.epub` and `.pdf` files
   - **Optional:** Use subfolders for grouping
     - Example: `books/cybersecurity/strategy/` → `cybersecurity_strategy`
5. **Generate metadata**: `python3.11 engine/scripts/generate_metadata.py`
6. **Build indices**:
   - Full: `python3.11 engine/scripts/indexer.py`
   - Per-topic: `python3.11 engine/scripts/reindex_topic.py <topic-id>`
7. **Test**: `python3.11 engine/scripts/research.py "AI ethics?" --topic ai`

graph TD
    A[books/] --> B[topic1/]
    A --> C[topic2/]
    A --> H[topic3/]

    B --> D[book1.epub]
    B --> E[book2.pdf]
    
    C --> F[book3.epub]
    C --> G[book4.pdf]
    
    H[topic3/<br/>root books] --> I[book5.epub]
    H --> J[subfolder1/<br/>topic3_subfolder1]
    H --> K[subfolder2/<br/>topic3_subfolder2]
    
    J --> L[book6.epub]
    K --> M[book7.epub]

---

## Usage via [openclaw](https://openclaw.ai)

openclaw skill install nonlinear/librarian

Use `research` trigger to consult Librarian on your AI conversations (see [clawdhub skill](https://clawhub.ai/nonlinear/librarian))

Make sure to **specify topic or book** in your question. Librarian will try to disambiguate based on metadata tags but the more focused the search, the better the results

**Example 1**: "`research` what does Bogdanov say about Mars in Molecular Red?"

**Example 2**: "`research` in my anthropocene books, what are the main critiques of geoengineering?"

**Example 3**: "`research` what tarot spreads work best for decision-making under uncertainty?"

> 👉 Without librarian skill your AI uses general knowledge. With it you get precise citations from your library

---


```mermaid
flowchart TB
    TRIGGER["🎤 Trigger + context"]:::ready
    TRIGGER --> METADATA["👷 Load metadata 1️⃣"]:::ready
    METADATA --> CHECK{"👷 Metadata exists?"}:::ready
    
    CHECK -->|No| ERROR["🎤 🤚 No metadata found:<br>Run librarian index 5️⃣"]:::ready
    CHECK -->|Yes| INFER{"🎤 Infer scope? 2️⃣"}:::ready
    
    INFER -->|confidence lower than 75%| CLARIFY["🎤 🤚 Say it again? 5️⃣"]:::ready
    INFER -->|confidence higher than 75%| BUILD["👷 Build command 3️⃣"]:::ready
    
    BUILD --> CHECK_SYSTEM{"⚙️ System working?"}:::ready
    
    CHECK_SYSTEM -->|No| BROKEN["🎤 🤚 System is broken 5️⃣"]:::ready
    CHECK_SYSTEM -->|Yes| EXEC["⚙️ Run python script with flags"]:::ready
    
    EXEC --> JSON["⚙️ Return JSON"]:::ready
    JSON --> CHECK_RESULTS{"👷 Results found?"}:::ready
    
    CHECK_RESULTS -->|No| EMPTY["🎤 🤚 No results found 5️⃣"]:::ready
    CHECK_RESULTS -->|Yes| FORMAT["🎤 Format output 4️⃣"]:::ready
    
    FORMAT --> RESPONSE["🎤 Librarian response"]:::ready

    classDef ready fill:#c8e6c9,stroke:#81c784,color:#2e7d32
```


---



> 🤖
>
> This project follows [backstage protocol](https://github.com/nonlinear/backstage) v0.3.4
>
> [README](README.md) 👏 [ROADMAP](backstage/ROADMAP.md) 👏 [CHANGELOG](backstage/CHANGELOG.md) 👏 checks: [local](backstage/checks/local/) <sup>4</sup>, [global](backstage/checks/global/) <sup>0</sup>
>
> 🤖



```mermaid
graph LR
    A[📋 v0.16.0 📦 Unified Indexing Pipeline | [notes](backstage/epic-notes/v0.16.0-unified-indexing.md)]
    B[📋 v0.17.0 🔀 Multi-Scope Queries | [notes](backstage/epic-notes/v0.17.0-multi-scope.md)]
    A --> B
    C[📋 v0.15.0 🎯 Skill as Protocol | [notes](backstage/epic-notes/v0.15.0-skill-protocol.md) | [translation](backstage/epic-notes/v0.15.0-skill-translation.md) | [best-practices](backstage/epic-notes/v0.15.0-best-practices.md)]
    B --> C
    D[📋 v0.18.0 🧪 Skill Validation & AI Testing | [notes](backstage/epic-notes/v0.18.0-skill-validation.md)]
    C --> D
    E[📋 v1.2.1 ✅ Research Enhancement | [notes](backstage/epic-notes/v1.2.1/)]
    D --> E
```



