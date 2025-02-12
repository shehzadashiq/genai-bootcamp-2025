package testutil

import (
	"testing"
)

func TestNewTestDB(t *testing.T) {
	db := NewTestDB(t)
	defer db.Cleanup()

	// Test database connection
	err := db.Ping()
	if err != nil {
		t.Fatalf("Failed to ping database: %v", err)
	}

	// Test migrations were applied
	var tableCount int
	err = db.QueryRow(`
		SELECT COUNT(*) 
		FROM sqlite_master 
		WHERE type='table' AND name NOT LIKE 'sqlite_%'
	`).Scan(&tableCount)
	if err != nil {
		t.Fatalf("Failed to count tables: %v", err)
	}

	expectedTables := 6 // words, groups, words_groups, etc.
	if tableCount != expectedTables {
		t.Errorf("Expected %d tables, got %d", expectedTables, tableCount)
	}
} 