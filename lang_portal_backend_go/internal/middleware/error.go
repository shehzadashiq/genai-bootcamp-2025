package middleware

import (
	"database/sql"
	"net/http"

	"github.com/gin-gonic/gin"
)

func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		if len(c.Errors) > 0 {
			err := c.Errors.Last().Err
			switch err {
			case sql.ErrNoRows:
				c.JSON(http.StatusNotFound, gin.H{
					"error": "Resource not found",
				})
			default:
				c.JSON(http.StatusInternalServerError, gin.H{
					"error": err.Error(),
				})
			}
		}
	}
} 