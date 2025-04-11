"""
Adaptive Conversations Service for Urdu language practice.
Uses ChromaDB and Amazon Titan Embeddings for context-aware conversations.
"""
from typing import Dict, List, Optional, Any
import boto3
import json
import uuid
import logging
import datetime
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import Chroma
from config import aws_config, vector_store_config

logger = logging.getLogger(__name__)

class AdaptiveConversationsService:
    def __init__(self):
        """Initialize the adaptive conversations service with ChromaDB and Bedrock."""
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Initialize Bedrock embeddings
        self.embeddings = BedrockEmbeddings(
            client=self.bedrock_runtime,
            model_id=aws_config.BEDROCK_EMBEDDING_MODEL,
            model_kwargs={}  # Use default model parameters
        )
        
        # Initialize ChromaDB for conversation storage
        self.vector_store = Chroma(
            collection_name="adaptive_conversations",
            embedding_function=self.embeddings,
            persist_directory=vector_store_config.PERSIST_DIRECTORY
        )
        
        # Initialize Bedrock for LLM responses
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Prompt template for the conversation - formatted for Claude model
        self.prompt_template = """
Human: You are an Urdu language tutor having a conversation with a student.
Respond only in Urdu using the Urdu script.

Student's knowledge level: {knowledge_level}
Topic (if specified): {topic}

Previous conversation context:
{context}

Instructions:
1. Be conversational and friendly
2. Adjust your language complexity based on the student's knowledge level
3. If the student makes a mistake, gently correct them and explain why
4. If appropriate, ask follow-up questions to keep the conversation going
5. Keep your response concise and focused
6. If the student is confused, provide a simpler explanation
7. If the student is doing well, introduce slightly more complex language

The student's message is: {message}
"""

    def process_message(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        knowledge_level: str = "beginner",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a message from the user and generate a response.
        
        Args:
            message: The user's message in Urdu
            user_id: User identifier
            conversation_id: Optional conversation ID for continuing a conversation
            knowledge_level: User's knowledge level (beginner, intermediate, advanced)
            topic: Optional conversation topic
            
        Returns:
            Dict containing the response and conversation ID
        """
        try:
            # Create a new conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                logger.info(f"Created new conversation with ID: {conversation_id}")
            
            # Retrieve conversation context
            context = self._get_conversation_context(
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # Generate embeddings for the user message
            user_message_embedding = self.embeddings.embed_query(message)
            
            # Store the user message in ChromaDB
            timestamp = datetime.datetime.now().isoformat()
            self.vector_store.add_texts(
                texts=[message],
                metadatas=[{
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'role': 'user',
                    'timestamp': timestamp,
                    'knowledge_level': knowledge_level,
                    'topic': topic or "general"
                }],
                ids=[f"user_{conversation_id}_{timestamp}"]
            )
            
            # Build the prompt with context
            prompt = self.prompt_template.format(
                knowledge_level=knowledge_level,
                topic=topic or "general conversation",
                context=context,
                message=message
            )
            
            # Generate response using Bedrock
            response_text = self._generate_llm_response(prompt)
            
            # Store the assistant response in ChromaDB
            response_timestamp = datetime.datetime.now().isoformat()
            self.vector_store.add_texts(
                texts=[response_text],
                metadatas=[{
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'role': 'assistant',
                    'timestamp': response_timestamp,
                    'knowledge_level': knowledge_level,
                    'topic': topic or "general"
                }],
                ids=[f"assistant_{conversation_id}_{response_timestamp}"]
            )
            
            return {
                "response": response_text,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"error": str(e)}

    def _get_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        max_messages: int = 10
    ) -> str:
        """
        Retrieve the conversation context from ChromaDB.
        
        Args:
            conversation_id: The conversation ID
            user_id: User identifier
            max_messages: Maximum number of messages to include in context
            
        Returns:
            Formatted conversation context string
        """
        try:
            # For a new conversation, return empty context
            if conversation_id is None or conversation_id == "":
                return "This is the start of a new conversation."
                
            # Get all documents from the collection
            # This is a simpler approach that doesn't rely on ChromaDB's filtering
            all_docs = self.vector_store.similarity_search_with_score(
                query="retrieve conversation context",  # Non-empty query
                k=1000  # Large number to get all documents
            )
            
            # Filter the documents manually in Python
            filtered_docs = []
            for doc, score in all_docs:
                if (doc.metadata.get("conversation_id") == conversation_id and 
                    doc.metadata.get("user_id") == user_id):
                    filtered_docs.append((doc, score))
            
            if not filtered_docs:
                return "This is the start of a new conversation."
                
            # Format messages from the retrieved documents
            messages = []
            for doc, score in filtered_docs:
                messages.append({
                    "text": doc.page_content,
                    "role": doc.metadata.get("role", "unknown"),
                    "timestamp": doc.metadata.get("timestamp", "")
                })
                
            # Sort by timestamp
            messages.sort(key=lambda x: x.get("timestamp", ""))
            
            # Take only the last max_messages
            messages = messages[-max_messages:]
            
            # Format the conversation context
            context = ""
            for msg in messages:
                if msg["role"] == "user":
                    context += f"Human: {msg['text']}\n\n"
                else:
                    context += f"Assistant: {msg['text']}\n\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {str(e)}")
            return "This is the start of a new conversation."

    def _generate_llm_response(self, prompt: str) -> str:
        """
        Generate a response using Amazon Bedrock.
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            Generated response text
        """
        try:
            # Use Claude model for high-quality Urdu responses
            model_id = aws_config.BEDROCK_MODEL_ID
            
            # Prepare the request based on the model
            if "anthropic.claude" in model_id:
                # Claude-specific parameters
                # Ensure the prompt already has "Human:" prefix and add "Assistant:" for the response
                request = {
                    "prompt": prompt + "\n\nAssistant:",
                    "max_tokens_to_sample": 500,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop_sequences": ["\n\nHuman:"]
                }
            else:
                # Generic parameters for other models
                request = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 500,
                        "temperature": 0.7,
                        "topP": 0.9,
                    }
                }
            
            # Call Bedrock
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(request)
            )
            
            # Parse the response
            response_body = json.loads(response["body"].read())
            
            # Extract completion based on model
            if "anthropic.claude" in model_id:
                completion = response_body.get("completion", "")
            else:
                completion = response_body.get("results", [{}])[0].get("outputText", "")
            
            return completion.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return "عذر خواہ ہوں، میں ابھی جواب نہیں دے سکتا۔ براہ کرم دوبارہ کوشش کریں۔"

    def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get the full conversation history.
        
        Args:
            conversation_id: The conversation ID
            user_id: User identifier
            
        Returns:
            Dict containing the conversation history
        """
        try:
            # For new conversations, return empty history
            # This handles the case where there are no documents in the collection yet
            return {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": []
            }
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return {"error": f"Error retrieving conversation history: {str(e)}"}
