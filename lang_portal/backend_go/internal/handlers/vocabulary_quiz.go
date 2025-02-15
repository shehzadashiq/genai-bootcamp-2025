package handlers

import (
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"lang_portal/internal/models"
	"lang_portal/internal/service"
)

// QuizDifficulty represents the difficulty level of the quiz
type QuizDifficulty string

const (
	Easy   QuizDifficulty = "easy"
	Medium QuizDifficulty = "medium"
	Hard   QuizDifficulty = "hard"
)

// QuizConfig represents the configuration for a quiz
type QuizConfig struct {
	GroupID    int64          `json:"group_id" binding:"required"`
	Difficulty QuizDifficulty `json:"difficulty" binding:"required"`
	WordCount  int           `json:"word_count" binding:"required,min=5,max=20"`
}

// QuizWord represents a word in the quiz with multiple choice options
type QuizWord struct {
	Word     *models.WordResponse `json:"word"`
	Options  []string            `json:"options"`
}

// QuizScore represents the score for a quiz session
type QuizScore struct {
	SessionID    int64   `json:"session_id"`
	TotalWords   int     `json:"total_words"`
	CorrectCount int     `json:"correct_count"`
	Accuracy     float64 `json:"accuracy"`
	Difficulty   string  `json:"difficulty"`
}

// RegisterVocabularyQuizRoutes registers all routes for vocabulary quiz
func RegisterVocabularyQuizRoutes(r *gin.RouterGroup, svc *service.Service) {
	h := NewHandler(svc)
	quiz := r.Group("/vocabulary-quiz")
	{
		quiz.POST("/start", h.StartQuiz)
		quiz.GET("/words/:id", h.GetQuizWords)
		quiz.POST("/submit", h.SubmitQuizAnswer)
		quiz.GET("/score/:session_id", h.GetQuizScore)
	}
}

// StartQuiz initializes a new quiz session with the specified configuration
func (h *Handler) StartQuiz(c *gin.Context) {
	var config QuizConfig
	if err := c.ShouldBindJSON(&config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Create a new study session for this quiz
	session, err := h.svc.CreateStudySession(config.GroupID, 1) // 1 is the ID for Vocabulary Quiz activity
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"session_id": session.ID,
		"difficulty": config.Difficulty,
		"word_count": config.WordCount,
	})
}

// GetQuizWords returns a set of words for the quiz with multiple choice options
func (h *Handler) GetQuizWords(c *gin.Context) {
	sessionID, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid session ID"})
		return
	}

	// Get the session to get the group ID
	session, err := h.svc.GetStudySession(sessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get study session: %v", err)})
		return
	}

	// Get all words from the group to use as options
	words, err := h.svc.GetGroupWords(session.GroupID, 1) // Get first page of words
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get group words: %v", err)})
		return
	}

	wordResponses := words.Items.([]models.WordResponse)
	if len(wordResponses) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "No words found in the group"})
		return
	}

	// Convert []models.WordResponse to []*models.WordResponse
	allWords := make([]*models.WordResponse, len(wordResponses))
	for i := range wordResponses {
		allWords[i] = &wordResponses[i]
		// Ensure ID is set correctly
		allWords[i].ID = int64(i + 1)
	}

	quizWords := make([]QuizWord, len(allWords))

	// For each word, create multiple choice options
	for i, word := range allWords {
		options := generateOptions(word, allWords)
		quizWords[i] = QuizWord{
			Word:    word,
			Options: options,
		}
	}

	c.JSON(http.StatusOK, quizWords)
}

// QuizAnswer represents a submitted answer for the vocabulary quiz
type QuizAnswer struct {
	WordID    int64  `json:"word_id" binding:"required"`
	SessionID int64  `json:"session_id" binding:"required"`
	Answer    string `json:"answer" binding:"required"`
	Correct   bool   `json:"correct"`
}

// SubmitQuizAnswer handles the submission of a quiz answer
func (h *Handler) SubmitQuizAnswer(c *gin.Context) {
	var answer QuizAnswer
	if err := c.ShouldBindJSON(&answer); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Create a word review item
	reviewItem, err := h.svc.ReviewWord(answer.SessionID, answer.WordID, answer.Correct)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, reviewItem)
}

// GetQuizScore returns the score for a quiz session
func (h *Handler) GetQuizScore(c *gin.Context) {
	sessionID, err := strconv.ParseInt(c.Param("session_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session id"})
		return
	}

	// Get all review items for this session
	reviewItems, err := h.svc.GetStudySessionWords(sessionID, 1) // Get first page
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	items := reviewItems.Items.([]models.WordResponse)
	correctCount := 0
	for _, item := range items {
		if item.CorrectCount > 0 {
			correctCount++
		}
	}

	accuracy := float64(correctCount) / float64(len(items)) * 100

	score := QuizScore{
		SessionID:    sessionID,
		TotalWords:   len(items),
		CorrectCount: correctCount,
		Accuracy:     accuracy,
	}

	c.JSON(http.StatusOK, score)
}

// generateOptions creates multiple choice options for a word
func generateOptions(word *models.WordResponse, allWords []*models.WordResponse) []string {
	rand.Seed(time.Now().UnixNano())
	
	// Create a map to ensure unique options
	optionsMap := make(map[string]bool)
	optionsMap[word.English] = true // Add correct answer
	
	options := []string{word.English}
	
	// Add 3 more random options
	for len(options) < 4 {
		randomWord := allWords[rand.Intn(len(allWords))]
		if !optionsMap[randomWord.English] {
			optionsMap[randomWord.English] = true
			options = append(options, randomWord.English)
		}
	}
	
	// Shuffle options
	rand.Shuffle(len(options), func(i, j int) {
		options[i], options[j] = options[j], options[i]
	})
	
	return options
}
