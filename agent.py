import os
import io
import base64
import httpx
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict,Literal,Annotated,Optional,List
from langgraph.graph import StateGraph,START,END
import asyncio
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage,SystemMessage,ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from pydantic import BaseModel,Field
from huggingface_hub import AsyncInferenceClient
from langchain_google_genai import ChatGoogleGenerativeAI

llm=ChatGroq(model="llama-3.3-70b-versatile", temperature=0,api_key=os.getenv("GROQ_API_KEY"))
vision_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0,api_key=os.getenv("GOOGLE_API_KEY"))

class ArticleSection(TypedDict):
    section_title: str
    paragraph_text: str
    image_url: Optional[str] 
    alt_text: Optional[str]

class BaseState(TypedDict):
    User_query:str
    revised_query:str
    Outline:str
    Grading:bool
    Feedback:str
    images:list[dict]
    alt_text: str
    article_sections: List[ArticleSection]
    Text_Grading: bool
    Text_Feedback: str
    Image_Grading: bool
    Image_Feedback: str
@tool
def web_search(query:str)->str:
    """Searches the web using DuckDuckGo to return relevant factual summaries."""
    try:
        with DDGS() as ddgs:
            results=[result for result in ddgs.text(query,max_results=4)]
            if not results:
                raise f"No results found for query: {query}"
            formatted_results = []
            for r in results:
                formatted_results.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---")
            return "\n".join(formatted_results)
    except Exception as e:
        return f"Search failed due to an error: {str(e)}"
    
async def query_rewrite(state:BaseState):
    user_query=state["User_query"]
    system_prompt="""
    You are the Lead Query Architect for a premium tech and business publication. Your objective is to take a user's raw, often brief topic suggestion and expand it into a highly detailed, multi-faceted "Research Directive."

    This directive will be passed to an autonomous Research Agent that relies on web search tools. If your output is too broad, the agent will fail to find specific, compelling facts.

    INSTRUCTIONS:
    1. Analyze the user's raw input and identify the core subject.
    2. Break the subject down into 3-4 highly specific sub-topics or "angles" that the Research Agent must investigate (e.g., technological mechanics, market impact, regulatory hurdles, or historical context).
    3. Identify 2-3 specific keywords or exact phrases the Research Agent should use in its search queries to find the most recent, high-quality data.
    4. Output your expansion strictly as a cohesive, highly detailed paragraph. Do not use bullet points or conversational filler.

    Your output must act as the ultimate, foolproof set of instructions for the downstream Research Agent.
    """

    human_prompt="""
    **QUERY EXPANSION INITIATION**
    Please process the following raw user input.

    **RAW USER INPUT:**
    <raw_query>
    {user_query}
    </raw_query>

    **EXECUTION DIRECTIVE:**
    Expand this raw input into the comprehensive Research Directive paragraph as defined in your instructions. Output ONLY the directive paragraph.
    """
    prompt=ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    flow=prompt|llm
    response=await flow.ainvoke(
        {
          "user_query":user_query
        }
    )
    return {"revised_query":response.content}

async def research(state:BaseState)->str:
    topic=state.get("revised_query")
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
    prompt=ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", Human_prompt)
    ])
    # format_messages creates a list by default when called
    messages=prompt.format_messages(
        topic=topic,
        target_audience=target_audience,
        tone=tone
    )
    llm_with_tools = llm.bind_tools([web_search])
    response=await llm_with_tools.ainvoke(messages)
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
        return {"Outline":response.content}
    
class DraftOutput(BaseModel):
    sections:List[ArticleSection]

