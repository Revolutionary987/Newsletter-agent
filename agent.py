import os 
from dotenv import load_dotenv
from typing import TypedDict,Literal,Annotated
from langgraph.graph import StateGraph,START,END
import asyncio
from langchain_core.messages import HumanMessage,SystemMessage,ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from pydantic import BaseModel,Field
llm=ChatGroq(model="llama-3.3-70b-versatile", temperature=0,api_key=os.getenv("GROQ_API_KEY"))

class BaseState(TypedDict):
    User_query:str
    Outline:str
    Draft:str
    Grading:bool
    Feedback:str
    images:list[str]
@tool
def web_search(query:str)->str:
    try:
        with DDGS as ddgs:
            results=[result for result in ddgs.text(query,max_results=4)]
            if not results:
                raise f"No results found for query: {query}"
            formatted_results = []
            for r in results:
                formatted_results.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---")
            return "\n".join(formatted_results)
    except Exception as e:
        return f"Search failed due to an error: {str(e)}"

    
async def research(state:BaseState)->str:
    topic=state.get("User_query")
    target_audience=state.get("audience", "General Public")
    tone=state.get("tone", "Professional")

    system_prompt="""
    You are the Lead Research Synthesizer for a professional, dynamic newsletter. Your objective is to extract accurate, up-to-date information on any user-provided subject and structure it into a "narrative blueprint" so the Editorial Node can craft an engaging, magazine-style article.

    When given a topic or query by the user, you must execute the following steps:
    1. Deconstruct the topic into targeted search queries to capture fundamental concepts, recent milestones, and expert perspectives.
    2. Filter the raw search data to remove generic marketing filler, irrelevant tangents, and duplicate news.
    3. Synthesize your findings into the following strict blueprint structure. 

    Your output MUST be formatted exactly as follows:

    - **The Hook / The Core Mystery:** What is the fundamental, fascinating question at the heart of this topic? (e.g., "What is driving the sudden leap in autonomous agents?", "How do decentralized energy grids actually work?", or "Why is the global bond market shifting so rapidly?")
    - **The Core Mechanics (Step-by-Step):** A simplified, highly accurate breakdown of the logic, science, or systems behind the topic. Break complex ideas into digestible, logical stages or components.
    - **Latest Milestones & Updates:** What are the most recent tests, discoveries, market shifts, or developments occurring right now? Name specific entities, companies, frameworks, or global events.
    - **The Big Picture / Broader Impact:** How will this topic alter the future of its respective industry, human behavior, or the global landscape?
    - **Verified Sources:** Clean URLs or article titles from your search execution.

    Do NOT write the final article or use poetic language. Your job is to provide the structured, factual skeleton that the Editor will use to write the final piece.
    """
    Human_prompt="""
        **INITIALIZATION COMMAND:**
        Initiate the research phase for the following newsletter parameters:
        
        - **Target Topic:** {topic}
        - **Target Audience:** {target_audience}
        - **Desired Tone of Final Article:** {tone}
        
        **EXECUTION DIRECTIVE:**
        If you need up-to-date facts and for topics you aren't confident or may require external innformation , use your search tools. If you have enough data, output ONLY the finalized "Narrative Blueprint".
        
        Do not output any conversational filler. Output ONLY the finalized "Narrative Blueprint" exactly as defined in your system instructions.

"""
    prompt=ChatPromptTemplate.from_messages(
        [
        ("system", system_prompt),
        ("human", Human_prompt)
    ]
    )
    # format_messages creates a list by default when called
    messages=prompt.format_messages(
        topic=topic,
        target_audience=target_audience,
        tone=tone
    )
    llm_with_tools = llm.bind_tools([web_search])
    response=await llm.ainvoke(messages)
    if response.tool_calls:
        messages.append(response)
    for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                tool_output = web_search.invoke(tool_call["args"]) 
                
                # Package the result back to the LLM
                tool_message = ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"]
                )
                messages.append(tool_message)
            final_response = await llm_with_tools.ainvoke(messages)
            return {"Outline": final_response.content}
       
    else:
        # If the LLM already knew the answer, just return it
        return {"Outline": response.content}

