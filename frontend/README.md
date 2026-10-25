# Finance Assistant Frontend

A responsive React single-page application built with Vite and TypeScript, serving as the user interface for the Personal Finance Assistant.

## Folder Structure
```text
frontend/
├── public/              # Static assets (favicon, icons)
├── src/
│   ├── assets/          # Images used in the UI
│   ├── components/      # Modals: AuthModal (sign in / register / demo), BankSyncModal (AA consent flow)
│   ├── pages/           # Routes: Dashboard, Transactions, ReviewQueue, UploadPage, Chat
│   ├── api.ts           # Axios client: base URL, auth header, 401 handling, API helpers
│   ├── demoData.ts      # Sample data shown only to the demo account when the backend is unreachable
│   ├── App.tsx          # Layout, sidebar, routing and auth state
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles and theme variables
├── package.json         # Node dependencies and scripts
├── vercel.json          # Vercel SPA routing
└── vite.config.ts       # Vite bundler configuration
```

## Architecture Highlights
- **Framework**: React 19 with Vite for fast HMR and optimized production builds. `npm run build` type-checks with `tsc -b` before bundling.
- **Styling**: Vanilla CSS (`index.css`) with CSS variables for theming and a glassmorphism design.
- **Routing**: `react-router-dom` for client-side navigation.
- **Data Fetching**: React hooks (`useState`, `useEffect`) with a central Axios client in `api.ts`.
- **Auth Handling**: the client attaches the stored JWT to every request. If the backend rejects an expired or invalid token (401), the session is cleared and the login modal reappears. "Demo Login" requests a real signed token from the backend.
- **Data Visualization**: `recharts` for cash-flow trends, forecasts and category breakdowns.
- **Icons & Notifications**: `lucide-react` icons and `react-hot-toast` notifications.

## Core Features
- **Interactive Dashboard**: financial health score, 30-day Prophet cash-flow forecast, monthly trends, category breakdown, AI coaching and savings goals.
- **NLP Quick Add**: type something like "spent 450 on Swiggy yesterday" and the backend turns it into a transaction.
- **Human-in-the-Loop (HITL) Queue**: review and approve or reject transactions flagged as duplicates, uncategorized, or unusual.
- **Uploads & Bank Sync**: upload CSV, PDF or image statements, add transactions manually, or run the simulated RBI Account Aggregator sync with OTP consent.
- **AI Advisor Chat**: ask questions about your spending; answers come from exact tool calculations on your own data.
- **Honest fallbacks**: if the backend is unreachable, real users see an error with a Retry button. Only the demo account falls back to clearly labelled sample data.

## Local Development

Requires Node.js 18+.

```bash
npm install      # install dependencies
npm run dev      # start the dev server on http://localhost:5173
npm run build    # type-check and build for production
```

## Environment Variables
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
If it's omitted, the client defaults to `http://localhost:8000/api/v1`.

## Deployment (Vercel)
1. Import the repository into Vercel and set the project's root directory to `frontend`.
2. Set `VITE_API_BASE_URL` to your production backend URL, including `/api/v1`.
3. Add the Vercel URL to the backend's `ALLOWED_ORIGINS` so CORS accepts requests from it.
4. Deploy.
 