import os
import io
import base64
import httpx
from dotenv import load_dotenv
load_dotenv()
import json
import re
from langchain_core.output_parsers import PydanticOutputParser
from typing import Literal,Annotated,Optional,List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
import asyncio
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage,SystemMessage,ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel,Field
from huggingface_hub import AsyncInferenceClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from deep_research_agent import workflow

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id="google/gemma-4-26B-A4B-it",
#     task="image-text-to-text",
#     huggingfacehub_api_token=os.getenv("HF_TOKEN")
# )

vision_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini", 
    temperature=0.1,
    max_retries=2
)

llm= ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4.1-nano",
    temperature=0.1,
    max_tokens=2048,
    max_retries=3
)

# vision_llm = ChatHuggingFace(llm=hf_endpoint)

class ArticleSection(TypedDict):
    section_title: str
    paragraph_text: str
    image_url: Optional[str] 
    alt_text: Optional[str]

class BaseState(TypedDict):
    User_query:str
    revised_query:str
    length:str
    final_article:str
    target_audience: str 
    tone: str
    Grading:bool
    Feedback:str
    key_points: str
    cleaned_content:str
    images:list[dict]
    alt_text: str
    article_sections: List[ArticleSection]
    Text_Grading: bool
    Text_Feedback: str
    Image_Grading: bool
    Image_Feedback: str
    revision_count: int

LENGTH_INSTRUCTIONS = {
    "Short (500–700 words)": (
        "Write a SHORT newsletter totalling 500–700 words across all sections combined. "
        "Use 3–4 sections. Every sentence must earn its place — no padding, no recap."
    ),
    "Medium (900–1200 words)": (
        "Write a MEDIUM newsletter totalling 900–1200 words across all sections combined. "
        "Use 4–5 sections with solid paragraph depth per section."
    ),
    "Long (1500–2000 words)": (
        "Write a LONG newsletter totalling 1500–2000 words across all sections combined. "
        "Use 5–7 sections. Include at least one data grid or timeline table in Markdown."
    ),
    "Deep-dive (2500+ words)": (
        "Write a DEEP-DIVE newsletter of 2500+ words across all sections combined. "
        "Use 6–8 sections with exhaustive technical depth, multiple data tables, "
        "and a Mermaid flowchart for any pipeline or architecture described."
    ),
}

AUDIENCE_STYLE = {
    "General Public": (
        "Write for curious, intelligent non-specialists. "
        "Define every technical term the first time it appears. "
        "Use real-world analogies to ground abstract concepts. "
        "Short sentences. Active voice. Never assume prior domain knowledge."
    ),
    "Tech Enthusiasts": (
        "Assume the reader is comfortable with software architecture, APIs, and benchmarks. "
        "Lead with technical mechanics before business context. "
        "Include specific version numbers, model names, and performance figures where available. "
        "Readers want depth — never simplify a concept that doesn't need simplifying."
    ),
    "Executives": (
        "Open every section with the business implication, not the technical detail. "
        "Frame data as decisions: what does this mean for budget, risk, or competitive position? "
        "Use tight, scannable prose with clear headers. "
        "One insight per paragraph. No jargon without a one-sentence plain-English translation."
    ),
    "Students": (
        "Teach from the ground up. "
        "Start each section with a clear learning objective stated as a question. "
        "Progress from core concept → real-world example → broader implication. "
        "Include a 'Key takeaway' sentence at the end of each section. "
        "An encouraging, intellectually curious tone throughout."
    ),
    "Investors": (
        "Lead with market size, TAM, growth rate, and competitive moat. "
        "Frame every technical development as a financial signal. "
        "Include valuation context, funding rounds, or revenue data where available. "
        "Explicitly name risk factors alongside opportunities. "
        "Think: what would a venture partner or fund manager need before writing a check?"
    ),
    "Researchers": (
        "Write with academic precision. "
        "Every empirical claim must reference its source citation inline. "
        "Acknowledge methodological limitations and conflicting findings — do not smooth them over. "
        "Avoid superlatives and marketing framing. "
        "Prefer passive constructions where they are standard in the field."
    ),
}