async def gen_draft(state:BaseState)->str:

    outline=state["Outline"]
    target_audience=state.get("audience", "General Public")
    tone=state.get("tone", "Professional")
    previous_feedback = state.get("Feedback", "")

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
    human_prompt="""
    **EDITORIAL TASK INITIATION**
    Please execute your drafting duties for the following assignment. 

    **PARAMETER CONSTRAINTS:**
    - Target Audience: {target_audience}
    - Required Tone: {tone}
    {revision_directive}
    **SOURCE MATERIAL (NARRATIVE BLUEPRINT):**
    Below is the raw factual data compiled by the Research Team. You must use this data to write the final article according to your system instructions. Do not add outside facts.

    <blueprint>
    {outline}
    </blueprint>
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    structured_llm=llm.with_structured_output(DraftOutput)
    flow=prompt|structured_llm
    response=await flow.ainvoke({"outline": outline,"target_audience": target_audience,"tone": tone,"revision_directive": revision_directive})
    return {"article_sections":response.sections}

class Gradee(BaseModel):
    is_pass: Annotated[bool,Field(description="Set to True if the draft is 100% factual and matches the formatting rules. Set to False if there are hallucinations or poor formatting.")]
    feedback: Annotated[str,Field(description="If is_pass is True, write 'Approved'. If False, provide a strict, bulleted list of specific corrections the writer must make.")]
    
async def check_hal(state:BaseState):
    outline=state["Outline"]
    sections = state["article_sections"]
    # 2. Stitch the sections together into a single text block for the grader
    compiled_draft = "\n\n".join([f"## {s['section_title']}\n{s['paragraph_text']}" for s in sections])
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    structured_llm=llm.with_structured_output(Gradee)
    flow=prompt|structured_llm
    response=await flow.ainvoke({"outline": outline,"draft":compiled_draft})
    return {
        "Grading": response.is_pass, 
        "Feedback": response.feedback
        }

class ImageSearchQuery(BaseModel):
    search_query: Annotated[str, Field(description="A highly targeted 2-3 word search query to find a real photograph on Pexels. Keep it literal.")]
    alt_text: Annotated[str, Field(description="A brief 5-word description of the expected image.")]

async def gen_image(state: BaseState):
    previous_feedback = state.get("Image_Feedback", "")
    sections = state["article_sections"]
    updated_sections = []
    revision_directive = ""
    if previous_feedback and previous_feedback != "Perfect":
        revision_directive = f"""
        **CRITICAL REVISION DIRECTIVE:**
        Your previous image search query was REJECTED for the following reason:
        {previous_feedback}
        
        You must generate a COMPLETELY DIFFERENT search query this time to fix the issue.
        """
    
    system_prompt = """You are the Lead Photo Editor for a premium business and tech publication.
    Your job is to read the finalized article draft and select the perfect hero image to sit at the top of the page.
    
    INSTRUCTIONS:
    1. Read the draft and identify the CORE THEME or main subject.
    2. Translate that theme into a physical, photographable scene. (e.g., If the article is about "AI disrupting finance," do not search for 'AI finance'. Search for 'stock market screens' or 'modern bank building').
    3. Generate a concise 2-3 word search query for the Pexels API.
    {revision_directive}

    Keep queries simple, literal, and highly relevant to the overall summary of the text.
    """
    for section in sections:
        paragraph = section["paragraph_text"]
        human_prompt = "**ARTICLE DRAFT TO SUMMARIZE:**\n\n{paragraph}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        editor_llm = llm.with_structured_output(ImageSearchQuery)
        flow = prompt | editor_llm
        llm_result = await flow.ainvoke({"paragraph": paragraph,"revision_directive": revision_directive}) 

        api_key = os.getenv("PEXELS_API_KEY")
        url = "https://api.pexels.com/v1/search"
        params = {"query": llm_result.search_query, "per_page": 1, "orientation": "landscape"}
        headers = {"Authorization": api_key}
        
        image_url = ""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status() 
                data = response.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    image_url = data["photos"][0]["src"]["landscape"]
            except Exception as e:
                print(f"Pexels Error: {e}")
            section["image_url"] = image_url
            section["alt_text"] = llm_result.alt_text
            updated_sections.append(section)
    return {"article_sections": updated_sections}
   
async def check_grade(state:BaseState)->Literal["Image_gen","Creating_draft"]:
    if state["Grading"]==True:
        return "Image_gen"
    else:
        return "Creating_draft"
class FinalPublicationGrade(BaseModel):
    text_approved: bool = Field(description="True if text is factual and formatted correctly.")
    text_feedback: str = Field(description="Feedback for the writer. Write 'Perfect' if approved.")
    image_approved: bool = Field(description="True if the image matches the text perfectly.")
    image_feedback: str = Field(description="Feedback for the photo editor. Write 'Perfect' if approved.")

async def final_checking(state:BaseState):
    sections = state["article_sections"]
    system_prompt = "You are the Editor-in-Chief. Evaluate the final text for factual accuracy and ensure the image is a highly professional, relevant match."
    message_content = [{"type": "text", "text": "Evaluate this entire newsletter and its images:"}]
    for sec in sections:
        # Add the text
        message_content.append({"type": "text", "text": f"## {sec['section_title']}\n{sec['paragraph_text']}"})

        # Add the image if it exists
        if sec.get("image_url"):
            message_content.append({
                "type": "image_url", 
                "image_url": {"url": sec["image_url"]}
            })
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message_content)
    ]
    grader_llm = vision_llm.with_structured_output(FinalPublicationGrade)
    result = await grader_llm.ainvoke(messages)
    
    return {
        "Text_Grading": result.text_approved,
        "Text_Feedback": result.text_feedback,
        "Image_Grading": result.image_approved,
        "Image_Feedback": result.image_feedback
    }

async def check(state:BaseState)->Literal["Creating_draft","Image_gen","__end__"]:
    if state["Text_Grading"]==False:
        return "Creating_draft"
    elif state["Image_Grading"]==False:
        return "Image_gen"
    else:
        return END
    
graph=StateGraph(BaseState)
graph.add_node("Research",research)
graph.add_node("Rewrite_query",query_rewrite)
graph.add_node("Creating_draft",gen_draft)
graph.add_node("Hallucination_check",check_hal)
graph.add_node("Image_gen",gen_image)
graph.add_node("Final_check",final_checking)

graph.add_edge(START,"Rewrite_query")
graph.add_edge("Rewrite_query","Research")
graph.add_edge("Research","Creating_draft")
graph.add_edge("Creating_draft","Hallucination_check")
graph.add_conditional_edges("Hallucination_check",check_grade)
graph.add_edge("Image_gen","Final_check")
graph.add_conditional_edges("Final_check",check)

workflow=graph.compile()