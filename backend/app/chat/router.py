from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..service import chat_service
from ..models.chat import (
    ChatSession, ChatSessionCreate, ChatMessageCreate, 
    ChatResponse, ChatSessionSummary
)
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSession)
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session"""
    session = await chat_service.create_session(session_data, current_user.id)
    return session


@router.get("/sessions", response_model=List[ChatSessionSummary])
async def get_sessions(
    current_user: User = Depends(get_current_user)
):
    """Get all chat sessions for the user"""
    sessions = await chat_service.get_user_sessions(current_user.id)
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with all messages"""
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message and get AI response"""
    try:
        response = await chat_service.process_message(
            session_id, message_data, current_user.id
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all messages in a session"""
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session.messages


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session"""
    success = await chat_service.delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Session deleted successfully"}


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    current_user: User = Depends(get_current_user)
):
    """Update session title"""
    session = await chat_service.update_session_title(
        session_id, title, current_user.id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session
