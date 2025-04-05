# Flashcards Learning Game

## Business Goal

Learn Urdu words and their English translations through an interactive flashcards game.

Create a curated database of the top 1000 most common Urdu words and their English translations using existing Word model data.

## Implementation Details

### Frontend Features
- The flashcard interface should display Urdu words and their English translations in a random order
- The flashcard should have a hint option
- You can either click on the card to flip it or press the space button
- The back of the flashcard should show:
    - English translation
    - Example sentence in Urdu text
    - Word information (verb, noun, adjective, etc.)
    - Etymology information if available
- Progress tracking:
    - Progress bar showing completion percentage
    - Streak counter for consecutive correct reviews
    - Score counter for total correct reviews
    - Time counter for session duration
- Navigation:
    - Restart button to start a new game
    - Back button to return to study activities page

### Technical Implementation

#### Database Models
1. FlashcardGame
   - user: TextField
   - score: IntegerField
   - streak: IntegerField
   - max_streak: IntegerField
   - total_cards: IntegerField
   - cards_reviewed: IntegerField
   - start_time: DateTimeField
   - end_time: DateTimeField
   - completed: BooleanField

2. FlashcardReview
   - game: ForeignKey(FlashcardGame)
   - word: ForeignKey(Word)
   - confidence_level: IntegerField (0-5 scale)
   - time_spent: IntegerField (seconds)
   - created_at: DateTimeField

3. FlashcardStats
   - user: TextField (unique)
   - cards_reviewed: IntegerField
   - total_time_spent: IntegerField (minutes)
   - best_streak: IntegerField
   - last_reviewed: DateTimeField

#### API Endpoints
- GET /api/flashcards/ - Get next set of flashcards
- POST /api/flashcards/ - Create new flashcard game
- GET /api/flashcards/stats/ - Get user statistics
- PUT /api/flashcards/{id}/ - Update flashcard review

#### Integration Points
- Uses existing Word model for flashcard content
- Integrates with StudySession for progress tracking
- Uses WordReviewItem for review history
- Leverages existing AWS services for:
  - Audio generation (Polly)
  - Translation services
  - Language validation
