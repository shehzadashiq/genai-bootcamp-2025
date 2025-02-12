package handlers

import (
	"lang_portal/internal/service"
	"net/http"

	"github.com/gin-gonic/gin"
)

func RegisterSystemRoutes(r *gin.RouterGroup, svc *service.Service) {
	h := NewHandler(svc)
	r.POST("/reset_history", h.ResetHistory)
	r.POST("/full_reset", h.FullReset)
}

func (h *Handler) ResetHistory(c *gin.Context) {
	if err := h.svc.ResetHistory(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Study history has been reset",
	})
}

func (h *Handler) FullReset(c *gin.Context) {
	if err := h.svc.FullReset(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "System has been fully reset",
	})
} 