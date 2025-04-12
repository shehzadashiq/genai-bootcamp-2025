from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging
import sys
import traceback
from services.adaptive_conversations_service import AdaptiveConversationsService

logger = logging.getLogger(__name__)

print("=" * 80)
print("ADAPTIVE CONVERSATIONS: Initializing views")
print("=" * 80)
sys.stdout.flush()

# Initialize the service
try:
    adaptive_conversations_service = AdaptiveConversationsService()
    print(f"ADAPTIVE CONVERSATIONS: Service initialized successfully: {adaptive_conversations_service.is_initialized}")
    sys.stdout.flush()
except Exception as e:
    print(f"ADAPTIVE CONVERSATIONS ERROR: Failed to initialize service: {str(e)}")
    traceback.print_exc()
    sys.stdout.flush()

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
    """
    Send a message to the adaptive conversations service.
    
    Request body:
    {
        "message": "User message in Urdu",
        "user_id": "user123",
        "conversation_id": "optional-conversation-id",
        "knowledge_level": "beginner|intermediate|advanced",
        "topic": "optional topic"
    }
    """
    try:
        print("=" * 80)
        print(f"ADAPTIVE CONVERSATIONS: Received message request")
        print(f"Request data: {request.data}")
        sys.stdout.flush()
        
        data = request.data
        message = data.get('message', '')
        user_id = data.get('user_id', '')
        conversation_id = data.get('conversation_id', None)
        knowledge_level = data.get('knowledge_level', 'beginner')
        topic = data.get('topic', None)
        
        # Log extracted parameters
        print(f"Extracted parameters:")
        print(f"  message: {message[:50]}..." if len(message) > 50 else f"  message: {message}")
        print(f"  user_id: {user_id}")
        print(f"  conversation_id: {conversation_id}")
        print(f"  knowledge_level: {knowledge_level}")
        print(f"  topic: {topic}")
        sys.stdout.flush()
        
        # Validate required fields
        if not message:
            print("Error: Missing required field 'message'")
            sys.stdout.flush()
            return JsonResponse({"error": "Missing required field: message"}, status=400)
        
        if not user_id:
            print("Error: Missing required field 'user_id'")
            sys.stdout.flush()
            return JsonResponse({"error": "Missing required field: user_id"}, status=400)
        
        # Check if service is initialized
        if not adaptive_conversations_service.is_initialized:
            print("Error: Adaptive conversations service is not properly initialized")
            sys.stdout.flush()
            return JsonResponse({
                "error": "Service not properly initialized. Please check AWS credentials and configuration."
            }, status=500)
        
        # Process the message
        print("Calling adaptive_conversations_service.process_message...")
        sys.stdout.flush()
        
        try:
            result = adaptive_conversations_service.process_message(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                knowledge_level=knowledge_level,
                topic=topic
            )
            
            print(f"Service result: {result}")
            sys.stdout.flush()
            
            return JsonResponse(result)
        except Exception as service_error:
            print(f"Service error: {str(service_error)}")
            traceback.print_exc()
            sys.stdout.flush()
            return JsonResponse({
                "error": f"Error processing message: {str(service_error)}"
            }, status=500)
            
    except Exception as e:
        print(f"Unhandled error in send_adaptive_message: {str(e)}")
        traceback.print_exc()
        sys.stdout.flush()
        logger.error(f"Unhandled error in send_adaptive_message: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

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
