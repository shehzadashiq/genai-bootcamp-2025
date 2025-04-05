import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, LinearProgress, IconButton, Grow } from '@mui/material';
import { Refresh, ArrowBack, VolumeUp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { flashcardsApi } from './api';
import { FlashcardGame } from './types';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';

export const Flashcards: React.FC = () => {
    const navigate = useNavigate();
    const { playAudio } = useAudioPlayer();
    const [game, setGame] = useState<FlashcardGame | null>(null);
    const [flipped, setFlipped] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        startNewGame();
    }, []);

    const startNewGame = async () => {
        setLoading(true);
        try {
            const newGame = await flashcardsApi.createGame('user1');
            setGame(newGame);
            setFlipped(false);
        } catch (error) {
            console.error('Error starting new game:', error);
        } finally {
            setLoading(false);
        }
    };

    const getCurrentWord = () => {
        if (!game || game.reviews.length === 0) return null;
        return game.reviews[game.reviews.length - 1].word;
    };

    const handleConfidenceLevel = async (level: number) => {
        if (!game || !getCurrentWord()) return;

        setLoading(true);
        try {
            const result = await flashcardsApi.reviewCard(game.id, {
                word_id: getCurrentWord()!.id,
                confidence_level: level,
                time_spent: 0 // TODO: Track actual time spent
            });

            if (result.game_completed) {
                // Show completion screen or navigate away
                navigate('/study-sessions');
            } else {
                const updatedGame = await flashcardsApi.getGame(game.id);
                setGame(updatedGame);
                setFlipped(false);
            }
        } catch (error) {
            console.error('Error submitting review:', error);
        } finally {
            setLoading(false);
        }
    };

    const currentWord = getCurrentWord();
    const progress = game ? (game.cards_reviewed / game.total_cards) * 100 : 0;

    if (loading) {
        return (
            <Box sx={{ width: '100%', mt: 4 }}>
                <LinearProgress />
            </Box>
        );
    }

    if (!game || !currentWord) {
        return (
            <Box sx={{ textAlign: 'center', mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                    No active flashcard game
                </Typography>
                <Button variant="contained" onClick={startNewGame}>
                    Start New Game
                </Button>
            </Box>
        );
    }

    return (
        <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <IconButton onClick={() => navigate('/study-sessions')}>
                    <ArrowBack />
                </IconButton>
                <IconButton onClick={startNewGame}>
                    <Refresh />
                </IconButton>
            </Box>

            <LinearProgress variant="determinate" value={progress} sx={{ mb: 3 }} />

            <Box sx={{ height: 200, position: 'relative' }}>
                <Card
                    sx={{
                        cursor: 'pointer',
                        height: '100%',
                        width: '100%',
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
                                height: '100%',
                                width: '100%',
                                position: 'absolute'
                            }}
                        >
                            <Typography variant="h4" gutterBottom>
                                {currentWord.urdu}
                            </Typography>
                            <Typography variant="subtitle1" color="textSecondary">
                                {currentWord.urdlish}
                            </Typography>
                            <IconButton onClick={(e) => {
                                e.stopPropagation();
                                playAudio(currentWord.urdu);
                            }}>
                                <VolumeUp />
                            </IconButton>
                        </CardContent>
                    </Grow>

                    <Grow in={flipped} timeout={300}>
                        <CardContent
                            sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '100%',
                                width: '100%',
                                position: 'absolute'
                            }}
                        >
                            <Typography variant="h4" gutterBottom>
                                {currentWord.english}
                            </Typography>
                            <Typography variant="subtitle1" color="textSecondary">
                                {currentWord.parts}
                            </Typography>
                        </CardContent>
                    </Grow>
                </Card>
            </Box>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Button
                    variant="contained"
                    color="error"
                    onClick={() => handleConfidenceLevel(1)}
                    disabled={!flipped}
                >
                    Hard
                </Button>
                <Button
                    variant="contained"
                    color="warning"
                    onClick={() => handleConfidenceLevel(2)}
                    disabled={!flipped}
                >
                    Medium
                </Button>
                <Button
                    variant="contained"
                    color="success"
                    onClick={() => handleConfidenceLevel(3)}
                    disabled={!flipped}
                >
                    Easy
                </Button>
            </Box>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="subtitle1">
                    Cards: {game.cards_reviewed} / {game.total_cards}
                </Typography>
                <Typography variant="subtitle1">
                    Current Streak: {game.streak}
                </Typography>
                <Typography variant="subtitle1">
                    Best Streak: {game.max_streak}
                </Typography>
            </Box>
        </Box>
    );
};