TONE_INSTRUCTIONS = {
    "Professional & Objective": (
        "Neutral, measured, authoritative. "
        "Present multiple perspectives where they exist. "
        "No editorialising. No exclamation marks. "
        "The reader should trust this as a reliable briefing document."
    ),
    "Inspiring": (
        "Forward-looking, energising, optimistic without being naive. "
        "Frame every challenge as a solvable problem. "
        "End each major section with a sentence that points toward possibility, not just current state. "
        "Verbs should be active and strong."
    ),
    "Conversational": (
        "Write like a brilliant friend who happens to be an expert. "
        "Contractions are fine. Rhetorical questions welcome. "
        "Vary sentence length deliberately — short punchy sentences after complex ones. "
        "Never sound like a press release."
    ),
    "Analytical": (
        "Logic-first. Every paragraph should follow a claim → evidence → implication structure. "
        "Quantify wherever possible. "
        "Flag uncertainty explicitly ('data is limited here', 'this is one interpretation'). "
        "No flourish — precision over style."
    ),
    "Educational": (
        "The primary goal is understanding, not just information transfer. "
        "Use the 'explain then exemplify' pattern throughout. "
        "Bold the single most important concept in each section. "
        "Summaries and 'what this means in practice' callouts are expected."
    ),
    "Bold & Opinionated": (
        "Take a clear, defensible position and hold it. "
        "Do not hedge with 'some argue' or 'it could be said'. "
        "Back opinions with cited evidence, but don't shy from the conclusion. "
        "The reader should finish feeling they've heard a sharp point of view, not a survey."
    ),
}
RESEARCH_DEPTH = {
    "Short (500–700 words)": (
        "Focus on high-signal, top-level data. Retrieve the 2-3 most impactful current statistics and a clear overarching narrative. "
        "Do not hunt for exhaustive historical timelines, edge cases, or deep technical specs. Keep the search tight and focused on immediate relevance."
    ),
    "Medium (900–1200 words)": (
        "Gather a balanced mix of macro context and specific supporting data. Target at least two distinct sub-topics or perspectives. "
        "Retrieve recent benchmarks, named examples, and at least one concrete case study to ground the concepts."
    ),
    "Long (1500–2000 words)": (
        "Hunt for comprehensive, multi-layered data. Retrieve historical context, comparative industry benchmarks, and multiple case studies. "
        "Specifically seek out structured data points, timelines, and contrasting viewpoints that can be used to build data tables."
    ),
    "Deep-dive (2500+ words)": (
        "Conduct an exhaustive, granular search. Retrieve raw datasets, architectural or pipeline specifics, edge cases, expert quotes, and deep methodological details. "
        "Hunt for niche sub-topics, regulatory impacts, and future projections. The agent must return enough raw material to sustain intense technical analysis."
    ),
}
async def query_rewrite(state:BaseState)->dict:
    """
    Expands the raw topic into a multi-angle research directive.
    Translates the final article's Tone, Audience, and Length into 
    specific data-gathering instructions for the web search agent.
    """
    system_prompt = """You are the Lead Research Director for a premium global publication. Your job is to take a raw user topic and write a precise, multi-angle Research Directive for an autonomous web-search agent.

    The agent can only find what you tell it to look for. Your directive dictates the quality of the final article. 

    INSTRUCTIONS FOR SYNTHESIZING THE PROFILES:
    - Use the target 'Length/Depth' to tell the agent exactly how broad, granular, and exhaustive its search must be.
    - Use the target 'Audience' and 'Tone' to tell the agent WHICH sources to trust and WHAT KIND of data to prioritize (e.g., if the audience is Investors, tell the agent to hunt for financial reports and market sizing; if the tone is Analytical, demand raw numbers over opinion pieces).

    WRITE A SINGLE DENSE PARAGRAPH that covers all of the following:
    1. The core technical or subject-matter angles to investigate.
    2. The specific data types to retrieve (statistics, dollar figures, benchmarks, named entities, dates).
    3. The exact types of sources to prioritize based on the audience/tone profiles.
    4. The mandatory key points (if any) as non-negotiable investigation targets.
    5. Two or three exact search phrases in quotes that will surface high-quality 2025–2026 data.

    Output ONLY the directive paragraph. No headers, no bullet points, no preamble."""
    audience_key = state.get("target_audience", "General Public")
    tone_key = state.get("tone", "Professional & Objective")
    length_key = state.get("length", "Medium (900–1200 words)")
    audience_desc = AUDIENCE_STYLE.get(audience_key, AUDIENCE_STYLE["General Public"])
    tone_desc = TONE_INSTRUCTIONS.get(tone_key, TONE_INSTRUCTIONS["Professional & Objective"])
    depth_desc = RESEARCH_DEPTH.get(length_key, RESEARCH_DEPTH["Medium (900–1200 words)"])

    human_prompt = """Raw topic: {user_query}

    TARGET AUDIENCE & TONE (Translate these writing goals into what data/sources to hunt for):
    - Audience: {audience_desc}
    - Tone: {tone_desc}

    RESEARCH DEPTH REQUIRED:
    {depth_desc}

    Key points that MUST be covered: {key_points}

    Write the Research Directive now."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])
    
    response = await (prompt | llm).ainvoke({
        "user_query":    state["User_query"],
        "audience_desc": audience_desc,
        "tone_desc":     tone_desc,
        "depth_desc":    depth_desc,
        "key_points":    state.get("key_points") or "None specified — cover the topic comprehensively.",
    })
    
    return {"revised_query": response.content}

class DraftOutput(BaseModel):
    sections:List[ArticleSection]

class Gradee(BaseModel):
    is_pass: Annotated[bool, Field(
        description=(
            "Set to True if the draft is broadly factual with no OBVIOUS invented statistics, "
            "wrong names, or fabricated quotes, AND has correct H2 section headers. "
            "Set to False ONLY for clear, serious violations. Minor paraphrasing is acceptable."
        )
    )]
    feedback: Annotated[str, Field(
        description=(
            "If is_pass is True, write exactly 'Approved'. "
            "If False, provide a numbered list of only the most critical corrections needed. "
            "Maximum 3 items. Be specific about what exact text needs changing."
        )
    )]
    
async def check_hal(state:BaseState):
    cleaned_content=state["cleaned_content"]
    sections = state["article_sections"]
    # final_article=state["final_article"]
    compiled_draft = "\n\n".join([f"## {s['section_title']}\n{s['paragraph_text']}" for s in sections])
    audience_key = state.get("target_audience", "General Public")
    tone_key = state.get("tone", "Professional & Objective")
    length_key = state.get("length", "Medium (900–1200 words)")
    
    audience_desc = AUDIENCE_STYLE.get(audience_key, AUDIENCE_STYLE["General Public"])
    tone_desc = TONE_INSTRUCTIONS.get(tone_key, TONE_INSTRUCTIONS["Professional & Objective"])
    length_desc = LENGTH_INSTRUCTIONS.get(length_key, LENGTH_INSTRUCTIONS["Medium (900–1200 words)"])
    system_prompt = """
    You are the Managing Editor. Evaluate the draft on three criteria.

    CRITERION 1 — FACTUAL GROUNDING:
    Check for OBVIOUS hallucinations only — invented statistics, wrong company names, 
    fabricated quotes. Minor paraphrasing of facts from the blueprint is ACCEPTABLE.
    Do NOT fail a draft for rewording a fact that is clearly derived from the blueprint.

    CRITERION 2 — TONE & AUDIENCE ALIGNMENT:
    Does the vocabulary roughly match the audience profile? 
    Minor tone deviations are acceptable. Only fail on complete mismatches.

    CRITERION 3 — LENGTH & STRUCTURE:
    - Does it have the roughly correct number of sections?
    - Does it use H2 headers?
    - Does it avoid obvious AI filler phrases like "In conclusion" or "It is important to note"?

    IMPORTANT: Be a reasonable editor, not a perfectionist. If the draft is 
    publication-ready with minor flaws, APPROVE IT. Only reject drafts with 
    serious factual errors or completely wrong structure.

    Set is_pass=True unless there are CLEAR, SPECIFIC violations.
    """
    human_prompt="""
    RESEARCH BLUEPRINT (Source of Truth):
    {cleaned_content}

    TARGET AUDIENCE PROFILE:
    {audience_desc}

    TONE PROFILE:
    {tone_desc}

    LENGTH & STRUCTURE CONSTRAINTS:
    {length_desc}

    SUBMITTED DRAFT:
    {compiled_draft}

    Evaluate the draft against all three criteria now
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    structured_llm=llm.with_structured_output(Gradee,method="json_schema", include_raw=False)
    flow=prompt|structured_llm
    response=await flow.ainvoke({"cleaned_content":cleaned_content,"compiled_draft":compiled_draft,"audience_desc":audience_desc,"tone_desc":tone_desc,"length_desc":length_desc})
    return {
        # to bypass warnings
        "Grading": (response.is_pass), 
        "Feedback": (response.feedback)
        }

