import os
import asyncio
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

load_dotenv()

research_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.1
)
tavily=TavilySearch(
    max_results=4,               
    search_depth="advanced", 
    include_raw_content=True
)
compressor_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="nvidia/nemotron-3-super-120b-a12b:free", 
    temperature=0.0 
)
writer_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openai/gpt-oss-120b:free", 
    temperature=0.4 
)
class ArticleSection(TypedDict):
    section_title: str
    paragraph_text: str
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

async def deep_research(state:Research)->str:
    """
    Autonomous ReAct agent wrapper. It executes multiple search/critique loops internally and returns a clean markdown dossier/content string.
    """
    researcher_prompt = SystemMessage(content="""You are an elite Autonomous Deep Research Agent operating with the cognitive depth, systematic thoroughness, and architectural precision of Gemini Deep Research and Perplexity Pro.

    Your goal is to completely map out the user's topic by uncovering granular engineering metrics, verified timelines, raw technical data, and industry benchmarks. 

    To prevent shallow analysis and mimic Gemini's deep crawling capabilities, you MUST execute the following 4-Phase Operational Protocol:

    =========================================
    PHASE 1: MULTI-ANGLE BREADTH EXPLORATION
    =========================================
    Do not just search for the literal user query. Break the topic down into its core architectural dimensions (e.g., market economic impact, underlying technical bottlenecks, competitive landscape, raw physics/science specs). Execute distinct, highly optimized search queries to establish a wide informational baseline across all these angles.

    =========================================
    PHASE 2: THE KNOWLEDGE-GAP CRITIQUE
    =========================================
    After every tool execution, review the retrieved raw text. You must explicitly identify what is MISSING. Ask yourself:
    - "What specific metrics, percentages, or dollar amounts are absent?"
    - "Is this data up-to-date for the current year (2026), or am I looking at stale historical trends?"
    - "Are there adjacent technologies, secondary players, or downstream dependencies I haven't searched for yet?"
    If gaps exist, immediately formulate a hyper-targeted follow-up query specifically designed to hunt down those missing variables.

    =========================================
    PHASE 3: VERIFICATION & DISCREPANCY RESOLUTION
    =========================================
    If you encounter conflicting viewpoints, varying statistics, or disputed timelines across different sources, do not guess. Treat this as an engineering bug. Execute a targeted verification search specifically querying the contradiction (e.g., "Source A claims X, Source B claims Y comparison") to determine the consensus or verify the premium source.

    =========================================
    PHASE 4: EXHAUSTIVE DOSSIER SYNTHESIS
    =========================================
    Only stop searching when you have exhausted all knowledge gaps or completed at least 3 distinct iterative search cycles. Compile your findings into an enterprise-grade technical Research Dossier using the following structure:

    1. EXECUTIVE SUMMARY: High-level overview of the topic's current state in 2026.
    2. CORE ARCHITECTURAL & TECHNICAL BREAKDOWN: Deep-dive mechanics, physics, software architectures, or structural elements.
    3. QUANTIFIABLE METRICS & DATA BENCHMARKS: An itemized, bulleted list of raw statistics, cost efficiencies, throughput speeds, percentages, and performance metrics.
    4. TIMELINE & RECENT DEVELOPMENTS (UP TO 2026): A chronological breakdown of major milestones and recent real-world implementations.
    5. SOURCE REPOSITORY: A numbered list of raw source URLs extracted from your tool outputs, mapped as citations [1], [2] next to facts in the text.

    CRITICAL INSTRUCTION: Completely ignore vague marketing fluff, PR buzzwords, or introductory summaries. If a search result doesn't contain hard data or concrete facts, discard it and search again.""")

    deep_research_agent = create_agent(
    model=research_llm,
    tools=[tavily],
    state_modifier=researcher_prompt,
    name="deep_research_subgraph"
)
    response=deep_research_agent.invoke({
        "messages":[{"role":"user","content":state["revised_query"]}]
    })
    compiled_content = response["messages"][-1].content
    return {"content":compiled_content}

