from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.agent import build_agent
import json

agent = build_agent()

app = FastAPI(title="Deep Research Agent API")

class ResearchRequest(BaseModel):
    query: str

@app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    async def event_stream():
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": request.query}]},
            config={"configurable": {"thread_id": "api-1"}},
            stream_mode="values",
        ):

            messages = chunk.get("messages", [])
            if not messages:
                continue
                
            last = messages[-1]
            msg_type = last.__class__.__name__

            if msg_type == "AIMessage":
                for tool_call in getattr(last, "tool_calls", []):
                    data = json.dumps({"tool": tool_call["name"], "input": tool_call["args"]})
                    yield f"event: tool_call\ndata: {data}\n\n"
                
                if isinstance(last.content, str) and last.content:
                    data = json.dumps({"content": last.content})
                    yield f"event: message\ndata: {data}\n\n"
            
            elif msg_type == "ToolMessage":
                data = json.dumps({"tool": last.name, "content": last.content[:300]})
                yield f"event: tool_result\ndata: {data}\n\n"
            
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")