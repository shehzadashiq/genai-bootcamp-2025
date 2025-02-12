package models

type PaginatedResponse struct {
	Items      interface{} `json:"items"`
	Pagination Pagination  `json:"pagination"`
}

type DashboardStats struct {
	SuccessRate        float64 `json:"success_rate"`
	TotalStudySessions int     `json:"total_study_sessions"`
	TotalActiveGroups  int     `json:"total_active_groups"`
	StudyStreakDays    int     `json:"study_streak_days"`
}

type StudyProgress struct {
	TotalWordsStudied   int `json:"total_words_studied"`
	TotalAvailableWords int `json:"total_available_words"`
}

type StudyActivityResponse struct {
	ID           int64  `json:"id"`
	Name         string `json:"name"`
	ThumbnailURL string `json:"thumbnail_url"`
	Description  string `json:"description"`
}

type StudySessionResponse struct {
	ID               int64  `json:"id"`
	ActivityName     string `json:"activity_name"`
	GroupName        string `json:"group_name"`
	StartTime        string `json:"start_time"`
	EndTime          string `json:"end_time"`
	ReviewItemsCount int    `json:"review_items_count"`
}

type WordResponse struct {
	Urdu         string `json:"urdu"`
	Urdlish      string `json:"urdlish"`
	English      string `json:"english"`
	CorrectCount int    `json:"correct_count"`
	WrongCount   int    `json:"wrong_count"`
}

type GroupResponse struct {
	ID        int64  `json:"id"`
	Name      string `json:"name"`
	WordCount int    `json:"word_count"`
}