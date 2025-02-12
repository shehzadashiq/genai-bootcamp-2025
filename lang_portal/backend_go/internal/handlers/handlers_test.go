package handlers

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"lang_portal/internal/service"
	"lang_portal/internal/testutil"

	"github.com/gin-gonic/gin"
)

const testDBPath = ":memory:"

type TestHandler struct {
	*Handler
	db *testutil.TestDB
}

func NewTestHandler(t *testing.T) *TestHandler {
	db := testutil.NewTestDB(t)
	db.Seed()
	svc := service.NewServiceWithDB(db.DB)
	return &TestHandler{
		Handler: NewHandler(svc),
		db: db,
	}
}

func setupTestRouter(t *testing.T) *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	
	h := NewTestHandler(t)
	
	// API routes
	api := r.Group("/api")
	{
		api.GET("/words", h.ListWords)
		api.GET("/words/:id", h.GetWord)
		api.GET("/dashboard/quick-stats", h.GetQuickStats)
		api.POST("/study_activities", h.CreateStudyActivity)
		api.POST("/study_sessions/:id/words/:word_id/review", h.ReviewWord)
		api.GET("/study_sessions", h.ListStudySessions)
		api.GET("/study_sessions/:id", h.GetStudySession)
		api.GET("/study_sessions/:id/words", h.GetStudySessionWords)
	}
	
	return r
}

func TestListWordsEndpoint(t *testing.T) {
	router := setupTestRouter(t)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/words?page=1", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	items, ok := response["items"].([]interface{})
	if !ok {
		t.Fatal("Expected items array in response")
	}

	if len(items) == 0 {
		t.Error("Expected non-empty items array")
	}
}

func TestCreateStudySessionEndpoint(t *testing.T) {
	router := setupTestRouter(t)

	payload := `{"group_id": 1, "study_activity_id": 1}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/study_activities", 
		strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status 201, got %d", w.Code)
	}
}

func TestErrorHandling(t *testing.T) {
	router := setupTestRouter(t)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/nonexistent", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", w.Code)
	}
}

func TestInvalidJSON(t *testing.T) {
	router := setupTestRouter(t)

	payload := `{"group_id": "invalid"}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/study_activities", 
		strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status 400, got %d", w.Code)
	}
}

func TestMissingParameters(t *testing.T) {
	router := setupTestRouter(t)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/words?page=invalid", nil)
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status 400, got %d", w.Code)
	}
} 