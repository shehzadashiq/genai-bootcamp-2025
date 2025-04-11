// Define the difficulty levels for the quiz
export type QuizDifficulty = 'easy' | 'medium' | 'hard';

// Configuration for starting a new quiz
export interface QuizConfig {
  groupId: number;
  wordCount: number;
  difficulty: QuizDifficulty;
}

// Quiz word with options
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

// Response from starting a quiz
export interface QuizResponse {
  session_id: number;
  words: QuizWord[];
}

// Answer submission
export interface QuizAnswer {
  sessionId: number;
  wordId: number;
  answer: string;
}

// Response from submitting an answer
export interface SubmitAnswerResponse {
  correct: boolean;
  correct_answer?: string;
}

// Quiz score
export interface QuizScore {
  total: number;
  correct: number;
  percentage: number;
}

// Word
export interface Word {
  id: number;
  urdu: string;
  urdlish: string;
  english: string;
}

// Word Matching Question
export interface WordMatchingQuestion {
  id: number;
  word_urdu: string;
  word_english: string;
  word_urdlish: string;
  selected_answer: string | null;
  is_correct: boolean | null;
  response_time: number | null;
}