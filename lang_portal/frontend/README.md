# Language Learning Portal Frontend

A modern web application for language learning, built with React, TypeScript, and Tailwind CSS.

## Overview

This application serves as a comprehensive language learning portal with three main functions:
- Inventory management for vocabulary
- Score tracking system for practice sessions
- Unified launchpad for various learning applications

## Features

### Dashboard
- Last Study Session tracking
- Study Progress visualization
- Quick Stats including:
  - Success rate
  - Total study sessions
  - Active groups
  - Study streak

### Study Activities
- Browse available learning activities
- Launch activities with specific word groups
- View detailed activity history
- Track progress across sessions

### Words Management
- Browse complete vocabulary inventory
- View detailed word information
- Track correct/incorrect usage statistics

## Technical Stack

- **TypeScript** - Statically typed JavaScript for enhanced development
- **React** - Frontend library for building user interfaces
- **Tailwind CSS** - Utility-first CSS framework
- **Vite.js** - Next generation frontend tooling
- **ShadCN UI** - High-quality React components
- **React Router** - Client-side routing
- **Axios** - HTTP client for API requests

## Project Structure

```text
frontend/
├── index.html          # Entry HTML file
├── package.json        # Project dependencies and scripts
├── tsconfig.json       # TypeScript configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── vite.config.ts      # Vite configuration
├── postcss.config.js   # PostCSS configuration for Tailwind
├── src/
│   ├── main.tsx                 # Application entry point
│   ├── App.tsx                  # Root component
│   ├── components/              # Reusable UI components
│   │   ├── ui/                  # ShadCN components
│   │   └── common/             # Custom shared components
│   ├── features/               # Feature-based modules
│   ├── hooks/                 # Shared custom hooks
│   ├── lib/                   # Utility functions
│   ├── styles/               # Global styles
│   ├── types/               # Shared TypeScript types
│   └── services/           # API services
└── public/                # Static assets
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn package manager

### Installation

1. Clone the repository

   ```bash
   git clone <repository-url>
   cd lang_portal/frontend
   ```

2. Install dependencies

   ```bash
   npm install
   # or
   yarn install
   ```

3. Create a `.env` file in the root directory (if needed)

   ```env
   VITE_API_URL=http://localhost:8080/api
   ```

### Development

Run the development server

```bash
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:5173`

### Building for Production

Build the application:
```bash
npm run build
# or
yarn build
```

Preview the production build:
```bash
npm run preview
# or
yarn preview
```

## API Endpoints

The application interacts with the following API endpoints:

### Dashboard
- `GET /api/dashboard/last_study_session`
- `GET /api/dashboard/study_progress`
- `GET /api/dashboard/quick_stats`

### Study Activities
- `GET /api/study_activities`
- `GET /api/study_activities/:id`
- `GET /api/study_activities/:id/study_sessions`
- `POST /api/study_activities`

### Words
- `GET /api/words`
- `GET /api/words/:id`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
