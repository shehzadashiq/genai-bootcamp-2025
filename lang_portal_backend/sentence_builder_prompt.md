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

Display both masculine and feminine forms for verbs (e.g., کھاتا/کھاتی).

### Backend Logic (Django)

Expose APIs to:

Fetch words categorized by type.

Submit a constructed sentence for validation.

Return grammar corrections or suggestions.

Store a list of valid sentence structures or use rule-based grammar validation.

Support sentences with or without the Urdu full stop (۔).

### Frontend (React)

- Display Urdu words in a user-friendly interface (supporting Right-to-Left text).
- Allow real-time sentence construction and preview.
- Show validation results or suggestions from the backend.
- UI that supports Right-to-Left (RTL) Urdu text rendering.
- Word bank categorized by part of speech (noun, verb, adjective, etc.).
- Submit button that sends sentence to backend API and displays feedback.
- Highlight grammar issues or suggest improvements.
- Option for users to manually mark sentences as correct when automatic validation fails.
- Display common sentence patterns as a reference for users.

## Vector Store (ChromaDB)

- Run embedded inside the Django backend.
- Store Urdu sentence embeddings with metadata (category, usage, level, etc.).
- Perform similarity search using cosine distance with a configurable threshold (currently 0.5).
- Use persistent storage for embeddings (persist_directory).
- Support for Roman Urdu to Urdu conversion (using transliteration models).
- Handle variations in sentence structure and punctuation.

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
- Embeddings: Amazon Bedrock (Titan model)

## Notes

- Urdu text must be displayed correctly and support Right-to-Left direction in Nastaleeq
- Use Unicode-compliant Urdu font (e.g., Noto Nastaliq Urdu)
- Ensure cross-browser compatibility for rendering Urdu script.
- Backend should expose clear, well-documented API endpoints.
- Keep ChromaDB persistent across app restarts using persist_directory.
- APIs should return responses in JSON.
- Validation should be flexible to accommodate different writing styles.
- Full stop character (۔) should be optional for valid sentences.

## Deliverables

- A Django project with APIs for sentence validation using RAG and ChromaDB.
- A React frontend with Urdu RTL support and sentence builder UI.
- Seed data for common Urdu words and example sentence structures. The Database needs to contain at least 1000 words.
- Seed dataset of Urdu words, sentences, and their embeddings stored in ChromaDB.
- Sample RAG pipeline with embedded query → retrieve → suggest workflow.
- Manual validation option for user satisfaction.

## Valid Urdu Sentence Structures

The Sentence Builder validates various Urdu sentence structures. Below are examples of valid sentence patterns:

### Basic Sentence Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| فاعل + مفعول + فعل (حال) | Subject + Object + Verb (Present) | وہ کتاب پڑھتا ہے۔ | He reads a book. |
| فاعل + مفعول + فعل (ماضی) | Subject + Object + Verb (Past) | اُس نے کھانا کھایا۔ | He ate the food. |
| فاعل + مفعول + فعل (مستقبل) | Subject + Object + Verb (Future) | وہ اسکول جائے گا۔ | He will go to school. |
| فاعل + صفت + مفعول + فعل | Subject + Adjective + Object + Verb | میں گرم چائے پیتا ہوں۔ | I drink hot tea. |

### Continuous Tense Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| فاعل + مفعول + رہا/رہی/رہے + ہے/ہیں | Subject + Object + is/are + Verb-ing | وہ کہانی سنا رہا ہے۔ | He is telling a story. |
| فاعل + مفعول + رہا/رہی/رہے + تھا/تھی/تھے | Subject + Object + was/were + Verb-ing | وہ گانا گا رہا تھا۔ | He was singing a song. |
| فاعل + مفعول + رہا/رہی/رہے + ہوگا/ہوں گے | Subject + Object + will be + Verb-ing | وہ کام کر رہا ہوگا۔ | He will be working. |

### Perfect Tense Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| فاعل + مفعول + چکا/چکی/چکے + ہے/ہیں | Subject + Object + has/have + Verb (done) | وہ کھانا کھا چکا ہے۔ | He has eaten the food. |
| فاعل + مفعول + چکا/چکی/چکے + تھا/تھی/تھے | Subject + Object + had + Verb (done) | وہ خط لکھ چکا تھا۔ | He had written the letter. |
| فاعل + مفعول + چکا/چکی/چکے + ہوگا/ہوں گے | Subject + Object + will have + Verb (done) | وہ کام مکمل کر چکا ہوگا۔ | He will have completed the task. |

### Question Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| کیا + فاعل + مفعول + فعل؟ | Do/Does/Did + Subject + Verb + Object? | کیا وہ اسکول جاتا ہے؟ | Does he go to school? |
| سوالیہ لفظ + فاعل + مفعول + فعل؟ | WH-word + Subject + Verb + Object? | تم کیا کھا رہے ہو؟ | What are you eating? |

### Imperative Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| فعل + (مفعول) | Verb + (Object) | دروازہ بند کرو۔ | Close the door. |
| نہ + فعل + (مفعول) | Don't + Verb + (Object) | شور نہ مچاؤ۔ | Don't make noise. |

### Compound Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| فاعل + مفعول + فعل + conjunction + فاعل + مفعول + فعل | Subject + Verb + and/but + Subject + Verb | وہ کھیلتا ہے اور ہنستا ہے۔ | He plays and laughs. |
| اگر + شرط + تو + نتیجہ | If + condition + then + result | اگر وہ آئے گا، تو ہم چلیں گے۔ | If he comes, then we will go. |

### Advanced Structures

| Urdu Structure | English Structure | Example (Urdu) | Example (English) |
|----------------|-------------------|----------------|-------------------|
| مفعول + فعل (passive) + گیا/گئی/گئے + ہے/تھا/تھی | Object + was + Verb (passive) | خط لکھا گیا۔ | The letter was written. |
| فاعل + ہی + مفعول + فعل | Subject + only/emphasis + Verb | وہی آیا تھا۔ | He (and no one else) had come. |
| فاعل + مفعول + نہیں + فعل | Subject + not + Verb + Object | وہ سکول نہیں گیا۔ | He did not go to school. |

### Word-by-Word Analysis Example

For the sentence: "میں گرم چائے پیتا ہوں" (I drink hot tea)

| Word | Role | Type |
|------|------|------|
| میں | Subject (فاعل) | Pronoun |
| گرم | Modifier (صفت) | Adjective |
| چائے | Object (مفعول) | Noun |
| پیتا | Verb Root (فعل) | Present tense |
| ہوں | Auxiliary Verb | Present Auxiliary |