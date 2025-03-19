import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DocSumService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize model and tokenizer
        self.model_name = "facebook/bart-large-cnn"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.model = self.model.to(self.device)
        
        # Set maximum input and output lengths
        self.max_input_length = 1024
        self.max_output_length = 256
    
    async def _fetch_content(self, url: str) -> str:
        """Fetch and extract text content from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Basic text cleaning
            text = ' '.join(text.split())
            
            return text
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            raise
    
    async def _chunk_text(self, text: str, max_length: int) -> list[str]:
        """Split text into chunks that fit within model's max input length."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_tokens = len(self.tokenizer.encode(word))
            if current_length + word_tokens > max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def _summarize_chunk(self, text: str) -> str:
        """Generate summary for a single chunk of text."""
        inputs = self.tokenizer(text, max_length=self.max_input_length, truncation=True, return_tensors="pt")
        inputs = inputs.to(self.device)
        
        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=self.max_output_length,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True
        )
        
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    async def generate_summary(self, url: str) -> str:
        """Generate summary for the content at the given URL."""
        try:
            # Fetch content
            content = await self._fetch_content(url)
            
            # Split into chunks if necessary
            chunks = await self._chunk_text(content, self.max_input_length)
            
            # Generate summary for each chunk
            chunk_summaries = []
            for chunk in chunks:
                summary = await self._summarize_chunk(chunk)
                chunk_summaries.append(summary)
            
            # Combine chunk summaries if necessary
            if len(chunk_summaries) > 1:
                combined_summary = " ".join(chunk_summaries)
                # Generate a final summary if the combined summary is too long
                if len(self.tokenizer.encode(combined_summary)) > self.max_input_length:
                    final_summary = await self._summarize_chunk(combined_summary)
                    return final_summary
                return combined_summary
            
            return chunk_summaries[0]
            
        except Exception as e:
            logger.error(f"Error generating summary for {url}: {str(e)}")
            raise
