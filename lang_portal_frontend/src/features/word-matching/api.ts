import api from '@/services/api';

export interface WordMatchingGame {
  id: number;
  user: string;
  score: number;
  max_streak: number;
  total_questions: number;
  correct_answers: number;
  start_time: string;
  end_time: string | null;
  completed: boolean;
  questions: WordMatchingQuestion[];
}

export interface WordMatchingQuestion {
  id: number;
  word_urdu: string;
  word_english: string;
  selected_answer: string | null;
  is_correct: boolean | null;
  response_time: number | null;
}

export interface WordMatchingStats {
  user: string;
  games_played: number;
  total_score: number;
  best_score: number;
  total_correct: number;
  total_questions: number;
  last_played: string | null;
  accuracy: number;
  average_score: number;
}

export const wordMatchingApi = {
  startGame: async (user: string, numQuestions: number = 10): Promise<WordMatchingGame> => {
    const response = await api.post('/word-matching/start_game/', {
      user,
      num_questions: numQuestions,
    });
    return response.data;
  },

  submitAnswer: async (
    gameId: number,
    questionId: number,
    answer: string,
    responseTime: number
  ): Promise<WordMatchingGame> => {
    const response = await api.post(`/word-matching/${gameId}/submit_answer/`, {
      question_id: questionId,
      answer,
      response_time: responseTime,
    });
    return response.data;
  },

  getOptions: async (gameId: number, questionId: number): Promise<string[]> => {
    const response = await api.get(`/word-matching/${gameId}/get_options/`, {
      params: { question_id: questionId },
    });
    return response.data.options;
  },

  getStats: async (user: string): Promise<WordMatchingStats> => {
    const response = await api.get('/word-matching-stats/', {
      params: { user },
    });
    return response.data;
  },
};
