# Finance Assistant Frontend

A modern, responsive React Single Page Application (SPA) built with Vite and TypeScript, serving as the user interface for the Personal Finance Assistant.

## Folder Structure
```text
frontend/
├── public/          # Static assets
├── src/
│   ├── components/  # Reusable UI components (Buttons, Layouts, Modals)
│   ├── pages/       # Route-level components (Dashboard, BankConnect, Login)
│   ├── services/    # API clients (e.g., api.ts using Axios)
│   ├── store/       # Global state management
│   ├── types/       # TypeScript interfaces and type definitions
│   └── utils/       # Helper functions and formatters
├── package.json     # Node dependencies and scripts
└── vite.config.ts   # Vite bundler configuration
```

## Architecture Highlights
- **Framework**: React 18 with Vite for lightning-fast HMR and optimized production builds.
- **Styling**: Pure vanilla CSS (`index.css`) utilizing CSS variables for theme management, fluid typography, and glassmorphism design principles.
- **Routing**: `react-router-dom` for client-side navigation without page reloads.
- **State Management & Data Fetching**: Standard React Hooks (`useState`, `useEffect`) interfacing with a centralized `api.ts` Axios client.
- **Data Visualization**: `recharts` for responsive, interactive charting (e.g., Cash Flow Trends, Category Breakdown).
- **Icons**: `lucide-react` for clean, consistent SVG iconography.

## Core Features
- **Interactive Dashboard**: Visualizes real-time financial health scores, 30-day Prophet cash-flow forecasts, and categorized spending breakdowns via Recharts.
- **NLP Quick Add**: Integrated text field backed by LangChain to add transactions via natural language parsing.
- **Human-in-the-Loop (HITL) Queue**: A dedicated review interface for transactions flagged by the ML anomaly detection pipeline, allowing users to resolve confidence thresholds.
- **Smart Uploads**: Drag-and-drop interface supporting CSV, PDF, and Image (Receipt) statements.

## Local Development

Ensure you have Node.js (v18+) installed.

Install dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```

Build for production:
```bash
npm run build
```

By default, the Vite dev server will run on `http://localhost:5173`.

## Environment Variables
Create a `.env` file in the root of this directory:
```env
VITE_API_URL=http://localhost:8000/api/v1
```
*(If omitted, the API client defaults to `http://localhost:8000/api/v1`). Note: The `api.ts` Axios client automatically attaches the `Bearer` token from local storage to all authenticated requests.*

## Deployment (Vercel)
This project is pre-configured for Vercel deployment via `vercel.json` in the repository root.
To deploy:
1. Import the repository into Vercel.
2. Set the `VITE_API_URL` environment variable to your production backend URL.
3. Deploy!
