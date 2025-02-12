package service

import (
	"testing"
)

func TestFullWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

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

	// 1. Create a group
	result, err := svc.db.Exec(`
		INSERT INTO groups (name) VALUES (?)
	`, "Test Group")
	if err != nil {
		t.Fatalf("Failed to create group: %v", err)
	}
	groupID, _ := result.LastInsertId()

	// 2. Add words to the group
	result, err = svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english)
		VALUES (?, ?, ?)
	`, "سلام", "salaam", "hello")
	if err != nil {
		t.Fatalf("Failed to insert word: %v", err)
	}
	wordID, _ := result.LastInsertId()

	// Link word to group
	_, err = svc.db.Exec(`
		INSERT INTO words_groups (word_id, group_id)
		VALUES (?, ?)
	`, wordID, groupID)
	if err != nil {
		t.Fatalf("Failed to link word to group: %v", err)
	}

	// 3. Create study activity
	activity, err := svc.CreateStudyActivity(groupID, 1)
	if err != nil {
		t.Fatalf("Failed to create study activity: %v", err)
	}

	// Create study session
	result, err = svc.db.Exec(`
		INSERT INTO study_sessions (group_id, created_at, study_activity_id)
		VALUES (?, datetime('now'), ?)
	`, groupID, activity.ID)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}
	sessionID, _ := result.LastInsertId()

	// 4. Review words
	_, err = svc.ReviewWord(sessionID, wordID, true)
	if err != nil {
		t.Fatalf("Failed to review word: %v", err)
	}

	// 5. Check progress
	progress, err := svc.GetStudyProgress()
	if err != nil {
		t.Fatalf("Failed to get progress: %v", err)
	}

	if progress.TotalWordsStudied != 1 {
		t.Errorf("Expected 1 word studied, got %d", progress.TotalWordsStudied)
	}
}

func TestStudySessionWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

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

	// Create group and add words
	_, err = svc.db.Exec(`
		INSERT INTO groups (name) VALUES ('Test Group');
		INSERT INTO words (urdu, urdlish, english) VALUES 
		('سلام', 'salaam', 'hello'),
		('شکریہ', 'shukriya', 'thank you');
		INSERT INTO words_groups (word_id, group_id) VALUES (1, 1), (2, 1);
	`)
	if err != nil {
		t.Fatalf("Failed to setup test data: %v", err)
	}

	// Create study activity
	activity, err := svc.CreateStudyActivity(1, 1)
	if err != nil {
		t.Fatalf("Failed to create activity: %v", err)
	}

	// Create study session
	result, err = svc.db.Exec(`
		INSERT INTO study_sessions (group_id, created_at, study_activity_id)
		VALUES (?, datetime('now'), ?)
	`, 1, activity.ID)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}
	sessionID, _ := result.LastInsertId()

	// Review multiple words
	_, err = svc.ReviewWord(sessionID, 1, true)
	if err != nil {
		t.Fatalf("Failed to review word 1: %v", err)
	}
	_, err = svc.ReviewWord(sessionID, 2, false)
	if err != nil {
		t.Fatalf("Failed to review word 2: %v", err)
	}

	// Check stats
	stats, err := svc.GetQuickStats()
	if err != nil {
		t.Fatalf("Failed to get stats: %v", err)
	}

	if stats.SuccessRate != 50.0 {
		t.Errorf("Expected 50%% success rate, got %.1f%%", stats.SuccessRate)
	}
} 