import streamlit as st
import requests
import json
from typing import Dict, Optional, Union
import os
from enum import Enum
import tempfile
import mimetypes
from pathlib import Path
import base64
import time
import io

# API endpoints
API_URL = os.getenv("API_URL", "http://localhost:8002")  # For browser access
INTERNAL_API_URL = os.getenv("INTERNAL_API_URL", API_URL)  # For container-to-container communication

class ContentType(str, Enum):
    URL = "url"
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    YOUTUBE = "youtube"
    DATASET = "dataset"

def init_session_state():
    """Initialize session state variables"""
    if "audio_cache" not in st.session_state:
        st.session_state["audio_cache"] = {}
    
    # Initialize cache flags for each content type
    cache_flags = [
        "url_cache", "text_cache", "doc_cache", "img_cache",
        "audio_cache_flag", "video_cache", "youtube_cache", "dataset_cache"
    ]
    for flag in cache_flags:
        if flag not in st.session_state:
            st.session_state[flag] = True

def is_valid_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be" in url

def is_valid_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))

def get_audio_content(audio_path: str) -> Optional[bytes]:
    """Fetch audio content from API using internal URL"""
    try:
        url = f"{INTERNAL_API_URL}{audio_path}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.error(f"Error fetching audio: {str(e)}")
        return None

def display_summary(response_data: Dict):
    if not response_data:
        return

    st.subheader("Summary")
    st.write(response_data["summary"])
    
    st.subheader("Urdu Summary")
    st.write(response_data["translated_summary"])
    
    if "audio_paths" in response_data:
        st.subheader("Audio")
        # st.write("Debug - Audio paths:", response_data["audio_paths"])  # Debug line
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("English Audio")
            if response_data["audio_paths"].get("en_audio"):
                audio_path = response_data["audio_paths"]["en_audio"]
                audio_content = get_audio_content(audio_path)
                if audio_content:
                    st.audio(audio_content, format='audio/mp3')
        
        with col2:
            st.write("Urdu Audio")
            if response_data["audio_paths"].get("ur_audio"):
                audio_path = response_data["audio_paths"]["ur_audio"]
                audio_content = get_audio_content(audio_path)
                if audio_content:
                    st.audio(audio_content, format='audio/mp3')

