export interface FlashcardWord {
    id: number;
    urdu: string;
    english: string;
    urdlish: string;
    type?: string;
    example?: string;
    etymology?: string;
}

export interface FlashcardGame {
    id: number;
    user: string;
    score: number;
    streak: number;
    max_streak: number;
    total_cards: number;
    cards_reviewed: number;
    start_time: string;
    end_time?: string;
    completed: boolean;
    reviews: FlashcardReview[];
    words: FlashcardWord[];
}

export interface FlashcardReview {
    id: number;
    game: number;
    word: FlashcardWord;
    confidence_level: number;
    time_spent: number | null;
    created_at: string;
}

export interface FlashcardStats {
    id: number;
    user: string;
    cards_reviewed: number;
    total_time_spent: number;
    best_streak: number;
    last_reviewed: string | null;
    average_time_per_card: number;
}

export interface ReviewCardRequest {
    word_id: number;
    confidence_level: number;
    time_spent: number;
}