class SmartImageDirectives(BaseModel):
    pexels_query: Annotated[str, Field(
        description=(
            "A 2–3 word literal, physical search query for a real stock photo. "
            "Strictly nouns and objects. No abstract words like 'AI' or 'future'. "
            "Examples: 'boardroom meeting', 'warehouse automation', 'laboratory drone'."
        )
    )]
    flux_prompt: Annotated[str, Field(
        description=(
            "A detailed, highly photorealistic, cinematic prompt for FLUX.1. "
            "Describe a real physical scene with lighting, mood, camera framing, and textures. "
            "Example: 'Candid wide-angle photograph of an advanced automated robotic warehouse floor, "
            "soft geometric amber overhead lighting, realistic metallic surfaces, volumetric dust motes, shot on 35mm lens, photorealistic.'"
        )
    )]
    alt_text: Annotated[str, Field(
        description="A plain 5–8 word description of what the visual shows for accessibility."
    )]

async def logic_gen_image(section_item,client,editor_llm,system_prompt,revision_directive):
        if isinstance(section_item, str):
            section_dict = {
                "section_title": "Section",
                "paragraph_text": section_item,
                "image_url": None,
                "alt_text": None
            }
        else:
            section_dict = section_item
        paragraph = section_dict.get("paragraph_text", "")
        human_prompt = "**ARTICLE SECTION TO ILLUSTRATE:**\n\n{paragraph}"
            
        prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", human_prompt)
            ])
            
        flow = prompt | editor_llm
        llm_result = await flow.ainvoke({
            "paragraph": paragraph, 
            "revision_directive": revision_directive
        }) 

        image_url = ""
        source_used = "None"
        pexels_key = os.getenv("PEXELS_API_KEY")
        if pexels_key:
            try:
                p_url = "https://api.pexels.com/v1/search"
                p_params = {"query": llm_result.pexels_query, "per_page": 1, "orientation": "landscape"}
                p_headers = {"Authorization": pexels_key}
                    
                response = await client.get(p_url, params=p_params, headers=p_headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("photos") and len(data["photos"]) > 0:
                        image_url = data["photos"][0]["src"]["landscape"]
                        source_used = "Pexels"
            except Exception as e:
                print(f"Pexels Error: {e}")

        if not image_url:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                hf_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
                hf_headers = {"Authorization": f"Bearer {hf_token}"}
                hf_payload = {"inputs": llm_result.flux_prompt}
                for attempt in range(3):
                    try:
                        hf_res = await client.post(hf_url, headers=hf_headers, json=hf_payload, timeout=60.0)
                            
                        if hf_res.status_code == 503:
                            print(f"HF Model warming up. Waiting 15s... (Attempt {attempt+1}/3)")
                            await asyncio.sleep(15)
                            continue
                                
                        if hf_res.status_code == 200:
                            b64_img = base64.b64encode(hf_res.content).decode('utf-8')
                            image_url = f"data:image/jpeg;base64,{b64_img}"
                            source_used = "Flux AI"
                            break
                    except Exception as e:
                        print(f"Flux Error: {e}")
                        break
        return {
        **section_dict,
        "image_url": image_url,
        "alt_text": llm_result.alt_text,
        "image_source": source_used
    }

async def gen_image(state: BaseState):
    previous_feedback = state.get("Image_Feedback", "")
    sections = state.get("article_sections", [])
    updated_sections = []
    
    revision_directive = ""
    if previous_feedback and previous_feedback not in ("Perfect", "Approved"):
        revision_directive = f"""
        **CRITICAL REVISION DIRECTIVE:**
        Your previous image generation assets were REJECTED by the editor for the following reason:
        {previous_feedback}
        
        You MUST change your approach completely for both the pexels_query and flux_prompt to fix this error.
        """
    system_prompt = """You are the Lead Photo Editor for a premium business and tech publication.
    Your job is to read a specific section of an article draft and generate two distinct image-retrieval directives to illustrate that exact section.
    
    Because our system uses a smart waterfall pipeline, you must provide inputs for two completely different engines:

    1. FOR THE PEXELS ENGINE (Stock Photo Search):
    - Generate an ultra-focused 2-3 word literal search query.
    - Translate abstract concepts into physical objects (e.g., instead of 'cybersecurity', use 'locked laptop' or 'server rack').
    - Never include words like 'AI', 'data', 'future', 'technology'.

    2. FOR THE FLUX ENGINE (AI Image Generation):
    - Generate a highly descriptive, cinematic prompt.
    - Enforce an editorial style: demand high realism, specific camera lenses (e.g., 'shot on 35mm lens'), professional lighting, and crisp details.
    - Avoid cartoonish or standard 3D-rendered styling. It must look like high-end photojournalism.

    {revision_directive}
    """
    editor_llm = llm.with_structured_output(SmartImageDirectives)

    async with httpx.AsyncClient() as client:
        tasks = [logic_gen_image(s, client, editor_llm, system_prompt, revision_directive) for s in state["article_sections"]]
        updated_sections = await asyncio.gather(*tasks)
        # to bypass warnings

    return {"article_sections": list(updated_sections)}
   
def check_grade(state:BaseState)->Literal["Image_gen","Subgraph"]:
    if state["Grading"]==True:
        return "Image_gen"
    elif state.get("revision_count", 0) >= 3:
        print("Max revisions reached! Forcing the graph to move forward to Image Generation.")
        return "Image_gen"
    else:
        return "Subgraph"
    
class FinalPublicationGrade(BaseModel):
    text_approved: bool = Field(description="True if the layout, formatting, and markdown structures are flawless.")
    text_feedback: str = Field(description="Feedback regarding layout or syntax fixes. Write 'Perfect' if approved.")
    image_approved: bool = Field(description="True if the generated image matches the contextual theme of its section perfectly.")
    image_feedback: str = Field(description="Highly specific feedback for the photo editor explaining why an image doesn't align with the text. Write 'Perfect' if approved.")

async def final_checking(state: BaseState) -> dict:
    sections = state.get("article_sections", [])
    current_outer_loop = state.get("revision_count", 0) + 1
    system_prompt = """You are the Editor-in-Chief of a high-end, premium global tech and business publication. Your final task is to run a rigorous multi-modal audit on the compiled document layout.

    Analyze the layout across three non-negotiable criteria:

    CRITERION 1: LANGUAGE QUALITY & TONE INTEGRITY
    - Audit the prose for professional readability, clean markdown headers (H2 for sections), and total elimination of lazy AI phrases.
    - Check that the information flows organically between sections without disjointed transitions or structural blanks.

    CRITERION 2: VISUAL QUALITY & AESTHETIC STANDARDS
    - Inspect the visual elements for professional artistic execution.
    - Reject assets that suffer from rendering artifacts, extreme blurriness, distortion, or cheap vector clip-art styles. Every visual must look like premium editorial design.

    CRITERION 3: CROSS-MODAL SYNCHRONIZATION (THE MATCH)
    - Evaluate the absolute coordination between the image and the text section it is bound to.
    - The visual assets must represent the concrete nouns, actions, or underlying data trends described in the paragraph. A high-quality text paired with an irrelevant or generic stock asset must fail.

    Populate the FinalPublicationGrade structure with rigorous precision based on these rules."""

    message_content = [{"type": "text", "text": "Begin premium publication layout audit now:"}]
    
    for sec in sections:
        message_content.append({
            "type": "text", 
            "text": f"## {sec.get('section_title', '')}\n{sec.get('paragraph_text', '')}"
        })

        if sec.get("image_url"):
            message_content.append({
                "type": "image_url", 
                "image_url": {"url": sec["image_url"]}
            })

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message_content)
    ]

    try:
        structured_vision_llm = vision_llm.with_structured_output(FinalPublicationGrade)
        result = await structured_vision_llm.ainvoke(messages)
        
        return {
            "Text_Grading": result.text_approved,
            "Text_Feedback": result.text_feedback,
            "Image_Grading": result.image_approved,
            "Image_Feedback": result.image_feedback,
            "revision_count": current_outer_loop
        }
    except Exception as e:
        print(f"Layout Vision Review Node Error: {e}")
        # Fail-safe state update: route back into the generator systems to maintain stability
        return {
            "Text_Grading": False,
            "Text_Feedback": "Pipeline execution warning: Evaluation framework timed out. Re-verifying text composition rules.",
            "Image_Grading": False,
            "Image_Feedback": "Pipeline execution warning: Asset validation layer exception. Force-regenerating visual layout blocks.",
            "revision_count": current_outer_loop
        }

