package models

import "time"

type PaginatedResponse struct {
	Items      interface{} `json:"items"`
	Pagination Pagination  `json:"pagination"`
}

type DashboardStats struct {
	TotalWordsStudied   int     `json:"total_words_studied"`
	CorrectCount        int     `json:"correct_count"`
	CorrectPercentage   int     `json:"correct_percentage"`
	TotalAvailableWords int     `json:"total_available_words"`
	TotalStudySessions  int     `json:"total_study_sessions"`
	TotalActiveGroups   int     `json:"total_active_groups"`
	StudyStreakDays     int     `json:"study_streak_days"`
}

type StudyProgress struct {
	TotalWordsStudied   int `json:"total_words_studied"`
	TotalAvailableWords int `json:"total_available_words"`
}

type StudyActivityResponse struct {
	ID           int64      `json:"id"`
	Name         string     `json:"name"`
	URL          *string    `json:"url,omitempty"`
	ThumbnailURL *string    `json:"thumbnail_url,omitempty"`
	Description  *string    `json:"description,omitempty"`
	CreatedAt    time.Time  `json:"created_at"`
}

type StudySessionResponse struct {
	ID               int64  `json:"id"`
	GroupID          int64  `json:"group_id"`
	ActivityName     string `json:"activity_name,omitempty"`
	GroupName        string `json:"group_name,omitempty"`
	StartTime        string `json:"start_time,omitempty"`
	EndTime          string `json:"end_time,omitempty"`
	ReviewItemsCount int    `json:"review_items_count"`
}

type WordResponse struct {
	ID           int64  `json:"id"`
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