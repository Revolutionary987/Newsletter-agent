import os
import json
import httpx
import asyncio
import datetime
from fastapi.responses import StreamingResponse
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from  agent import workflow
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional,Literal
from dotenv import load_dotenv
import traceback
from agent import workflow,ArticleSection
import pdfkit
import base64
from jinja2 import Environment, FileSystemLoader
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
env = Environment(loader=FileSystemLoader("templates"))

def create_pdf_base64_sync(topic: str, article_sections: list) -> str:
    """
    Synchronous function that actually renders the HTML and calls pdfkit.
    """
    try:
        # Load your exact template file 
        template = env.get_template("newsletter_preview.html")
        
        # Inject dynamic variables (Topic, Sections, and Current Date)
        current_month = datetime.now().strftime("%B %Y")
        html_content = template.render(
            newsletter_title=topic,
            article_sections=article_sections,
            date=current_month
        )
        
        # Set borderless A4 PDF options
        options = {
            'page-size': 'A4',
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
            'encoding': "UTF-8"
        }
        
        # Compile HTML into raw PDF binary bytes
        # False makes sure that the pdf is not stored in harddrive and will be compiled in server's RAM
        pdf_bytes = pdfkit.from_string(html_content, False, options=options)
        
        # Convert binary bytes to Base64 text string for frontend delivery
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        # Tells the browser that this isn't just text. This is a Base64 encoded PDF file. I should download it."
        return f"data:application/pdf;base64,{base64_pdf}"
        
    except Exception as e:
        print(f"PDF Compilation Error: {e}")
        return None
async def generate_newsletter_base64(topic: str, article_sections: list) -> str:
    """
    Async wrapper so pdfkit doesn't freeze the FastAPI event loop.
    """
    # Creating async code by allocating threads 
    return await asyncio.to_thread(create_pdf_base64_sync, topic, article_sections)

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
                        pdf_url = await generate_newsletter_base64(request.topic,sections)
                        
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