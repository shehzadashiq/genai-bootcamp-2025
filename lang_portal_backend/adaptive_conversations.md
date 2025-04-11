# Adaptive Conversation Application

## Overview

Create an application that can have an adaptive conversation in Urdu

The application should feel natural and adaptive to the user's previous answers

Build a Python-based adaptive conversational application in Urdu using a large language model (LLM) for dynamic dialogue generation.

It needs to integrate into the existing application. It's entry point is the study_activities page.

It will be on the endpoint `http://localhost:5173/apps/adaptive-conversations`

## Key Features:

- The system should converse exclusively in Urdu, adapting its tone and content based on user input.
- Use Amazon Bedrock Embeddings (amazon.titan-embed-text-v1) to generate vector representations of each user and assistant utterance.
- Store and retrieve these embeddings using ChromaDB for semantic search and memory.
- Supports different knowledge levels (ابتدائی/beginner, درمیانہ/intermediate, ماہر/advanced) to adjust response complexity.
- Integrate a conversational loop:

  - Accept user input in Urdu.
  - Embed the input with Amazon Bedrock Embeddings.
  - Search ChromaDB for similar past embeddings to retain context and improve response relevance.
  - Pass relevant retrieved context along with the current user input into the LLM prompt.
  - Generate an Urdu response from the LLM (using Claude model).
  - Store both input and output embeddings in ChromaDB.
  

## System Architecture Overview

### Frontend (React)

- Simple chat interface in Urdu with RTL support
- Knowledge level selection (beginner, intermediate, advanced)
- Option to start new conversations
- Sends/receives messages via Django API using axios
- Persistent conversation history using localStorage

### Backend (Django)

- REST API (Django REST Framework) to handle:
  - Message submission
  - Conversation context retrieval
  - LLM response generation
- Uses Amazon Bedrock for:
  - Titan Embeddings (amazon.titan-embed-text-v1) for vector representations
  - Claude model for generating high-quality Urdu responses
- Stores/retrieves messages and embeddings in ChromaDB
- Tracks user knowledge level and adjusts response difficulty

### ChromaDB

- Stores
  - User utterances
  - Assistant responses
  - Embeddings
  - Metadata like user ID, timestamp, conversation ID, knowledge level

## API Endpoints

### 1. Send Message

**Endpoint:** `/api/adaptive-conversations/message/`

**Method:** POST

**Request Body:**
```json
{
  "message": "آپ کیسے ہیں؟",
  "user_id": "user-1",
  "conversation_id": "2208b084-c297-46ff-83cf-156c319181d9",
  "knowledge_level": "beginner",
  "topic": "general"
}
```

**Response:**
```json
{
  "response": "میں ٹھیک ہوں، شکریہ! آپ کیسے ہیں؟",
  "conversation_id": "2208b084-c297-46ff-83cf-156c319181d9",
  "knowledge_level": "beginner"
}
```

**Notes:**
- `conversation_id` is optional in the request. If not provided, a new conversation will be created.
- `knowledge_level` can be "beginner", "intermediate", or "advanced".
- `topic` is optional and helps guide the conversation context.

### 2. Get Conversation History

**Endpoint:** `/api/adaptive-conversations/history/{conversation_id}`

**Method:** GET

**Query Parameters:**
- `user_id`: The ID of the user (required)

**Response:**
```json
{
  "conversation_id": "2208b084-c297-46ff-83cf-156c319181d9",
  "user_id": "user-1",
  "messages": [
    {
      "text": "آپ کیسے ہیں؟",
      "role": "user",
      "timestamp": "2025-04-11T08:00:00.000Z",
      "knowledge_level": "beginner",
      "topic": "general"
    },
    {
      "text": "میں ٹھیک ہوں، شکریہ! آپ کیسے ہیں؟",
      "role": "assistant",
      "timestamp": "2025-04-11T08:00:01.000Z",
      "knowledge_level": "beginner",
      "topic": "general"
    }
  ]
}
```

**Notes:**
- For new conversations, an empty `messages` array will be returned.
- Messages are sorted by timestamp in ascending order.

## Requirements

### Frontend (React)

- Urdu chat interface (RTL layout)
- Knowledge level selection dropdown
- Submit user messages to Django backend
- Display assistant responses
- Support for starting new conversations

### Backend (Django):

- API endpoint to receive a message from the frontend
- Generate Amazon Bedrock Embeddings (amazon.titan-embed-text-v1) for user input and store it in ChromaDB
- Retrieve relevant past context from ChromaDB for that user/conversation
- Format prompts appropriately for the Claude model
- Return responses in proper JSON format

## Behavioral Logic

- Adjust assistant's tone and depth based on user's previous answers
- Track repeated errors and provide follow-up explanations or examples
- Optionally categorize user progress by topic

### Sample Use Case

- User answers a grammar question incorrectly
- Assistant replies in Urdu and English, saying:
"یہ تھوڑا غلط ہے، کیونکہ… [explanation]۔ آیئے ایک اور مثال دیکھتے ہیں۔"
- Then it asks a similar but simpler follow-up question

## Deliverables

- Django views/DRF endpoints
- ChromaDB integration
- Sample embedding function with Titan
- React chat UI (basic is fine)
- Urdu-only dialogue flow

### ChromaDB Implementation Details

- Store messages as documents
- Metadata should include:
  - user_id
  - role (user/assistant)
  - conversation_id
  - topic (optional)
  - knowledge_level (e.g., beginner/intermediate/advanced)
- Use similarity search to retrieve relevant context
- Configure with appropriate similarity threshold (0.7)
- Use Titan embeddings with dimension 1536

### Bonus (Optional)

- Categorize conversations by topics (e.g., Urdu grammar, literature, everyday conversation).
- Estimate user's progress over time using simple scoring logic.