def check(state: BaseState) -> Literal["Subgraph", "Image_gen", "__end__"]:
    outer_loops = state.get("revision_count", 0)
    if state.get("Text_Grading", False) and state.get("Image_Grading", False):
        print("✅ VISION CHECK PASSED: Newsletter is perfect!")
        return "__end__"
        
    if outer_loops >= 3:
        print(f" MASTER ESCAPE HATCH TRIGGERED: Hit max outer loops ({outer_loops}). Forcing completion to save costs.")
        return "__end__"
        
    # 3. If under the limit, route back to fix the specific problem
    if not state.get("Text_Grading", False):
        print(f" Vision rejected text. Rerouting to Subgraph. (Attempt {outer_loops}/3)")
        return "Subgraph"  
    elif not state.get("Image_Grading", False):
        print(f"Vision rejected images. Rerouting to Image_gen. (Attempt {outer_loops}/3)")
        return "Image_gen"
    
graph=StateGraph(BaseState)
graph.add_node("Rewrite_query",query_rewrite)
graph.add_node("Subgraph",workflow)
graph.add_node("Hallucination_check",check_hal)
graph.add_node("Image_gen",gen_image)
graph.add_node("Final_check",final_checking)

graph.add_edge(START,"Rewrite_query")
graph.add_edge("Rewrite_query","Subgraph")
graph.add_edge("Subgraph","Hallucination_check")
graph.add_conditional_edges("Hallucination_check",check_grade)
graph.add_edge("Image_gen","Final_check")
graph.add_conditional_edges("Final_check",check)

workflow=graph.compile()