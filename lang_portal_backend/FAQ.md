# Frequently Asked Questions (FAQ)

## General Questions

### Q: What languages does the application support?
**A:** The application primarily supports:
- Urdu (target language)
- Hindi (with automatic conversion to Urdu)
- English (as fallback)

### Q: Why are Hindi transcripts converted to Urdu?
**A:** Due to limited availability of Urdu transcripts, we use Hindi transcripts and convert them to Urdu script. This approach provides:
1. Wider content availability
2. Better accuracy through AWS Translate
3. Fallback character mapping when needed

### Q: How reliable is the Hindi to Urdu conversion?
**A:** We use a two-tier approach:
1. Primary: AWS Translate
   - Handles complex grammar
   - Maintains word order
   - Converts numerals
   - Preserves punctuation

2. Fallback: Character mapping
   - Direct script conversion
   - Special case handling
   - Post-processing fixes

## YouTube Integration

### Q: What types of videos work best?
**A:** Look for videos that:
- Have Hindi or Urdu captions
- Are educational content
- Have clear speech
- Are under 10 minutes

### Q: Why can't I find transcripts for some videos?
**A:** This could be because:
- Video has no captions
- Captions are disabled
- Language not supported
- Auto-generated captions unavailable

### Q: How do I get the video ID?
**A:** From a YouTube URL:
```
https://www.youtube.com/watch?v=oJC038O16o8
                               ^^^^^^^^^^^
                               This is the ID
```

## Question Generation

### Q: How are questions generated?
**A:** Using Amazon Bedrock:
- AI-based generation
- Multiple choice format
- Explanations included
- Quality validation

### Q: Can I customize the number of questions?
**A:** Yes, through:
- Configuration settings
- UI options
- API parameters

### Q: Why do some questions seem incorrect?
**A:** This might be due to:
- Complex language patterns
- Translation artifacts
- Content length
- Model limitations

## Audio Generation

### Q: Which text-to-speech service is used?
**A:** We use:
1. Amazon Polly (primary)
   - Better quality
   - Natural voice
   - Language support

2. gTTS (fallback)
   - Reliable backup
   - No AWS dependency
   - Basic functionality

### Q: Why does the audio sometimes sound different?
**A:** This happens when:
- Switching between Polly and gTTS
- Different voice models
- Text length variations
- Service availability

## Vector Store

### Q: How does exercise storage work?
**A:** Using ChromaDB:
- Semantic search enabled
- Metadata filtering
- Exercise versioning
- Efficient retrieval

### Q: Can I search for similar exercises?
**A:** Yes, through:
- Semantic similarity
- Language filtering
- Content matching
- Customizable thresholds

## Technical Issues

### Q: What AWS permissions do I need?
**A:** Required permissions:
```json
{
    "Version": "2012-10-01",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "translate:TranslateText",
                "bedrock:InvokeModel",
                "polly:SynthesizeSpeech"
            ],
            "Resource": "*"
        }
    ]
}
```

### Q: How do I handle AWS service errors?
**A:** The system:
1. Uses fallback systems
2. Retries operations
3. Provides error messages
4. Logs issues

### Q: What are the system requirements?
**A:** Minimum requirements:
- Python 3.8+
- 4GB RAM
- 1GB disk space
- Internet connection

## Performance

### Q: How is audio caching handled?
**A:** Through:
- Session state storage
- Unique cache keys
- TTL management
- Memory optimization

### Q: What affects processing speed?
**A:** Key factors:
1. Video length
2. Transcript availability
3. AWS service response
4. Network connection

## Security

### Q: How is rate limiting implemented?
**A:** Through:
- Request counting
- Time windows
- User tracking
- Service quotas

### Q: Is content moderation available?
**A:** Yes, we check:
- Text safety
- Language validity
- Content appropriateness
- User inputs

## Support

### Q: Where can I find more help?
**A:** Check these resources:
1. [README.md](README.md) - Overview
2. [QUICKSTART.md](QUICKSTART.md) - Getting started
3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
4. [API.md](API.md) - API documentation
5. [STREAMLIT_APP.md](STREAMLIT_APP.md) - UI guide

### Q: How do I report issues?
**A:** You can:
1. Check existing issues
2. Create detailed reports
3. Include error logs
4. Provide examples

### Q: Can I contribute to the project?
**A:** Yes! See:
1. [DEVELOPMENT.md](DEVELOPMENT.md) - Dev guide
2. [CONTRIBUTING.md](CONTRIBUTING.md) - Guidelines
3. GitHub issues
4. Pull requests
