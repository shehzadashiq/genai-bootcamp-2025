from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
from services.adaptive_conversations_service import AdaptiveConversationsService

logger = logging.getLogger(__name__)
adaptive_conversations_service = AdaptiveConversationsService()

class AdaptiveConversationsViewSet(viewsets.ViewSet):
    """ViewSet for adaptive conversations."""
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message to the adaptive conversation system."""
        try:
            data = request.data
            message = data.get('message', '')
            user_id = data.get('user_id', '')
            conversation_id = data.get('conversation_id')
            knowledge_level = data.get('knowledge_level', 'beginner')
            topic = data.get('topic')
            
            if not message or not user_id:
                return Response(
                    {"error": "Message and user_id are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            result = adaptive_conversations_service.process_message(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                knowledge_level=knowledge_level,
                topic=topic
            )
            
            if "error" in result:
                return Response(
                    {"error": result["error"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response({
                "response": result["response"],
                "conversation_id": result["conversation_id"]
            })
            
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def conversation_history(self, request, pk=None):
        """Get conversation history."""
        try:
            conversation_id = pk
            user_id = request.query_params.get('user_id', '')
            
            if not conversation_id or not user_id:
                return Response(
                    {"error": "Conversation ID and user_id are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            history = adaptive_conversations_service.get_conversation_history(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # Always return a valid response, even if history is empty
            # This prevents 500 errors when starting a new conversation
            if "error" in history and history["error"] != "Conversation not found":
                return Response(
                    {"error": history["error"]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # If the error is just that the conversation is not found, 
            # return an empty history instead of an error
            return Response(history)
            
        except Exception as e:
            logger.error(f"Error in conversation_history: {str(e)}")
            # Return an empty history instead of an error for a better user experience
            return Response({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": []
            })

# Standalone view functions for direct URL routing

@api_view(['POST'])
@csrf_exempt
def send_adaptive_message(request):
    """Standalone view function for sending a message to the adaptive conversation system."""
    try:
        data = request.data
        message = data.get('message', '')
        user_id = data.get('user_id', '')
        conversation_id = data.get('conversation_id')
        knowledge_level = data.get('knowledge_level', 'beginner')
        topic = data.get('topic')
        
        if not message or not user_id:
            return Response(
                {"error": "Message and user_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = adaptive_conversations_service.process_message(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            knowledge_level=knowledge_level,
            topic=topic
        )
        
        if "error" in result:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return Response({
            "response": result["response"],
            "conversation_id": result["conversation_id"],
            "knowledge_level": knowledge_level
        })
        
    except Exception as e:
        logger.error(f"Error in send_adaptive_message: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@csrf_exempt
def get_conversation_history(request, conversation_id):
    """Standalone view function for getting conversation history."""
    try:
        user_id = request.query_params.get('user_id', '')
        
        if not conversation_id or not user_id:
            return Response(
                {"error": "Conversation ID and user_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        history = adaptive_conversations_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        # Always return a valid response, even if history is empty
        # This prevents 500 errors when starting a new conversation
        if "error" in history and history["error"] != "Conversation not found":
            return Response(
                {"error": history["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # If the error is just that the conversation is not found, 
        # return an empty history instead of an error
        return Response(history)
        
    except Exception as e:
        logger.error(f"Error in get_conversation_history: {str(e)}")
        # Return an empty history instead of an error for a better user experience
        return Response({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "messages": []
        })
