package service

import (
	"database/sql"
	"fmt"
	"lang_portal/internal/db/seeder"
	"lang_portal/internal/models"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type Service struct {
	db     *models.DB
	seeder *seeder.Seeder
}

// NewService creates a new service with the given database path
func NewService(dbPath string) (*Service, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %v", err)
	}

	modelDB := models.NewDB(db)
	svc := &Service{
		db:     modelDB,
		seeder: seeder.NewSeeder(modelDB),
	}

	// Initialize database schema
	if err := svc.initSchema(); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %v", err)
	}

	// Seed data from JSON files
	if err := svc.seedData(); err != nil {
		return nil, fmt.Errorf("failed to seed data: %v", err)
	}

	return svc, nil
}

// NewServiceWithDB creates a new service with an existing database connection
func NewServiceWithDB(db *sql.DB) *Service {
	modelDB := models.NewDB(db)
	return &Service{
		db:     modelDB,
		seeder: seeder.NewSeeder(modelDB),
	}
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

	// Get total words studied and correct count
	err := s.db.QueryRow(`
		SELECT 
			COALESCE(COUNT(*), 0), 
			COALESCE(SUM(CASE WHEN correct THEN 1 ELSE 0 END), 0)
		FROM word_review_items
		WHERE study_session_id IN (SELECT id FROM study_sessions WHERE created_at >= datetime('now', '-30 days'))
	`).Scan(&stats.TotalWordsStudied, &stats.CorrectCount)
	if err != nil {
		return nil, err
	}

	// Calculate correct percentage
	if stats.TotalWordsStudied > 0 {
		stats.CorrectPercentage = int((float64(stats.CorrectCount) / float64(stats.TotalWordsStudied)) * 100)
	}

	// Get total available words
	err = s.db.QueryRow(`
		SELECT COUNT(*) FROM words
	`).Scan(&stats.TotalAvailableWords)
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
	activity, err := s.db.GetStudyActivity(id)
	if err != nil {
		return nil, err
	}

	return &models.StudyActivityResponse{
		ID:           activity.ID,
		Name:         activity.Name,
		ThumbnailURL: activity.ThumbnailURL,
		Description:  activity.Description,
		CreatedAt:    activity.CreatedAt,
	}, nil
}

