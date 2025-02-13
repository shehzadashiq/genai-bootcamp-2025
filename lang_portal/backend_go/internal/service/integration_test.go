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
	_, err = svc.db.Exec(`
		INSERT INTO study_activities (id, name, description)
		VALUES (1, 'Vocabulary Quiz', 'Test your vocabulary knowledge')
	`)
	if err != nil {
		t.Fatalf("Failed to create study activity: %v", err)
	}

	// Create study session
	session, err := svc.CreateStudySession(groupID, 1)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}

	// 4. Review words
	_, err = svc.ReviewWord(session.ID, wordID, true)
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

	// Insert test data and get group ID
	result, err := svc.db.Exec(`
		INSERT INTO groups (name) VALUES (?)
	`, "Test Group")
	if err != nil {
		t.Fatalf("Failed to insert test group: %v", err)
	}
	groupID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get group ID: %v", err)
	}

	// Create study activity
	_, err = svc.db.Exec(`
		INSERT INTO study_activities (id, name, description)
		VALUES (1, 'Vocabulary Quiz', 'Test your vocabulary knowledge')
	`)
	if err != nil {
		t.Fatalf("Failed to create activity: %v", err)
	}

	// Create a study session
	session, err := svc.CreateStudySession(groupID, 1)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}

	// Test retrieving the study session
	retrievedSession, err := svc.GetStudySession(session.ID)
	if err != nil {
		t.Fatalf("Failed to get study session: %v", err)
	}

	if retrievedSession.GroupName != "Test Group" {
		t.Errorf("Expected group name 'Test Group', got '%s'", retrievedSession.GroupName)
	}

	// First create group
	result, err = svc.db.Exec(`INSERT INTO groups (name) VALUES ('Test Group')`)
	if err != nil {
		t.Fatalf("Failed to create group: %v", err)
	}
	groupID, err = result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get group ID: %v", err)
	}

	// Then create words
	result, err = svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english) VALUES 
		('سلام', 'salaam', 'hello')`)
	if err != nil {
		t.Fatalf("Failed to create first word: %v", err)
	}
	word1ID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get first word ID: %v", err)
	}

	result, err = svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english) VALUES 
		('شکریہ', 'shukriya', 'thank you')`)
	if err != nil {
		t.Fatalf("Failed to create second word: %v", err)
	}
	word2ID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get second word ID: %v", err)
	}

	// Finally link words to group
	_, err = svc.db.Exec(`INSERT INTO words_groups (word_id, group_id) VALUES (?, ?), (?, ?)`,
		word1ID, groupID, word2ID, groupID)
	if err != nil {
		t.Fatalf("Failed to link words to group: %v", err)
	}

	// Create study activity
	_, err = svc.db.Exec(`
		INSERT INTO study_activities (id, name, description)
		VALUES (2, 'Vocabulary Quiz', 'Test your vocabulary knowledge')
	`)
	if err != nil {
		t.Fatalf("Failed to create activity: %v", err)
	}

	// Create study session
	session, err = svc.CreateStudySession(groupID, 2)
	if err != nil {
		t.Fatalf("Failed to create study session: %v", err)
	}

	// Review multiple words
	_, err = svc.ReviewWord(session.ID, word1ID, true)
	if err != nil {
		t.Fatalf("Failed to review word 1: %v", err)
	}
	_, err = svc.ReviewWord(session.ID, word2ID, false)
	if err != nil {
		t.Fatalf("Failed to review word 2: %v", err)
	}

	// Check stats
	stats, err := svc.GetQuickStats()
	if err != nil {
		t.Fatalf("Failed to get stats: %v", err)
	}

	if stats.SuccessRate != 50.0 {
		t.Errorf("Expected success rate 50.0, got %f", stats.SuccessRate)
	}
}