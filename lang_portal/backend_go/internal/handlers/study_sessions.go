package handlers

import (
	"lang_portal/internal/service"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

func RegisterStudySessionsRoutes(r *gin.RouterGroup, svc *service.Service) {
	h := NewHandler(svc)
	sessions := r.Group("/study_sessions")
	{
		sessions.GET("", h.ListStudySessions)
		sessions.GET("/:id", h.GetStudySession)
		sessions.GET("/:id/words", h.GetStudySessionWords)
		sessions.POST("/:id/words/:word_id/review", h.ReviewWord)
	}
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
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
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