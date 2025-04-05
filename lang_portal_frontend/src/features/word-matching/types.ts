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
