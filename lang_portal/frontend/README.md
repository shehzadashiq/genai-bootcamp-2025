# Language Learning Portal Frontend

A modern web application for language learning, built with React, TypeScript, and Tailwind CSS.

## Overview

This application serves as a comprehensive language learning portal with three main functions:
- Inventory management for vocabulary
- Score tracking system for practice sessions
- Unified launchpad for various learning applications

## Features

### Dashboard
- Last Study Session tracking with:
  - Start and end times
  - Activity name
  - Group name
  - Words reviewed count
- Study Progress visualization with:
  - Total words studied
  - Total available words
  - Progress bar
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
- View detailed word information including:
  - Urdu text
  - Urdlish transliteration
  - English translation
  - Correct/incorrect usage statistics

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
│   │   ├── dashboard/         # Dashboard components
│   │   ├── study-activities/ # Study activity components
│   │   ├── study-sessions/  # Study session components
│   │   └── words/          # Word management components
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

3. Create a `.env` file in the root directory

   ```env
   VITE_API_URL=http://localhost:8080/api
   ```

### Development

Run the development server:

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

### Type Checking

Run TypeScript type checking:

```bash
npm run typecheck
# or
yarn typecheck
```

## API Integration

The frontend communicates with the backend through RESTful API endpoints. All API calls are centralized in the `services/api.ts` file. The application uses Axios for making HTTP requests and handles responses with proper TypeScript types.

Key API endpoints:

- `/api/dashboard/*` - Dashboard statistics and last session
- `/api/study_activities/*` - Study activity management
- `/api/study_sessions/*` - Study session tracking
- `/api/words/*` - Word inventory and review
- `/api/groups/*` - Word group management

## Component Architecture

The application follows a feature-based architecture where each major feature has its own directory containing:

- Components specific to the feature
- Feature-specific types
- Feature-specific hooks
- Feature-specific utilities

Common components and utilities are placed in shared directories.

## State Management

The application uses React's built-in state management with:

- `useState` for local component state
- `useEffect` for side effects and data fetching
- Custom hooks for shared logic
- Props for component communication

## Styling

The application uses Tailwind CSS for styling with:

- Custom theme configuration
- Responsive design
- Dark mode support
- ShadCN UI components

## Error Handling

The application implements comprehensive error handling:

- API error handling with proper user feedback
- Loading states for async operations
- Fallback UI for error states
- Type-safe error boundaries

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

Please ensure your code:
- Follows TypeScript best practices
- Includes proper error handling
- Has responsive design
- Is properly typed
- Follows the existing code style

## License

This project is licensed under the MIT License.
