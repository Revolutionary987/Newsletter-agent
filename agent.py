import os 
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph,START,END
import asyncio
from langchain_core.messages import HumanMessage,SystemMessage,ToolMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from duckduckgo_search import DDGS

llm=ChatGroq(model="llama-3.3-70b-versatile", temperature=0,api_key=os.getenv("GROQ_API_KEY"))

class BaseState(TypedDict):
    User_query:str
    Outline:str
    Draft:str
    Grading:str
    hal_check:str
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

    
async def research(state:BaseState):
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
    
    

graph=StateGraph(BaseState)
graph.add_node("Research",research)
graph.add_node("Generate_outline",outline)
graph.add_node("Creating_draft",gen_draft)
graph.add_node("Hallucination_check",check_hal)
# graph.add_node("Generate_score",grade)
graph.add_node("Image_gen",gen_image)

graph.add_edge(START,"Research")
graph.add_edge("Research","Generate_outline")
graph.add_edge("Generate_outline","Creating_draft")
graph.add_conditional_edges("Creating_draft",check_grade)
graph.add_edge("Image_gen",END)