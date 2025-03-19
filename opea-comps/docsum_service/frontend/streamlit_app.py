import streamlit as st
import requests
import json
from typing import Optional
import os
import time

# Constants
API_URL = os.getenv("API_URL", "http://localhost:8002")
MAX_RETRIES = 3
RETRY_DELAY = 2

def validate_url(url: str) -> bool:
    """Basic URL validation."""
    return url.startswith(('http://', 'https://'))

def wait_for_api() -> bool:
    """Wait for API to be ready."""
    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(RETRY_DELAY)
    return False

def get_summary(url: str, use_cache: bool = True) -> Optional[dict]:
    """Get summary from the API."""
    try:
        # Check if API is ready
        if not wait_for_api():
            st.error("Could not connect to API service. Please try again later.")
            return None
            
        response = requests.post(
            f"{API_URL}/summarize",
            json={"url": url, "use_cache": use_cache}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Document Summarizer",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Document Summarizer")
    st.markdown("""
    This application summarizes web pages and provides the summary in Urdu with audio support.
    Simply enter a URL below to get started!
    """)
    
    # Display API status
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success("API service is ready!")
        else:
            st.warning("API service is not responding correctly")
    except requests.exceptions.RequestException:
        st.error("Could not connect to API service")
    
    # URL input
    url = st.text_input("Enter webpage URL:", key="url_input")
    col1, col2 = st.columns([1, 4])
    use_cache = col1.checkbox("Use cache", value=True)
    
    if col2.button("Generate Summary", type="primary"):
        if not url:
            st.warning("Please enter a URL")
        elif not validate_url(url):
            st.error("Please enter a valid URL (starting with http:// or https://)")
        else:
            with st.spinner("Generating summary..."):
                result = get_summary(url, use_cache)
                
                if result:
                    # Display original summary
                    st.subheader("English Summary")
                    st.write(result["summary"])
                    
                    # Display Urdu summary
                    st.subheader("Urdu Summary")
                    st.markdown(f'<div dir="rtl" lang="ur">{result["translated_summary"]}</div>', 
                              unsafe_allow_html=True)
                    
                    # Display audio player if available
                    if result.get("audio_url"):
                        st.subheader("Audio Version")
                        st.audio(result["audio_url"])
    
    # Add some spacing
    st.markdown("---")
    
    # Add footer
    st.markdown("""
    <div style='text-align: center'>
        <p>Built with ❤️ using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
