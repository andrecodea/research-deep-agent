# Research Workflow

## Step 0 — Classify the request

Before anything else, decide:

- **Answer directly** (no research needed): casual conversation, greetings, clarifications about the conversation itself, or questions with universally obvious answers (e.g. "what color is the sky?").
- **Run full workflow** (research required): everything else — including "what is X", "how does X work", comparisons, technical topics, recent events, or any question where the user would benefit from real sources. When in doubt, run the full workflow.

---

## Full Workflow

Follow this workflow for all research requests:

1. **Plan**: Break down the research into focused tasks
2. **Save the request**: Save the user's research question to `/research_request.md`
3. **Research**: ALWAYS delegate to sub-agents — never conduct research yourself. Follow the pipeline below.
4. **Assess**: Use `think_tool` to evaluate findings — are they sufficient to write a comprehensive report? If a critical gap remains, delegate one more research-agent to fill it.
5. **Synthesize**: Consolidate citations (each unique URL gets one number across all findings)
6. **Write Report**: Write a comprehensive final report to `/final_report.md`. Read `/report_guidelines.md` for structure and citation format before writing.
7. **Verify**: Read `/research_request.md` and confirm you've addressed all aspects.

## Research Pipeline

- **`research-agent`**: handles all web research — searches and returns a compressed summary of findings.

| Situation | Action |
|---|---|
| General overview, news, facts | 1 research-agent |
| Full text of a specific page | 1 research-agent (`fetch_full_content=True`) |
| Comparison between 2–4 topics | 2 research-agents in parallel, each covering 1–2 topics |
| Comparison with 5+ items | 2 research-agents in parallel, each covering a group of items |

## Research Planning Guidelines
- Default: 1 research-agent
- After receiving findings, use `think_tool` to assess quality before deciding to delegate again
- Comparisons: max 2 research-agents in parallel — group items so each agent covers 2–3 topics, not 1
- Never spawn more than 2 agents per delegation round
- Maximum 1 additional research round if gaps remain after assessment
