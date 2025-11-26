import os
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, AIMessage

# For the ReAct agent in LangGraph
from langgraph.prebuilt import create_react_agent

# Core components for the agent
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

# SQL and Database setup
from langchain_community.utilities import SQLDatabase 
from langchain_community.tools import QuerySQLDatabaseTool
from django.db import connection
from django.conf import settings
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Helper function to create SQLAlchemy engine from Django settings
def get_sqlalchemy_engine():
    db_config = settings.DATABASES['default'].copy()
    engine_str = db_config.pop('ENGINE', '')
    name = db_config.pop('NAME')
    user = db_config.pop('USER', '')
    password = quote_plus(db_config.pop('PASSWORD', ''))
    host = db_config.pop('HOST', '')
    port = db_config.pop('PORT', '')
    
    # Pop other irrelevant keys
    db_config.pop('OPTIONS', None)
    db_config.pop('TEST', None)
    db_config.pop('TIME_ZONE', None)
    db_config.pop('CONN_MAX_AGE', None)
    
    if 'sqlite' in engine_str:
        url = f"sqlite:///{name}"
    elif 'postgresql' in engine_str:
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    elif 'mysql' in engine_str:
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    elif 'oracle' in engine_str:
        url = f"oracle+cx_oracle://{user}:{password}@{host}:{port}/{name}"
    else:
        raise ValueError(f"Unsupported database engine: {engine_str}")
    
    return create_engine(url)

# --- 1. Tool Setup: Database Connection ---

# Create SQLAlchemy engine using Django settings
engine = get_sqlalchemy_engine()

# Initialize SQLDatabase using the engine
db = SQLDatabase(engine=engine, include_tables=['agent_app_project'])

# Create the SQL tool for the agent to use
property_retrieval_tool = QuerySQLDatabaseTool(
    db=db, 
    name="retrieve_property_info"
)
tools = [property_retrieval_tool]

# --- 2. Agent Model and Chain Setup ---

# Initialize the Chat Model 
# (Ensure OPENAI_API_KEY is set in your environment)
model: BaseChatModel = ChatOpenAI(model="gpt-4o", temperature=0)

# Define the System Prompt
SYSTEM_PROMPT = """
You are Silver Land Properties AI assistant, a specialized property sales agent.
Your primary goal is to understand the user's preferences (city, unit size, budget) and recommend suitable properties from the database using the available tools.
Use the 'retrieve_property_info' tool ONLY when you need to search the database based on specific criteria (e.g., city, bedrooms, price).
The table to query is 'agent_app_project'. The key columns are: 'project_name', 'city', 'no_of_bedrooms', 'price_usd'.
Do not make up project names or details. If the tool returns no results, state that politely.
After providing recommendations, you must subtly nudge the user toward scheduling a property viewing.
"""

# Build the ReAct agent using LangGraph (replaces legacy AgentExecutor)
agent_executor = create_react_agent(
    model, 
    tools, 
    prompt=SYSTEM_PROMPT
)

# --- 3. LangGraph State Definition ---

class ConversationState(TypedDict):
    """Represents the state of our conversation."""
    conversation_id: str
    messages: Annotated[List[BaseMessage], lambda x, y: x + y] 
    lead_data: dict 


# --- 4. LangGraph Node Definition ---

def agent_node(state: ConversationState):
    """Node that runs the ReAct agent logic."""
    
    messages = state['messages']
    
    # Invoke the ReAct agent with the conversation history
    result = agent_executor.invoke({"messages": messages})
    
    # Return only the newly added messages to append to state
    return {"messages": result["messages"][len(messages):]}


# --- 5. LangGraph Graph Builder (Simplified) ---

# Build the graph
workflow = StateGraph(ConversationState)

# Add the single agent node
workflow.add_node("agent", agent_node)

# Set the entry point and connect it directly to the end
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# Compile the graph
agent_graph = workflow.compile()