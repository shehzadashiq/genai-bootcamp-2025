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
    if "audio_cache" not in st.session_state:
        st.session_state.audio_cache = {}

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

def process_text(text: str):
    try:
        with st.spinner('Generating summary and audio...'):
            response = requests.post(
                f"{INTERNAL_API_URL}/summarize",
                json={
                    "content_type": ContentType.TEXT,
                    "content": text,
                    "use_cache": False
                }
            )
            if response.status_code == 200:
                display_summary(response.json())
            else:
                st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def process_file(file, content_type: ContentType):
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
                        'use_cache': 'true'  # Form data should be strings
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

def process_youtube(url: str):
    try:
        with st.spinner('Extracting video transcript and generating summary...'):
            response = requests.post(
                f"{INTERNAL_API_URL}/summarize",
                json={
                    "content_type": ContentType.YOUTUBE,
                    "content": url,
                    "use_cache": False
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
        "Audio/Video", "YouTube", "Dataset"
    ])
    
    # URL Tab
    with tabs[0]:
        st.subheader("URL Summary")
        url = st.text_input("Enter URL")
        use_cache = st.checkbox("Use Cache", value=True)
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
        text = st.text_area("Enter Text")
        if st.button("Generate Summary", key="text_button"):
            if text:
                process_text(text)
            else:
                st.error("Please enter some text")

    # Document Tab
    with tabs[2]:
        st.subheader("Document Summary")
        st.write("Supported formats: TXT, DOC, DOCX, PDF")
        doc_file = st.file_uploader(
            "Upload Document",
            type=["txt", "doc", "docx", "pdf"],
            key="doc_upload"
        )
        if doc_file is not None:
            if st.button("Generate Summary", key="doc_button"):
                process_file(doc_file, ContentType.DOCUMENT)

    # Image Tab
    with tabs[3]:
        st.subheader("Image Summary")
        st.write("Upload an image for OCR and summarization")
        image_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "jpeg", "png", "tiff"],
            key="image_upload"
        )
        if image_file is not None:
            st.image(image_file, caption="Uploaded Image")
            if st.button("Generate Summary", key="image_button"):
                process_file(image_file, ContentType.IMAGE)

    # Audio/Video Tab
    with tabs[4]:
        st.subheader("Audio/Video Summary")
        st.write("Upload an audio file for transcription and summarization")
        audio_file = st.file_uploader(
            "Upload Audio",
            type=["mp3", "wav", "ogg"],
            key="audio_upload"
        )
        if audio_file is not None:
            st.audio(audio_file)
            if st.button("Generate Summary", key="audio_button"):
                process_file(audio_file, ContentType.AUDIO)

    # YouTube Tab
    with tabs[5]:
        st.subheader("YouTube Summary")
        youtube_url = st.text_input("Enter YouTube URL")
        if st.button("Generate Summary", key="youtube_button"):
            if youtube_url:
                if is_valid_youtube_url(youtube_url):
                    process_youtube(youtube_url)
                else:
                    st.error("Please enter a valid YouTube URL")
            else:
                st.error("Please enter a YouTube URL")

    # Dataset Tab
    with tabs[6]:
        st.subheader("Dataset Summary")
        st.write("Upload structured data for summarization")
        dataset_file = st.file_uploader(
            "Upload Dataset",
            type=["csv", "json", "xlsx", "xls"],
            key="dataset_upload"
        )
        if dataset_file is not None:
            if st.button("Generate Summary", key="dataset_button"):
                process_file(dataset_file, ContentType.DATASET)

if __name__ == "__main__":
    main()
