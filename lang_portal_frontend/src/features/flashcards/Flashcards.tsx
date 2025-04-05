import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, IconButton, Grow, Switch, useTheme } from '@mui/material';
import { ArrowBack, VolumeUp, HelpOutline, Star, ArrowForward, PlayArrow, Shuffle, Settings, Fullscreen } from '@mui/icons-material';
import { flashcardsApi } from './api';
import { FlashcardGame } from './types';

export const Flashcards: React.FC = () => {
    const theme = useTheme();
    const [game, setGame] = useState<FlashcardGame | null>(null);
    const [flipped, setFlipped] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentIndex, setCurrentIndex] = useState(0);

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
        }
    }, [game, currentIndex]);

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
        if (!game?.words?.length) return;
        const shuffledWords = [...game.words].sort(() => Math.random() - 0.5);
        setGame(prev => prev ? { ...prev, words: shuffledWords } : null);
        setCurrentIndex(0);
        setFlipped(false);
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
        <Box sx={{ 
            height: '70vh',
            display: 'flex',
            flexDirection: 'column',
            bgcolor: theme.palette.background.default,
            borderRadius: 4,
            p: 3,
            position: 'relative'
        }}>
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
                    <IconButton sx={{ color: 'black.300' }}>
                        <VolumeUp />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }}>
                        <Star />
                    </IconButton>
                </Box>
            </Box>

            {/* Card content */}
            <Card
                sx={{
                    cursor: 'pointer',
                    flexGrow: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'transparent',
                    boxShadow: 'none',
                    position: 'relative'
                }}
                onClick={() => setFlipped(!flipped)}
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
                                <Typography 
                                    variant="h4" 
                                    sx={{ 
                                        fontSize: '1.75rem'
                                    }}
                                >
                                    {currentWord.urdlish}
                                </Typography>
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
                                    {currentWord.english}
                                </Typography>
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
                    <Typography sx={{ color: 'black.300' }}>Track progress</Typography>
                    <Switch size="small" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <IconButton sx={{ color: 'black.300' }} onClick={handlePrevious}>
                        <ArrowBack />
                    </IconButton>
                    <Typography sx={{ color: 'black.300' }}>
                        {currentIndex + 1} / {game.words.length}
                    </Typography>
                    <IconButton sx={{ color: 'black.300' }} onClick={handleNext}>
                        <ArrowForward />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }}>
                        <PlayArrow />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }} onClick={handleShuffle}>
                        <Shuffle />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }}>
                        <Settings />
                    </IconButton>
                    <IconButton sx={{ color: 'black.300' }}>
                        <Fullscreen />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
};
