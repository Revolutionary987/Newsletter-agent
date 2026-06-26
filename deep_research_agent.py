import os
import asyncio
import json
import re
from dotenv import load_dotenv
from typing import List,Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
from langchain.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
import ast
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
load_dotenv()

from langchain_openai import ChatOpenAI

# 1. Instantiate the individual models clearly
llama_main = ChatGroq(  # base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("GROQ_API_NEW"),
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_retries=1 
)
qwen3_coder = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="qwen/qwen3-coder:free",
    temperature=0.1,
    max_retries=1,
    max_tokens=8000
)
gpt_mini= ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=2048,
    max_retries=3
)
qwen_backup = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="qwen/qwen3-next-80b-a3b-instruct:free",
    temperature=0.1,
    max_retries=1
)
# qwen_llm=ChatNVIDIA(
#     base_url="https://integrate.api.nvidia.com/v1",
#     model="qwen/qwen2.5-coder-32b-instruct",
#     api_key=os.getenv("NVIDIA_API_KEY"), 
#     temperature=0.1,
#     top_p=0.1,
#     max_tokens=1024,
# )
gpt_oss_backup = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openai/gpt-oss-20b:free",
    temperature=0.1
)
research_llm = llama_main.with_fallbacks([gpt_mini,qwen_backup, qwen3_coder,gpt_oss_backup])

tavily=TavilySearch(
    max_results=4,               
    search_depth="advanced", 
    include_raw_content=False
)
# compressor_llm = ChatOpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     model="nvidia/nemotron-3-super-120b-a12b:free", 
#     temperature=0.0
# )
compressor_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini", 
    temperature=0.1
)
groq_llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=4096
)
gpt_writer = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini", 
    temperature=0.3,
    max_tokens=8000
)
writer_llm = groq_llm.with_fallbacks([gpt_writer,qwen3_coder])
class ArticleSection(TypedDict):
    section_title: str
    paragraph_text: str
    image_subject: Optional[str]
    image_url: Optional[str] 
    alt_text: Optional[str]

class DraftOutput(BaseModel):
    sections: List[ArticleSection]

class Research(TypedDict):
    content:str
    revised_query:str
    target_audience: str
    tone: str
    cleaned_content:str
    final_article:str
    Feedback:str
    article_sections: List[ArticleSection]
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


async def deep_research(state:Research)->dict:
    """
    Autonomous ReAct agent wrapper. It executes multiple search/critique loops internally and returns a clean markdown dossier/content string.
    """
    audience = state.get("target_audience", "General Public")
    length = state.get("length", "Medium (900–1200 words)")

    researcher_prompt =f"""You are an elite Autonomous Deep Research Agent. Your only job is to use the search tool repeatedly to build an exhaustive, cited dossier strictly tailored for an audience of: {audience}. You must NOT answer from memory.

    MANDATORY EXECUTION PROTOCOL — follow these phases in order:

    PHASE 1 — TARGETED BREADTH SEARCH (minimum 3 distinct queries)
    Break the user's topic into its core dimensions based on what matters most to <audience_rules>{audience}</audience_rules>. 
    - For Executives/Investors: Search for market economic impact, ROI, risks, and competitive landscape.
    - For Tech Enthusiasts/Researchers: Search for underlying technical bottlenecks, raw physics/science specs, and benchmarks.
    - For General/Students: Search for historical context, foundational mechanics, and real-world impact.
    Run distinct, highly optimized search queries to establish a wide informational baseline across these targeted angles.

    PHASE 2 — THE KNOWLEDGE-GAP CRITIQUE
    After every tool execution, review the retrieved raw text. You must explicitly identify what is MISSING to write a comprehensive {length} article for this specific audience. Ask yourself:
    - "What specific metrics, percentages, or dollar amounts are absent?"
    - "Is this data up-to-date for the current year (2026), or am I looking at stale historical trends?"
    - "Have I fully satisfied the specific interests of the <audience_rules>{audience}</audience_rules>?"
    If gaps exist, immediately formulate a hyper-targeted follow-up query. Do not repeat the exact same search query twice. If a search yields poor results, you must change your keywords.

    PHASE 3 — VERIFICATION & DISCREPANCY RESOLUTION
    If you encounter conflicting viewpoints, varying statistics, or disputed timelines across different sources, do not guess. Treat this as an engineering bug. Execute a targeted verification search specifically querying the contradiction to determine the consensus. If you cannot find hard data to resolve a gap after multiple searches, explicitly state: 'Data unavailable for [metric/fact]'. Never hallucinate data.
    PHASE 4 — DYNAMIC DOSSIER SYNTHESIS
    Only stop searching when you have exhausted all knowledge gaps or completed at least 3 distinct iterative search cycles. Compile your findings into an enterprise-grade Research Dossier.
    
    CRITICAL COMPILATION INSTRUCTIONS:
    1. Do NOT use a generic or fixed template. Organize your headers and data logically based exclusively on what the <audience_rules>{audience}</audience_rules> needs to know.
    2. Every single fact, metric, and claim MUST end with its source citation [URL] or [Source Name].
    3. Include a "SOURCE REPOSITORY" section at the end: a numbered list of all URLs used, mapped as citations [1], [2] next to facts in the text.
    4. Completely ignore vague marketing fluff or PR buzzwords. If it isn't a hard fact, discard it.
    5.Completely ignore vague marketing fluff or PR buzzwords. If it isn't a hard fact, discard it.
    """

    deep_research_agent = create_agent(
    model=research_llm,
    tools=[tavily],
    system_prompt=researcher_prompt,
    name="deep_research_subgraph"
)
    response=await deep_research_agent.ainvoke({
        "messages":[{"role":"user","content":state["revised_query"]}]
    })
    compiled_content = response["messages"][-1].content
    return {"content":compiled_content}