async def gen_draft(state:BaseState)->str:

    outline=state["Outline"]
    target_audience=state.get("audience", "General Public")
    tone=state.get("tone", "Professional")

    system_prompt="""
    You are the Senior Editor and Lead Staff Writer for a premium, magazine-style newsletter. Your objective is to take the factual "Narrative Blueprint" provided by the Research team and transform it into a captivating, highly readable article.

    You will receive:
    1. The target audience and desired tone.
    2. The structured "Narrative Blueprint" containing the facts, core mechanics, and latest updates.

    Your writing MUST adhere to the following editorial standards:
    - **No Hallucinations:** You must base your article STRICTLY on the facts provided in the blueprint. Do not invent new milestones, statistics, or events.
    - **Engaging Flow:** Seamlessly transition between the "Hook", the "Core Mechanics", and the "Broader Impact". Do not just list facts; tell the story of the technology, concept, or event.
    - **Formatting:** Use rich Markdown formatting. Include a compelling main Headline (`#`), subheadings for distinct sections (`##`), and bullet points where appropriate to break up dense technical mechanics.
    - **Tone Alignment:** Strictly match the requested tone and tailor the vocabulary to the target audience.

    Output the final article in the following structure:
    - [Catchy Main Headline]
    - [Introduction / The Hook]
    - [Body Paragraphs / Subheadings detailing mechanics and updates]
    - [Conclusion / The Big Picture]
    - [A sign-off line: "- Written by [Generate a realistic journalist name]"]

    Do not output any introductory or concluding conversational text (e.g., "Here is your article:"). Output ONLY the final, polished newsletter text.

    """

    human_prompt="""
    **EDITORIAL TASK INITIATION**
    Please execute your drafting duties for the following assignment. 

    **PARAMETER CONSTRAINTS:**
    - Target Audience: {target_audience}
    - Required Tone: {tone}

    **SOURCE MATERIAL (NARRATIVE BLUEPRINT):**
    Below is the raw factual data compiled by the Research Team. You must use this data to write the final article according to your system instructions. Do not add outside facts.

    <blueprint>
    {outline}
    </blueprint>
    """
    prompt=ChatPromptTemplate.from_messages(
        "system",system_prompt,
        "human",human_prompt
)
    flow=prompt|llm
    response=await flow.ainvoke(prompt)
    return {"Draft",response.content}

class Gradee(BaseModel):
    is_pass: Annotated[bool,Field(description="Set to True if the draft is 100% factual and matches the formatting rules. Set to False if there are hallucinations or poor formatting.")]
    feedback: Annotated[str,Field(description="If is_pass is True, write 'Approved'. If False, provide a strict, bulleted list of specific corrections the writer must make.")]\
    
async def check_hal(state:BaseState):
    outline=state["Outline"]
    draft=state["Draft"]

    system_prompt="""
    You are the Managing Editor and Chief Fact-Checker for a premium newsletter. Your objective is to review the writer's Draft against the original Research Blueprint to ensure strict quality and factual accuracy.

    You must evaluate the draft on two criteria:
    1. FACTUAL GROUNDING (Hallucination Check): Does the draft contain any statistics, dates, quotes, or claims that are NOT present in the Narrative Blueprint? If it contains invented facts, it fails.
    2. EDITORIAL GRADING: Does the draft strictly follow the requested formatting (Markdown headers, bullet points) and match the requested tone? Is it engaging to read?

    You must output your evaluation strictly as a JSON object with the following schema:
    - "is_pass" (boolean): true if the draft is perfectly factual and well-written. false if it contains hallucinations or poor formatting.
    - "feedback" (string): If is_pass is true, output "Approved." If is_pass is false, provide a direct, actionable list of exactly what the writer needs to fix (e.g., "Remove the hallucinated date in paragraph 2. Make the tone more professional.").

    Do not output any text outside of this JSON structure.
    """
    human_prompt="""
    **QUALITY ASSURANCE REVIEW COMMAND**
    Evaluate the following draft.

    **THE FACTUAL BLUEPRINT (Source of Truth):**
    <blueprint>
    {outline}
    </blueprint>

    **THE GENERATED DRAFT (Text to Evaluate):**
    <draft>
    {draft}
    </draft>

    **EVALUATION DIRECTIVE:**
    Compare the <draft> to the <blueprint>. Output your JSON evaluation dictating whether the draft is approved to publish or requires a rewrite.
    """

    prompt=ChatPromptTemplate.from_messages(
        "system",system_prompt,
        "human",human_prompt
    )
    flow=prompt|llm
    response=await flow.ainvoke(prompt)
    return {
        "Grading": response.is_pass, 
        "Feedback": response.feedback
        }

async def check_grade(state:BaseState)->Literal["Image_gen","Research"]:
    if state["Grading"]== False:
        return "Research"
    else:
        return "Image_gen"
    
async def gen_image(state:BaseState):
    
graph=StateGraph(BaseState)
graph.add_node("Research",research)
# graph.add_node("Generate_outline",outline)
graph.add_node("Creating_draft",gen_draft)
graph.add_node("Hallucination_check",check_hal)
# graph.add_node("Generate_score",grade)
graph.add_node("Image_gen",gen_image)

graph.add_edge(START,"Research")
graph.add_edge("Research","Generate_outline")
graph.add_edge("Generate_outline","Creating_draft")
graph.add_conditional_edges("Creating_draft",check_grade)
graph.add_edge("Image_gen",END)