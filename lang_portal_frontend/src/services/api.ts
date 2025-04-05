import axios from 'axios';
import { StudySessionResponse, PaginatedResponse } from '@/types';
import type { WordMatchingGame, WordMatchingStats } from '@/features/word-matching/types';

// Create a base axios instance with common configuration
const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: false,  // Set to false since we're not using credentials
});

// Add request interceptor to handle CORS preflight
api.interceptors.request.use((config) => {
  // Add timestamp to prevent caching
  const timestamp = new Date().getTime();
  config.url = config.url + (config.url?.includes('?') ? '&' : '?') + `_t=${timestamp}`;
  return config;
});

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  getLastStudySession: () => api.get<StudySessionResponse>('/dashboard/last_study_session/'),
  getStudyProgress: () => api.get('/dashboard/study_progress/'),
  getQuickStats: () => api.get('/dashboard/quick-stats/'),
};

export const studyActivitiesApi = {
  getAll: () => api.get<PaginatedResponse<any>>('/study_activities/'),
  getById: (id: string) => api.get(`/study_activities/${id}/`),
  getStudySessions: (id: string) => api.get<PaginatedResponse<StudySessionResponse>>(`/study_activities/${id}/study_sessions/`),
  create: (data: { group_id: number; study_activity_id: number }) => 
    api.post<StudySessionResponse>('/study_activities/', data),
};

export const wordsApi = {
  getAll: (page: number = 1) => api.get<PaginatedResponse<any>>(`/words?page=${page}`),
  getById: (id: string) => api.get(`/words/${id}/`),
  submitReview: (sessionId: number, wordId: number, correct: boolean) =>
    api.post(`/study_sessions/${sessionId}/words/${wordId}/review`, { correct }),
};

export const groupsApi = {
  getAll: (page: number = 1) => api.get<PaginatedResponse<any>>(`/groups?page=${page}`),
  getById: (id: string) => api.get(`/groups/${id}/`),
  getWords: (id: string, page: number = 1) => api.get<PaginatedResponse<any>>(`/groups/${id}/words?page=${page}`),
  getStudySessions: (id: string, page: number = 1) => api.get<PaginatedResponse<StudySessionResponse>>(`/groups/${id}/study_sessions?page=${page}`),
};

export const studySessionsApi = {
  getAll: (page: number = 1) => api.get<PaginatedResponse<any>>(`/study_sessions?page=${page}`),
  getById: (id: string) => api.get(`/study_sessions/${id}/`),
  getWords: (id: string, page: number = 1) => api.get<PaginatedResponse<any>>(`/study_sessions/${id}/words?page=${page}`),
};

export const vocabularyQuizApi = {
  startQuiz: async (groupId: number, wordCount: number = 10) => {
    const response = await api.post('/vocabulary_quiz/start', {
      group_id: groupId,
      word_count: wordCount,
    });
    return response.data;
  },

  getWords: async (sessionId: number) => {
    const response = await api.get(`/vocabulary_quiz/words/${sessionId}`);
    return response;
  },

  submitAnswer: async (answer: { word_id: number; session_id: number; answer: string; correct: boolean }) => {
    const response = await api.post('/vocabulary_quiz/answer', answer);
    return response.data;
  },

  getScore: async (sessionId: number) => {
    const response = await api.get(`/vocabulary_quiz/score/${sessionId}`);
    return response.data;
  },
};

export const settingsApi = {
  resetHistory: () => api.post('/reset_history'),
  fullReset: () => api.post('/full_reset'),
};

export const wordMatchingApi = {
  startGame: async (user: string, numQuestions: number = 10): Promise<WordMatchingGame> => {
    const response = await api.post('/word-matching/start_game/', {
      user,
      num_questions: numQuestions,
    });
    return response.data;
  },

  submitAnswer: async (gameId: number, questionId: number, answer: string, responseTime: number) => {
    const response = await api.post(`/word-matching/${gameId}/submit_answer/`, {
      question_id: questionId,
      answer,
      response_time: responseTime,
    });
    return response.data;
  },

  getOptions: async (gameId: number, questionId: number) => {
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

export default api;
