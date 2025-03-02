import axios from 'axios';

const BASE_URL = 'http://localhost:8080/api';

interface QuizWord {
  word: {
    id: number;
    urdu: string;
    urdlish: string;
    english: string;
    correct_count: number;
  };
  options: string[];
}

interface QuizAnswer {
  word_id: number;
  session_id: number;
  answer: string;
  correct: boolean;
}

interface QuizScore {
  session_id: number;
  total_words: number;
  correct_count: number;
  accuracy: number;
  difficulty: string;
}

export const vocabularyQuizApi = {
  startQuiz: async (groupId: number, wordCount: number = 10) => {
    const response = await axios.post(`${BASE_URL}/vocabulary-quiz/start`, {
      group_id: groupId,
      word_count: wordCount,
    });
    return response.data;
  },

  getWords: async (sessionId: number) => {
    const response = await axios.get<QuizWord[]>(`${BASE_URL}/vocabulary-quiz/words/${sessionId}`);
    return response;
  },

  submitAnswer: async (answer: QuizAnswer) => {
    const response = await axios.post(`${BASE_URL}/vocabulary-quiz/answer`, answer);
    return response.data;
  },

  getScore: async (sessionId: number) => {
    const response = await axios.get<QuizScore>(`${BASE_URL}/vocabulary-quiz/score/${sessionId}`);
    return response.data;
  },
};
