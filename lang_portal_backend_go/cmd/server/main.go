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
	log.Printf("Starting server initialization...\n")
	svc, err := service.NewService("words.db")
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}
	defer svc.Close()

	// Setup router
	log.Printf("Setting up router...\n")
	r := gin.New()
	
	// Add middleware
	log.Printf("Adding middleware...\n")
	r.Use(middleware.Logger())
	r.Use(middleware.CORS())
	r.Use(middleware.ErrorHandler())
	r.Use(gin.Recovery())

	api := r.Group("/api")

	// Register routes
	log.Printf("Registering routes...\n")
	handlers.RegisterDashboardRoutes(api, svc)
	handlers.RegisterStudyActivitiesRoutes(api, svc)
	handlers.RegisterWordsRoutes(api, svc)
	handlers.RegisterGroupsRoutes(api, svc)
	handlers.RegisterStudySessionsRoutes(api, svc)
	handlers.RegisterSystemRoutes(api, svc)
	handlers.RegisterVocabularyQuizRoutes(api, svc)

	// Start server
	log.Printf("Starting server on port 8080...\n")
	log.Fatal(r.Run(":8080"))
} 