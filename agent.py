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
from duckduckgo_search import DDGS
from pydantic import BaseModel,Field
from huggingface_hub import AsyncInferenceClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from langchain_community.tools.tavily_search import TavilySearchResults
from deep_research_agent import workflow

hf_endpoint = HuggingFaceEndpoint(
    repo_id="google/gemma-4-26B-A4B-it",
    task="image-text-to-text",
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)
llm=ChatOpenAI(base_url="https://openrouter.ai/api/v1",api_key=os.getenv("OPENROUTER_API_KEY"),model="meta-llama/llama-3.3-70b-instruct:free",temperature=0.1)

vision_llm = ChatHuggingFace(llm=hf_endpoint)

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
    
async def query_rewrite(state:BaseState):
    user_query=state["User_query"]
    key_points = state.get("key_points", "None specified by user.")
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

    **MANDATORY KEY POINTS TO INVESTIGATE:**
    {key_points}

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
          "user_query":user_query,
          "key_points":key_points
        }
    )
    return {"revised_query":response.content}

class DraftOutput(BaseModel):
    sections:List[ArticleSection]

class Gradee(BaseModel):
    is_pass: Annotated[bool,Field(description="Set to True if the draft is 100% factual and matches the formatting rules. Set to False if there are hallucinations or poor formatting.")]
    feedback: Annotated[str,Field(description="If is_pass is True, write 'Approved'. If False, provide a strict, bulleted list of specific corrections the writer must make.")]
    
async def check_hal(state:BaseState):
    cleaned_content=state["cleaned_content"]
    sections = state["article_sections"]
    final_article=state["final_article"]
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
    {cleaned_content}
    </blueprint>

    **THE GENERATED DRAFT (Text to Evaluate):**
    <draft>
    {final_article}
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
    response=await flow.ainvoke({"cleaned_content":cleaned_content,"final_article":compiled_draft})
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
   
async def check_grade(state:BaseState)->Literal["Image_gen","Subgraph"]:
    if state["Grading"]==True:
        return "Image_gen"
    else:
        return "Subgraph"
class FinalPublicationGrade(BaseModel):
    text_approved: bool = Field(description="True if text is factual and formatted correctly.")
    text_feedback: str = Field(description="Feedback for the writer. Write 'Perfect' if approved.")
    image_approved: bool = Field(description="True if the image matches the text perfectly.")
    image_feedback: str = Field(description="Feedback for the photo editor. Write 'Perfect' if approved.")

async def final_checking(state:BaseState):
    sections = state["article_sections"]
    parser = PydanticOutputParser(pydantic_object=FinalPublicationGrade)
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
    format_instruction = f"""
    STOP! Evaluation complete. Now, pack your entire review into the required data structure.
    
    You are strictly forbidden from outputting conversational introductory remarks, greetings, markdown headers, or bullet points.
    Output a SINGLE, clean, well-formed JSON object matching this schema blueprint precisely:
    
    {parser.get_format_instructions()}
    
    Your response must begin with '{{' and end with '}}'. Do not wrap the JSON in markdown code blocks (```json).
    """
    message_content.append({"type": "text", "text": format_instruction})
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message_content)
    ]
    max_retries = 3
    for attempt in range(max_retries):
        try:
            raw_response = await vision_llm.ainvoke(messages)
            content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                clean_json_str = json_match.group(0)
                data = json.loads(clean_json_str)
                return {
                    "Text_Grading": data.get("text_approved", data.get("Text_Grading", False)),
                    "Text_Feedback": data.get("text_feedback", data.get("Text_Feedback", "No text feedback provided")),
                    "Image_Grading": data.get("image_approved", data.get("Image_Grading", False)),
                    "Image_Feedback": data.get("image_feedback", data.get("Image_Feedback", "No image feedback provided"))
                }
            else:
                result = parser.parse(content)
                return {
                    "Text_Grading": result.text_approved,
                    "Text_Feedback": result.text_feedback,
                    "Image_Grading": result.image_approved,
                    "Image_Feedback": result.image_feedback
                }
        except Exception as e:
            print(f"JSON Parsing failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise ValueError("The Editor Agent failed to format its grading response. Aborting publication for safety.")

async def check(state:BaseState)->Literal["Subgraph","Image_gen","__end__"]:
    if state["Text_Grading"]==False:
        return "Subgraph"
    elif state["Image_Grading"]==False:
        return "Image_gen"
    else:
        return END
    
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