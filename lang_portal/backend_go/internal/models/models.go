package models

import (
	"database/sql"
	"fmt"
	"time"
)

// Core domain models
type Word struct {
	ID      int64  `json:"id"`
	Urdu    string `json:"urdu"`
	Urdlish string `json:"urdlish"`
	English string `json:"english"`
	Parts   string `json:"parts"` // JSON string
}

type Group struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`
}

type QuizConfig struct {
	GroupID    int64  `json:"group_id" binding:"required"`
	WordCount  int    `json:"word_count" binding:"required,min=1"`
	Difficulty string `json:"difficulty" binding:"required,oneof=beginner intermediate advanced"`
}

type StudySession struct {
	ID              int64     `json:"id"`
	GroupID         int64     `json:"group_id"`
	CreatedAt       time.Time `json:"created_at"`
	StudyActivityID int64     `json:"study_activity_id"`
}

type StudyActivity struct {
	ID           int64     `json:"id"`
	Name         string    `json:"name"`
	URL          *string   `json:"url,omitempty"`
	ThumbnailURL *string   `json:"thumbnail_url,omitempty"`
	Description  *string   `json:"description,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
}

// WordReviewItem represents a review of a word in a study session
type WordReviewItem struct {
	WordID         int64     `json:"word_id"`
	StudySessionID int64     `json:"study_session_id"`
	Correct        bool      `json:"correct"`
	CreatedAt      time.Time `json:"created_at"`
}

type Pagination struct {
	TotalItems   int `json:"total_items"`
	CurrentPage  int `json:"current_page"`
	TotalPages   int `json:"total_pages"`
	ItemsPerPage int `json:"items_per_page"`
}

// Study Activities database methods
func (db *DB) GetStudyActivities(limit, offset int) ([]*StudyActivity, error) {
	query := `
		SELECT id, name, url, thumbnail_url, description, created_at
		FROM study_activities
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
	`
	rows, err := db.Query(query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var activities []*StudyActivity
	for rows.Next() {
		activity := &StudyActivity{}
		var (
			url          sql.NullString
			thumbnailURL sql.NullString
			description  sql.NullString
			createdAt    sql.NullTime
		)
		err := rows.Scan(
			&activity.ID,
			&activity.Name,
			&url,
			&thumbnailURL,
			&description,
			&createdAt,
		)
		if err != nil {
			return nil, err
		}
		if url.Valid {
			activity.URL = &url.String
		}
		if thumbnailURL.Valid {
			activity.ThumbnailURL = &thumbnailURL.String
		}
		if description.Valid {
			activity.Description = &description.String
		}
		if createdAt.Valid {
			activity.CreatedAt = createdAt.Time
		}
		activities = append(activities, activity)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return activities, nil
}

func (db *DB) CountStudyActivities() (int, error) {
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM study_activities").Scan(&count)
	return count, err
}

func (db *DB) GetStudyActivity(id int64) (*StudyActivity, error) {
	var (
		activity     StudyActivity
		url          sql.NullString
		thumbnailURL sql.NullString
		description  sql.NullString
		createdAt    sql.NullTime
	)
	err := db.QueryRow(`
		SELECT id, name, url, thumbnail_url, description, created_at
		FROM study_activities WHERE id = ?
	`, id).Scan(
		&activity.ID,
		&activity.Name,
		&url,
		&thumbnailURL,
		&description,
		&createdAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("study activity %d not found", id)
		}
		return nil, err
	}

	if url.Valid {
		activity.URL = &url.String
	}
	if thumbnailURL.Valid {
		activity.ThumbnailURL = &thumbnailURL.String
	}
	if description.Valid {
		activity.Description = &description.String
	}
	if createdAt.Valid {
		activity.CreatedAt = createdAt.Time
	}

	return &activity, nil
}

func (db *DB) GetStudyActivitySessions(activityID int64, limit, offset int) ([]*StudySession, error) {
	query := `
		SELECT s.id, s.group_id, s.study_activity_id, s.created_at
		FROM study_sessions s
		WHERE s.study_activity_id = ?
		ORDER BY s.created_at DESC
		LIMIT ? OFFSET ?
	`

	rows, err := db.Query(query, activityID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sessions []*StudySession
	for rows.Next() {
		session := &StudySession{}
		err := rows.Scan(
			&session.ID,
			&session.GroupID,
			&session.StudyActivityID,
			&session.CreatedAt,
		)
		if err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

func (db *DB) CountStudyActivitySessions(activityID int64) (int, error) {
	var count int
	err := db.QueryRow(
		"SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = ?",
		activityID,
	).Scan(&count)
	return count, err
}

func (db *DB) CreateStudySession(session *StudySession) error {
	result, err := db.Exec(
		"INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, ?)",
		session.GroupID,
		session.StudyActivityID,
		session.CreatedAt,
	)
	if err != nil {
		return err
	}

	id, err := result.LastInsertId()
	if err != nil {
		return err
	}

	session.ID = id
	return nil
}
