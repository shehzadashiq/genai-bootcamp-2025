package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"lang_portal/internal/models"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestStartQuiz(t *testing.T) {
	h := NewTestHandler(t)
	router := setupTestRouter(t)

	tests := []struct {
		name       string
		config     QuizConfig
		wantStatus int
	}{
		{
			name: "valid config",
			config: QuizConfig{
				GroupID:    1,
				Difficulty: Easy,
				WordCount:  10,
			},
			wantStatus: http.StatusCreated,
		},
		{
			name: "invalid word count",
			config: QuizConfig{
				GroupID:    1,
				Difficulty: Easy,
				WordCount:  2, // Min is 5
			},
			wantStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.config)
			req := httptest.NewRequest("POST", "/api/vocabulary-quiz/start", bytes.NewBuffer(body))
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			assert.Equal(t, tt.wantStatus, w.Code)
			if tt.wantStatus == http.StatusCreated {
				var resp map[string]interface{}
				err := json.Unmarshal(w.Body.Bytes(), &resp)
				assert.NoError(t, err)
				assert.Contains(t, resp, "session_id")
			}
		})
	}
}

func TestGetQuizWords(t *testing.T) {
	h := NewTestHandler(t)
	router := setupTestRouter(t)

	// Create a test session first
	session, err := h.svc.CreateStudySession(1, 1)
	assert.NoError(t, err)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/vocabulary-quiz/words/%d", session.ID), nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var words []QuizWord
	err = json.Unmarshal(w.Body.Bytes(), &words)
	assert.NoError(t, err)
	assert.NotEmpty(t, words)

	// Verify each word has 4 options
	for _, word := range words {
		assert.Len(t, word.Options, 4)
		assert.Contains(t, word.Options, word.Word.English) // Correct answer must be in options
	}
}

func TestSubmitQuizAnswer(t *testing.T) {
	h := NewTestHandler(t)
	router := setupTestRouter(t)

	// Create a test session
	session, err := h.svc.CreateStudySession(1, 1)
	assert.NoError(t, err)

	answer := QuizAnswer{
		WordID:    1,
		SessionID: session.ID,
		Answer:    "test",
		IsCorrect: true,
	}

	body, _ := json.Marshal(answer)
	req := httptest.NewRequest("POST", "/api/vocabulary-quiz/submit", bytes.NewBuffer(body))
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var reviewItem models.WordReviewItem
	err = json.Unmarshal(w.Body.Bytes(), &reviewItem)
	assert.NoError(t, err)
	assert.Equal(t, answer.WordID, reviewItem.WordID)
	assert.Equal(t, answer.StudySessionID, reviewItem.StudySessionID)
	assert.Equal(t, answer.IsCorrect, reviewItem.Correct)
}

func TestGetQuizScore(t *testing.T) {
	h := NewTestHandler(t)
	router := setupTestRouter(t)

	// Create a test session
	session, err := h.svc.CreateStudySession(1, 1)
	assert.NoError(t, err)

	// Submit some test answers
	answers := []QuizAnswer{
		{WordID: 1, SessionID: session.ID, Answer: "test1", IsCorrect: true},
		{WordID: 2, SessionID: session.ID, Answer: "test2", IsCorrect: false},
		{WordID: 3, SessionID: session.ID, Answer: "test3", IsCorrect: true},
	}

	for _, answer := range answers {
		_, err := h.svc.ReviewWord(answer.SessionID, answer.WordID, answer.IsCorrect)
		assert.NoError(t, err)
	}

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/vocabulary-quiz/score/%d", session.ID), nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var score QuizScore
	err = json.Unmarshal(w.Body.Bytes(), &score)
	assert.NoError(t, err)
	assert.Equal(t, session.ID, score.SessionID)
	assert.Equal(t, 3, score.TotalWords)
	assert.Equal(t, 2, score.CorrectCount)
	assert.InDelta(t, 66.67, score.Accuracy, 0.01)
}
