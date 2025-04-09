import { useState, useCallback } from 'react';

export const useAudioPlayer = () => {
    const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

    const playAudio = useCallback(async (text: string) => {
        try {
            // Stop any currently playing audio
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }

            // Create new audio element
            const response = await fetch(`/api/tts?text=${encodeURIComponent(text)}`);
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const newAudio = new Audio(audioUrl);

            // Clean up old audio URL if it exists
            if (audio) {
                URL.revokeObjectURL(audio.src);
            }

            // Play the new audio
            await newAudio.play();
            setAudio(newAudio);

            // Clean up when audio finishes
            newAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                setAudio(null);
            };
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }, [audio]);

    return { playAudio };
};
