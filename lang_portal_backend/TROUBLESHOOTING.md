# Troubleshooting Guide

## Common Issues and Solutions

### 1. Transcript Retrieval Issues

#### No Hindi/Urdu Transcript Available
**Symptoms:**
- Error: "No transcript found in any language"
- System falls back to English transcript
- No transcripts available

**Solutions:**
1. Verify video has captions:
   - Open video in YouTube
   - Check CC button is available
   - Try manual captions if auto-generated not available

2. Check video ID format:
   ```python
   # Correct format examples:
   oJC038O16o8  # 11 characters
   dQw4w9WgXcQ  # No special characters
   ```

3. Try alternative videos:
   - Look for videos with Hindi titles/descriptions
   - Check educational channels
   - Use videos from news sources

#### Hindi to Urdu Conversion Fails

**Symptoms:**
- AWS Translate error
- Character mapping issues
- Mixed script output

**Solutions:**
1. AWS Translate Issues:
   ```bash
   # Check AWS credentials
   aws configure list
   aws translate test-hi-ur --text "नमस्ते"
   ```

2. Verify IAM Permissions:
   ```json
   {
       "Version": "2012-10-01",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": "translate:TranslateText",
               "Resource": "*"
           }
       ]
   }
   ```

3. Character Mapping Fallback:
   - Check `language_service.py` logs
   - Verify character mappings in config
   - Monitor normalization rules

### 2. Question Generation Issues

#### JSON Parsing Errors

**Symptoms:**
- "Failed to parse question generation response as JSON"
- Invalid question format
- Missing fields in response

**Solutions:**
1. Check Bedrock Response:
   ```python
   # Verify response format
   {
       "questions": [
           {
               "question": "...",
               "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
               "correct_answer": 0,
               "explanation": "..."
           }
       ]
   }
   ```

2. Text Length:
   - Keep input text under 2000 tokens
   - Split long transcripts into sections
   - Remove special characters

3. Model Parameters:
   ```python
   # Adjust in config.py
   BEDROCK_MODEL_KWARGS = {
       "temperature": 0.7,  # Lower for more consistent output
       "top_p": 0.9,
       "max_tokens": 2000
   }
   ```

### 3. Audio Generation Issues

#### Polly Synthesis Fails

**Symptoms:**
- Error in audio generation
- Silent audio output
- gTTS fallback activates

**Solutions:**
1. Check Text Length:
   ```python
   # Maximum characters per request
   MAX_POLLY_CHARS = 3000
   
   # Split long text
   def chunk_text(text):
       return [text[i:i+MAX_POLLY_CHARS] 
               for i in range(0, len(text), MAX_POLLY_CHARS)]
   ```

2. Verify Voice Settings:
   ```python
   # config.py
   POLLY_VOICE_ID = "Aditi"  # Supports Hindi/Urdu
   POLLY_OUTPUT_FORMAT = "mp3"
   ```

3. Monitor AWS Quotas:
   - Characters per month
   - Concurrent requests
   - Neural TTS usage

### 4. Vector Store Issues

#### ChromaDB Connection Errors

**Symptoms:**
- Failed to initialize vector store
- Search returns no results
- Persistence errors

**Solutions:**
1. Check Directory Permissions:
   ```bash
   # Windows
   icacls ./chroma_db
   
   # Fix permissions
   icacls ./chroma_db /grant Users:F
   ```

2. Verify Embeddings:
   ```python
   # Test embedding generation
   from vector_store import VectorStore
   
   store = VectorStore()
   embedding = store.embeddings.embed_query("Test text")
   print(f"Embedding dimensions: {len(embedding)}")  # Should be 1536
   ```

3. Database Maintenance:
   ```python
   # Rebuild collections if needed
   import chromadb
   
   client = chromadb.Client()
   client.reset()  # Warning: Deletes all data
   ```

### 5. AWS Service Issues

#### Authentication Failures

**Symptoms:**
- AWS credential errors
- Service access denied
- Region configuration issues

**Solutions:**
1. Check Environment Variables:
   ```bash
   # Required variables
   echo %AWS_ACCESS_KEY_ID%
   echo %AWS_SECRET_ACCESS_KEY%
   echo %AWS_REGION%
   ```

2. Test AWS CLI:
   ```bash
   aws configure
   aws sts get-caller-identity
   ```

3. Verify Service Status:
   - Check AWS Service Health Dashboard
   - Monitor service quotas
   - Review CloudWatch logs

### 6. Application Startup Issues

#### Streamlit App Won't Start

**Symptoms:**
- Port already in use
- Module import errors
- Configuration missing

**Solutions:**
1. Check Port Usage:
   ```bash
   # Windows
   netstat -ano | findstr :8501
   taskkill /PID <PID> /F
   ```

2. Verify Dependencies:
   ```bash
   pip install -r requirements.txt
   pip list | findstr streamlit
   ```

3. Configuration Files:
   ```bash
   # Required files
   dir /b config.py
   dir /b .env
   dir /b vector_store_config.py
   ```

### 7. Performance Optimization

#### Slow Response Times

**Symptoms:**
- Long loading times
- High memory usage
- Delayed question generation

**Solutions:**
1. Cache Management:
   ```python
   # Clear Streamlit cache
   st.cache_data.clear()
   
   # Monitor cache size
   print(len(st.session_state.audio_cache))
   ```

2. Batch Processing:
   ```python
   # Process transcript segments in batches
   BATCH_SIZE = 5
   for i in range(0, len(segments), BATCH_SIZE):
       batch = segments[i:i+BATCH_SIZE]
       process_batch(batch)
   ```

3. Resource Monitoring:
   ```python
   # Log performance metrics
   import time
   
   start = time.time()
   result = operation()
   print(f"Operation took {time.time() - start:.2f}s")
   ```

## Logging

### Enable Debug Logging

Add to `config.py`:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Key Log Locations
1. Application Logs: `app.log`
2. Streamlit Logs: `~/.streamlit/logs/`
3. ChromaDB Logs: `./chroma_db/chroma.log`

## Support

For additional support:
1. Check GitHub Issues
2. Review AWS Documentation
3. Consult Streamlit Community
4. Examine CloudWatch Logs
