# Docker Setup for Language Learning Portal

This document provides instructions for running the Language Learning Portal application using Docker containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- AWS credentials with appropriate permissions for Bedrock, Polly, and Translate services

## Setup Instructions

1. **Configure Environment Variables**

   Copy the example environment file and update it with your AWS credentials:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and add your AWS credentials:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_DEFAULT_REGION

2. **Build and Start the Containers**

   ```bash
   docker-compose up -d
   ```

   This will build and start three containers:
   - Backend (Django REST API)
   - Frontend (React application)
   - Database (PostgreSQL)

3. **Access the Application**

   - Frontend: http://localhost
   - Backend API: http://localhost:8080

4. **View Container Logs**

   ```bash
   docker-compose logs -f
   ```

   To view logs for a specific service:

   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

5. **Stop the Containers**

   ```bash
   docker-compose down
   ```

   To remove volumes as well:

   ```bash
   docker-compose down -v
   ```

## Development Workflow

For development, you might want to run the frontend in development mode:

1. Modify the `docker-compose.yml` file to use the development server for the frontend:

   ```yaml
   frontend:
     build:
       context: ./lang_portal_frontend
       dockerfile: Dockerfile.dev  # Create this file with development settings
     ports:
       - "5173:5173"  # Default Vite development port
     volumes:
       - ./lang_portal_frontend:/app
       - /app/node_modules
     command: npm run dev
   ```

2. Create a `Dockerfile.dev` in the frontend directory:

   ```dockerfile
   FROM node:20-alpine
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci
   COPY . .
   EXPOSE 5173
   CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
   ```

## AWS IAM Requirements

Ensure your AWS credentials have the following permissions:

- Amazon Bedrock: `bedrock:ListFoundationModels`, `bedrock:InvokeModel`, `bedrock-runtime:InvokeModel`
- Amazon Polly: `polly:DescribeVoices`, `polly:SynthesizeSpeech`
- Amazon Translate: `translate:TranslateText`, `translate:ListLanguages`

## Troubleshooting

- **Backend Container Fails to Start**: Check the logs with `docker-compose logs backend`. Ensure your AWS credentials are correctly set in the `.env` file.
- **Frontend Container Fails to Build**: Check for any build errors with `docker-compose logs frontend`.
- **Database Connection Issues**: Ensure the database container is running with `docker-compose ps`. Check the database logs with `docker-compose logs db`.
