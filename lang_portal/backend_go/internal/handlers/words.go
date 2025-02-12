package handlers

import (
	"lang_portal/internal/service"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

func RegisterWordsRoutes(r *gin.RouterGroup, svc *service.Service) {
	h := NewHandler(svc)
	words := r.Group("/words")
	{
		words.GET("", h.ListWords)
		words.GET("/:id", h.GetWord)
	}
}

func (h *Handler) GetWord(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	word, err := h.svc.GetWord(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, word)
} 