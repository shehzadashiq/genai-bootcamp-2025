# Listening Learning App

## Business Goal

You are an Applied AI Engineer and you have been tasked to build a Language Listening Comprehension App. 

There are practice listening comprehension examples for language learning tests on youtube.

Pull the youtube content, and use that to generate out similar style listening comprehension.

## Sample Urdu Listening Examples on YouTube

- [https://www.youtube.com/watch?v=l4C4MGhCORg&ab_channel=LearnUrduwithUrduPod101.com](20 Minutes of Urdu Listening Comprehension for Beginner)
- [https://www.youtube.com/watch?v=ERPpRU9R7l4&list=PLAW1UtJAglQHb_PgJQOoRcufH-pXmSeGU&ab_channel=LearnUrduwithUrduPod101.com](Urdu Listening Practice - At a Pakistani Bookstore)
- [https://www.youtube.com/watch?v=nkSvWptB2iQ&list=PLAW1UtJAglQHb_PgJQOoRcufH-pXmSeGU&index=2&ab_channel=LearnUrduwithUrduPod101.com](Urdu Listening Practice - At a Pakistani Restaurant)


## Technical Uncertainty

- Don’t know Urdu
- Accessing or storing documents as vector store with Sqlite3
- TSS (Text-to-Speech Synthesis) might not exist for Urdu OR might not be good enough.
- ASR (Automatic Speech Recognition) might not exist for Urdu OR might not be good enough.
- Can you pull transcripts for the target videos?

## Technical Requirements
- Youtube Transcript API
- LLM + Tool Use “Agent”
- Sqlite3 - Knowledge Base 
- Text to Speech (TTS) eg. Amazon Polly
- AI Coding Assistant eg. Amazon Developer Q, Windsurf, Cursor, Github Copilot
- Frontend eg. Streamlit.
- Guardrails
- (Optional) Speech to Text, (ASR) Transcribe. eg Amazon Transcribe. OpenWhisper
<!-- - Amazon Bedrock as my local machine is not powerful enough. -->


# Language Listening App Requirments

- Pulling Transcriptions from Youtube
- Format the data to be inserted into a vector store
- We fetch similar questions based on inputted topic
- Generate a question in the frontend UI
- Generate audio so students listen.

## Python Packages

- boto3
- youtube-transcript-api
- chromadb
- streamlit