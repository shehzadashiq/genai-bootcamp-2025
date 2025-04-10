# Adaptive Conversation Application

## Overview

Create an application that can have an adaptive conversation in Urdu

The application should feel natural and adaptive to the user's previous answers

Build a Python-based adaptive conversational application in Urdu using a large language model (LLM) for dynamic dialogue generation.

It needs to integrate into the existing application. It's entry point is the study_activities page.

It will be on the endpoint `http://localhost:5173/apps/adaptive-conversations`

## Key Features:

- The system should converse exclusively in Urdu, adapting its tone and content based on user input.
- Use Amazon Titan Embeddings (amazon.titan-embed-text-v1) to generate vector representations of each user and assistant utterance.
- Store and retrieve these embeddings using ChromaDB for semantic search and memory.
- Integrate a conversational loop:

  - Accept user input in Urdu.
  - Embed the input with Amazon Titan Embeddings.
  - Search ChromaDB for similar past embeddings to retain context and improve response relevance.
  - Pass relevant retrieved context along with the current user input into the LLM prompt.
  - Generate an Urdu response from the LLM.
  - Store both input and output embeddings in ChromaDB.
  

## System Architecture Overview

### Frontend (React)

- Simple chat interface in Urdu
- Sends/receives messages via Django API (likely using fetch or axios)

### Backend (Django)

- REST API (Django REST Framework) to handle:
  - Message submission
  - Conversation context retrieval
  - LLM response generation
- Calls Amazon Titan to get embeddings
- Stores/retrieves messages and embeddings in ChromaDB
- Tracks user knowledge and adjusts response difficulty

### ChromaDB

- Stores
  - User utterances
  - Assistant responses
  - Embeddings
  - Metadata like user ID, timestamp, conversation ID

## Requirements

### Frontend (React)

- Urdu chat interface (RTL layout)
- Submit user messages to Django backend
- Display assistant responses

### Backend (Django):

- API endpoint to receive a message from the frontend
- Generate Amazon Titan Embeddings (amazon.titan-embed-text-v1) for user input and store it in ChromaDB
- Retrieve relevant past context from ChromaDB for that user/conversation
- Feed context + current user message to an LLM to generate a response (in Urdu)
- If user's response is incorrect or indicates confusion, gently explain the issue and offer help
- Return LLM response to frontend and store it (with embeddings) in ChromaDB

### ChromaDB

- Store messages as documents
- Metadata should include:
  - user_id
  - role (user/assistant)
  - conversation_id
  - topic (optional)
  - knowledge_level (e.g., beginner/intermediate/advanced)
 
## Behavioral Logic

- Adjust assistant’s tone and depth based on user’s previous answers
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
- `Sample embedding function with Titan
- React chat UI (basic is fine)
- Urdu-only dialogue flow

### Bonus (Optional)

- Categorize conversations by topics (e.g., Urdu grammar, literature, everyday conversation).
- Estimate user's progress over time using simple scoring logic.