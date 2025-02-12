package service

import (
	"sync"
	"testing"
)

func TestConcurrentWordReviews(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Add mutex to protect database access
	var mu sync.Mutex

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
	// Create group
	result, err := svc.db.Exec(`INSERT INTO groups (name) VALUES ('Test Group')`)
	if err != nil {
		t.Fatalf("Failed to create group: %v", err)
	}
	groupID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get group ID: %v", err)
	}

	// Create word
	result, err = svc.db.Exec(`INSERT INTO words (urdu, urdlish, english) VALUES ('سلام', 'salaam', 'hello')`)
	if err != nil {
		t.Fatalf("Failed to create word: %v", err)
	}
	wordID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get word ID: %v", err)
	}

	// Link word to group
	_, err = svc.db.Exec(`INSERT INTO words_groups (word_id, group_id) VALUES (?, ?)`, wordID, groupID)
	if err != nil {
		t.Fatalf("Failed to link word to group: %v", err)
	}

	// Create study activity
	result, err = svc.db.Exec(`
		INSERT INTO study_activities (name, description, created_at) 
		VALUES ('Test Activity', 'Test Description', datetime('now'))`)
	if err != nil {
		t.Fatalf("Failed to create study activity: %v", err)
	}
	activityID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get activity ID: %v", err)
	}

	// Create study session
	result, err = svc.db.Exec(`
		INSERT INTO study_sessions (group_id, created_at, study_activity_id) 
		VALUES (?, datetime('now'), ?)`, groupID, activityID)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}
	sessionID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get session ID: %v", err)
	}

	var wg sync.WaitGroup
	reviewCount := 10
	errChan := make(chan error, reviewCount)

	// Concurrently submit reviews
	for i := 0; i < reviewCount; i++ {
		wg.Add(1)
		go func(wordID, sessionID int64) {
			defer wg.Done()
			mu.Lock()
			_, err := svc.ReviewWord(sessionID, wordID, true)
			mu.Unlock()
			if err != nil {
				errChan <- err
				return
			}
		}(wordID, sessionID)
	}

	wg.Wait()
	close(errChan)

	// Check for any errors from goroutines
	for err := range errChan {
		t.Errorf("ReviewWord failed: %v", err)
	}

	// Verify review count
	mu.Lock()
	var count int
	err = svc.db.QueryRow("SELECT COUNT(*) FROM word_review_items").Scan(&count)
	mu.Unlock()
	if err != nil {
		t.Fatalf("Failed to count reviews: %v", err)
	}

	if count != reviewCount {
		t.Errorf("Expected %d reviews, got %d", reviewCount, count)
	}
} 