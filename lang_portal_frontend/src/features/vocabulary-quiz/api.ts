import { axiosInstance as api } from '@/lib/axios';

// Define types for the quiz API responses
export interface QuizWord {
  word: {
    id: number;
    urdu: string;
    english: string;
    hindi?: string;
    example?: string;
  };
  options: string[];
}

export interface QuizResponse {
  session_id: number;
  words: QuizWord[];
}

export interface SubmitAnswerResponse {
  correct: boolean;
  correct_answer?: string;
}

export interface SubmitQuizResponse {
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
}

export const vocabularyQuizApi = {
  startQuiz: (groupId: number, wordCount: number, difficulty: string = 'easy') => 
    api.post<QuizResponse>('/vocabulary-quiz/start/', {
      group_id: groupId,
      word_count: wordCount,
      difficulty: difficulty
    }),
  
  submitAnswer: (sessionId: number, wordId: number, answer: string) =>
    api.post<SubmitAnswerResponse>('/vocabulary-quiz/submit/', {
      session_id: sessionId,
      word_id: wordId,
      answer: answer
    }),
    
  submitQuiz: (sessionId: number, answers: Array<{ word_id: number, selected_id: number, id?: number }>) =>
    api.post<SubmitQuizResponse>('/vocabulary-quiz/submit/', {
      session_id: sessionId,
      answers: answers
    })
};
