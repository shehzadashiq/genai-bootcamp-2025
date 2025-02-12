package handlers

import (
	"lang_portal/internal/service"
	"net/http"

	"github.com/gin-gonic/gin"
)

func RegisterDashboardRoutes(r *gin.RouterGroup, svc *service.Service) {
	h := NewHandler(svc)
	dashboard := r.Group("/dashboard")
	{
		dashboard.GET("/last_study_session", h.GetLastStudySession)
		dashboard.GET("/study_progress", h.GetStudyProgress)
		dashboard.GET("/quick-stats", h.GetQuickStats)
	}
}

func (h *Handler) GetLastStudySession(c *gin.Context) {
	session, err := h.svc.GetLastStudySession()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, session)
}

func (h *Handler) GetStudyProgress(c *gin.Context) {
	progress, err := h.svc.GetStudyProgress()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, progress)
}

func (h *Handler) GetQuickStats(c *gin.Context) {
	stats, err := h.svc.GetQuickStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, stats)
} 