func (s *Service) GetStudyActivitySessions(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100

	rows, err := s.db.Query(`
		SELECT ss.id, g.name, sa.name,
			   ss.created_at,
			   strftime('%Y-%m-%dT%H:%M:%SZ', datetime(ss.created_at, '+10 minutes')),
			   COUNT(wri.word_id)
		FROM study_sessions ss
		LEFT JOIN study_activities sa ON ss.study_activity_id = sa.id
		LEFT JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE ss.study_activity_id = ?
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
		var (
			activityName sql.NullString
			groupName    sql.NullString
			startTime    sql.NullTime
			endTimeStr   sql.NullString
			reviewCount  sql.NullInt64
		)

		err := rows.Scan(
			&session.ID,
			&groupName,
			&activityName,
			&startTime,
			&endTimeStr,
			&reviewCount,
		)
		if err != nil {
			return nil, err
		}

		if activityName.Valid {
			session.ActivityName = activityName.String
		}
		if groupName.Valid {
			session.GroupName = groupName.String
		}
		if startTime.Valid {
			session.StartTime = startTime.Time.Format(time.RFC3339)
		}
		if endTimeStr.Valid {
			session.EndTime = endTimeStr.String
		}
		if reviewCount.Valid {
			session.ReviewItemsCount = int(reviewCount.Int64)
		}

		sessions = append(sessions, session)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

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
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) CreateStudySessionWithActivity(groupID int64, activityName string) (*models.StudySessionResponse, error) {
	// First check if the group exists
	_, err := s.GetGroup(groupID)
	if err != nil {
		return nil, fmt.Errorf("group not found: %v", err)
	}

	// Get the activity ID
	var activityID int64
	err = s.db.QueryRow(`
		SELECT id FROM study_activities WHERE name = ?
	`, activityName).Scan(&activityID)
	if err != nil {
		return nil, fmt.Errorf("activity not found: %v", err)
	}

	return s.CreateStudySession(groupID, activityID)
}

func (s *Service) CreateStudySession(groupID int64, studyActivityID int64) (*models.StudySessionResponse, error) {
	// Begin a transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// First check if group exists
	_, err = s.GetGroup(groupID)
	if err != nil {
		return nil, fmt.Errorf("group not found: %v", err)
	}

	// Check if group has words
	groupWords, err := s.GetGroupWords(groupID, 1)
	if err != nil {
		return nil, fmt.Errorf("failed to get group words: %v", err)
	}
	if groupWords.Items == nil || len(groupWords.Items.([]models.WordResponse)) == 0 {
		return nil, fmt.Errorf("group has no words")
	}

	// Then check if study activity exists
	_, err = s.GetStudyActivity(studyActivityID)
	if err != nil {
		return nil, fmt.Errorf("study activity not found: %v", err)
	}

	// Create study session
	now := time.Now()
	result, err := tx.Exec(`
		INSERT INTO study_sessions (group_id, study_activity_id, created_at)
		VALUES (?, ?, ?)
	`, groupID, studyActivityID, now)
	if err != nil {
		return nil, fmt.Errorf("failed to create study session: %v", err)
	}

	sessionID, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("failed to get session id: %v", err)
	}

	// Initialize word review items for all words in the group
	words := groupWords.Items.([]models.WordResponse)
	for _, word := range words {
		_, err = tx.Exec(`
			INSERT INTO word_review_items (study_session_id, word_id, correct, created_at)
			VALUES (?, ?, false, CURRENT_TIMESTAMP)
		`, sessionID, word.ID)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize word review item: %v", err)
		}
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %v", err)
	}

	// Return the created session
	return s.GetStudySession(sessionID)
}

func (s *Service) GetStudyActivities(page int) (*models.PaginatedResponse, error) {
	itemsPerPage := 100
	offset := (page - 1) * itemsPerPage

	activities, err := s.db.GetStudyActivities(itemsPerPage, offset)
	if err != nil {
		return nil, err
	}

	total, err := s.db.CountStudyActivities()
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: activities,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:   (total + itemsPerPage - 1) / itemsPerPage,
			TotalItems:   total,
			ItemsPerPage: itemsPerPage,
		},
	}, nil
}

func (s *Service) CreateStudyActivity(groupID int64, activityID int64) (*models.StudyActivityResponse, error) {
	var activity models.StudyActivityResponse
	err := s.db.QueryRow(`
		INSERT INTO study_activities (group_id, activity_id, created_at)
		VALUES (?, ?, CURRENT_TIMESTAMP)
		RETURNING id, group_id, activity_id, created_at
	`, groupID, activityID).Scan(&activity.ID, &activity.Name, &activity.Description, &activity.CreatedAt)
	if err != nil {
		return nil, err
	}
	return &activity, nil
}

// Words methods
func (s *Service) ListWords(page int) (*models.PaginatedResponse, error) {
	if page < 1 {
		return nil, fmt.Errorf("invalid page number: %d", page)
	}
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
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
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

func (s *Service) CreateWord(word *models.Word) error {
	// Begin a transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	result, err := tx.Exec(`
		INSERT INTO words (urdu, urdlish, english)
		VALUES (?, ?, ?)
	`, word.Urdu, word.Urdlish, word.English)
	if err != nil {
		return fmt.Errorf("failed to create word: %v", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get word id: %v", err)
	}
	word.ID = id

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
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
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
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
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("group not found")
		}
		return nil, fmt.Errorf("failed to get group: %v", err)
	}
	return &group, nil
}

func (s *Service) GetGroupWords(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100
	rows, err := s.db.Query(`
		SELECT w.id, w.urdu, w.urdlish, w.english,
			   COUNT(CASE WHEN wri2.correct THEN 1 END) as correct_count,
			   COUNT(CASE WHEN NOT wri2.correct THEN 1 END) as wrong_count
		FROM words w
		JOIN words_groups wg ON w.id = wg.word_id
		LEFT JOIN word_review_items wri2 ON w.id = wri2.word_id
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
		if err := rows.Scan(&word.ID, &word.Urdu, &word.Urdlish, &word.English,
			&word.CorrectCount, &word.WrongCount); err != nil {
			return nil, err
		}
		words = append(words, word)
	}

	var total int
	err = s.db.QueryRow(`
		SELECT COUNT(DISTINCT w.id)
		FROM words w
		JOIN words_groups wg ON w.id = wg.word_id
		WHERE wg.group_id = ?
	`, id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: words,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetGroupStudySessions(id int64, page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100

	rows, err := s.db.Query(`
		SELECT ss.id, g.name, sa.name,
			   ss.created_at,
			   strftime('%Y-%m-%dT%H:%M:%SZ', datetime(ss.created_at, '+10 minutes')),
			   COUNT(wri.word_id)
		FROM study_sessions ss
		LEFT JOIN study_activities sa ON ss.study_activity_id = sa.id
		LEFT JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE ss.group_id = ?
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
		var (
			activityName sql.NullString
			groupName    sql.NullString
			startTime    sql.NullTime
			endTimeStr   sql.NullString
			reviewCount  sql.NullInt64
		)

		err := rows.Scan(
			&session.ID,
			&groupName,
			&activityName,
			&startTime,
			&endTimeStr,
			&reviewCount,
		)
		if err != nil {
			return nil, err
		}

		if activityName.Valid {
			session.ActivityName = activityName.String
		}
		if groupName.Valid {
			session.GroupName = groupName.String
		}
		if startTime.Valid {
			session.StartTime = startTime.Time.Format(time.RFC3339)
		}
		if endTimeStr.Valid {
			session.EndTime = endTimeStr.String
		}
		if reviewCount.Valid {
			session.ReviewItemsCount = int(reviewCount.Int64)
		}

		sessions = append(sessions, session)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	var total int
	err = s.db.QueryRow(`
		SELECT COUNT(DISTINCT ss.id)
		FROM study_sessions ss
		WHERE ss.group_id = ?
	`, id).Scan(&total)
	if err != nil {
		return nil, err
	}

	return &models.PaginatedResponse{
		Items: sessions,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) ListStudySessions(page int) (*models.PaginatedResponse, error) {
	offset := (page - 1) * 100

	// First, get total count
	var totalCount int
	err := s.db.QueryRow(`
		SELECT COUNT(DISTINCT ss.id)
		FROM study_sessions ss
	`).Scan(&totalCount)
	if err != nil {
		return nil, err
	}

	// If no records exist, return empty response with pagination
	if totalCount == 0 {
		return &models.PaginatedResponse{
			Items: []interface{}{},
			Pagination: models.Pagination{
				CurrentPage:  page,
				TotalPages:   0,
				TotalItems:   0,
				ItemsPerPage: 100,
			},
		}, nil
	}

	rows, err := s.db.Query(`
		SELECT ss.id, sa.name as activity_name, g.name as group_name,
			   ss.created_at as start_time,
			   strftime('%Y-%m-%dT%H:%M:%SZ', datetime(ss.created_at, '+10 minutes')) as end_time,
			   COUNT(wri.word_id) as review_items_count
		FROM study_sessions ss
		LEFT JOIN study_activities sa ON ss.study_activity_id = sa.id
		LEFT JOIN groups g ON ss.group_id = g.id
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
		var (
			activityName sql.NullString
			groupName    sql.NullString
			startTime    sql.NullTime
			endTimeStr   sql.NullString
			reviewCount  sql.NullInt64
		)

		err := rows.Scan(
			&session.ID,
			&activityName,
			&groupName,
			&startTime,
			&endTimeStr,
			&reviewCount,
		)
		if err != nil {
			return nil, err
		}

		if activityName.Valid {
			session.ActivityName = activityName.String
		}
		if groupName.Valid {
			session.GroupName = groupName.String
		}
		if startTime.Valid {
			session.StartTime = startTime.Time.Format(time.RFC3339)
		}
		if endTimeStr.Valid {
			session.EndTime = endTimeStr.String
		}
		if reviewCount.Valid {
			session.ReviewItemsCount = int(reviewCount.Int64)
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
			TotalPages:   (total + 99) / 100,
			TotalItems:   total,
			ItemsPerPage: 100,
		},
	}, nil
}

func (s *Service) GetStudySession(id int64) (*models.StudySessionResponse, error) {
	var session models.StudySessionResponse
	var (
		activityName sql.NullString
		groupName    sql.NullString
		startTime    sql.NullTime
		endTimeStr   sql.NullString
		reviewCount  sql.NullInt64
		groupID      sql.NullInt64
	)

	query := `
		SELECT ss.id, ss.group_id, sa.name, g.name,
			   ss.created_at,
			   strftime('%Y-%m-%dT%H:%M:%SZ', datetime(ss.created_at, '+10 minutes')),
			   COUNT(wri.word_id)
		FROM study_sessions ss
		LEFT JOIN study_activities sa ON ss.study_activity_id = sa.id
		LEFT JOIN groups g ON ss.group_id = g.id
		LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
		WHERE ss.id = ?
		GROUP BY ss.id
	`

	err := s.db.QueryRow(query, id).Scan(
		&session.ID,
		&groupID,
		&activityName,
		&groupName,
		&startTime,
		&endTimeStr,
		&reviewCount,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("study session not found")
		}
		return nil, fmt.Errorf("error getting study session: %v", err)
	}

	if groupID.Valid {
		session.GroupID = groupID.Int64
	}
	if activityName.Valid {
		session.ActivityName = activityName.String
	}
	if groupName.Valid {
		session.GroupName = groupName.String
	}
	if startTime.Valid {
		session.StartTime = startTime.Time.Format(time.RFC3339)
	}
	if endTimeStr.Valid {
		session.EndTime = endTimeStr.String
	}
	if reviewCount.Valid {
		session.ReviewItemsCount = int(reviewCount.Int64)
	}

	return &session, nil
}

func (s *Service) GetStudySessionWords(id int64, page int) (*models.PaginatedResponse, error) {
	// Get all words for this session
	rows, err := s.db.Query(`
		SELECT w.id, w.urdu, w.urdlish, w.english
		FROM words w
		INNER JOIN word_review_items wri ON w.id = wri.word_id
		WHERE wri.study_session_id = ?
	`, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get study session words: %v", err)
	}
	defer rows.Close()

	var words []models.WordResponse
	for rows.Next() {
		var word models.WordResponse
		err := rows.Scan(&word.ID, &word.Urdu, &word.Urdlish, &word.English)
		if err != nil {
			return nil, fmt.Errorf("failed to scan word: %v", err)
		}
		words = append(words, word)
	}

	return &models.PaginatedResponse{
		Items: words,
		Pagination: models.Pagination{
			CurrentPage:  page,
			TotalPages:   1,
			TotalItems:   len(words),
			ItemsPerPage: len(words),
		},
	}, nil
}

func (s *Service) ReviewWord(sessionID int64, wordID int64, correct bool) (*models.WordReviewItem, error) {
	// Begin a transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Insert the review item
	_, err = tx.Exec(`
		INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
		VALUES (?, ?, ?, datetime('now'))
		ON CONFLICT(study_session_id, word_id) DO UPDATE SET
		correct = ?,
		created_at = datetime('now')
	`, wordID, sessionID, correct, correct)
	if err != nil {
		return nil, fmt.Errorf("failed to review word: %v", err)
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %v", err)
	}

	// Return the review item
	return &models.WordReviewItem{
		WordID:         wordID,
		StudySessionID: sessionID,
		Correct:        correct,
		CreatedAt:      time.Now(),
	}, nil
}

func (s *Service) AddWordsToGroup(groupID int64, wordIDs []int64) error {
	// Begin a transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Add each word to the group
	for _, wordID := range wordIDs {
		_, err = tx.Exec(`
			INSERT INTO words_groups (word_id, group_id)
			VALUES (?, ?)
		`, wordID, groupID)
		if err != nil {
			return fmt.Errorf("failed to add word to group: %v", err)
		}
	}

	// Update word count
	_, err = tx.Exec(`
		UPDATE groups 
		SET word_count = (
			SELECT COUNT(*) 
			FROM words_groups 
			WHERE group_id = ?
		)
		WHERE id = ?
	`, groupID, groupID)
	if err != nil {
		return fmt.Errorf("failed to update word count: %v", err)
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}

func (s *Service) AddWordsToStudySession(sessionID int64, wordIDs []int64) error {
	// Begin a transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// First delete any existing word review items for this session
	_, err = tx.Exec(`DELETE FROM word_review_items WHERE study_session_id = ?`, sessionID)
	if err != nil {
		return fmt.Errorf("failed to clean up existing word review items: %v", err)
	}

	// Add each word to the study session
	for _, wordID := range wordIDs {
		_, err = tx.Exec(`
			INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
			VALUES (?, ?, false, datetime('now'))
		`, wordID, sessionID)
		if err != nil {
			return fmt.Errorf("failed to add word to study session: %v", err)
		}
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
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

func (s *Service) initSchema() error {
	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Create tables
	schema := []string{
		`CREATE TABLE IF NOT EXISTS words (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			urdu TEXT NOT NULL,
			urdlish TEXT NOT NULL,
			english TEXT NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS groups (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			word_count INTEGER DEFAULT 0,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS words_groups (
			word_id INTEGER NOT NULL,
			group_id INTEGER NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (group_id) REFERENCES groups(id),
			PRIMARY KEY (word_id, group_id)
		)`,
		`CREATE TABLE IF NOT EXISTS study_activities (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			group_id INTEGER NOT NULL,
			activity_id INTEGER NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (group_id) REFERENCES groups(id)
		)`,
		`CREATE TABLE IF NOT EXISTS study_sessions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			group_id INTEGER NOT NULL,
			study_activity_id INTEGER NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (group_id) REFERENCES groups(id),
			FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
		)`,
		`CREATE TABLE IF NOT EXISTS word_review_items (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			word_id INTEGER NOT NULL,
			study_session_id INTEGER NOT NULL,
			correct BOOLEAN NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
		)`,
	}

	// Execute schema
	for _, query := range schema {
		if _, err := tx.Exec(query); err != nil {
			return fmt.Errorf("failed to execute schema: %v", err)
		}
	}

	// Verify tables were created
	tables := []string{"words", "groups", "words_groups", "study_activities", "study_sessions", "word_review_items"}
	for _, table := range tables {
		var count int
		err = tx.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?`, table).Scan(&count)
		if err != nil {
			return fmt.Errorf("failed to verify table %s: %v", table, err)
		}
		if count != 1 {
			return fmt.Errorf("table %s was not created", table)
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}

func (s *Service) seedData() error {
	return s.seeder.SeedFromJSON("db/seeds")
}
