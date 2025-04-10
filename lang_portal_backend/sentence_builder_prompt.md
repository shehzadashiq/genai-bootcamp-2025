# Sentence Builder

## Business Goal

You are an Applied AI Engineer and you have been tasked to build a Sentence Builder App which will help users learn to construct grammatically correct Urdu sentences interactively. 

Create a full-stack web application called Urdu Sentence Builder that helps users learn to construct grammatically correct Urdu sentences interactively. The frontend should be built using React, and the backend should be powered by Django and Django REST Framework.

Use ChromaDB as the vector database for storing and retrieving sentence embeddings.

It needs to integrate into the existing application. It's entry point is the study_activities page.

It will be on the endpoint `http://localhost:5173/apps/sentence-builder`   

## Core Features

### Interactive Sentence Construction

Allow users to drag and drop or select words to form a grammatically correct Urdu sentence.

Provide feedback on whether the constructed sentence is valid or suggest corrections.

### Word Categories

Categorize words by parts of speech: nouns, verbs, adjectives, pronouns, etc.

Let users pick words from dropdowns or cards based on the category.

### Backend Logic (Django)

Expose APIs to:

Fetch words categorized by type.

Submit a constructed sentence for validation.

Return grammar corrections or suggestions.

Store a list of valid sentence structures or use rule-based grammar validation.

### Frontend (React)

- Display Urdu words in a user-friendly interface (supporting Right-to-Left text).
- Allow real-time sentence construction and preview.
- Show validation results or suggestions from the backend.
- UI that supports Right-to-Left (RTL) Urdu text rendering.
- Word bank categorized by part of speech (noun, verb, adjective, etc.).
- Submit button that sends sentence to backend API and displays feedback.
- Highlight grammar issues or suggest improvements.

## Vector Store (ChromaDB)

- Run embedded inside the Django backend.
- Store Urdu sentence embeddings with metadata (category, usage, level, etc.).
- Perform similarity search using cosine distance.
- Use persistent storage for embeddings (persist_directory).
- Support for Roman Urdu to Urdu conversion (using transliteration models).

### Optional Features

- A database of common sentence patterns
- Audio pronunciation for each word using Google TTS
- Sentence pattern templates
- Support for Roman Urdu input and translation to proper Urdu

## Tech Stack

- Frontend: React, Tailwind CSS (optional), axios (for API calls)
- Backend: Python, Django, Django REST Framework
- Database: SQLite
- RAG Vector Store DB: ChromaDB (With Persistence)

## Notes

- Urdu text must be displayed correctly and support Right-to-Left direction in Nastaleeq
- Use Unicode-compliant Urdu font (e.g., Noto Nastaliq Urdu)
- Ensure cross-browser compatibility for rendering Urdu script.
- Backend should expose clear, well-documented API endpoints.
- Keep ChromaDB persistent across app restarts using persist_directory.
- APIs should return responses in JSON.

## Deliverables

- A Django project with APIs for sentence validation using RAG and ChromaDB.
- A React frontend with Urdu RTL support and sentence builder UI.
- Seed data for common Urdu words and example sentence structures. The Database needs to contain at least 1000 words.
- Seed dataset of Urdu words, sentences, and their embeddings stored in ChromaDB.
- Sample RAG pipeline with embedded query → retrieve → suggest workflow.