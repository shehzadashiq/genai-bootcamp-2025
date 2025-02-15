package handlers

import (
	"lang_portal/internal/service"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

func RegisterStudySessionsRoutes(r *gin.RouterGroup, svc *service.Service) {
	fmt.Printf("Registering study session routes\n")
	h := NewHandler(svc)
	sessions := r.Group("/study_sessions")
	{
		fmt.Printf("Adding GET route for study sessions list\n")
		sessions.GET("", h.ListStudySessions)
		fmt.Printf("Adding GET route for single study session\n")
		sessions.GET("/:id", h.GetStudySession)
		fmt.Printf("Adding GET route for study session words\n")
		sessions.GET("/:id/words", h.GetStudySessionWords)
		fmt.Printf("Adding POST route for word review\n")
		sessions.POST("/:id/words/:word_id/review", h.ReviewWord)
		fmt.Printf("Adding POST route for creating study session\n")
		sessions.POST("", h.CreateStudySession)
	}
	fmt.Printf("Finished registering study session routes\n")
}

func (h *Handler) ListStudySessions(c *gin.Context) {
	page := c.DefaultQuery("page", "1")
	pageNum, _ := strconv.Atoi(page)

	sessions, err := h.svc.ListStudySessions(pageNum)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, sessions)
}

func (h *Handler) GetStudySession(c *gin.Context) {
	fmt.Printf("GetStudySession handler called with params: %+v\n", c.Params)
	
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		fmt.Printf("Invalid ID: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	fmt.Printf("Getting study session with ID: %d\n", id)
	session, err := h.svc.GetStudySession(id)
	if err != nil {
		fmt.Printf("Error getting study session: %v\n", err)
		if err.Error() == "study session not found" {
			c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	fmt.Printf("Returning study session: %+v\n", session)
	c.JSON(http.StatusOK, session)
}

func (h *Handler) GetStudySessionWords(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	page := c.DefaultQuery("page", "1")
	pageNum, _ := strconv.Atoi(page)

	words, err := h.svc.GetStudySessionWords(id, pageNum)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, words)
}

func (h *Handler) ReviewWord(c *gin.Context) {
	sessionID, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session id"})
		return
	}

	wordID, err := strconv.ParseInt(c.Param("word_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid word id"})
		return
	}

	var req struct {
		Correct bool `json:"correct" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	review, err := h.svc.ReviewWord(sessionID, wordID, req.Correct)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, review)
}

// CreateStudySessionRequest represents the request body for creating a study session
type CreateStudySessionRequest struct {
	GroupID      int64  `json:"group_id" binding:"required"`
	ActivityName string `json:"activity_name" binding:"required"`
}

func (h *Handler) CreateStudySession(c *gin.Context) {
	fmt.Printf("CreateStudySession handler called with method: %s, path: %s\n", c.Request.Method, c.Request.URL.Path)

	var req CreateStudySessionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		fmt.Printf("Error binding JSON: %v\n", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}

	fmt.Printf("Creating study session with group_id: %d, activity_name: %s\n", req.GroupID, req.ActivityName)

	session, err := h.svc.CreateStudySessionWithActivity(req.GroupID, req.ActivityName)
	if err != nil {
		fmt.Printf("Error creating study session: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	fmt.Printf("Successfully created study session: %+v\n", session)
	c.JSON(http.StatusCreated, session)
}