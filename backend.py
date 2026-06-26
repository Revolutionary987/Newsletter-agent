import os
import io
import re
import json
import httpx
import markdown
import asyncio
import base64
import traceback
from weasyprint import HTML
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://newsletter-agent-jvvq.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class initial(BaseModel):
    topic: str
    audience: Optional[str] = "General Public"
    tone: Optional[str]     = "Professional & Objective"
    length: Literal["short", "medium", "long", "deep-dive"]
    key_points: Optional[str] = None

LENGTH_MAP = {
    "short":     "Short (500–700 words)",
    "medium":    "Medium (900–1200 words)",
    "long":      "Long (1500–2000 words)",
    "deep-dive": "Deep-dive (2500+ words)"
}

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


# ---------------------------------------------------------------------------
# MARKDOWN → HTML CONVERTER
# xhtml2pdf only understands HTML tags, not Markdown syntax.
# This runs AFTER LangGraph finishes — it never touches graph state.
# ---------------------------------------------------------------------------
def strip_markdown(text: str) -> str:
    if not text:
        return ""
    # Headers → bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'<strong>\1</strong>', text, flags=re.MULTILINE)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__',     r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_',   r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Bullet points → HTML list
    text = re.sub(r'^\s*[-*+]\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>(\s*<li>.*?</li>)*)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    # Paragraph breaks
    text = re.sub(r'\n{2,}', '</p><p>', text)
    text = f'<p>{text}</p>'
    return text


# ---------------------------------------------------------------------------
# IMAGE → BASE64 CONVERTER
# xhtml2pdf fails silently on external URLs due to User-Agent blocks.
# Embedding images as base64 data URIs is the only reliable approach.
# ---------------------------------------------------------------------------
async def fetch_image_as_base64(url: str) -> str:
    if not url:
        return ""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"},
                timeout=15.0,
                follow_redirects=True
            )
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                # Skip SVGs — xhtml2pdf can't render them
                if "svg" in content_type:
                    print(f"Skipping SVG image: {url}")
                    return ""
                b64 = base64.b64encode(resp.content).decode("utf-8")
                return f"data:{content_type};base64,{b64}"
            else:
                print(f"Image fetch failed ({resp.status_code}): {url}")
    except Exception as e:
        print(f"Image fetch error for {url}: {e}")
    return ""


# ---------------------------------------------------------------------------
# PDF RENDERER
# Uses xhtml2pdf (pisa) to convert final HTML → PDF bytes → base64 string.
# Runs in a thread via asyncio.to_thread so FastAPI event loop isn't blocked.
# ---------------------------------------------------------------------------
def create_pdf_base64_sync(html_content: str) -> str:
    try:
        from xhtml2pdf import pisa

        pdf_stream  = io.BytesIO()
        log_stream  = io.StringIO()

        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_stream,
            log=log_stream
        )

        # Print any CSS warnings xhtml2pdf emits
        warnings = log_stream.getvalue()
        if warnings.strip():
            print(f"xhtml2pdf warnings:\n{warnings}")

        if pisa_status.err:
            print(f"xhtml2pdf fatal error code: {pisa_status.err}")
            return ""

        pdf_bytes = pdf_stream.getvalue()
        pdf_stream.close()

        if not pdf_bytes:
            print("xhtml2pdf produced empty output")
            return ""

        return "data:application/pdf;base64," + base64.b64encode(pdf_bytes).decode("utf-8")

    except Exception as e:
        print(f"PDF generation exception: {e}")
        traceback.print_exc()
        return ""


async def generate_pdf(topic: str, article_sections: list) -> str:
    # 1. Download all images and convert to base64 in parallel
    image_tasks   = [fetch_image_as_base64(s.get("image_url", "")) for s in article_sections]
    base64_images = await asyncio.gather(*image_tasks)

    # 2. Build clean section dicts:
    #    - paragraph_text: Markdown → Actual HTML!
    clean_sections = []
    for i, section in enumerate(article_sections):
        raw_markdown = section.get("paragraph_text", "")
        
        # 💡 THE FIX: Convert Markdown to HTML, enabling tables and lists
        html_text = markdown.markdown(raw_markdown, extensions=['tables', 'fenced_code'])

        clean_sections.append({
            "section_title":  section.get("section_title",  ""),
            "paragraph_text": html_text,
            "image_url":      base64_images[i],
            "alt_text":       section.get("alt_text",       ""),
            "image_source":   section.get("image_source",   ""),
        })

    # 3. Render Jinja2 template with clean data
    template     = env.get_template("newsletter_preview.html")
    html_content = template.render(
        newsletter_title = topic,
        article_sections = clean_sections,
        date             = datetime.now().strftime("%B %Y")
    )

    # 4. Convert HTML → PDF in a background thread
    return await asyncio.to_thread(create_pdf_base64_sync, html_content)

# ---------------------------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/v1/generate")
async def agent_call(request: initial):
    # Import here to avoid circular import at module level
    from agent import workflow

    async def event_generator():
        try:
            initial_state = {
                "User_query":      request.topic,
                "target_audience": request.audience,
                "tone":            request.tone,
                "length":          LENGTH_MAP.get(request.length, "Medium (900–1200 words)"),
                "key_points":      request.key_points
            }

            final_sections = []

            async for chunk in workflow.astream(initial_state, stream_mode="updates"):
                print("RAW CHUNK:", chunk)
                for node_name, node_output in chunk.items():
                    print(f"  NODE: {node_name}, KEYS: {list(node_output.keys())}")

                    # Always track the latest article_sections from any node
                    if "article_sections" in node_output and node_output["article_sections"]:
                        final_sections = node_output["article_sections"]

                    # Keep frontend progress bar alive
                    yield f"data: {json.dumps({'status': 'running', 'node': node_name})}\n\n"

            # Graph finished — now render PDF
            if final_sections:
                yield f"data: {json.dumps({'status': 'running', 'node': 'Rendering PDF'})}\n\n"

                pdf_url = await generate_pdf(request.topic, final_sections)

                if pdf_url:
                    print("PDF generated successfully")
                else:
                    print("PDF generation failed — sending sections without PDF")

                # ✅ Always send 'complete' so frontend never hangs
                yield f"data: {json.dumps({'status': 'complete', 'sections': final_sections, 'pdf_url': pdf_url or ''})}\n\n"

            else:
                yield f"data: {json.dumps({'status': 'error', 'detail': 'Pipeline produced no sections'})}\n\n"

        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")