async def context_node(state:Research)->str:
    """
    Ingests the massive raw content from deep_research node and uses Nemotron's 1-Million 
    token context window to distill it into a strict markdown outline.
    """
    audience = state.get("target_audience", "General Public")
    tone     = state.get("tone", "Professional & Objective")
    length   = state.get("length", "Medium (900–1200 words)")

    system_prompt = """You are an elite Data Compression Engine. Your job is to distill a messy research dossier into a dense, structured outline that a downstream writer will use to draft a highly targeted newsletter.

    CRITICAL DIRECTIVE:
    You must dynamically structure this outline to serve the specific target audience. Do NOT use a generic template.
    - If the audience is 'Executives' or 'Investors', prioritize and group ROI, market risks, financial metrics, and timelines.
    - If the audience is 'Tech Enthusiasts' or 'Researchers', prioritize deep architecture, system bottlenecks, and benchmarks.
    - If the audience is 'Students' or 'General Public', group the data chronologically or by core foundational concepts.

    STRICT RULES:
    1. Zero Fluff: Delete all narrative filler, transitions, introductions, and conclusions. You are building a data skeleton.
    2. Fact Preservation: Retain 100% of verifiable facts, numbers, dates, proper nouns, and URLs.
    3. Citation Integrity: Keep every citation bracket (e.g., [1], [2]) exactly as found attached to its specific claim. Never merge citations.
    4. Formatting: Use H3 (###) for major topic clusters, and standard bullet points for the exact extracted facts.

    VISUAL SUBJECTS REQUIREMENT (MANDATORY):
    At the very end of your output, you MUST provide a visual mapping for the photo editor. 
    For each major H3 topic cluster you created, write one line in this exact format:
    VISUAL: [2–4 word literal, photographable subject, e.g., "server rack data centre", "surgeon operating room"]"""

    human_prompt = """TARGET AUDIENCE: {target_audience}
    TARGET TONE: {tone}
    EXPECTED LENGTH: {length}

    Compress the following research dossier accordingly:

    {raw_data}"""

    prompt=ChatPromptTemplate.from_messages([
        ("system",system_prompt),
        ("human",human_prompt)
    ])
    flow=prompt|compressor_llm
    response=await flow.ainvoke({"target_audience": audience,"tone": tone,"length": length,"raw_data": state["content"]})
    return {"cleaned_content":response.content}

