from youtube_transcript_api import YouTubeTranscriptApi
import chromadb
import os
from typing import List, Dict
import re

class ListeningService:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(name="listening_exercises")

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL."""
        video_id_match = re.search(r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)', url)
        if not video_id_match:
            raise ValueError("Invalid YouTube URL")
        return video_id_match.group(1)

    def get_transcript(self, video_url: str) -> List[Dict]:
        """Get transcript from YouTube video."""
        try:
            video_id = self.extract_video_id(video_url)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            raise Exception(f"Failed to get transcript: {str(e)}")

    def store_transcript(self, video_url: str, transcript: List[Dict]):
        """Store transcript in vector database."""
        video_id = self.extract_video_id(video_url)
        texts = [item['text'] for item in transcript]
        self.collection.add(
            documents=texts,
            metadatas=[{"video_id": video_id, "start": item['start']} for item in transcript],
            ids=[f"{video_id}_{i}" for i in range(len(texts))]
        )

    def generate_questions(self, transcript: List[Dict], num_questions: int = 5) -> List[Dict]:
        """Generate listening comprehension questions from transcript."""
        # In a real implementation, this would use an LLM to generate questions
        # For now, we'll return a simple example
        return [{
            "question": "What is being discussed in this segment?",
            "timestamp": segment['start'],
            "text": segment['text'],
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A"
        } for segment in transcript[:num_questions]]

    def get_questions_for_video(self, video_url: str) -> List[Dict]:
        """Get or generate questions for a video."""
        transcript = self.get_transcript(video_url)
        self.store_transcript(video_url, transcript)
        return self.generate_questions(transcript)

    def get_transcript_with_stats(self, video_url: str) -> Dict:
        """Get transcript and generate statistics."""
        transcript = self.get_transcript(video_url)
        
        # Calculate statistics
        total_duration = sum(segment['duration'] for segment in transcript)
        total_words = sum(len(segment['text'].split()) for segment in transcript)
        avg_words_per_minute = (total_words / total_duration) * 60
        
        # Get word frequency
        words = [word.lower() for segment in transcript for word in segment['text'].split()]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 10 most frequent words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats = {
            "total_duration": round(total_duration, 2),
            "total_words": total_words,
            "avg_words_per_minute": round(avg_words_per_minute, 2),
            "segments_count": len(transcript),
            "top_words": dict(top_words)
        }
        
        return {
            "transcript": transcript,
            "statistics": stats
        }
