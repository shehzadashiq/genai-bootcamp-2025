package handlers

import (
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
	"strings"
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

// StartQuizRequest represents the request body for starting a quiz
type StartQuizRequest struct {
	GroupID  int64 `json:"group_id" binding:"required"`
	WordCount int  `json:"word_count" binding:"required,min=5,max=20"`
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

// QuizAnswer represents a submitted answer for the vocabulary quiz
type QuizAnswer struct {
	WordID    int64  `json:"word_id" binding:"required"`
	SessionID int64  `json:"session_id" binding:"required"`
	Answer    string `json:"answer" binding:"required"`
	Correct   bool   `json:"correct"`
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

// StartQuiz starts a new vocabulary quiz session
func (h *Handler) StartQuiz(c *gin.Context) {
	var req StartQuizRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("StartQuiz: Invalid request body: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	fmt.Printf("StartQuiz: Starting quiz for group %d with %d words\n", req.GroupID, req.WordCount)
	// Create a new study session
	session, err := h.svc.CreateStudySession(req.GroupID, 1) // 1 is the ID for vocabulary quiz activity
	if err != nil {
		fmt.Printf("StartQuiz: Failed to create study session: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create study session: %v", err)})
		return
	}

	// Get words from the group
	groupWords, err := h.svc.GetGroupWords(req.GroupID, 1)
	if err != nil {
		fmt.Printf("StartQuiz: Failed to get group words: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get group words: %v", err)})
		return
	}

	allWords := groupWords.Items.([]models.WordResponse)
	if len(allWords) == 0 {
		fmt.Printf("StartQuiz: No words found in group %d\n", req.GroupID)
		c.JSON(http.StatusNotFound, gin.H{"error": "No words found in the group"})
		return
	}

	fmt.Printf("StartQuiz: Found %d words in group %d\n", len(allWords), req.GroupID)

	// Shuffle and select words for the quiz
	rand.Seed(time.Now().UnixNano())
	rand.Shuffle(len(allWords), func(i, j int) {
		allWords[i], allWords[j] = allWords[j], allWords[i]
	})

	// Select the requested number of words
	wordCount := req.WordCount
	if wordCount <= 0 {
		wordCount = 10 // Default to 10 words
	}
	if wordCount > len(allWords) {
		wordCount = len(allWords)
	}
	selectedWords := allWords[:wordCount]

	fmt.Printf("StartQuiz: Selected %d words for quiz\n", len(selectedWords))

	// Add words to study session
	wordIDs := make([]int64, len(selectedWords))
	for i, word := range selectedWords {
		wordIDs[i] = word.ID
	}

	err = h.svc.AddWordsToStudySession(session.ID, wordIDs)
	if err != nil {
		fmt.Printf("StartQuiz: Failed to add words to session: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to add words to session: %v", err)})
		return
	}

	fmt.Printf("StartQuiz: Created session %d with %d words\n", session.ID, len(selectedWords))
	c.JSON(http.StatusOK, gin.H{
		"session_id": session.ID,
		"word_count": len(selectedWords),
	})
}