async def context_node(state:Research)->str:
    """
    Ingests the massive raw content from deep_research node and uses Nemotron's 1-Million 
    token context window to distill it into a strict markdown outline.
    """
    system_prompt = SystemMessage(content="""You are an elite, enterprise-grade Data Compression Engine operating with the structural rigidity, cross-modal retention, and architectural precision of an industrial knowledge-graph compiler.

    Your sole objective is to ingest an exhaustive, messy, long-form research dossier and compress it into a highly dense, hyper-structured technical outline. You must optimize for 100% factual retention while eliminating 100% of narrative fluff.

    To achieve maximum data density and leverage your massive context capacity, you MUST execute the following 4-Phase Operational Protocol:

    <operational_protocol>
    PHASE 1: NARRATIVE LIQUIDATION & FILTERING
    Analyze the raw dossier token-by-token. Instantly identify and permanently delete all introductory text, conversational filler, marketing transitions, adjectives, and hand-waving conclusions. Retain ONLY hard nouns, verifiable numbers, functional architectures, and exact technical variables.

    PHASE 2: CROSS-REFERENCE METRIC MAPPING
    Extract every single quantifiable datapoint and group them into strict technical vectors. You must systematically isolate:
    - System Architectures & Tech Stacks (frameworks, models, nodes, specs)
    - Hard Financials & Dollar Amounts (costs, market capitalizations, ROI, budgets)
    - Performance & Throughput Metrics (speeds, benchmarks, latency, energy densities, percentages)
    - Chronological Timelines (verified milestones up to the current year, 2026)

    PHASE 3: UNBROKEN CITATION COHERENCY
    You are strictly forbidden from separating a fact from its source. Every single metric, architecture, or timeline event you extract MUST maintain its exact original source citation bracket (e.g., [1], [2], [3]) directly appended to the end of the bullet point. If a fact lacks an explicit citation from the dossier, group it under a global structural parent note.

    PHASE 4: HIGH-DENSITY MARKDOWN GENERATION
    Output your final synthesis using a rigid hierarchical outline. Use Markdown nested bullet points and bold key variables. Adhere to this exact structure:

    ### 1. CORE TECHNICAL & ARCHITECTURAL SPECS
    * **[Component/Stack Element]**: Detailed specification string or structural feature. [Citation]
    * **[Bottleneck/Dependency]**: Core friction point or underlying engineering limitation. [Citation]

    ### 2. QUANTIFIABLE DATA & PERFORMANCE BENCHMARKS
    * **[Metric Name]**: Exact raw statistics, percentage shifts, or numerical throughput values. [Citation]
    * **[Financial/Cost Variable]**: Capital expenditures, processing costs, or asset evaluations. [Citation]

    ### 3. VERIFIED TIMELINE & LOGISTICAL DEVELOPMENTS (UP TO 2026)
    * **[YYYY-MM / Quarter]**: Specific real-world deployment milestone or physical implementation update. [Citation]
    </operational_protocol>
                                       
    CRITICAL CONSTRAINT: Do not write an introduction. Do not write a summary or conclusion. Do not include any conversational transitions (e.g., "Here is the compressed data..."). Output starts directly with the first markdown header.""")
    human_prompt="Here is the raw scraped dossier:\n\n{raw_data}"
    prompt=ChatPromptTemplate.from_messages(
        ("system",system_prompt),
        ("human",human_prompt)
    )
    flow=prompt|compressor_llm
    response=await flow.ainvoke({"raw_data": state["content"]})
    return {"cleaned_content":response.content}

