import React, { useState, useEffect, useCallback } from 'react';
import { Box, Card, CardContent, Typography, Button, IconButton, Grow, Switch, useTheme, Dialog, DialogTitle, DialogContent, DialogActions, Slider, FormControlLabel } from '@mui/material';
import { ArrowBack, VolumeUp, HelpOutline, Star, ArrowForward, PlayArrow, Shuffle, Settings, Fullscreen, Pause } from '@mui/icons-material';
import { flashcardsApi } from './api';
import { audioApi } from '@/services/audio';
import { FlashcardGame } from './types';

export const Flashcards: React.FC = () => {
    const theme = useTheme();
    const [game, setGame] = useState<FlashcardGame | null>(null);
    const [flipped, setFlipped] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [isPlayingAudio, setIsPlayingAudio] = useState(false);
    const [isAutoPlaying, setIsAutoPlaying] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState(3); // seconds per card
    const [showTranscription, setShowTranscription] = useState(true);

    // Reference to the container for fullscreen
    const containerRef = React.useRef<HTMLDivElement>(null);

    useEffect(() => {
        const initGame = async () => {
            setLoading(true);
            try {
                console.log('Initializing game...');
                const newGame = await flashcardsApi.createGame('user1', 10);
                console.log('Game created:', newGame);
                setGame(newGame);
            } catch (error) {
                console.error('Error creating game:', error);
                setError('Failed to create game');
            } finally {
                setLoading(false);
            }
        };

        initGame();
    }, []);

    useEffect(() => {
        if (game) {
            console.log('Game updated:', game);
            const word = getCurrentWord();
            console.log('Current word:', word);
            // Load audio for the current word
            if (word) {
                loadWordAudio(word.urdu);
            }
        }
    }, [game, currentIndex]);

    const loadWordAudio = async (text: string) => {
        try {
            const url = await audioApi.getWordAudio(text);
            setAudioUrl(url);
        } catch (error) {
            console.error('Error loading audio:', error);
        }
    };

    const playAudio = async () => {
        if (!audioUrl || isPlayingAudio) return;
        
        setIsPlayingAudio(true);
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
            setIsPlayingAudio(false);
            URL.revokeObjectURL(audioUrl); // Clean up the blob URL
            setAudioUrl(null);
        };
        
        try {
            await audio.play();
        } catch (error) {
            console.error('Error playing audio:', error);
            setIsPlayingAudio(false);
        }
    };

    const getCurrentWord = () => {
        if (!game || !game.words) return null;
        console.log('Current game:', game);
        console.log('Current index:', currentIndex);
        return game.words[currentIndex];
    };

    const handleNext = async () => {
        if (!game || !game.words) return;

        // Get current word before moving to next
        const currentWord = getCurrentWord();
        if (!currentWord) return;

        // Submit review for current word
        try {
            const updatedGame = await flashcardsApi.submitReview(game.id, {
                word_id: currentWord.id,
                confidence_level: 3, // Default to medium confidence
                time_spent: 0
            });
            setGame(updatedGame);
        } catch (error) {
            console.error('Error submitting review:', error);
        }

        // Move to next word
        const nextIndex = (currentIndex + 1) % game.words.length;
        setCurrentIndex(nextIndex);
        setFlipped(false);
    };

    const handlePrevious = () => {
        if (!game?.words?.length) return;
        console.log('Handling previous, current index:', currentIndex);
        setFlipped(false);
        const prevIndex = (currentIndex - 1 + game.words.length) % game.words.length;
        console.log('Moving to previous index:', prevIndex);
        setCurrentIndex(prevIndex);
    };

    const handleShuffle = () => {
        if (!game?.words) return;
        
        const shuffledWords = [...game.words]
            .map(value => ({ value, sort: Math.random() }))
            .sort((a, b) => a.sort - b.sort)
            .map(({ value }) => value);

        setGame(prev => prev ? { ...prev, words: shuffledWords } : null);
        setCurrentIndex(0);
        setFlipped(false);
    };

    // Auto-play functionality
    useEffect(() => {
        let timeoutId: NodeJS.Timeout;
        
        if (isAutoPlaying && game?.words) {
            if (!flipped) {
                // Show front for half the time
                timeoutId = setTimeout(() => {
                    setFlipped(true);
                }, playbackSpeed * 500);
            } else {
                // Show back for half the time, then move to next card
                timeoutId = setTimeout(() => {
                    handleNext();
                    setFlipped(false);
                }, playbackSpeed * 500);
            }
        }

        return () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        };
    }, [isAutoPlaying, currentIndex, flipped, game?.words]);

    // Fullscreen handling
    const toggleFullscreen = useCallback(() => {
        if (!document.fullscreenElement && containerRef.current) {
            containerRef.current.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    }, []);

    // Handle fullscreen change events
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => {
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, []);

    const toggleAutoPlay = () => {
        setIsAutoPlaying(!isAutoPlaying);
        if (!isAutoPlaying) {
            setFlipped(false); // Start with front side when beginning auto-play
        }
    };

    const currentWord = getCurrentWord();

    if (loading) {
        return (
            <Box sx={{ 
                height: '70vh',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: theme.palette.background.default,
                borderRadius: 4,
                p: 3,
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Typography variant="h5" sx={{ color: 'black.300' }}>
                    Loading flashcards...
                </Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ 
                height: '70vh',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: theme.palette.background.default,
                borderRadius: 4,
                p: 3,
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Typography variant="h5" sx={{ color: 'error.main' }}>
                    {error}
                </Typography>
            </Box>
        );
    }

    if (!game || !currentWord) {
        return (
            <Box sx={{ 
                height: '70vh',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: theme.palette.background.default,
                borderRadius: 4,
                p: 3,
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Typography variant="h5" sx={{ color: 'black.300' }}>
                    No flashcards available
                </Typography>
            </Box>
        );
    }

    return (
        <Box 
            ref={containerRef}
            sx={{ 
                p: 4, 
                height: isFullscreen ? '100vh' : 'auto',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'background.default'
            }}
        >
            {/* Settings Dialog */}
            <Dialog open={showSettings} onClose={() => setShowSettings(false)}>
                <DialogTitle>Flashcard Settings</DialogTitle>
                <DialogContent>
                    <Box sx={{ width: 300, mt: 2 }}>
                        <Typography gutterBottom>
                            Playback Speed (seconds per card)
                        </Typography>
                        <Slider
                            value={playbackSpeed}
                            onChange={(_, value) => setPlaybackSpeed(value as number)}
                            min={1}
                            max={10}
                            step={0.5}
                            marks
                            valueLabelDisplay="auto"
                        />
                        <Box sx={{ mt: 3 }}>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={showTranscription}
                                        onChange={(e) => setShowTranscription(e.target.checked)}
                                    />
                                }
                                label="Show Urdu Transcription"
                            />
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowSettings(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            {/* Top bar */}
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 4
            }}>
                <Button
                    startIcon={<HelpOutline />}
                    sx={{ color: 'black.300' }}
                >
                    Get a hint
                </Button>
                <Box>
                    <IconButton 
                        sx={{ color: 'black.300' }} 
                        onClick={playAudio}
                        disabled={!audioUrl || isPlayingAudio}
                    >
                        <VolumeUp />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }}>
                        <Star />
                    </IconButton>
                </Box>
            </Box>

            {/* Card content */}
            <Card 
                onClick={() => setFlipped(!flipped)}
                sx={{ 
                    position: 'relative',
                    minHeight: '300px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    flex: 1
                }}
            >
                <Grow in={!flipped} timeout={300}>
                    <CardContent
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            position: 'absolute',
                            width: '100%',
                            textAlign: 'center'
                        }}
                    >
                        {currentWord ? (
                            <>
                                <Typography 
                                    variant="h2" 
                                    sx={{ 
                                        mb: 2,
                                        fontSize: '2.5rem'
                                    }}
                                >
                                    {currentWord.urdu}
                                </Typography>
                                {showTranscription && (
                                    <Typography 
                                        variant="h4" 
                                        sx={{ 
                                            fontSize: '1.75rem'
                                        }}
                                    >
                                        {currentWord.urdlish}
                                    </Typography>
                                )}
                            </>
                        ) : (
                            <Typography variant="h4">No word available</Typography>
                        )}
                    </CardContent>
                </Grow>

                <Grow in={flipped} timeout={300}>
                    <CardContent
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            position: 'absolute',
                            width: '100%',
                            textAlign: 'center',
                            padding: 4
                        }}
                    >
                        {currentWord ? (
                            <>
                                <Typography 
                                    variant="h2" 
                                    sx={{ 
                                        mb: 2,
                                        fontSize: '2.5rem'
                                    }}
                                >
                                    {currentWord.english}
                                </Typography>
                                
                                {/* Word Type */}
                                <Typography 
                                    variant="subtitle1" 
                                    sx={{ 
                                        mb: 2,
                                        color: 'text.secondary'
                                    }}
                                >
                                    {currentWord.type || 'Unknown type'}
                                </Typography>

                                {/* Example Sentence */}
                                {currentWord.example && (
                                    <Box sx={{ mb: 2 }}>
                                        <Typography 
                                            variant="h6" 
                                            sx={{ 
                                                mb: 1,
                                                color: 'text.secondary'
                                            }}
                                        >
                                            Example:
                                        </Typography>
                                        <Typography 
                                            variant="body1" 
                                            sx={{ 
                                                fontStyle: 'italic',
                                                direction: 'rtl'
                                            }}
                                        >
                                            {currentWord.example}
                                        </Typography>
                                    </Box>
                                )}

                                {/* Etymology */}
                                {currentWord.etymology && (
                                    <Box sx={{ mt: 2 }}>
                                        <Typography 
                                            variant="h6" 
                                            sx={{ 
                                                mb: 1,
                                                color: 'text.secondary'
                                            }}
                                        >
                                            Etymology:
                                        </Typography>
                                        <Typography variant="body2">
                                            {currentWord.etymology}
                                        </Typography>
                                    </Box>
                                )}
                            </>
                        ) : (
                            <Typography variant="h4">No word available</Typography>
                        )}
                    </CardContent>
                </Grow>
            </Card>

            {/* Bottom bar */}
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                mt: 4
            }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography sx={{ color: 'text.secondary' }}>Track progress</Typography>
                    <Switch size="small" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <IconButton sx={{ color: 'text.secondary' }} onClick={handlePrevious}>
                        <ArrowBack />
                    </IconButton>
                    <Typography sx={{ color: 'text.secondary' }}>
                        {currentIndex + 1} / {game.words.length}
                    </Typography>
                    <IconButton sx={{ color: 'text.secondary' }} onClick={handleNext}>
                        <ArrowForward />
                    </IconButton>
                    <IconButton 
                        sx={{ color: isAutoPlaying ? 'primary.main' : 'text.secondary' }} 
                        onClick={toggleAutoPlay}
                    >
                        {isAutoPlaying ? <Pause /> : <PlayArrow />}
                    </IconButton>
                    <IconButton sx={{ color: 'text.secondary' }} onClick={handleShuffle}>
                        <Shuffle />
                    </IconButton>
                    <IconButton sx={{ color: 'text.secondary' }} onClick={() => setShowSettings(true)}>
                        <Settings />
                    </IconButton>
                    <IconButton 
                        sx={{ color: isFullscreen ? 'primary.main' : 'text.secondary' }} 
                        onClick={toggleFullscreen}
                    >
                        <Fullscreen />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
};
