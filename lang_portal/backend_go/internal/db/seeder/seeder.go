package seeder

import (
	"encoding/json"
	"fmt"
	"io"
	"lang_portal/internal/models"
	"os"
	"path/filepath"
)

// Seeder handles database seeding operations
type Seeder struct {
	db *models.DB
}

// NewSeeder creates a new seeder instance
func NewSeeder(db *models.DB) *Seeder {
	return &Seeder{db: db}
}

// SeedFromJSON reads JSON files from a directory and seeds the database
func (s *Seeder) SeedFromJSON(seedDir string) error {
	// Seed study activities
	if err := s.seedStudyActivities(filepath.Join(seedDir, "study_activities.json")); err != nil {
		return fmt.Errorf("failed to seed study activities: %v", err)
	}

	return nil
}

// seedStudyActivities seeds study activities from a JSON file
func (s *Seeder) seedStudyActivities(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %v", err)
	}

	var activities []models.StudyActivity
	if err := json.Unmarshal(data, &activities); err != nil {
		return fmt.Errorf("failed to parse JSON: %v", err)
	}

	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Clear existing study activities
	_, err = tx.Exec("DELETE FROM study_activities")
	if err != nil {
		return fmt.Errorf("failed to clear study activities: %v", err)
	}

	// Insert new study activities
	stmt, err := tx.Prepare(`
		INSERT INTO study_activities (id, name, url, thumbnail_url, description)
		VALUES (?, ?, ?, ?, ?)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, activity := range activities {
		_, err = stmt.Exec(
			activity.ID,
			activity.Name,
			activity.URL,
			activity.ThumbnailURL,
			activity.Description,
		)
		if err != nil {
			return fmt.Errorf("failed to insert study activity: %v", err)
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}
