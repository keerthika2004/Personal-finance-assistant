# Finance Assistant Frontend

A modern, responsive React Single Page Application (SPA) built with Vite and TypeScript, serving as the user interface for the Personal Finance Assistant.

## Architecture Highlights
- **Framework**: React 18 with Vite for lightning-fast HMR and optimized production builds.
- **Styling**: Pure vanilla CSS (`index.css`) utilizing CSS variables for theme management, fluid typography, and glassmorphism design principles.
- **Routing**: `react-router-dom` for client-side navigation without page reloads.
- **State Management & Data Fetching**: Standard React Hooks (`useState`, `useEffect`) interfacing with a centralized `api.ts` Axios client.
- **Data Visualization**: `recharts` for responsive, interactive charting (e.g., Cash Flow Trends, Category Breakdown).
- **Icons**: `lucide-react` for clean, consistent SVG iconography.

## Core Features
- **Interactive Dashboard**: Provides real-time financial health scores, cumulative AI cash-flow forecasting, and categorized spending breakdowns.
- **NLP Quick Add**: Features an integrated NLP input field backed by LangChain, allowing users to type transactions in natural language for automatic categorization and entry.
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

By default, the Vite server will run on `http://localhost:5173`.

## Environment Variables
Create a `.env` file in the root of this directory:
```env
VITE_API_URL=http://localhost:8000/api/v1
```
*(If omitted, the API client defaults to `http://localhost:8000/api/v1`)*
