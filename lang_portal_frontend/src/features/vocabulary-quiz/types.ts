export type QuizDifficulty = 'easy' | 'medium' | 'hard';

export interface QuizConfig {
  groupId: number;
  difficulty: QuizDifficulty;
  wordCount: number;
}

export interface Word {
  id: number;
  urdu: string;
  urdlish: string;
  english: string;
}

export interface QuizWord {
  word: Word;
  options: string[];
}

export interface QuizAnswer {
  wordId: number;
  sessionId: number;
  answer: string;
  isCorrect: boolean;
}

export interface QuizScore {
  sessionId: number;
  totalWords: number;
  correctCount: number;
  accuracy: number;
  difficulty: string;
}

export interface WordMatchingQuestion {
  id: number;
  word_urdu: string;
  word_english: string;
word_urdlish: string;
  selected_answer: string | null;
  is_correct: boolean | null;
  response_time: number | null;
}