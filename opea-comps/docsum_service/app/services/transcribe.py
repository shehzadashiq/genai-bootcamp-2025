import boto3
import logging
import os
import tempfile
from typing import Optional
import time
import json
import aiohttp
import requests

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

    async def transcribe_audio(self, file_content: bytes, mime_type: str) -> Optional[str]:
        """Transcribe audio content using AWS Transcribe."""
        if mime_type not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {mime_type}")

        try:
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
