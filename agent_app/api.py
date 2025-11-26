# agent_app/api.py

import json
import uuid
from typing import Any, Dict, List, Optional
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from ninja import Router, Schema
from langchain_core.messages import HumanMessage, AIMessage

# Ensure these imports exist from your project structure
from .models import Conversation, Lead, Message
from .graph import agent_graph, ConversationState 

# --- SCHEMAS ---

class LeadSchema(Schema):
    # Defining schemas for output data structure
    session_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class MessageSchema(Schema):
    sender: str
    text: str
    timestamp: Optional[str] = None

    @staticmethod
    def from_orm(message_obj: Message) -> 'MessageSchema':
        # Helper to convert a Django Message object to a Pydantic schema
        return MessageSchema(
            sender=message_obj.sender,
            text=message_obj.text,
            timestamp=message_obj.timestamp.isoformat() if message_obj.timestamp else None
        )

class ConversationSchema(Schema):
    id: int
    lead: LeadSchema
    start_time: str
    messages: List[MessageSchema]
    state_payload: ConversationState # Note: ConversationState is a TypedDict from graph.py

class ChatRequestSchema(Schema):
    message: str
    conversation_id: int

class ChatResponseSchema(Schema):
    conversation_id: int
    reply: str
    updated_state: ConversationState

router = Router()

# --- ENDPOINTS ---

@router.post("/conversations", response={201: ConversationSchema})
def start_conversation(request: HttpRequest):
    """Initializes a new chat session."""
    
    # 1. Create a new Lead for the session
    session_id = str(uuid.uuid4())
    lead = Lead.objects.create(session_id=session_id)

    # 2. Create a new Conversation link
    # FIX APPLIED: Only pass valid model fields ('lead') to Conversation.objects.create()
    conversation = Conversation.objects.create(lead=lead)
    
    # 3. Define the initial state for LangGraph
    initial_ai_message = AIMessage(content="Hello! I'm the Silver Land Properties AI assistant. How can I help you find your dream property today?")
    
    starting_state = ConversationState(
        conversation_id=str(conversation.id),
        messages=[initial_ai_message],
        lead_data={}
    )
    
    # 4. Save the initial message to the database
    Message.objects.create(
        conversation=conversation,
        sender='AI',
        text=initial_ai_message.content
    )

    # 5. Return the initial state
    return 201, {
        "id": conversation.id,
        "lead": LeadSchema.from_orm(lead),
        "start_time": conversation.start_time.isoformat(),
        "messages": [MessageSchema.from_orm(m) for m in conversation.messages.all()],
        "state_payload": starting_state
    }


@router.post("/agents/chat", response=ChatResponseSchema)
def chat(request: HttpRequest, data: ChatRequestSchema):
    """Sends a message to the agent and gets a response."""
    
    # 1. Fetch Conversation
    conversation = get_object_or_404(Conversation, id=data.conversation_id)
    
    # 2. Reconstruct the previous state by loading messages from the DB
    current_messages: List[Any] = []
    
    for msg in conversation.messages.order_by('timestamp'):
        if msg.sender == 'Human':
            current_messages.append(HumanMessage(content=msg.text))
        elif msg.sender == 'AI':
            current_messages.append(AIMessage(content=msg.text))

    # Add the new human message
    new_human_message = HumanMessage(content=data.message)
    current_messages.append(new_human_message)
    
    # Save the new human message to the DB
    Message.objects.create(
        conversation=conversation,
        sender='Human',
        text=data.message
    )

    # 3. Define the input state
    input_state = ConversationState(
        conversation_id=str(conversation.id),
        messages=current_messages,
        lead_data={} # Keep track of lead data via tools or database updates
    )

    # 4. Run the graph
    output_state = agent_graph.invoke(input_state)
    
    # 5. Extract the AI's final response
    ai_response = output_state["messages"][-1]
    
    if isinstance(ai_response, AIMessage):
        reply_text = ai_response.content
    else:
        # If the graph outputs a ToolMessage or other type, the agent failed to synthesize
        reply_text = "Sorry, I am still processing the previous request or encountered an internal error."
    
    # 6. Save the AI's response to the database
    if isinstance(ai_response, AIMessage):
        Message.objects.create(
            conversation=conversation,
            sender='AI',
            text=reply_text
        )

    # 7. Return the response
    return {
        "conversation_id": conversation.id,
        "reply": reply_text,
        "updated_state": output_state
    }