# VALCO_RULES.md

## ValCo TSSS MVP V3.1 Core Workflow

```text
raw candidates up to 1,000
→ dedup
→ extraction/normalization
→ hard filter
→ eligible pool
→ deterministic scoring/ranking
→ Top10 recommended
→ analyst/user final3
→ export/audit
```

## Runtime LLM Rules

FreeLLMAPI is the only runtime inference gateway.

The application must not call provider LLM APIs directly, including but not limited to:

- `api.openai.com`
- `generativelanguage.googleapis.com`
- `api.groq.com`
- `api.anthropic.com`
- `api.mistral.ai`
- `api.cohere.com`

FreeLLMAPI may only:

- extract
- normalize
- classify
- draft note

FreeLLMAPI must not:

- select final3
- decide final valuation
- override deterministic filters
- bypass analyst/user decision
- bypass audit log requirements

## Candidate Pool Rules

- Raw pool cap is 1,000 candidates.
- Raw pool is only raw data, not eligible comparables.
- Dedup must run before hard filter.
- Hard filter must flag/reject, not silently drop.
- Eligible pool is the only source for Top10.
- Deterministic scoring produces Top10.
- Analyst/user selects final3.
- Override requires audit log.

## Missing Data Rule

If data is missing, incomplete, or uncertain:

- Do not fabricate.
- Do not infer unsupported values.
- Use null, TODO, safe fallback, or explicit insufficient_data status.
- Copy only fields already present from RawCandidate during extraction fallback.
