"""Manual integration test — runs the agent and reports latency, TTFT and token usage."""

import sys
import io
import json
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
RUNS_DIR = ROOT / "tests" / "runs"
RUNS_DIR.mkdir(exist_ok=True)
WORKSPACE_DIR = ROOT / "workspace"

def _clean_workspace():
    """Remove agent-generated files from workspace before each run."""
    for f in ("research_request.md", "final_report.md"):
        p = WORKSPACE_DIR / f
        if p.exists():
            p.unlink()

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class UsageTracker(BaseCallbackHandler):
    """Captures token usage from every LLM call in the graph."""

    def __init__(self):
        self.calls: list[dict] = []

    def on_llm_end(self, response: LLMResult, **kwargs):
        for generations in response.generations:
            for gen in generations:
                usage = getattr(gen.message, "usage_metadata", None) if hasattr(gen, "message") else None
                if usage:
                    n = len(self.calls) + 1
                    inp = usage.get("input_tokens", 0)
                    out = usage.get("output_tokens", 0)
                    print(f"  [LLM #{n}] in={inp:,}  out={out:,}  total={inp+out:,}")
                    self.calls.append({"input_tokens": inp, "output_tokens": out})

    @property
    def total_input(self) -> int:
        return sum(c["input_tokens"] for c in self.calls)

    @property
    def total_output(self) -> int:
        return sum(c["output_tokens"] for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output


def run(query: str):
    from backend.agent import build_agent

    _clean_workspace()
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    tracker = UsageTracker()
    agent = build_agent()

    first_chunk_time: float | None = None
    ttft_ms: float | None = None
    start = time.perf_counter()
    final_content: str = ""

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            config={
                "configurable": {"thread_id": "test-1"},
                "callbacks": [tracker],
            },
            stream_mode="values",
        ):
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
                ttft_ms = (first_chunk_time - start) * 1000
                print(f"[TTFT] {ttft_ms:.0f}ms\n")

            messages = chunk.get("messages", [])
            if messages:
                last = messages[-1]
                content = getattr(last, "content", None)
                if content and isinstance(content, str):
                    final_content = content
                    print(content, end="\r")

    except Exception as e:
        print(f"[ERROR] {e}")
        raise
    finally:
        end = time.perf_counter()
        total_ms = (end - start) * 1000

        metrics = {
            "latency_ms": round(total_ms),
            "ttft_ms": round(ttft_ms) if ttft_ms else None,
            "input_tokens": tracker.total_input,
            "output_tokens": tracker.total_output,
            "total_tokens": tracker.total_tokens,
            "llm_calls": len(tracker.calls),
        }

        print(f"\n\n{'='*60}")
        print(f"[LATENCY]       {total_ms / 1000:.1f}s ({total_ms:.0f}ms)")
        print(f"[TTFT]          {ttft_ms:.0f}ms" if ttft_ms else "[TTFT]          N/A")
        print(f"[INPUT TOKENS]  {metrics['input_tokens']}")
        print(f"[OUTPUT TOKENS] {metrics['output_tokens']}")
        print(f"[TOTAL TOKENS]  {metrics['total_tokens']}")
        print(f"[LLM CALLS]     {metrics['llm_calls']}")
        print(f"{'='*60}\n")

        _save_run(query, final_content, metrics)


def _save_run(query: str, result: str, metrics: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = query[:40].replace(" ", "_").replace("?", "").replace("/", "-")
    filename = RUNS_DIR / f"{timestamp}_{slug}.json"

    run_data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "result": result,
        "metrics": metrics,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(run_data, f, ensure_ascii=False, indent=2)

    print(f"[RUN SAVED] {filename.relative_to(ROOT)}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "o que é context engineering para agentes de IA?"
    run(query)
