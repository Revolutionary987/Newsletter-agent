import os
import json
from fastapi.responses import StreamingResponse
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from  agent import workflow
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional,Literal
from dotenv import load_dotenv
import traceback
load_dotenv()

app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://newsletter-agent-jvvq.onrender.com","http://localhost:3000","http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class initial(BaseModel):
    topic: str
    audience: Optional[str] = "General Public"
    tone: Optional[str] = "Professional"
    length:Literal["short", "medium", "long","deep-dive"]
    key_points:Optional[str]=None

LENGTH_MAP = {
    "short": "Short (500–700 words)",
    "medium": "Medium (900–1200 words)",
    "long": "Long (1500–2000 words)",
    "deep-dive": "Deep-dive (2500+ words)"
}

@app.post("/api/v1/generate")
async def agent_call(request: initial):
    async def event_generator():
        try:
            initial_state={
            "User_query": request.topic,
            "target_audience": request.audience,
            "tone": request.tone,
            "length": LENGTH_MAP.get(request.length, "Medium (900–1200 words)"),
            "key_points":request.key_points
        }
            # stream mode = updates means it returns a dictionary but for messages it returns a tuple
            # Add this temporarily to server.py to debug
            async for chunk in workflow.astream(initial_state, stream_mode="updates"):
                print("RAW CHUNK:", chunk)  # ← add this
                for node_name, node_output in chunk.items():
                    print(f"  NODE: {node_name}, KEYS: {list(node_output.keys())}")  # ← and this
                    if node_name == "Image_gen":
                        sections = node_output.get("article_sections", [])
                        print(f"  SECTIONS COUNT: {len(sections)}")  # ← and this
                        yield f"data: {json.dumps({'status': 'complete', 'sections': sections})}\n\n"
                    else:
                        yield f"data: {json.dumps({'status': 'running', 'node': node_name})}\n\n"
        except Exception as e:
            traceback.print_exc()
            # yield returns or streams the value one by one but return sends the value all at once
            # refer return and yield diff 
            yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")