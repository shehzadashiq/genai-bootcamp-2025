package service

import (
	"sync"
	"testing"
)

func TestConcurrentWordReviews(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Clear existing data
	_, err := svc.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM study_sessions;
		DELETE FROM words_groups;
		DELETE FROM words;
		DELETE FROM study_activities;
		DELETE FROM groups;
	`)
	if err != nil {
		t.Fatalf("Failed to clear data: %v", err)
	}

	// Setup test data
	_, err = svc.db.Exec(`
		INSERT INTO groups (name) VALUES ('Test Group');
		INSERT INTO words (urdu, urdlish, english) VALUES ('سلام', 'salaam', 'hello');
		INSERT INTO study_activities (name, description, created_at) 
			VALUES ('Test Activity', 'Test Description', datetime('now'));
		INSERT INTO words_groups (word_id, group_id) VALUES (1, 1);
		INSERT INTO study_sessions (group_id, created_at, study_activity_id) 
			VALUES (1, datetime('now'), 1);
	`)
	if err != nil {
		t.Fatalf("Failed to insert test data: %v", err)
	}

	var wg sync.WaitGroup
	reviewCount := 10

	// Concurrently submit reviews
	for i := 0; i < reviewCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := svc.ReviewWord(1, 1, true)
			if err != nil {
				t.Errorf("ReviewWord failed: %v", err)
			}
		}()
	}

	wg.Wait()

	// Verify review count
	var count int
	err = svc.db.QueryRow("SELECT COUNT(*) FROM word_review_items").Scan(&count)
	if err != nil {
		t.Fatalf("Failed to count reviews: %v", err)
	}

	if count != reviewCount {
		t.Errorf("Expected %d reviews, got %d", reviewCount, count)
	}
} 