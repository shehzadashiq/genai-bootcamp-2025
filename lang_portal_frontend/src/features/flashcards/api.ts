import api from '@/services/api';
import { FlashcardGame, FlashcardStats, ReviewCardRequest } from './types';

const BASE_URL = '/flashcards';

export const flashcardsApi = {
    createGame: async (user: string, totalCards: number = 10): Promise<FlashcardGame> => {
        const response = await api.post(`${BASE_URL}/`, { user, total_cards: totalCards });
        return response.data;
    },

    getGame: async (gameId: number): Promise<FlashcardGame> => {
        const response = await api.get(`${BASE_URL}/${gameId}/`);
        return response.data;
    },

    reviewCard: async (gameId: number, data: ReviewCardRequest): Promise<{
        success: boolean;
        game_completed: boolean;
        current_streak: number;
        cards_remaining: number;
    }> => {
        const response = await api.post(`${BASE_URL}/${gameId}/review_card/`, data);
        return response.data;
    },

    getStats: async (user: string): Promise<FlashcardStats> => {
        const response = await api.get(`${BASE_URL}/stats/`, {
            params: { user }
        });
        return response.data;
    }
};