// GetQuizWords returns a list of words for a quiz
func (h *Handler) GetQuizWords(c *gin.Context) {
	sessionID, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		fmt.Printf("GetQuizWords: Invalid session ID: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid session ID"})
		return
	}

	fmt.Printf("GetQuizWords: Getting session %d\n", sessionID)
	// Get session to verify it exists
	session, err := h.svc.GetStudySession(sessionID)
	if err != nil {
		fmt.Printf("GetQuizWords: Session not found: %v\n", err)
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("Study session not found: %v", err)})
		return
	}

	fmt.Printf("GetQuizWords: Getting words for session %d\n", sessionID)
	// Get all review items for this session
	reviewItems, err := h.svc.GetStudySessionWords(sessionID, 1) // Get first page
	if err != nil {
		fmt.Printf("GetQuizWords: Failed to get review items: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get review items: %v", err)})
		return
	}

	wordResponses := reviewItems.Items.([]models.WordResponse)
	if len(wordResponses) == 0 {
		fmt.Printf("GetQuizWords: No words found in session %d\n", sessionID)
		c.JSON(http.StatusNotFound, gin.H{"error": "No words found in the session"})
		return
	}

	fmt.Printf("GetQuizWords: Getting all words for group %d\n", session.GroupID)
	// Get all words from the group to use as options
	groupWords, err := h.svc.GetGroupWords(session.GroupID, 1)
	if err != nil {
		fmt.Printf("GetQuizWords: Failed to get group words: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get group words: %v", err)})
		return
	}

	allWords := groupWords.Items.([]models.WordResponse)
	quizWords := make([]QuizWord, len(wordResponses))

	// Use session ID as random seed to ensure consistent options
	rand.Seed(sessionID)

	// For each quiz word, generate options
	for i, word := range wordResponses {
		// Create a map to track used English translations
		usedTranslations := make(map[string]bool)
		usedTranslations[word.English] = true // Mark correct answer as used

		// Get semantically related words based on word type and common terms
		var relatedWords []models.WordResponse
		wordLower := strings.ToLower(word.English)
		
		// Check for family relationships
		if strings.Contains(wordLower, "brother") || strings.Contains(wordLower, "sister") ||
			strings.Contains(wordLower, "mother") || strings.Contains(wordLower, "father") ||
			strings.Contains(wordLower, "aunt") || strings.Contains(wordLower, "uncle") ||
			strings.Contains(wordLower, "cousin") || strings.Contains(wordLower, "son") ||
			strings.Contains(wordLower, "daughter") || strings.Contains(wordLower, "husband") ||
			strings.Contains(wordLower, "wife") || strings.Contains(wordLower, "parent") ||
			strings.Contains(wordLower, "child") || strings.Contains(wordLower, "family") {
			// Find other family-related words
			for _, w := range allWords {
				wLower := strings.ToLower(w.English)
				if (strings.Contains(wLower, "brother") || strings.Contains(wLower, "sister") ||
					strings.Contains(wLower, "mother") || strings.Contains(wLower, "father") ||
					strings.Contains(wLower, "aunt") || strings.Contains(wLower, "uncle") ||
					strings.Contains(wLower, "cousin") || strings.Contains(wLower, "son") ||
					strings.Contains(wLower, "daughter") || strings.Contains(wLower, "husband") ||
					strings.Contains(wLower, "wife") || strings.Contains(wLower, "parent") ||
					strings.Contains(wLower, "child") || strings.Contains(wLower, "family")) &&
					w.ID != word.ID {
					relatedWords = append(relatedWords, w)
				}
			}
		} else if strings.HasPrefix(wordLower, "to ") {
			// For verbs, find other verbs with similar meaning or context
			for _, w := range allWords {
				if strings.HasPrefix(strings.ToLower(w.English), "to ") && w.ID != word.ID {
					relatedWords = append(relatedWords, w)
				}
			}
		} else if strings.Contains(wordLower, "room") || strings.Contains(wordLower, "house") ||
			strings.Contains(wordLower, "building") || strings.Contains(wordLower, "door") ||
			strings.Contains(wordLower, "window") || strings.Contains(wordLower, "wall") ||
			strings.Contains(wordLower, "floor") || strings.Contains(wordLower, "ceiling") {
			// Find other house/building related words
			for _, w := range allWords {
				wLower := strings.ToLower(w.English)
				if (strings.Contains(wLower, "room") || strings.Contains(wLower, "house") ||
					strings.Contains(wLower, "building") || strings.Contains(wLower, "door") ||
					strings.Contains(wLower, "window") || strings.Contains(wLower, "wall") ||
					strings.Contains(wLower, "floor") || strings.Contains(wLower, "ceiling")) &&
					w.ID != word.ID {
					relatedWords = append(relatedWords, w)
				}
			}
		} else if strings.Contains(wordLower, "food") || strings.Contains(wordLower, "drink") ||
			strings.Contains(wordLower, "eat") || strings.Contains(wordLower, "cook") ||
			strings.Contains(wordLower, "meal") || strings.Contains(wordLower, "breakfast") ||
			strings.Contains(wordLower, "lunch") || strings.Contains(wordLower, "dinner") {
			// Find other food/drink related words
			for _, w := range allWords {
				wLower := strings.ToLower(w.English)
				if (strings.Contains(wLower, "food") || strings.Contains(wLower, "drink") ||
					strings.Contains(wLower, "eat") || strings.Contains(wLower, "cook") ||
					strings.Contains(wLower, "meal") || strings.Contains(wLower, "breakfast") ||
					strings.Contains(wLower, "lunch") || strings.Contains(wLower, "dinner")) &&
					w.ID != word.ID {
					relatedWords = append(relatedWords, w)
				}
			}
		}

		// Create a list of options, starting with the correct answer
		selectedOptions := make([]string, 0, 4)
		selectedOptions = append(selectedOptions, word.English)

		// Add related options first
		relatedWords = shuffle(relatedWords)
		for _, w := range relatedWords {
			if len(selectedOptions) >= 4 {
				break
			}
			if !usedTranslations[w.English] {
				selectedOptions = append(selectedOptions, w.English)
				usedTranslations[w.English] = true
			}
		}

		// If we still need more options, add some random ones
		if len(selectedOptions) < 4 {
			shuffledWords := shuffle(allWords)
			for _, w := range shuffledWords {
				if len(selectedOptions) >= 4 {
					break
				}
				if !usedTranslations[w.English] {
					selectedOptions = append(selectedOptions, w.English)
					usedTranslations[w.English] = true
				}
			}
		}

		// Final shuffle of all options
		rand.Shuffle(len(selectedOptions), func(i, j int) {
			selectedOptions[i], selectedOptions[j] = selectedOptions[j], selectedOptions[i]
		})

		fmt.Printf("GetQuizWords: Generated options for word %d (%s): %v\n", word.ID, word.English, selectedOptions)
		
		// Create a copy of the word to avoid pointer issues
		wordCopy := word
		quizWords[i] = QuizWord{
			Word:    &wordCopy,  // Use pointer to the copy instead of the loop variable
			Options: selectedOptions,
		}
	}

	fmt.Printf("GetQuizWords: Returning %d words for session %d\n", len(quizWords), sessionID)
	c.JSON(http.StatusOK, gin.H{
		"words": quizWords,
	})
}

