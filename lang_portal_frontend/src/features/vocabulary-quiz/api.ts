import { axiosInstance } from '@/lib/axios';
import { QuizConfig, QuizWord, QuizScore, QuizAnswer } from './types';

export const vocabularyQuizApi = {
  startQuiz: async (config: QuizConfig) => {
    const { data } = await axiosInstance.post('/vocabulary-quiz/start', config);
    return data;
  },

  getQuizWords: async (sessionId: string): Promise<QuizWord[]> => {
    const { data } = await axiosInstance.get(`/vocabulary-quiz/words/${sessionId}`);
    return data;
  },

  submitAnswer: async (answer: QuizAnswer) => {
    const { data } = await axiosInstance.post('/vocabulary-quiz/submit', answer);
    return data;
  },

  getQuizScore: async (sessionId: string): Promise<QuizScore> => {
    const { data } = await axiosInstance.get(`/vocabulary-quiz/score/${sessionId}`);
    return data;
  },
};
