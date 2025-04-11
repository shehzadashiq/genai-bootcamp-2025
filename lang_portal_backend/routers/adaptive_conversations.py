from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from services.adaptive_conversations_service import AdaptiveConversationsService

logger = logging.getLogger(__name__)

router = APIRouter()
adaptive_conversations_service = AdaptiveConversationsService()

class ConversationMessage(BaseModel):
    message: str
    user_id: str
    conversation_id: Optional[str] = None
    knowledge_level: Optional[str] = "beginner"
    topic: Optional[str] = None

class ConversationResponse(BaseModel):
    response: str
    conversation_id: str
    error: Optional[str] = None

@router.post("/api/adaptive-conversations/message")
async def send_message(message_data: ConversationMessage) -> ConversationResponse:
    """Send a message to the adaptive conversation system and get a response."""
    logger.info(f"[/api/adaptive-conversations/message] Received message from user: {message_data.user_id}")
    try:
        result = adaptive_conversations_service.process_message(
            message=message_data.message,
            user_id=message_data.user_id,
            conversation_id=message_data.conversation_id,
            knowledge_level=message_data.knowledge_level,
            topic=message_data.topic
        )
        
        if "error" in result:
            logger.error(f"[/api/adaptive-conversations/message] Error processing message: {result['error']}")
            return ConversationResponse(response="", conversation_id="", error=result["error"])
            
        logger.info(f"[/api/adaptive-conversations/message] Successfully processed message for conversation: {result['conversation_id']}")
        return ConversationResponse(
            response=result["response"],
            conversation_id=result["conversation_id"]
        )
    except Exception as e:
        logger.error(f"[/api/adaptive-conversations/message] Error processing message: {str(e)}")
        return ConversationResponse(response="", conversation_id="", error=str(e))

@router.get("/api/adaptive-conversations/history/{conversation_id}")
async def get_conversation_history(conversation_id: str, user_id: str) -> Dict:
    """Get the conversation history for a specific conversation."""
    logger.info(f"[/api/adaptive-conversations/history] Retrieving history for conversation: {conversation_id}")
    try:
        result = adaptive_conversations_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if "error" in result:
            logger.error(f"[/api/adaptive-conversations/history] Error retrieving history: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])
            
        logger.info(f"[/api/adaptive-conversations/history] Successfully retrieved history for conversation: {conversation_id}")
        return result
    except Exception as e:
        logger.error(f"[/api/adaptive-conversations/history] Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
