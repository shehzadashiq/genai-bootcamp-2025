package main

import (
	"lang_portal/internal/handlers"
	"lang_portal/internal/middleware"
	"lang_portal/internal/service"
	"log"

	"github.com/gin-gonic/gin"
)

func main() {
	// Initialize services
	svc, err := service.NewService("words.db")
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}
	defer svc.Close()

	// Setup router
	r := gin.New()
	
	// Add middleware
	r.Use(middleware.Logger())
	r.Use(middleware.CORS())
	r.Use(middleware.ErrorHandler())
	r.Use(gin.Recovery())

	api := r.Group("/api")

	// Register routes
	handlers.RegisterDashboardRoutes(api, svc)
	handlers.RegisterStudyActivitiesRoutes(api, svc)
	handlers.RegisterWordsRoutes(api, svc)
	handlers.RegisterGroupsRoutes(api, svc)
	handlers.RegisterStudySessionsRoutes(api, svc)
	handlers.RegisterSystemRoutes(api, svc)

	// Start server
	log.Fatal(r.Run(":8080"))
} 