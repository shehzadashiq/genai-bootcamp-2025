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
import os
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import Chroma
from config import aws_config, vector_store_config
import shutil

logger = logging.getLogger(__name__)

class AdaptiveConversationsService:
    def __init__(self):
        """Initialize the service."""
        try:
            # Check if AWS credentials are available
            if not os.environ.get('AWS_ACCESS_KEY_ID') or not os.environ.get('AWS_SECRET_ACCESS_KEY'):
                logger.warning("AWS credentials not found in environment variables")
                self.is_initialized = False
                return
                
            logger.debug("Initializing AdaptiveConversationsService")
            
            # Initialize Bedrock client
            logger.debug(f"Initializing Bedrock client with region: {aws_config.AWS_REGION}")
            self.bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=aws_config.AWS_REGION
            )
            
            # Initialize Bedrock embeddings
            logger.debug(f"Initializing Bedrock embeddings with model: {aws_config.BEDROCK_EMBEDDING_MODEL}")
            self.embeddings = BedrockEmbeddings(
                client=self.bedrock,
                model_id=aws_config.BEDROCK_EMBEDDING_MODEL
            )
            
            # Initialize ChromaDB
            logger.debug(f"Initializing ChromaDB with persist directory: {vector_store_config.PERSIST_DIRECTORY}")
            
            # COMPLETELY RESET THE VECTOR STORE DIRECTORY
            # This is a more aggressive approach to fix the ChromaDB corruption
            if os.path.exists(vector_store_config.PERSIST_DIRECTORY):
                # Create backup directory
                backup_dir = os.path.join(os.path.dirname(vector_store_config.PERSIST_DIRECTORY), 
                                         f"vector_store_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                try:
                    # Copy the entire directory to backup
                    if not os.path.exists(backup_dir):
                        shutil.copytree(vector_store_config.PERSIST_DIRECTORY, backup_dir)
                    logger.warning(f"Created backup of vector store at: {backup_dir}")
                    
                    # Remove the entire vector store directory
                    shutil.rmtree(vector_store_config.PERSIST_DIRECTORY)
                    logger.warning("Removed corrupted vector store directory")
                    
                    # Create a fresh directory
                    os.makedirs(vector_store_config.PERSIST_DIRECTORY, exist_ok=True)
                    logger.info("Created fresh vector store directory")
                except Exception as e:
                    logger.error(f"Error during vector store reset: {str(e)}", exc_info=True)
            
            try:
                # Initialize ChromaDB with a clean state
                self.vector_store = Chroma(
                    collection_name="adaptive_conversations",
                    embedding_function=self.embeddings,
                    persist_directory=vector_store_config.PERSIST_DIRECTORY
                )
                
                # Initialize prompt template
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

                self.is_initialized = True
                logger.info("AdaptiveConversationsService initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {str(e)}", exc_info=True)
                self.is_initialized = False
                
        except Exception as e:
            logger.error(f"Failed to initialize AdaptiveConversationsService: {str(e)}", exc_info=True)
            self.is_initialized = False

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
            # Check if service is properly initialized
            if not self.is_initialized:
                logger.warning("Service not properly initialized. Returning fallback response.")
                return {
                    "response": "عذر خواہ ہوں، میں ابھی جواب نہیں دے سکتا۔ براہ کرم دوبارہ کوشش کریں۔",
                    "conversation_id": conversation_id or str(uuid.uuid4())
                }
                
            # Create a new conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                logger.info(f"Created new conversation with ID: {conversation_id}")
            
            # Skip ChromaDB operations in local development if there are issues
            try:
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
            except Exception as e:
                logger.error(f"Error with ChromaDB operations: {str(e)}", exc_info=True)
                context = "This is the start of a new conversation."
            
            # Build the prompt with context
            prompt = self.prompt_template.format(
                knowledge_level=knowledge_level,
                topic=topic or "general conversation",
                context=context,
                message=message
            )
            
            # Generate response using Bedrock
            response_text = self._generate_llm_response(prompt)
            
            # Skip ChromaDB operations for storing response if there were issues earlier
            try:
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
            except Exception as e:
                logger.error(f"Error storing assistant response in ChromaDB: {str(e)}", exc_info=True)
            
            return {
                "response": response_text,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "response": "عذر خواہ ہوں، میں ابھی جواب نہیں دے سکتا۔ براہ کرم دوبارہ کوشش کریں۔",
                "conversation_id": conversation_id or str(uuid.uuid4())
            }

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
            # Check if AWS credentials are available
            if not os.environ.get('AWS_ACCESS_KEY_ID') or not os.environ.get('AWS_SECRET_ACCESS_KEY'):
                logger.error("AWS credentials not found in environment variables")
                return "آپ کے سوال کا جواب دینے میں مجھے معذرت ہے۔ AWS کریڈینشلز کی کمی کی وجہ سے میں آپ کی مدد نہیں کر سکتا۔"
                
            # Use Claude model for high-quality Urdu responses
            model_id = aws_config.BEDROCK_MODEL_ID
            
            # Check if we have the required permissions for Bedrock
            try:
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
                logger.debug(f"Invoking Bedrock model: {model_id}")
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
                error_message = str(e)
                logger.error(f"Error invoking Bedrock model: {error_message}", exc_info=True)
                
                # Check for specific permission errors
                if "AccessDeniedException" in error_message:
                    logger.error("AWS Bedrock access denied. Check IAM permissions for bedrock:InvokeModel and bedrock-runtime:InvokeModel")
                    return "آپ کے سوال کا جواب دینے میں مجھے معذرت ہے۔ AWS Bedrock تک رسائی کی اجازت نہیں ہے۔ براہ کرم IAM اجازتوں کی جانچ کریں۔"
                
                return "عذر خواہ ہوں، میں ابھی جواب نہیں دے سکتا۔ براہ کرم دوبارہ کوشش کریں۔"
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
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
            # Check if service is properly initialized
            if not self.is_initialized:
                return {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "messages": []
                }
                
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
