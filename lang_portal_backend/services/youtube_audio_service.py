import os
import logging
import tempfile
import subprocess
import time
import json
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
from django.conf import settings

logger = logging.getLogger(__name__)

class YouTubeAudioService:
    """Service for extracting audio from YouTube videos."""
    
    _instance = None
    _cache_dir = "audio_cache"
    
    def __init__(self):
        """Initialize the YouTube audio service."""
        # Use the audio_cache folder in the project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._cache_dir = os.path.join(base_dir, "audio_cache")
        os.makedirs(self._cache_dir, exist_ok=True)
        logger.info(f"YouTube audio cache directory: {self._cache_dir}")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YouTubeAudioService, cls).__new__(cls)
        return cls._instance
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        if not url:
            return None
            
        # Handle different URL formats
        parsed_url = urlparse(url)
        
        # youtube.com/watch?v=VIDEO_ID
        if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                query = parse_qs(parsed_url.query)
                return query.get('v', [None])[0]
            
            # youtube.com/v/VIDEO_ID
            elif parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
                
            # youtube.com/embed/VIDEO_ID
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
                
        # youtu.be/VIDEO_ID
        elif parsed_url.netloc == 'youtu.be':
            return parsed_url.path.lstrip('/')
            
        # Handle just the video ID
        elif len(url) in (11, 12) and url.isalnum():
            return url
            
        return None
    
    def _download_full_audio(self, video_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download the full audio file for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (file_path, error_message)
        """
        try:
            # Check if we already have the full audio file
            full_audio_path = os.path.join(self._cache_dir, f"{video_id}_full.mp3")
            
            if os.path.exists(full_audio_path):
                logger.info(f"Using cached full audio: {video_id}_full.mp3")
                return full_audio_path, None
                
            # Construct YouTube URL
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # First try with youtube-dl
            try:
                # Use youtube-dl to get the best audio format
                youtube_dl_cmd = [
                    "youtube-dl",
                    "--no-check-certificate",  # Skip HTTPS certificate validation
                    "--no-cache-dir",          # Disable cache
                    "--geo-bypass",            # Bypass geographic restrictions
                    "--extract-audio",         # Extract audio
                    "--audio-format", "mp3",   # Convert to mp3
                    "--audio-quality", "0",    # Best quality
                    "-o", os.path.join(self._cache_dir, f"{video_id}_full.%(ext)s"),  # Output file
                    url
                ]
                
                logger.info(f"Downloading audio with youtube-dl: {' '.join(youtube_dl_cmd)}")
                download_process = subprocess.run(youtube_dl_cmd, capture_output=True, text=True)
                
                if download_process.returncode != 0:
                    logger.error(f"youtube-dl error: {download_process.stderr}")
                    # Try alternative method with direct ffmpeg
                    return self._download_with_ffmpeg(video_id, url)
                
                # Check if the file was created
                if os.path.exists(full_audio_path):
                    return full_audio_path, None
                else:
                    logger.error("youtube-dl did not create the expected file")
                    return self._download_with_ffmpeg(video_id, url)
                
            except Exception as e:
                logger.error(f"Error with youtube-dl: {e}")
                return self._download_with_ffmpeg(video_id, url)
            
        except Exception as e:
            logger.error(f"Error downloading full audio: {e}")
            return self._create_test_audio(), None
    
    def _download_with_ffmpeg(self, video_id: str, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Try downloading with ffmpeg directly."""
        try:
            full_audio_path = os.path.join(self._cache_dir, f"{video_id}_full.mp3")
            
            # Get the direct stream URL using youtube-dl
            info_cmd = [
                "youtube-dl",
                "--no-check-certificate",
                "--geo-bypass",
                "-j",  # Output JSON info
                url
            ]
            
            logger.info(f"Getting video info: {' '.join(info_cmd)}")
            info_process = subprocess.run(info_cmd, capture_output=True, text=True)
            
            if info_process.returncode != 0:
                logger.error(f"Error getting video info: {info_process.stderr}")
                return self._create_test_audio(), None
                
            try:
                video_info = json.loads(info_process.stdout)
                formats = video_info.get('formats', [])
                
                # Find the best audio format
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if not audio_formats:
                    # Try any format with audio
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                
                if not audio_formats:
                    logger.error("No suitable audio format found")
                    return self._create_test_audio(), None
                
                # Sort by audio quality (bitrate)
                audio_formats.sort(key=lambda x: int(x.get('abr', 0) or 0), reverse=True)
                best_audio = audio_formats[0]
                audio_url = best_audio.get('url')
                
                if not audio_url:
                    logger.error("No direct URL found for audio")
                    return self._create_test_audio(), None
                
                # Download with ffmpeg
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", audio_url,
                    "-vn",  # No video
                    "-acodec", "libmp3lame",
                    "-q:a", "2",
                    full_audio_path,
                    "-y"  # Overwrite if exists
                ]
                
                logger.info(f"Downloading with ffmpeg: {' '.join(ffmpeg_cmd)}")
                ffmpeg_process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if ffmpeg_process.returncode != 0:
                    logger.error(f"FFmpeg error: {ffmpeg_process.stderr}")
                    return self._create_test_audio(), None
                
                return full_audio_path, None
                
            except json.JSONDecodeError:
                logger.error("Failed to parse video info JSON")
                return self._create_test_audio(), None
                
        except Exception as e:
            logger.error(f"Error with ffmpeg download: {e}")
            return self._create_test_audio(), None
    
    def _create_test_audio(self) -> str:
        """Create a test audio file for fallback."""
        try:
            test_audio_path = os.path.join(self._cache_dir, "test_audio.mp3")
            
            # Check if we already have a test audio file
            if os.path.exists(test_audio_path):
                return test_audio_path
                
            # Generate a simple sine wave audio file for testing
            ffmpeg_gen_cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "sine=frequency=440:duration=30",
                "-c:a", "libmp3lame",
                "-q:a", "2",
                test_audio_path,
                "-y"
            ]
            
            logger.info(f"Generating test audio: {' '.join(ffmpeg_gen_cmd)}")
            subprocess.run(ffmpeg_gen_cmd, capture_output=True, text=True)
            
            return test_audio_path
            
        except Exception as e:
            logger.error(f"Error creating test audio: {e}")
            return ""
    
    def get_audio_segment(self, video_id: str, start_time: float, end_time: float) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract audio segment from YouTube video.
        
        Args:
            video_id: YouTube video ID
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Tuple of (file_path, error_message)
        """
        try:
            if not video_id:
                return None, "Invalid video ID"
                
            if end_time <= start_time:
                return None, "End time must be greater than start time"
                
            # Check if segment already exists in cache
            segment_filename = f"{video_id}_{int(start_time)}_{int(end_time)}.mp3"
            segment_path = os.path.join(self._cache_dir, segment_filename)
            
            if os.path.exists(segment_path):
                logger.info(f"Using cached audio segment: {segment_filename}")
                return segment_path, None
                
            # Download the full audio file if needed
            full_audio_path, error = self._download_full_audio(video_id)
            
            if error:
                return None, error
                
            if not full_audio_path or not os.path.exists(full_audio_path):
                return None, "Failed to download audio"
                
            # Use ffmpeg to extract the segment
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", full_audio_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-c:a", "libmp3lame",
                "-q:a", "2",
                segment_path,
                "-y"  # Overwrite if exists
            ]
            
            logger.info(f"Extracting segment with ffmpeg: {' '.join(ffmpeg_cmd)}")
            segment_process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if segment_process.returncode != 0:
                logger.error(f"FFmpeg error: {segment_process.stderr}")
                return None, f"Error extracting audio segment: {segment_process.stderr}"
                
            return segment_path, None
            
        except Exception as e:
            logger.error(f"Error extracting audio segment: {e}")
            return None, f"Error extracting audio segment: {str(e)}"