def process_url(url: str, use_cache: bool = True):
    try:
        with st.spinner('Generating summary and audio...'):
            response = requests.post(
                f"{INTERNAL_API_URL}/summarize",
                json={
                    "content_type": ContentType.URL,
                    "content": url,
                    "use_cache": use_cache
                }
            )
            if response.status_code == 200:
                display_summary(response.json())
            else:
                st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def process_text(text: str, use_cache: bool = True):
    try:
        with st.spinner('Generating summary and audio...'):
            response = requests.post(
                f"{INTERNAL_API_URL}/summarize",
                json={
                    "content_type": ContentType.TEXT,
                    "content": text,
                    "use_cache": use_cache
                }
            )
            if response.status_code == 200:
                display_summary(response.json())
            else:
                st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def process_file(file, content_type: ContentType, use_cache: bool = True):
    try:
        with st.spinner('Processing file and generating summary...'):
            # Create a temporary file with the correct extension
            suffix = Path(file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file.flush()

                # Send the file for processing
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (file.name, f, file.type)}
                    data = {
                        'content_type': content_type.value,  # Use enum value
                        'use_cache': 'true' if use_cache else 'false'  # Form data should be strings
                    }
                    response = requests.post(
                        f"{INTERNAL_API_URL}/summarize/file",
                        files=files,
                        data=data
                    )

            os.unlink(tmp_file.name)  # Clean up the temporary file

            if response.status_code == 200:
                display_summary(response.json())
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    if 'detail' in error_json:
                        error_msg = str(error_json['detail'])
                except:
                    pass
                st.error(f"Error: {error_msg}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def process_youtube(url: str, use_cache: bool = True):
    try:
        with st.spinner('Extracting video transcript and generating summary...'):
            response = requests.post(
                f"{INTERNAL_API_URL}/summarize",
                json={
                    "content_type": ContentType.YOUTUBE,
                    "content": url,
                    "use_cache": use_cache
                }
            )
            if response.status_code == 200:
                display_summary(response.json())
            else:
                st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def main():
    st.set_page_config(
        page_title="Document Summary Service",
        page_icon="📄",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("Document Summary Service")
    st.write("Generate summaries from various content types in Urdu with audio")
    
    tabs = st.tabs([
        "URL", "Text", "Document", "Image",
        "Audio", "Video", "YouTube", "Dataset"
    ])
    
    # URL Tab
    with tabs[0]:
        st.subheader("URL Summary")
        url = st.text_input("Enter URL", key="url_input")
        use_cache = st.checkbox("Use Cache", value=True, key="url_cache")
        if st.button("Generate Summary", key="url_button"):
            if url:
                if is_valid_url(url):
                    process_url(url, use_cache)
                else:
                    st.error("Please enter a valid URL")
            else:
                st.error("Please enter a URL")
    
    # Text Tab
    with tabs[1]:
        st.subheader("Text Summary")
        text = st.text_area("Enter Text", key="text_input")
        use_cache = st.checkbox("Use Cache", value=True, key="text_cache")
        if st.button("Generate Summary", key="text_button"):
            if text:
                process_text(text, use_cache)
            else:
                st.error("Please enter some text")
    
    # Document Tab
    with tabs[2]:
        st.subheader("Document Summary")
        st.write("Supported formats: PDF, DOC, DOCX, TXT")
        doc_file = st.file_uploader("Upload Document", type=["pdf", "doc", "docx", "txt"], key="doc_upload")
        use_cache = st.checkbox("Use Cache", value=True, key="doc_cache")
        if doc_file:
            if st.button("Generate Summary", key="doc_button"):
                process_file(doc_file, ContentType.DOCUMENT, use_cache)
    
    # Image Tab
    with tabs[3]:
        st.subheader("Image Summary")
        st.write("Supported formats: JPG, PNG, TIFF")
        img_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "tiff"], key="img_upload")
        use_cache = st.checkbox("Use Cache", value=True, key="img_cache")
        if img_file:
            st.image(img_file, caption="Uploaded Image")
            if st.button("Generate Summary", key="img_button"):
                process_file(img_file, ContentType.IMAGE, use_cache)
    
    # Audio Tab
    with tabs[4]:
        st.subheader("Audio Summary")
        st.write("Supported formats: MP3, WAV")
        audio_file = st.file_uploader("Upload Audio", type=["mp3", "wav"], key="audio_upload")
        use_cache = st.checkbox("Use Cache", value=True, key="audio_cache_flag")
        if audio_file:
            st.audio(audio_file)
            if st.button("Generate Summary", key="audio_button"):
                process_file(audio_file, ContentType.AUDIO, use_cache)
    
    # Video Tab
    with tabs[5]:
        st.subheader("Video Summary")
        st.write("Supported formats: MP4")
        video_file = st.file_uploader("Upload Video", type=["mp4"], key="video_upload")
        use_cache = st.checkbox("Use Cache", value=True, key="video_cache")
        if video_file:
            st.video(video_file)
            if st.button("Generate Summary", key="video_button"):
                process_file(video_file, ContentType.VIDEO, use_cache)
    
    # YouTube Tab
    with tabs[6]:
        st.subheader("YouTube Summary")
        youtube_url = st.text_input("Enter YouTube URL", key="youtube_input")
        use_cache = st.checkbox("Use Cache", value=True, key="youtube_cache")
        if st.button("Generate Summary", key="youtube_button"):
            if youtube_url:
                if is_valid_youtube_url(youtube_url):
                    process_youtube(youtube_url, use_cache)
                else:
                    st.error("Please enter a valid YouTube URL")
            else:
                st.error("Please enter a YouTube URL")
    
    # Dataset Tab
    with tabs[7]:
        st.subheader("Dataset Summary")
        st.write("Supported formats: CSV, JSON, XLSX")
        dataset_file = st.file_uploader("Upload Dataset", type=["csv", "json", "xlsx"], key="dataset_upload")
        use_cache = st.checkbox("Use Cache", value=True, key="dataset_cache")
        if dataset_file:
            if st.button("Generate Summary", key="dataset_button"):
                process_file(dataset_file, ContentType.DATASET, use_cache)

if __name__ == "__main__":
    main()
