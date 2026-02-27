from datetime import datetime
from typing import List, Optional, Dict, Any
from ..database import chat_sessions, chat_messages
from ..models.chat import (
    ChatSession, ChatSessionCreate, ChatMessageCreate, 
    ChatResponse, ChatSessionSummary, ChatMessage, 
    MessageRole, ChatIntent
)
from ..ai.groq_client import get_groq_client
import uuid


class ChatService:
    def __init__(self):
        self.groq_client = get_groq_client()

    async def create_session(self, session_data: ChatSessionCreate, user_id: str) -> ChatSession:
        """Create a new chat session"""
        session_dict = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": session_data.title,
            "messages": [],
            "context": {},
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await chat_sessions.insert_one(session_dict)
        
        # If initial message provided, add it
        if session_data.initial_message:
            message_data = ChatMessageCreate(content=session_data.initial_message)
            await self.process_message(session_dict["id"], message_data, user_id)
        
        return ChatSession(**session_dict)

    async def get_user_sessions(self, user_id: str) -> List[ChatSessionSummary]:
        """Get all chat sessions for a user"""
        cursor = chat_sessions.find(
            {"user_id": user_id, "is_active": True}
        ).sort("updated_at", -1)
        
        sessions = []
        async for session_doc in cursor:
            messages = session_doc.get("messages", [])
            last_message = messages[-1]["content"] if messages else None
            
            summary = ChatSessionSummary(
                id=session_doc["id"],
                title=session_doc.get("title"),
                message_count=len(messages),
                last_message=last_message,
                created_at=session_doc["created_at"],
                updated_at=session_doc["updated_at"]
            )
            sessions.append(summary)
        
        return sessions

    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific chat session"""
        session_doc = await chat_sessions.find_one({
            "id": session_id,
            "user_id": user_id,
            "is_active": True
        })
        
        if not session_doc:
            return None
        
        return ChatSession(**session_doc)

    async def process_message(
        self, 
        session_id: str, 
        message_data: ChatMessageCreate, 
        user_id: str
    ) -> ChatResponse:
        """Process user message and generate AI response"""
        # Get session
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        # Add user message
        user_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=message_data.content,
            metadata=message_data.metadata
        )
        
        # Update session with user message
        await chat_sessions.update_one(
            {"id": session_id},
            {
                "$push": {"messages": user_message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Generate AI response (placeholder for now - will be enhanced in Iteration 2)
        ai_response = await self._generate_ai_response(
            message_data.content, 
            session, 
            user_id
        )
        
        # Add AI message
        ai_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            metadata=ai_response.metadata
        )
        
        # Update session with AI message
        await chat_sessions.update_one(
            {"id": session_id},
            {
                "$push": {"messages": ai_message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Update session title if it's the first exchange
        if not session.title and len(session.messages) == 0:
            title = self._generate_session_title(message_data.content)
            await chat_sessions.update_one(
                {"id": session_id},
                {"$set": {"title": title}}
            )
        
        return ai_response

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        result = await chat_sessions.update_one(
            {"id": session_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def update_session_title(
        self, 
        session_id: str, 
        title: str, 
        user_id: str
    ) -> Optional[ChatSession]:
        """Update session title"""
        await chat_sessions.update_one(
            {"id": session_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        
        return await self.get_session(session_id, user_id)

    async def _generate_ai_response(
        self, 
        user_message: str, 
        session: ChatSession, 
        user_id: str
    ) -> ChatResponse:
        """Generate AI response (basic implementation)"""
        # For now, return a simple response
        # This will be enhanced with actual AI logic in Iteration 2
        
        # Simple intent classification (placeholder)
        intent = self._classify_intent_basic(user_message)
        
        # Generate response based on intent
        if intent == ChatIntent.GENERAL_QUERY:
            content = "I'm here to help you with your financial data. You can ask me about revenue, expenses, customers, or cash flow. Once the AI features are fully implemented, I'll be able to provide specific insights from your data."
        elif intent == ChatIntent.REVENUE_QUERY:
            content = "I'll help you analyze your revenue. This feature will be available once the AI integration is complete."
        elif intent == ChatIntent.EXPENSE_QUERY:
            content = "I can help you understand your expenses. This feature will be available once the AI integration is complete."
        else:
            content = "I'm still learning about your financial data. This feature will be enhanced with AI capabilities in the next iteration."
        
        return ChatResponse(
            session_id=session.id,
            message_id=str(uuid.uuid4()),
            content=content,
            intent=intent,
            confidence=0.5,  # Placeholder confidence
            data_sources=[],  # Will be populated with actual data sources
            metadata={"iteration": "3", "status": "basic_response"}
        )

    def _classify_intent_basic(self, message: str) -> ChatIntent:
        """Basic intent classification (placeholder)"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["revenue", "income", "earnings"]):
            return ChatIntent.REVENUE_QUERY
        elif any(word in message_lower for word in ["expense", "spend", "cost"]):
            return ChatIntent.EXPENSE_QUERY
        elif any(word in message_lower for word in ["customer", "client"]):
            return ChatIntent.TOP_CUSTOMER_QUERY
        elif any(word in message_lower for word in ["cashflow", "cash flow"]):
            return ChatIntent.CASHFLOW_QUERY
        elif any(word in message_lower for word in ["trend", "trending"]):
            return ChatIntent.TREND_QUERY
        elif any(word in message_lower for word in ["forecast", "predict"]):
            return ChatIntent.FORECAST_QUERY
        elif any(word in message_lower for word in ["compare", "comparison"]):
            return ChatIntent.COMPARISON_QUERY
        else:
            return ChatIntent.GENERAL_QUERY

    def _generate_session_title(self, first_message: str) -> str:
        """Generate a title for the session based on first message"""
        # Simple title generation - take first 50 characters
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title


chat_service = ChatService()
