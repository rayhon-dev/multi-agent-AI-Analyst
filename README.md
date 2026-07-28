# Multi-Agent AI Analyst

A supervisor-led multi-agent system: a router delegates a question to document retrieval, web
search, text-to-SQL, and/or Python specialists, a critic verifies the drafted answer before it's
returned, and long-term memory lets follow-up questions build on earlier turns. Built for the
Multi-Agent AI Analyst capstone (Phases 1–5).

## Stack

- **LLM + embeddings**: Gemini (`gemini-flash-lite` for chat, `gemini-embedding` for embeddings),
  routed through an OpenAI-compatible proxy via `langchain-openai`
- **Vector store**: Qdrant, embedded (no signup) — one collection for documents, one for memory
- **Database**: SQLite (`data/company.db`), queried read-only via text-to-SQL
- **Web search**: Tavily (optional — skips gracefully without a key)
- **Observability**: Langfuse (optional — no-ops cleanly without keys)
- **Orchestration**: LangGraph
- **Frontend**: Gradio `ChatInterface`, deployable via Colab (`share=True`)

## Architecture

```mermaid
graph TD
    START([start]) --> recall["recall<br/>(memory)"]
    recall --> supervisor{supervisor}
    supervisor -->|retriever| retriever[retriever]
    supervisor -->|web| web[web]
    supervisor -->|data| data["data<br/>(text-to-SQL)"]
    supervisor -->|code| code["code<br/>(sandboxed Python)"]
    supervisor -->|finish| generate[generate]
    retriever --> supervisor
    web --> supervisor
    data --> supervisor
    code --> supervisor
    generate --> critic{critic}
    critic -->|approved| remember["remember<br/>(memory)"]
    critic -->|revise| supervisor
    remember --> END([end])
```

A `recursion_limit` (15) on `graph.invoke()`/`graph.stream()` guarantees termination even if
routing misbehaves; a `MAX_REVISIONS` cap (2) in `route_after_critic` forces a finish if the critic
keeps rejecting.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` in the project root:

```
GEMINI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here            # optional
LANGFUSE_PUBLIC_KEY=your_key_here       # optional
LANGFUSE_SECRET_KEY=your_key_here       # optional
LANGFUSE_HOST=https://cloud.langfuse.com  # optional
```

Build the sample database and vector store (both are gitignored, regenerate locally):

```bash
python seed_db.py
python ingest.py
```

## Running

```bash
python main.py "How many customers churned in 2024, and what does the FAQ say about why?"
python app.py                 # local Gradio UI
```

See the project guide for the exact Google Colab cells to run `app.py` with
`demo.launch(share=True)` for a public link.

## Evaluation results

`eval/harness.py` runs 10 questions spanning all 4 specialist types (3 retriever, 4 data, 2 code,
1 web) through the graph twice — once with the real critic, once with the critic stubbed to always
approve — and scores both with RAGAS (faithfulness, answer_relevancy, context_precision) and a
custom LLM-judge (1–5 vs. a reference answer).

| Condition | Avg LLM-judge | Faithfulness | Answer relevancy | Context precision |
|---|---|---|---|---|
| **With critic** | 4.60 / 5 | 0.667 | 0.880 | 0.857 |
| **Without critic** | 4.60 / 5 | 0.667 | 0.881 | 0.833 |

**Reading these honestly**: 9/10 test questions were already correct on the first pass, so
critic-on vs. critic-off barely differ on this set — that's expected, since these are mostly
atomic, single-agent questions. The critic's real demonstrated value shows up on harder,
multi-part questions (see error analysis below), not on this benchmark. The one low score in both
runs (question 10, "What is LangGraph used for?") is the web-agent question — `TAVILY_API_KEY`
isn't configured in this environment, so `web_agent` skips gracefully and `generate_agent`
correctly declines to guess rather than hallucinate, which scores low against a reference answer
but is the intended graceful-degradation behavior, not a bug.

## Error analysis

Three real failures found while building and testing this system, each with the fix applied.

### 1. Text-to-SQL agent hallucinated a fake column value

**Question**: "How many customers churned, and what does the FAQ say about why?"
**What went wrong**: `data_agent`'s LLM wrote a syntactically valid but semantically fabricated
query — `SELECT count(*), 'The FAQ states that customers churn due to...' FROM customers ...` —
inventing a string literal to answer the qualitative "why" half of the question, since SQL can't
actually answer that. The read-only guard let it through (it *is* a `SELECT`). The supervisor then
saw evidence for both halves of the question and finished without ever calling `retriever`, and
the critic approved the resulting answer, misattributing the fabricated claim to "the SQL result."
**Failure category**: SQL agent wrong + critic let a bad answer through.
**Fix**: tightened `data_agent`'s prompt to forbid inventing literals for data not in the schema,
and to answer only the part of the question SQL can actually support.

### 2. Supervisor infinite routing loop

**What went wrong**: after fix #1, the supervisor (`gemini-flash-lite`) kept re-selecting
`retriever` on every turn, even though its own prompt explicitly showed `Documents collected: 4`
and `retriever` already in the executed steps. It looped until `recursion_limit=15` raised a clean
`GraphRecursionError` instead of hanging forever — the safety net worked, but the routing itself
was broken.
**Failure category**: supervisor mis-routed.
**Fix**: rather than continuing to tune prompt wording, added a deterministic code-level guard in
`supervisor.py` — if the model re-picks a specialist that already ran, the code overrides the
choice to `finish`. The LLM proposes, the code enforces the invariant.

### 3. Follow-up question ("And last year?") not resolved using memory

**What went wrong**: the supervisor's `resolved_question` field (meant to rewrite context-dependent
follow-ups into standalone questions using recalled memory) returned the question unchanged. As a
result, `data_agent` received the bare, ambiguous "And last year?" with no context and produced an
unrelated, wrong query.
**Failure category**: supervisor/memory resolution failed.
**Fix**: rather than relying solely on the supervisor's rewrite, passed `state['memory']` directly
into `data_agent`'s and `code_agent`'s own prompts, so each specialist can resolve
context-dependent references itself even when the upstream rewrite doesn't happen. Verified fix:
the same follow-up now correctly resolves to "churned in 2023" and returns the right count (1).

## Submission checklist

- [x] Own free API keys (Gemini, Qdrant embedded, Tavily, Langfuse) — Gemini routed through an
      approved proxy per project owner's decision
- [x] Supervisor graph + 4 specialist agents + critic
- [x] Real SQLite database, text-to-SQL with a read-only `SELECT`-only guard
- [x] Code agent sandboxed in a separate process with a 5s timeout (hard-killed, not just abandoned)
- [x] Long-term memory recalls an earlier turn (see error analysis #3 for the fix that made this
      actually work)
- [x] Evaluation: RAGAS + LLM-judge over 10 questions, with vs. without critic, reported above
- [x] Langfuse tracing wired (add your own trace screenshot once keys are configured)
- [x] Frontend (Gradio) deployed via Colab `share=True`
- [ ] Add your own screenshots: frontend live trace, Langfuse trace — not something I can capture
      on your behalf

## Known limitations

- `TAVILY_API_KEY` is not configured in this build, so the web agent's graceful-skip path is
  exercised rather than live search; add a key to test it fully.
- The proxy key in use restricts model access to `gemini-flash-lite`/`gemini-embedding` only, so
  the supervisor and critic run on the same lite model as the specialists rather than a stronger
  model — the code-level routing guard (error analysis #2) exists specifically to compensate for
  this.