async def gen_content(state: Research) -> dict:
    previous_feedback = state.get("Feedback", "")
    audience          = state.get("target_audience", "General Public")
    tone              = state.get("tone", "Professional & Objective")
    length            = state.get("length", "Medium (900–1200 words)")
    
    current_count = state.get("revision_count", 0)
    
    audience_style     = AUDIENCE_STYLE.get(audience, AUDIENCE_STYLE["General Public"])
    tone_instruction   = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["Professional & Objective"])
    length_instruction = LENGTH_INSTRUCTIONS.get(length, LENGTH_INSTRUCTIONS["Medium (900–1200 words)"])

    is_revision = bool(previous_feedback and previous_feedback not in ("Perfect", "Approved.", "Approved"))

    if is_revision:
        # NEW: The model must see its previous mistake to fix it!
        current_draft = json.dumps(state.get("article_sections", []), indent=2)
        
        system_prompt = """You are a Master Copyeditor. Your previous draft was REJECTED by the Managing Editor. 
        Your ONLY priority right now is to take the previous draft and refactor it to fix the exact formatting and structural violations listed by the editor.
        
        CRITICAL CORE RULES:
        - You must strictly adjust the length to fit: {length_instruction}
        - You must fix all markdown layout errors (e.g., Use H2 headers for sections).
        - Strip out any generic AI transition padding or non-factual statements.
        Do not write a brand new article; fix the current one."""
        
        human_prompt = """<editor_rejection_notes>
        {previous_feedback}
        </editor_rejection_notes>

        <current_imperfect_sections>
        {current_draft}
        </current_imperfect_sections>

        Apply these editorial corrections directly into the structured output format now."""
        
    else:
        system_prompt = """You are the Chief Editor. Ingest the data blueprint and synthesize it into a premium newsletter matching these operational vectors:

        1. ADAPTIVE TONE & STYLE:
        - AUDIENCE DIRECTIVE: {audience_style}
        - TONE DIRECTIVE: {tone_instruction}
        - No generic AI transitions, introductions, or conversational padding.

        2. STRUCTURAL MANDATE:
        - {length_instruction}
        - Use clean Markdown heading hierarchy (H2 for sections) inside the text content.

        3. VISUAL MAPPING:
        - Provide a concrete, photographable real-world description for the image_subject field of every section."""

        human_prompt = """[TARGET FOCUS AREA]: {user_query}
        [COMPRESSED DATA BLUEPRINT]: {cleaned_content}
        
        Generate the structured content output now."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])
    
    structured_writer = writer_llm.with_structured_output(DraftOutput)
    chain = prompt | structured_writer
    
    try:
        invoke_inputs = {
            "user_query": state.get("revised_query", "User Topic"),
            "cleaned_content": state.get("cleaned_content", ""),
            "audience_style": audience_style,
            "tone_instruction": tone_instruction,
            "length_instruction": length_instruction
        }
        if is_revision:
            invoke_inputs["previous_feedback"] = previous_feedback
            invoke_inputs["current_draft"] = current_draft
        parsed_data= await chain.ainvoke(invoke_inputs)
        if isinstance(parsed_data, dict):
            raw_sections = parsed_data.get("sections", [])
        else:
            raw_sections = parsed_data.sections
            
        sections_list = []
        for s in raw_sections:
            is_dict = isinstance(s, dict)
            sections_list.append({
                "section_title": s.get("section_title", "Untitled Section") if is_dict else getattr(s, "section_title", "Untitled Section"),
                "paragraph_text": s.get("paragraph_text", "") if is_dict else getattr(s, "paragraph_text", ""),
                "image_subject": s.get("image_subject", None) if is_dict else getattr(s, "image_subject", None),
                "image_url": s.get("image_url", None) if is_dict else getattr(s, "image_url", None),
                "alt_text": s.get("alt_text", None) if is_dict else getattr(s, "alt_text", None)
            })
        
        # NEW: Increment the counter and clear feedback
        return {
            "article_sections": sections_list, 
            "Feedback": "",
            "revision_count": current_count + 1
        }

    except Exception as e:
        print(f"Content Generation Error: {e}")
        raise ValueError(f"Generation failed: {e}")
    
def check_subgraph(state:Research):
    feedback=state.get("Feedback", "")
    if not feedback: 
        return "Deep_research"
    if feedback not in ("Perfect","Approved.","Approved"):
        return "Content_generation"
    else:
        return END

subgraph=StateGraph(Research)
subgraph.add_node("Deep_research",deep_research)
subgraph.add_node("Compressor",context_node)
subgraph.add_node("Content_generation",gen_content)

subgraph.add_conditional_edges(START,check_subgraph)
subgraph.add_edge("Deep_research","Compressor")
subgraph.add_edge("Compressor","Content_generation")
subgraph.add_edge("Content_generation",END)

workflow=subgraph.compile()