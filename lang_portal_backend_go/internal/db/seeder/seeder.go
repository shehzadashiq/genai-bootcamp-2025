package seeder

import (
	"database/sql"
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

	// Seed word groups and words
	if err := s.seedWordGroups(filepath.Join(seedDir, "word_groups.json")); err != nil {
		return fmt.Errorf("failed to seed word groups: %v", err)
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

// seedWordGroups seeds word groups and their words from a JSON file
func (s *Seeder) seedWordGroups(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %v", err)
	}

	type WordGroup struct {
		Name        string `json:"name"`
		Description string `json:"description"`
		Words       []struct {
			Urdu    string `json:"urdu"`
			Urdlish string `json:"urdlish"`
			English string `json:"english"`
		} `json:"words"`
	}

	var groups []WordGroup
	if err := json.Unmarshal(data, &groups); err != nil {
		return fmt.Errorf("failed to parse JSON: %v", err)
	}

	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	for _, group := range groups {
		// Get or create group
		var groupID int64
		err := tx.QueryRow(`
			SELECT id FROM groups WHERE name = ?
		`, group.Name).Scan(&groupID)
		if err == sql.ErrNoRows {
			// Insert new group
			result, err := tx.Exec(`
				INSERT INTO groups (name)
				VALUES (?)
			`, group.Name)
			if err != nil {
				return fmt.Errorf("failed to insert group: %v", err)
			}
			groupID, err = result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get group ID: %v", err)
			}
		} else if err != nil {
			return fmt.Errorf("failed to query group: %v", err)
		}

		// Insert words and create word-group associations
		for _, word := range group.Words {
			// Insert word
			result, err := tx.Exec(`
				INSERT INTO words (urdu, urdlish, english)
				VALUES (?, ?, ?)
			`, word.Urdu, word.Urdlish, word.English)
			if err != nil {
				return fmt.Errorf("failed to insert word: %v", err)
			}

			wordID, err := result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get word ID: %v", err)
			}

			// Create word-group association
			_, err = tx.Exec(`
				INSERT INTO words_groups (word_id, group_id)
				VALUES (?, ?)
			`, wordID, groupID)
			if err != nil {
				return fmt.Errorf("failed to associate word with group: %v", err)
			}
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}

type StudyActivity struct {
	ID           int    `json:"id"`
	Name         string `json:"name"`
	URL          string `json:"url"`
	ThumbnailURL string `json:"thumbnail_url"`
	Description  string `json:"description"`
}

type WordGroup struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Words       []struct {
		Urdu    string `json:"urdu"`
		Urdlish string `json:"urdlish"`
		English string `json:"english"`
	} `json:"words"`
}

func (s *Seeder) SeedTestData() error {
	// Get the current working directory and find the project root
	wd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get working directory: %v", err)
	}

	// Find the project root by looking for db/seeds directory
	var seedsDir string
	for dir := wd; dir != filepath.Dir(dir); dir = filepath.Dir(dir) {
		if _, err := os.Stat(filepath.Join(dir, "db", "seeds")); err == nil {
			seedsDir = filepath.Join(dir, "db", "seeds")
			break
		}
	}
	if seedsDir == "" {
		return fmt.Errorf("failed to find db/seeds directory")
	}

	// Read and parse study activities
	studyActivitiesBytes, err := os.ReadFile(filepath.Join(seedsDir, "study_activities.json"))
	if err != nil {
		return fmt.Errorf("failed to read study activities: %v", err)
	}

	var studyActivities []StudyActivity
	if err := json.Unmarshal(studyActivitiesBytes, &studyActivities); err != nil {
		return fmt.Errorf("failed to parse study activities: %v", err)
	}

	// Read and parse word groups
	wordGroupsBytes, err := os.ReadFile(filepath.Join(seedsDir, "word_groups.json"))
	if err != nil {
		return fmt.Errorf("failed to read word groups: %v", err)
	}

	var wordGroups []WordGroup
	if err := json.Unmarshal(wordGroupsBytes, &wordGroups); err != nil {
		return fmt.Errorf("failed to parse word groups: %v", err)
	}

	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Clear existing data
	_, err = tx.Exec(`DELETE FROM word_review_items`)
	if err != nil {
		return fmt.Errorf("failed to clear word_review_items: %v", err)
	}
	_, err = tx.Exec(`DELETE FROM study_sessions`)
	if err != nil {
		return fmt.Errorf("failed to clear study_sessions: %v", err)
	}
	_, err = tx.Exec(`DELETE FROM study_activities`)
	if err != nil {
		return fmt.Errorf("failed to clear study_activities: %v", err)
	}
	_, err = tx.Exec(`DELETE FROM words_groups`)
	if err != nil {
		return fmt.Errorf("failed to clear words_groups: %v", err)
	}
	_, err = tx.Exec(`DELETE FROM words`)
	if err != nil {
		return fmt.Errorf("failed to clear words: %v", err)
	}
	_, err = tx.Exec(`DELETE FROM groups`)
	if err != nil {
		return fmt.Errorf("failed to clear groups: %v", err)
	}

	// Insert groups first
	for i, group := range wordGroups {
		groupID := i + 1
		_, err := tx.Exec(`INSERT INTO groups (id, name, word_count) VALUES (?, ?, ?)`,
			groupID, group.Name, len(group.Words))
		if err != nil {
			return fmt.Errorf("failed to insert group: %v", err)
		}

		// Insert words and word_groups
		for _, word := range group.Words {
			// Let SQLite auto-increment handle the word IDs
			result, err := tx.Exec(`INSERT INTO words (urdu, urdlish, english) VALUES (?, ?, ?)`,
				word.Urdu, word.Urdlish, word.English)
			if err != nil {
				return fmt.Errorf("failed to insert word: %v", err)
			}

			// Get the auto-generated word ID
			wordID, err := result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get last insert ID: %v", err)
			}

			_, err = tx.Exec(`INSERT INTO words_groups (word_id, group_id) VALUES (?, ?)`,
				wordID, groupID)
			if err != nil {
				return fmt.Errorf("failed to insert word_group: %v", err)
			}
		}
	}

	// Insert study activities
	for _, activity := range studyActivities {
		_, err := tx.Exec(`INSERT INTO study_activities (id, group_id, activity_id) VALUES (?, ?, ?)`,
			activity.ID, 1, activity.ID) // Using first group for all activities in test data
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
