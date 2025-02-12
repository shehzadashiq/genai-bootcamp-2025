package service

import (
	"database/sql"
	"lang_portal/internal/models"
	"lang_portal/internal/testutil"
	"testing"
)

const testDBPath = "test.db"

func setupTestDB(t *testing.T) *Service {
	db := testutil.NewTestDB(t)
	db.Seed()
	return NewServiceWithDB(db.DB)
}

func teardownTestDB(t *testing.T) {
	// Nothing to do - in-memory database cleans itself up
}

func TestGetWord(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Insert test data
	result, err := svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english, parts)
		VALUES (?, ?, ?, ?)
	`, "سلام", "salaam", "hello", `{"type":"greeting"}`)
	if err != nil {
		t.Fatalf("Failed to insert test word: %v", err)
	}

	wordID, err := result.LastInsertId()
	if err != nil {
		t.Fatalf("Failed to get last insert ID: %v", err)
	}

	// Test getting the word
	word, err := svc.GetWord(wordID)
	if err != nil {
		t.Fatalf("GetWord failed: %v", err)
	}

	// Verify the result
	if word.ID != wordID {
		t.Errorf("Expected word ID %d, got %d", wordID, word.ID)
	}
	if word.Urdu != "سلام" {
		t.Errorf("Expected Urdu 'سلام', got '%s'", word.Urdu)
	}
	if word.English != "hello" {
		t.Errorf("Expected English 'hello', got '%s'", word.English)
	}
}

func TestCreateStudyActivity(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Insert test group
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

	// Test creating study activity
	activity, err := svc.CreateStudyActivity(groupID, 1)
	if err != nil {
		t.Fatalf("CreateStudyActivity failed: %v", err)
	}

	if activity.ID == 0 {
		t.Error("Expected non-zero activity ID")
	}
}

func TestGetStudyProgress(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Insert test data
	_, err := svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english)
		VALUES 
			('سلام', 'salaam', 'hello'),
			('شکریہ', 'shukriya', 'thank you')
	`)
	if err != nil {
		t.Fatalf("Failed to insert test words: %v", err)
	}

	// Test getting progress with no reviews
	progress, err := svc.GetStudyProgress()
	if err != nil {
		t.Fatalf("GetStudyProgress failed: %v", err)
	}

	if progress.TotalAvailableWords != 4 {
		t.Errorf("Expected 4 available words, got %d", progress.TotalAvailableWords)
	}
}

func TestListWords(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Clear existing seed data first
	_, err := svc.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM words_groups;
		DELETE FROM words;
	`)
	if err != nil {
		t.Fatalf("Failed to clear existing data: %v", err)
	}

	// Insert multiple test words
	_, err = svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english) VALUES 
		('سلام', 'salaam', 'hello'),
		('شکریہ', 'shukriya', 'thank you'),
		('خدا حافظ', 'khuda hafiz', 'goodbye')
	`)
	if err != nil {
		t.Fatalf("Failed to insert test words: %v", err)
	}

	// Test pagination
	response, err := svc.ListWords(1)
	if err != nil {
		t.Fatalf("ListWords failed: %v", err)
	}

	words := response.Items.([]models.WordResponse)
	if len(words) != 3 {
		t.Errorf("Expected 3 words, got %d", len(words))
	}
}

func TestGetQuickStats(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Clear existing data
	_, err := svc.db.Exec(`DELETE FROM word_review_items`)
	if err != nil {
		t.Fatalf("Failed to clear review items: %v", err)
	}

	// Insert test data with some correct and incorrect reviews
	_, err = svc.db.Exec(`
		INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) 
		VALUES (1, 1, true, datetime('now')), (1, 1, false, datetime('now'));
	`)
	if err != nil {
		t.Fatalf("Failed to insert test data: %v", err)
	}

	stats, err := svc.GetQuickStats()
	if err != nil {
		t.Fatalf("GetQuickStats failed: %v", err)
	}

	if stats.SuccessRate != 50.0 {
		t.Errorf("Expected 50%% success rate, got %.1f%%", stats.SuccessRate)
	}
}

func TestReviewWord(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Setup test data
	_, err := svc.db.Exec(`
		INSERT INTO words (urdu, urdlish, english) VALUES ('سلام', 'salaam', 'hello');
		INSERT INTO study_sessions (group_id, created_at, study_activity_id) 
		VALUES (1, datetime('now'), 1);
	`)
	if err != nil {
		t.Fatalf("Failed to insert test data: %v", err)
	}

	// Test reviewing a word
	review, err := svc.ReviewWord(1, 1, true)
	if err != nil {
		t.Fatalf("ReviewWord failed: %v", err)
	}

	if !review.Correct {
		t.Error("Expected review to be marked as correct")
	}
}

func TestGetWordNotFound(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	_, err := svc.GetWord(999)
	if err != sql.ErrNoRows {
		t.Errorf("Expected ErrNoRows, got %v", err)
	}
}

func TestListWordsEmptyDB(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Clear existing data in correct order
	_, err := svc.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM words_groups;
		DELETE FROM words;
	`)
	if err != nil {
		t.Fatalf("Failed to clear words: %v", err)
	}

	response, err := svc.ListWords(1)
	if err != nil {
		t.Fatalf("ListWords failed: %v", err)
	}

	words := response.Items.([]models.WordResponse)
	if len(words) != 0 {
		t.Errorf("Expected empty list, got %d words", len(words))
	}
}

func TestInvalidPagination(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	_, err := svc.ListWords(0)
	if err == nil {
		t.Error("Expected error for invalid page number")
	}
}

func TestTransactionRollback(t *testing.T) {
	svc := setupTestDB(t)
	defer teardownTestDB(t)

	// Clear existing data
	_, err := svc.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM words_groups;
		DELETE FROM words;
	`)
	if err != nil {
		t.Fatalf("Failed to clear data: %v", err)
	}

	// Start with known state
	var initialCount int
	svc.db.QueryRow("SELECT COUNT(*) FROM words").Scan(&initialCount)

	tx, err := svc.db.Begin()
	if err != nil {
		t.Fatalf("Failed to begin transaction: %v", err)
	}

	_, err = tx.Exec(`INSERT INTO words (urdu, urdlish, english) VALUES ('test1', 'test1', 'test1')`)
	if err != nil {
		tx.Rollback()
		t.Fatalf("Failed to insert first word: %v", err)
	}

	_, err = tx.Exec(`INSERT INTO words (urdu, urdlish, english) VALUES (NULL, 'test2', 'test2')`)
	if err != nil {
		tx.Rollback()
	} else {
		err = tx.Commit()
	}

	// Verify no changes were committed
	var finalCount int
	svc.db.QueryRow("SELECT COUNT(*) FROM words").Scan(&finalCount)
	if finalCount != initialCount {
		t.Errorf("Expected count to remain %d, got %d", initialCount, finalCount)
	}
} 