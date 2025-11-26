# agent_app/schemas.py

from ninja import Schema
from typing import List, Optional
from uuid import UUID

class ChatInput(Schema):
    message: str
    conversation_id: UUID

class ChatOutput(Schema):
    conversation_id: UUID
    reply: str
    shortlisted_project_ids: List[int] = []

class ConversationStartOutput(Schema):
    conversation_id: UUID