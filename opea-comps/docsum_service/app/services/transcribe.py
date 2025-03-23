import boto3
import logging
import os
import tempfile
from typing import Optional
import time
import json
import aiohttp
import requests
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class TranscribeService:
    def __init__(self):
        self.client = boto3.client('transcribe')
        self.s3 = boto3.client('s3')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("AWS_BUCKET_NAME environment variable is required")
            
        self.supported_formats = {
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav',
            'audio/ogg': 'ogg'
        }
        
        self.supported_video_formats = {
            'video/mp4': 'mp4',
            'video/mpeg': 'mpeg',
            'video/ogg': 'ogg'
        }

    async def extract_audio_from_video(self, video_content: bytes, mime_type: str) -> tuple[bytes, str]:
        """Extract audio from video file."""
        if mime_type not in self.supported_video_formats:
            raise ValueError(f"Unsupported video format: {mime_type}")

        # Save video content to temporary file
        video_ext = self.supported_video_formats[mime_type]
        with tempfile.NamedTemporaryFile(suffix=f'.{video_ext}', delete=False) as video_file:
            video_file.write(video_content)
            video_file.flush()
            video_path = video_file.name

        try:
            # Extract audio using moviepy
            audio_path = video_path + '.mp3'
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path)
            video.close()

            # Read the extracted audio
            with open(audio_path, 'rb') as audio_file:
                audio_content = audio_file.read()

            return audio_content, 'audio/mpeg'

        finally:
            # Clean up temporary files
            try:
                os.unlink(video_path)
                os.unlink(audio_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {str(e)}")

    async def transcribe_audio(self, file_content: bytes, mime_type: str) -> Optional[str]:
        """Transcribe audio content using AWS Transcribe."""
        try:
            # If it's a video, extract the audio first
            if mime_type in self.supported_video_formats:
                logger.info("Extracting audio from video file")
                file_content, mime_type = await self.extract_audio_from_video(file_content, mime_type)

            if mime_type not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {mime_type}")

            # Create a temporary file
            ext = self.supported_formats[mime_type]
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                tmp_file_path = tmp_file.name

            try:
                # Upload to S3
                job_name = f"transcribe-{int(time.time())}"
                s3_key = f"uploads/{job_name}.{ext}"
                logger.info(f"Uploading audio to S3: {s3_key}")
                self.s3.upload_file(tmp_file_path, self.bucket_name, s3_key)

                # Start transcription job
                logger.info(f"Starting transcription job: {job_name}")
                self.client.start_transcription_job(
                    TranscriptionJobName=job_name,
                    Media={'MediaFileUri': f"s3://{self.bucket_name}/{s3_key}"},
                    MediaFormat=ext,
                    LanguageCode='en-US'
                )

                # Wait for completion
                while True:
                    status = self.client.get_transcription_job(TranscriptionJobName=job_name)
                    job_status = status['TranscriptionJob']['TranscriptionJobStatus']
                    
                    if job_status == 'COMPLETED':
                        # Get the transcript using requests instead of aiohttp
                        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                        logger.info(f"Transcription completed. Fetching from: {transcript_uri}")
                        
                        response = requests.get(transcript_uri)
                        response.raise_for_status()  # Raise exception for bad status codes
                        
                        transcript_json = response.json()
                        return transcript_json['results']['transcripts'][0]['transcript']
                    
                    elif job_status == 'FAILED':
                        failure_reason = status['TranscriptionJob'].get('FailureReason', 'Unknown error')
                        logger.error(f"Transcription job failed: {failure_reason}")
                        return None
                    
                    logger.info(f"Job status: {job_status}, waiting...")
                    time.sleep(5)

            finally:
                # Clean up
                try:
                    os.unlink(tmp_file_path)
                    logger.info(f"Deleting temporary file: {tmp_file_path}")
                    self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
                    logger.info(f"Deleting S3 object: {s3_key}")
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup error: {str(cleanup_error)}")

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
            return None
