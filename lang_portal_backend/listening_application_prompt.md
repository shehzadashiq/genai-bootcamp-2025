# Listening Learning App

## Business Goal

You are an Applied AI Engineer and you have been tasked to build a Language Listening Comprehension App. 

There are practice listening comprehension examples for language learning tests on youtube.

Pull the youtube content, and use that to generate out similar style listening comprehension.

## Japanese Listening Examples on YouTube

- [https://www.youtube.com/watch?v=sY7L5cfCWno&ab_channel=TheNihongoNook](JLPT N5 JAPANESE LISTENING PRACTICE TEST 2024 WITH ANSWERS ちょうかい)

## Sample Urdu Listening Examples on YouTube

- [https://www.youtube.com/watch?v=l4C4MGhCORg&ab_channel=LearnUrduwithUrduPod101.com](20 Minutes of Urdu Listening Comprehension for Beginner)
- [https://www.youtube.com/watch?v=ERPpRU9R7l4&list=PLAW1UtJAglQHb_PgJQOoRcufH-pXmSeGU&ab_channel=LearnUrduwithUrduPod101.com](Urdu Listening Practice - At a Pakistani Bookstore)
- [https://www.youtube.com/watch?v=nkSvWptB2iQ&list=PLAW1UtJAglQHb_PgJQOoRcufH-pXmSeGU&index=2&ab_channel=LearnUrduwithUrduPod101.com](Urdu Listening Practice - At a Pakistani Restaurant)
- [https://www.youtube.com/watch?v=T_ztWECep-o&ab_channel=Mehfill%28TahirUbaidChaudhry%29](Talaffuz | A Masterclass On Urdu Pronunciation | Session 1 | Tahir Ubaid Chaudhry)
- [https://www.youtube.com/watch?v=a71y8_fWRcA&ab_channel=LooseTalk](Loose Talk Episode 251 [Subtitle Eng] | Moin Akhtar | Anwar Maqsood | ARY Digital)
- [https://www.youtube.com/watch?v=lr454mTPTlY&ab_channel=ACNDIGITALNETWORK](Moin Akhtar Interview | Old is Gold)
- [https://www.youtube.com/watch?v=oJC038O16o8&ab_channel=OnePaperMCQs](urdu class 1 tafheem| hindi urdu)


## Technical Uncertainty

- Videos with Urdu Transcripts are extremely limited and hard to find
- Videos with Hindi Transcripts do not translate well to Urdu script
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
- Use Amazon Bedrock for transcription and question generation.


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
- langchain
- faiss-cpu
- sentence-transformers