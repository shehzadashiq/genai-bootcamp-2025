# Streamlit Application Guide

## Overview

The Language Learning Portal is built using Streamlit, providing an interactive web interface for language learning with a focus on Urdu listening comprehension. The application offers three main modes of operation and integrates with various AWS services for enhanced functionality.

## Getting Started

### Running the App

1. Start the application:
```bash
streamlit run listening_app.py
```

2. Access the interface:
- Open browser at `http://localhost:8501`
- Default credentials in `.env` file

### Interface Layout

```
├── Sidebar
│   └── Mode Selection
│       ├── YouTube Exercise
│       ├── Practice
│       └── My Exercises
└── Main Content
    ├── Title
    ├── Mode-specific Interface
    └── Exercise Display
```

## Application Modes

### 1. YouTube Exercise Mode

#### Interface Elements
```python
st.title("Language Listening Practice")
st.write("## Create Exercise from YouTube")
video_id = st.text_input("Enter YouTube Video ID")
create_button = st.button("Create Exercise")
```

#### Usage Steps
1. Enter YouTube Video ID
   - Example: `oJC038O16o8`
   - Format: 11-character string
   - Source: YouTube URL after `v=`

2. Click "Create Exercise"
   - Progress spinner appears
   - System processes video:
     1. Fetches transcript
     2. Converts script (if needed)
     3. Generates questions
     4. Creates audio

3. View Exercise
   ```
   ├── Video Preview
   ├── Transcript Text
   ├── Audio Player
   └── Questions Section
       ├── Question Text
       ├── Multiple Choice Options
       └── Show Answer Button
   ```

### 2. Practice Mode

#### Interface Elements
```python
st.write("## Practice Exercises")
text = st.text_area("Enter text for practice")
generate_button = st.button("Generate Exercise")
```

#### Usage Steps
1. Enter Custom Text
   - Paste or type text
   - Supports Hindi/Urdu script
   - Maximum length: 2000 characters

2. Click "Generate Exercise"
   - System processes text:
     1. Converts script (if needed)
     2. Generates questions
     3. Creates audio

3. Practice Interface
   ```
   ├── Original Text
   ├── Audio Player
   └── Questions Section
       ├── Question Text
       ├── Multiple Choice Options
       └── Show Answer Button
   ```

### 3. My Exercises Mode

#### Interface Elements
```python
st.write("## My Exercises")
exercises = vector_store.list_exercises()
for exercise in exercises:
    st.write(f"### Exercise {exercise['id']}")
    load_button = st.button(f"Load Exercise {exercise['id']}")
```

#### Usage Steps
1. View Exercise List
   - Displays saved exercises
   - Shows exercise metadata
   - Sort by date/similarity

2. Load Exercise
   - Click on exercise
   - System retrieves:
     1. Stored text
     2. Generated questions
     3. Cached audio

3. Exercise Interface
   - Same as YouTube/Practice modes
   - Additional options:
     - Delete exercise
     - Share exercise
     - Update notes

## Session State Management

### Key States
```python
# Initialize states
if 'exercises' not in st.session_state:
    st.session_state.exercises = []
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = None
if 'audio_cache' not in st.session_state:
    st.session_state.audio_cache = {}
```

### Cache Management
```python
# Audio caching
cache_key = f"{text}:{language}"
if cache_key in st.session_state.audio_cache:
    return st.session_state.audio_cache[cache_key]
```

## Component Details

### 1. Audio Player
```python
st.audio(
    base64.b64decode(exercise['audio']),
    format='audio/mp3'
)
```
- Supports: MP3 format
- Controls: Play, Pause, Seek
- Volume control available

### 2. Question Display
```python
for i, q in enumerate(exercise['questions']):
    st.write(f"### Question {i+1}")
    st.write(q['question'])
    
    # Options
    for option in q['options']:
        st.write(option)
    
    # Answer button
    if st.button(f"Show Answer {i+1}"):
        st.write(f"Correct Answer: {q['options'][q['correct_answer']]}")
        st.write(f"Explanation: {q['explanation']}")
```
- Multiple choice format
- Interactive answer reveal
- Explanation provided

### 3. Progress Indicators
```python
with st.spinner("Creating exercise..."):
    exercise = app.create_exercise_from_youtube(video_id)
```
- Spinner during processing
- Progress bars where applicable
- Error messages on failure

## Styling and Layout

### Custom Theme
```python
st.set_page_config(
    page_title="Language Learning Portal",
    page_icon="🎯",
    layout="wide"
)
```

### CSS Customization
```python
st.markdown("""
<style>
.stButton button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 24px;
    border-radius: 4px;
}
.stAudio {
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)
```

## Error Handling

### User Feedback
```python
try:
    # Operation code
except Exception as e:
    st.error(f"Error: {str(e)}")
    st.write("Please check your configuration and try again.")
```

### Progress Messages
```python
with st.spinner("Operation in progress..."):
    try:
        result = long_running_operation()
        st.success("Operation completed!")
    except Exception as e:
        st.error("Operation failed")
```

## Performance Tips

### 1. Caching
- Use `@st.cache_data` for data operations
- Use `@st.cache_resource` for resource initialization
- Clear cache when needed: `st.cache_data.clear()`

### 2. Session State
- Store user preferences
- Cache audio data
- Maintain exercise history

### 3. Component Updates
- Use callbacks for state updates
- Avoid unnecessary recomputation
- Batch similar operations

## Deployment

### Local Development
```bash
streamlit run listening_app.py --server.port 8501
```

### Production
```bash
streamlit run listening_app.py \
    --server.port 80 \
    --server.address 0.0.0.0 \
    --server.maxUploadSize 5
```

## Configuration

### Streamlit Config
```yaml
# .streamlit/config.toml
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 5

[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### Environment Variables
```bash
# .env
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5
```

## Troubleshooting

### Common Issues

1. **App Won't Start**
   - Check port availability
   - Verify Python environment
   - Confirm dependencies

2. **Slow Performance**
   - Clear cache
   - Reduce batch sizes
   - Monitor memory usage

3. **UI Issues**
   - Clear browser cache
   - Check CSS loading
   - Verify component updates

### Debug Mode
```bash
streamlit run listening_app.py --logger.level=debug
```

## Best Practices

1. **State Management**
   - Use session state for user data
   - Clear cache appropriately
   - Handle state transitions

2. **Error Handling**
   - Provide clear error messages
   - Use try-except blocks
   - Log errors properly

3. **UI/UX**
   - Consistent styling
   - Clear navigation
   - Responsive design

4. **Performance**
   - Cache expensive operations
   - Batch API calls
   - Optimize resource usage
