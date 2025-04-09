import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from .services.tts import TextToSpeechService
from services.youtube_audio_service import YouTubeAudioService

tts_service = TextToSpeechService()
youtube_audio_service = YouTubeAudioService()

@api_view(['POST'])
def synthesize_speech(request):
    """Generate audio for the given text."""
    text = request.data.get('text')
    if not text:
        return Response({"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Generate audio file
        audio_filename = tts_service.generate_audio(text)
        if not audio_filename:
            return Response(
                {"error": "Failed to generate audio"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get full path to audio file
        audio_path = os.path.join(tts_service.cache_dir, audio_filename)
        
        # Return audio file
        return FileResponse(
            open(audio_path, 'rb'),
            content_type='audio/mpeg',
            as_attachment=True,
            filename=audio_filename
        )

    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_youtube_audio_segment(request, video_id):
    """Extract audio segment from YouTube video based on start and end timestamps."""
    try:
        # Get start and end times from query parameters
        start_time = float(request.GET.get('start', 0))
        end_time = float(request.GET.get('end', 0))
        
        if end_time <= start_time:
            return Response(
                {"error": "End time must be greater than start time"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract audio segment
        audio_path, error = youtube_audio_service.get_audio_segment(video_id, start_time, end_time)
        
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not audio_path or not os.path.exists(audio_path):
            return Response(
                {"error": "Failed to extract audio segment"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return audio file
        return FileResponse(
            open(audio_path, 'rb'),
            content_type='audio/mpeg',
            as_attachment=True,
            filename=os.path.basename(audio_path)
        )
        
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameters: {str(e)}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
