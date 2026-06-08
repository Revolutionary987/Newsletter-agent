import os 
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph,START,END
import asyncio
from langchain.messages import HumanMessage,SystemMessage


class BaseState(TypedDict):
    User_query:str
    Outline:str
    Draft:str
    Grading:str
    hal_check:str
    images:str


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