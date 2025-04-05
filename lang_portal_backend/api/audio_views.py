import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from .services.tts import TextToSpeechService

tts_service = TextToSpeechService()

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
