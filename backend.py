import os
import json
import httpx
from fastapi.responses import StreamingResponse
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from  agent import workflow
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional,Literal
from dotenv import load_dotenv
import traceback
from agent import workflow,ArticleSection
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
    template_id: str

LENGTH_MAP = {
    "short": "Short (500–700 words)",
    "medium": "Medium (900–1200 words)",
    "long": "Long (1500–2000 words)",
    "deep-dive": "Deep-dive (2500+ words)"
}
async def generate_pdf(sections: list[ArticleSection], topic: str, template_id: str) -> str:
    api_key = os.getenv("APITEMPLATE_KEY")
    if not api_key:
        print("Missing APITEMPLATE_KEY")
        return None
    url = "https://api.apitemplate.io/v1/create"
    headers = {"X-API-KEY": api_key}
    payload = {
        "template_id": template_id,
        "data": {
            "newsletter_title": topic,
            "sections": sections # Passes your titles, text, and image_urls directly
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                result = response.json()
                return result.get("download_url")
            else:
                print(f"PDF Generation Failed: {response.text}")
                return None
        except Exception as e:
            print(f"PDF Request Error: {e}")
            return None
 
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
                print("RAW CHUNK:", chunk) 
                for node_name, node_output in chunk.items():
                    print(f"  NODE: {node_name}, KEYS: {list(node_output.keys())}") 
                    if node_name == "Image_gen" or node_name=="gen_image" :
                        sections = node_output.get("article_sections", [])
                        print(f"  SECTIONS COUNT: {len(sections)}") 
                        yield f"data: {json.dumps({'status': 'running', 'node': 'Rendering Layout'})}\n\n"
                        pdf_url = await generate_pdf(sections, request.topic, request.template_id)
                        
                        # Return everything back to your React app in one clean package
                        yield f"data: {json.dumps({'status': 'complete', 'sections': sections, 'pdf_url': pdf_url})}\n\n"
                    else:
                        yield f"data: {json.dumps({'status': 'running', 'node': node_name})}\n\n"
        except Exception as e:
            traceback.print_exc()
            # yield returns or streams the value one by one but return sends the value all at once
            # refer return and yield diff 
            yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")