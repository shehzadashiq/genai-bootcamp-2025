package service

import (
	"database/sql"
	"fmt"
	"lang_portal/internal/models"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type Service struct {
	db *sql.DB
}

func NewService(dbPath string) *Service {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		panic(err)
	}
	return &Service{db: db}
}

func (s *Service) Close() error {
	return s.db.Close()
}

// Dashboard methods
func (s *Service) GetLastStudySession() (*models.StudySessionResponse, error) {
	var session models.StudySessionResponse
	err := s.db.QueryRow(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   datetime(ss.created_at, '+10 minutes') as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		JOIN study_activities sa ON ss.study_activity_id = sa.id
		JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		GROUP BY ss.id
		ORDER BY ss.created_at DESC
		LIMIT 1
	`).Scan(&session.ID, &session.ActivityName, &session.GroupName,
		&session.StartTime, &session.EndTime, &session.ReviewItemsCount)
	if err != nil {
		return nil, err
	}
	return &session, nil
}

func (s *Service) GetStudyProgress() (*models.StudyProgress, error) {
	var progress models.StudyProgress
	err := s.db.QueryRow(`
		SELECT COUNT(DISTINCT word_id), (SELECT COUNT(*) FROM words)
		FROM word_review_items
	`).Scan(&progress.TotalWordsStudied, &progress.TotalAvailableWords)
	if err != nil {
		return nil, err
	}
	return &progress, nil
}

func (s *Service) GetQuickStats() (*models.DashboardStats, error) {
	var stats models.DashboardStats

	// Calculate success rate
	err := s.db.QueryRow(`
		SELECT COALESCE(AVG(CASE WHEN correct THEN 100.0 ELSE 0.0 END), 0)
		FROM word_review_items
	`).Scan(&stats.SuccessRate)
	if err != nil {
		return nil, err
	}

	// Get total study sessions
	err = s.db.QueryRow(`
		SELECT COUNT(*) FROM study_sessions
	`).Scan(&stats.TotalStudySessions)
	if err != nil {
		return nil, err
	}

	// Get total active groups
	err = s.db.QueryRow(`
		SELECT COUNT(DISTINCT group_id) 
		FROM study_sessions 
		WHERE created_at >= datetime('now', '-30 days')
	`).Scan(&stats.TotalActiveGroups)
	if err != nil {
		return nil, err
	}

	// Calculate study streak
	err = s.db.QueryRow(`
		WITH RECURSIVE dates(date) AS (
			SELECT date(max(created_at)) FROM study_sessions
			UNION ALL
			SELECT date(date, '-1 day')
			FROM dates
			WHERE EXISTS (
				SELECT 1 FROM study_sessions 
				WHERE date(created_at) = date(date, '-1 day')
			)
		)
		SELECT COUNT(*) FROM dates
	`).Scan(&stats.StudyStreakDays)
	if err != nil {
		return nil, err
	}

	return &stats, nil
}

// Study activities methods
func (s *Service) GetStudyActivity(id int64) (*models.StudyActivityResponse, error) {
	var activity models.StudyActivityResponse
	err := s.db.QueryRow(`
		SELECT id, name, thumbnail_url, description
		FROM study_activities WHERE id = ?
	`, id).Scan(&activity.ID, &activity.Name, &activity.ThumbnailURL, &activity.Description)
	if err != nil {
		return nil, err
	}
	return &activity, nil
}

func (s *Service) GetStudyActivitySessions(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   datetime(ss.created_at, '+10 minutes') as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		JOIN study_activities sa ON ss.study_activity_id = sa.id
		JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE sa.id = ?
		GROUP BY ss.id
		ORDER BY ss.created_at DESC
		LIMIT 100 OFFSET ?
	`, id, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sessions []models.StudySessionResponse
	for rows.Next() {
		var session models.StudySessionResponse
		if err := rows.Scan(&session.ID, &session.ActivityName, &session.GroupName,
			&session.StartTime, &session.EndTime, &session.ReviewItemsCount); err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}

	// Get total count for pagination
	var total int
	err = s.db.QueryRow(`
		SELECT COUNT(DISTINCT ss.id)
		FROM study_sessions ss
		WHERE ss.study_activity_id = ?
	`, id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: sessions,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) CreateStudyActivity(groupID, studyActivityID int64) (*models.StudyActivityResponse, error) {
	result, err := s.db.Exec(`
		INSERT INTO study_activities (group_id, created_at)
		VALUES (?, ?)
	`, groupID, time.Now())
	if err != nil {
		return nil, err
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, err
	}

	return &models.StudyActivityResponse{
		ID:          id,
		Name:        fmt.Sprintf("Study Session %d", id),
		Description: "New study session",
	}, nil
}

// Words methods
func (s *Service) ListWords(page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT w.id, w.urdu, w.urdlish, w.english,
			   COUNT(CASE WHEN wri.correct THEN 1 END) as correct_count,
			   COUNT(CASE WHEN NOT wri.correct THEN 1 END) as wrong_count
		FROM words w
		LEFT JOIN word_review_items wri ON w.id = wri.word_id
		GROUP BY w.id
		LIMIT 100 OFFSET ?
	`, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var words []models.WordResponse
	for rows.Next() {
		var word models.WordResponse
		if err := rows.Scan(&word.ID, &word.Urdu, &word.Urdlish, &word.English,
			&word.CorrectCount, &word.WrongCount); err != nil {
			return nil, err
		}
		words = append(words, word)
	}

	// Get total count for pagination
	var total int
	err = s.db.QueryRow("SELECT COUNT(*) FROM words").Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: words,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetWord(id int64) (*models.WordResponse, error) {
	var word models.WordResponse
	err := s.db.QueryRow(`
		SELECT w.id, w.urdu, w.urdlish, w.english,
			   COUNT(CASE WHEN wri.correct THEN 1 END) as correct_count,
			   COUNT(CASE WHEN NOT wri.correct THEN 1 END) as wrong_count
		FROM words w
		LEFT JOIN word_review_items wri ON w.id = wri.word_id
		WHERE w.id = ?
		GROUP BY w.id
	`, id).Scan(&word.ID, &word.Urdu, &word.Urdlish, &word.English, &word.CorrectCount, &word.WrongCount)
	if err != nil {
		return nil, err
	}
	return &word, nil
}

// Groups methods
func (s *Service) ListGroups(page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT g.id, g.name, COUNT(wg.word_id) as word_count
		FROM groups g
		LEFT JOIN words_groups wg ON g.id = wg.group_id
		GROUP BY g.id
		LIMIT 100 OFFSET ?
	`, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var groups []models.GroupResponse
	for rows.Next() {
		var group models.GroupResponse
		if err := rows.Scan(&group.ID, &group.Name, &group.WordCount); err != nil {
			return nil, err
		}
		groups = append(groups, group)
	}

	var total int
	err = s.db.QueryRow("SELECT COUNT(*) FROM groups").Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: groups,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetGroup(id int64) (*models.GroupResponse, error) {
	var group models.GroupResponse
	err := s.db.QueryRow(`
		SELECT g.id, g.name, COUNT(wg.word_id) as word_count
		FROM groups g
		LEFT JOIN words_groups wg ON g.id = wg.group_id
		WHERE g.id = ?
		GROUP BY g.id
	`, id).Scan(&group.ID, &group.Name, &group.WordCount)
	if err != nil {
		return nil, err
	}
	return &group, nil
}

func (s *Service) GetGroupWords(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT w.urdu, w.urdlish, w.english,
			   COUNT(CASE WHEN wri.correct THEN 1 END) as correct_count,
			   COUNT(CASE WHEN NOT wri.correct THEN 1 END) as wrong_count
		FROM words w
		JOIN words_groups wg ON w.id = wg.word_id
		LEFT JOIN word_review_items wri ON w.id = wri.word_id
		WHERE wg.group_id = ?
		GROUP BY w.id
		LIMIT 100 OFFSET ?
	`, id, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var words []models.WordResponse
	for rows.Next() {
		var word models.WordResponse
		if err := rows.Scan(&word.Urdu, &word.Urdlish, &word.English,
			&word.CorrectCount, &word.WrongCount); err != nil {
			return nil, err
		}
		words = append(words, word)
	}

	var total int
	err = s.db.QueryRow("SELECT COUNT(*) FROM words_groups WHERE group_id = ?", id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: words,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetGroupStudySessions(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   datetime(ss.created_at, '+10 minutes') as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		JOIN study_activities sa ON ss.study_activity_id = sa.id
		JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE g.id = ?
		GROUP BY ss.id
		ORDER BY ss.created_at DESC
		LIMIT 100 OFFSET ?
	`, id, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sessions []models.StudySessionResponse
	for rows.Next() {
		var session models.StudySessionResponse
		if err := rows.Scan(&session.ID, &session.ActivityName, &session.GroupName,
			&session.StartTime, &session.EndTime, &session.ReviewItemsCount); err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}

	var total int
	err = s.db.QueryRow(`
		SELECT COUNT(*) FROM study_sessions WHERE group_id = ?
	`, id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: sessions,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) ListStudySessions(page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   datetime(ss.created_at, '+10 minutes') as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		JOIN study_activities sa ON ss.study_activity_id = sa.id
		JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		GROUP BY ss.id
		ORDER BY ss.created_at DESC
		LIMIT 100 OFFSET ?
	`, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sessions []models.StudySessionResponse
	for rows.Next() {
		var session models.StudySessionResponse
		if err := rows.Scan(&session.ID, &session.ActivityName, &session.GroupName,
			&session.StartTime, &session.EndTime, &session.ReviewItemsCount); err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}

	var total int
	err = s.db.QueryRow("SELECT COUNT(*) FROM study_sessions").Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: sessions,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetStudySession(id int64) (*models.StudySessionResponse, error) {
	var session models.StudySessionResponse
	
	err := s.db.QueryRow(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   datetime(ss.created_at, '+10 minutes') as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		JOIN study_activities sa ON ss.study_activity_id = sa.id
		JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE ss.id = ?
		GROUP BY ss.id
	`, id).Scan(&session.ID, &session.ActivityName, &session.GroupName,
		&session.StartTime, &session.EndTime, &session.ReviewItemsCount)
	if err != nil {
		return nil, err
	}

	return &session, nil
}

func (s *Service) GetStudySessionWords(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT w.urdu, w.urdlish, w.english,
			   COUNT(CASE WHEN wri2.correct THEN 1 END) as correct_count,
			   COUNT(CASE WHEN NOT wri2.correct THEN 1 END) as wrong_count
		FROM word_review_items wri
		JOIN words w ON wri.word_id = w.id
		LEFT JOIN word_review_items wri2 ON w.id = wri2.word_id
		WHERE wri.study_session_id = ?
		GROUP BY w.id
		LIMIT 100 OFFSET ?
	`, id, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var words []models.WordResponse
	for rows.Next() {
		var word models.WordResponse
		if err := rows.Scan(&word.Urdu, &word.Urdlish, &word.English,
			&word.CorrectCount, &word.WrongCount); err != nil {
			return nil, err
		}
		words = append(words, word)
	}

	var total int
	err = s.db.QueryRow(`
		SELECT COUNT(DISTINCT word_id) 
		FROM word_review_items 
		WHERE study_session_id = ?
	`, id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: words,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:  (total + 99) / 100,
			TotalItems:  total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) ReviewWord(sessionID, wordID int64, correct bool) (*models.WordReviewItem, error) {
	now := time.Now()
	_, err := s.db.Exec(`
		INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
		VALUES (?, ?, ?, ?)
	`, wordID, sessionID, correct, now)
	if err != nil {
		return nil, err
	}

	return &models.WordReviewItem{
		WordID:         wordID,
		StudySessionID: sessionID,
		Correct:        correct,
		CreatedAt:      now,
	}, nil
}

// System methods
func (s *Service) ResetHistory() error {
	_, err := s.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM study_sessions;
		DELETE FROM study_activities;
	`)
	return err
}

func (s *Service) FullReset() error {
	_, err := s.db.Exec(`
		DELETE FROM word_review_items;
		DELETE FROM study_sessions;
		DELETE FROM study_activities;
		DELETE FROM words_groups;
		DELETE FROM words;
		DELETE FROM groups;
	`)
	return err
} 