// isNoun checks if a word is likely a noun based on common patterns
func isNoun(word string) bool {
	// Skip common prefixes that indicate non-nouns
	commonPrefixes := []string{
		"to ", "is ", "are ", "was ", "were ",
		"this ", "that ", "these ", "those ",
		"my ", "your ", "his ", "her ", "its ", "our ", "their ",
		"a ", "an ", "the ",
		"in ", "on ", "at ", "by ", "for ", "with ", "from ",
		"and ", "or ", "but ", "if ", "when ", "where ", "how ",
		"what ", "who ", "whom ", "whose ", "which ",
		"yes ", "no ", "okay ", "please ", "thank ",
	}

	word = strings.ToLower(word)
	for _, prefix := range commonPrefixes {
		if strings.HasPrefix(word, prefix) {
			return false
		}
	}

	// Check for pronouns and common non-nouns
	pronouns := []string{
		"i", "you", "he", "she", "it", "we", "they",
		"me", "him", "her", "us", "them",
		"this", "that", "these", "those",
		"who", "what", "where", "when", "why", "how",
	}

	for _, pronoun := range pronouns {
		if word == pronoun {
			return false
		}
	}

	// Check for family relation terms
	familyTerms := []string{
		"mother", "father", "sister", "brother",
		"aunt", "uncle", "grandfather", "grandmother",
		"son", "daughter", "cousin", "wife", "husband",
		"parent", "child", "sibling",
	}

	for _, term := range familyTerms {
		if strings.Contains(word, term) {
			return true
		}
	}

	// Common object words are likely nouns
	objectWords := []string{
		"table", "chair", "bed", "door", "window",
		"phone", "book", "pen", "pencil", "paper",
		"plate", "cup", "glass", "spoon", "fork", "knife",
		"room", "house", "car", "bike", "computer",
		"television", "radio", "clock", "watch", "camera",
		"key", "lock", "bowl", "utensil", "fan",
		"ceiling", "floor", "wall", "roof", "door",
		"cupboard", "drawer", "shelf", "mirror", "picture",
		"mobile", "phone", "laptop", "tablet", "screen",
	}

	for _, obj := range objectWords {
		if strings.Contains(word, obj) {
			return true
		}
	}

	return false
}

// isPronoun checks if a word is a pronoun
func isPronoun(word string) bool {
	pronouns := []string{
		"i", "you", "he", "she", "it", "we", "they",
		"me", "him", "her", "us", "them",
		"this", "that", "these", "those",
		"who", "what", "where", "when", "why", "how",
		"my", "your", "his", "her", "its", "our", "their",
		"mine", "yours", "hers", "ours", "theirs",
	}

	word = strings.ToLower(word)
	for _, pronoun := range pronouns {
		if word == pronoun {
			return true
		}
	}

	return false
}

// shuffle returns a shuffled copy of the input slice
func shuffle(words []models.WordResponse) []models.WordResponse {
	result := make([]models.WordResponse, len(words))
	copy(result, words)
	rand.Shuffle(len(result), func(i, j int) {
		result[i], result[j] = result[j], result[i]
	})
	return result
}

// SubmitQuizAnswer handles the submission of a quiz answer
func (h *Handler) SubmitQuizAnswer(c *gin.Context) {
	var answer QuizAnswer
	if err := c.ShouldBindJSON(&answer); err != nil {
		fmt.Printf("SubmitQuizAnswer: Invalid request body: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	fmt.Printf("SubmitQuizAnswer: Submitting answer for word %d in session %d\n", answer.WordID, answer.SessionID)
	// Add the review item
	reviewItem, err := h.svc.ReviewWord(answer.SessionID, answer.WordID, answer.Correct)
	if err != nil {
		fmt.Printf("SubmitQuizAnswer: Failed to submit answer: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to submit answer: %v", err)})
		return
	}

	fmt.Printf("SubmitQuizAnswer: Successfully submitted answer for word %d\n", answer.WordID)
	c.JSON(http.StatusOK, gin.H{
		"word_id":     reviewItem.WordID,
		"session_id":  reviewItem.StudySessionID,
		"correct":     reviewItem.Correct,
		"created_at":  reviewItem.CreatedAt,
	})
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
		if item.CorrectCount > item.WrongCount {
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
