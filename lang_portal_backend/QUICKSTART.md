# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Prerequisites
- Python 3.8+
- AWS account with access to:
  - Bedrock
  - Polly
  - Translate

### 2. Installation
```bash
# Clone and setup
git clone <repository-url>
cd lang_portal_backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create `.env` file:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

### 4. Run Application
```bash
streamlit run listening_app.py
```
Access at: http://localhost:8501

## 🎯 Quick Examples

### 1. YouTube Exercise
1. Get video ID from YouTube URL:
   ```
   https://youtube.com/watch?v=oJC038O16o8
                              ^^^^^^^^^^^
   ```
2. Paste ID in app
3. Click "Create Exercise"

### 2. Practice Mode
1. Paste Hindi/Urdu text
2. Click "Generate Exercise"
3. Practice with generated questions

### 3. My Exercises
1. Create exercises in YouTube/Practice mode
2. Access saved exercises here
3. Search by similarity

## 🛠️ Common Issues

### No Transcript Found
✅ Solution:
- Verify video has captions
- Try another video
- Check video ID format

### Script Conversion Fails
✅ Solution:
- Check AWS credentials
- System will use fallback
- Try shorter text

### Audio Generation Issues
✅ Solution:
- Check AWS credentials
- System uses gTTS fallback
- Verify text length

## 📱 Features

### Core
- YouTube transcript extraction
- Hindi → Urdu conversion
- Question generation
- Audio synthesis

### Storage
- ChromaDB vector store
- Exercise history
- Audio caching

### Languages
- Primary: Urdu
- Support: Hindi
- Fallback: English

## 🆘 Need Help?

### Documentation
- [Full Documentation](README.md)
- [API Guide](API.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Streamlit App Guide](STREAMLIT_APP.md)

### Support
- Check GitHub Issues
- Review AWS Docs
- Contact Support Team
