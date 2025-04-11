export interface WordCategory {
  id: number;
  name: string;
  description: string;
}

export interface Word {
  id: number;
  urdu_word: string;
  roman_urdu: string;
  english_translation: string;
  category: number;
  category_name: string;
  difficulty_level: number;
}

export interface SentencePattern {
  id: number;
  pattern: string;
  description: string;
  example: string;
  difficulty_level: number;
}

export interface UserSentence {
  id: number;
  sentence: string;
  is_valid: boolean;
  feedback: string;
  created_at: string;
  pattern: number | null;
  user_id: string | null;
}

export interface SentenceFeedbackType {
  isValid: boolean;
  feedback: string;
  similarPatterns: Array<{
    pattern: string;
    example: string;
    similarity: number;
  }>;
}
