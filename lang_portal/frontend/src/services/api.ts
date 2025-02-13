import axios from 'axios';
import { StudySessionResponse, PaginatedResponse } from '@/types';

const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getLastStudySession: () => api.get<StudySessionResponse>('/dashboard/last_study_session'),
  getStudyProgress: () => api.get('/dashboard/study_progress'),
  getQuickStats: () => api.get('/dashboard/quick-stats'),
};

export const studyActivitiesApi = {
  getAll: () => api.get<PaginatedResponse<any>>('/study_activities'),
  getById: (id: string) => api.get(`/study_activities/${id}`),
  getStudySessions: (id: string) => api.get<PaginatedResponse<StudySessionResponse>>(`/study_activities/${id}/study_sessions`),
  create: (data: { group_id: number; study_activity_id: number }) => 
    api.post<StudySessionResponse>('/study_activities', data),
};

export const wordsApi = {
  getAll: (page: number = 1) => api.get(`/words?page=${page}`),
  getById: (id: string) => api.get(`/words/${id}`),
  submitReview: (sessionId: number, wordId: number, correct: boolean) =>
    api.post(`/study_sessions/${sessionId}/words/${wordId}/review`, { correct }),
};

export const groupsApi = {
  getAll: (page: number = 1) => api.get<PaginatedResponse<any>>(`/groups?page=${page}`),
  getById: (id: string) => api.get(`/groups/${id}`),
  getWords: (id: string, page: number = 1) => api.get(`/groups/${id}/words?page=${page}`),
  getStudySessions: (id: string, page: number = 1) => api.get<PaginatedResponse<StudySessionResponse>>(`/groups/${id}/study_sessions?page=${page}`),
};

export const studySessionsApi = {
  getAll: (page: number = 1) => api.get<PaginatedResponse<StudySessionResponse>>(`/study_sessions?page=${page}`),
  getById: (id: string) => api.get<StudySessionResponse>(`/study_sessions/${id}`),
  getWords: (id: string, page: number = 1) => api.get(`/study_sessions/${id}/words?page=${page}`),
};

export const settingsApi = {
  resetHistory: () => api.post('/reset_history'),
  fullReset: () => api.post('/full_reset'),
};

export default api;