async def gen_content(state:Research)->str:
    previous_feedback=state.get("Feedback")
    system_prompt="""You are the Chief Editor and Lead Writer for a premium publication. Your objective is to ingest a hyper-dense, cited data blueprint and synthesize it into a highly engaging, custom-tailored newsletter.

    To achieve maximum performance, you MUST execute your response according to these Operational Vectors:

    <dynamic_parameters>
    - TARGET AUDIENCE: {target_audience}
    - DESIRED TONE: {tone}
    </dynamic_parameters>

    <operational_vectors>
    1. ADAPTIVE TONE & STYLE
    - You must strictly calibrate your vocabulary, complexity, and narrative style to perfectly match the {target_audience}. 
    - Ensure the writing embodies a {tone} tone throughout the entire piece.
    - Never use generic AI transitions, introductory boilerplate, or conversational padding (e.g., "In this section...", "Let's dive into...").
    - Bold critical variables and core concepts to make the document highly scannable.

    2. LOGICAL FLOWCHART COMPILATION (MERMAID.JS)
    - Carefully evaluate if the technical data contains a multi-step pipeline, user-flow, or system architecture.
    - If it does, you MUST construct a highly precise, syntax-perfect Mermaid.js diagram to visually map out that architecture.
    - Follow strict Mermaid syntax conventions. Ensure all nodes have explicit textual descriptors.

    3. SACROSANCT DATA PROVENANCE (CITATIONS)
    - You are strictly prohibited from dropping source citations. Every single bracketed citation (e.g., [1], [2]) present in the input blueprint must be cleanly migrated into your final synthesis.
    - Append the citation bracket directly to the specific metric, feature, or claim it validates.

    4. ADAPTIVE STRUCTURAL LAYOUT
    Your output must maintain a logical flow suited for the {target_audience}, but MUST include:
    - # [A Catchy, High-Impact Headline]
    - ## [Context / The Big Picture]
    - ## [Core Mechanics & Frameworks] (Include Mermaid diagram here if applicable)
    - ## [Empirical Data & Milestones] (Include cleanly formatted Markdown data grids or itemized breakdowns of cited metrics)
    
    5. ZERO CONVERSATIONAL LEAKAGE
    - Do not include greetings, sign-offs, or meta-commentary.
    - Begin printing text immediately at the main H1 Markdown title (#) and stop instantly after the final paragraph.
    </operational_vectors>
    """
    revision_directive = ""
    if previous_feedback and previous_feedback != "Perfect":
        revision_directive = f"""
        **CRITICAL REVISION DIRECTIVE:**
        Your previous draft was REJECTED by the Managing Editor for the following reasons:
        <feedback>
        {previous_feedback}
        </feedback>
        
        You MUST completely rewrite the draft, ensuring every single piece of feedback is addressed and fixed.
        """

    human_prompt = """
    <runtime_execution_manifest>
        [TARGET USER FOCUS AREA]:
        {user_query}

        [COMPRESSED DATA BLUEPRINT (CITED)]:
        {cleaned_content}

        {revised_directive}
        COMPILATION MANDATE:
        Execute your system prompt protocols perfectly. Adapt the blueprint data into pristine paragraphs tailored to the specified audience and tone. Do not leak any system text or XML brackets into your final output.
    </runtime_execution_manifest>
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    structured_writer = writer_llm.with_structured_output(DraftOutput)
    flow = prompt | structured_writer
    response = await flow.ainvoke({
        "target_audience": state.get("target_audience", "General Tech Enthusiasts"),
        "tone": state.get("tone", "Informative and engaging"),
        "user_query": state.get("user_query"),
        "cleaned_content": state.get("cleaned_content"),
        "revised_directive":revision_directive
    })
    
    return {"final_article": response.sections}

subgraph=StateGraph(Research)
subgraph.add_node("Deep_research",deep_research)
subgraph.add_node("Compressor",context_node)
subgraph.add_node("Content_generation",gen_content)

subgraph.add_edge(START,"Deep_research")
subgraph.add_edge("Deep_research","Compressor")
subgraph.add_edge("Compressor","Content_generation")
subgraph.add_edge("Content_generation",END)

workflow=subgraph.compile()