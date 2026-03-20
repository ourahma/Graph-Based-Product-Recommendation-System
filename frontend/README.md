# Graph-Based Product Recommendation System
## Frontend UI

A modern, responsive React/Next.js web application for exploring graph-based product recommendations, customer segmentation, and analytics powered by Neo4j.

**Key Features:**
- 📊 Real-time dashboard with system metrics and KPIs
- 🎯 Intelligent product recommendations (customer & product-based)
- 👥 Customer segmentation via Louvain community detection
- 📈 Interactive analytics with Recharts visualizations
- 🕸️ Network visualization and relationship exploration
- ⚙️ Admin panel for algorithm control and monitoring
- 🎨 Dark-themed modern UI with Tailwind CSS
- 📱 Fully responsive (mobile, tablet, desktop)
- ♿ Accessible components with semantic HTML

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Architecture](#architecture)
- [API Integration](#api-integration)
- [State Management](#state-management)
- [Styling & Design](#styling--design)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)
- [Contributing](#contributing)

---

## Overview

This frontend provides an intuitive interface to interact with the graph-based recommendation engine. Explore customer segments, discover product recommendations, analyze purchasing patterns, and manage the recommendation algorithms — all through a beautiful, interactive web application.

### Who Is It For?

- **Product Managers**: Explore recommendation quality and customer segments
- **Data Analysts**: Analyze category trends and customer behavior
- **Operations**: Monitor algorithm execution and system health
- **Executives**: View KPIs and business metrics at a glance

---

## Tech Stack

| Layer              | Technology        | Version |
| ------------------ | ----------------- | ------- |
| Framework          | Next.js (App Router) | 16.2.0+ |
| UI Library         | React             | 18.3.1+ |
| Language           | TypeScript        | 5.2.0+  |
| Styling            | Tailwind CSS      | 3.3.0+  |
| State Management   | Zustand           | 4.4.0+  |
| HTTP Client        | Axios             | 1.6.0+  |
| Charts             | Recharts          | 2.10.0+ |
| Icons              | Lucide React      | 0.294.0+ |

---

## Features

### 🎯 Recommendations Page

**Customer-Based Recommendations:**
- Search for any customer ID
- Get personalized product recommendations
- View confidence scores with visual breakdown (CF + PageRank)
- See why each product was recommended
- Filter by product type (toggle customer/product search)

**Product-Based Recommendations:**
- Enter any product ID
- Discover similar products ("You might also like")
- View similarity scores
- See co-purchase patterns

### 👥 Customers Page

**Customer List:**
- Browse all customers with purchase history
- Real-time search by name or ID
- Filter by purchase behavior:
  - All customers
  - No purchases
  - Less than 5 purchases
  - More than 5 purchases
- Sort by total purchases
- Responsive table view

**Customer Segments:**
- View all Louvain communities
- Each segment shows:
  - Member count
  - Regional distribution
  - Sample countries and demographics
- Click to explore customers in each segment

**Top Customers:**
- Ranked by lifetime value
- Shows total spent, order count, favorite categories
- Segment membership visible

### 📊 Dashboard

**System Metrics:**
- Total unique customers
- Total unique products
- Total relationships (purchases + reviews)
- Graph density and centrality metrics

**Top Recommendations:**
- Display top 10 products by PageRank
- Category distribution
- Real-time system status

### 📈 Analytics

**Category Analysis:**
- Product count per category
- Total purchases and revenue
- Average customer ratings
- Interactive bar charts and pie charts

**Graph Statistics:**
- Network density
- Average degree
- Clustering coefficient
- Community count (from Louvain)
- Node and relationship distribution

### 🕸️ Graph Network

**Network Visualization:**
- Customer-product relationship statistics
- Community distribution (visual breakdown)
- Relationship type distribution (PURCHASED, REVIEWED, SIMILAR_TO, etc.)
- Dense/sparse network metrics

**Customer Insights:**
- Similar customer pairs
- Top customer nodes by importance
- Regional distribution
- Purchase pattern analysis

### ⚙️ Admin Panel

**Algorithm Control:**
- Run full GDS pipeline with custom customer limit
- Monitor execution status in real-time
- View detailed algorithm reports:
  - Community count (Louvain)
  - Nodes processed per algorithm
  - Relationships created
  - Performance metrics

**System Monitoring:**
- Cache statistics
- Last run timestamp
- Pipeline status (running/idle)
- Error logging and debugging info

---

## Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── page.tsx                  # Dashboard
│   ├── recommendations/
│   │   └── page.tsx              # Recommendations search
│   ├── customers/
│   │   └── page.tsx              # Customers list & segments
│   ├── products/
│   │   └── page.tsx              # Product catalog
│   ├── analytics/
│   │   └── page.tsx              # Analytics & insights
│   ├── graph/
│   │   └── page.tsx              # Network visualization
│   ├── admin/
│   │   └── page.tsx              # Algorithm control
│   └── layout.tsx                # Root layout
│
├── components/
│   ├── Layout.tsx                # Navigation & wrapper
│   └── ui/
│       └── index.tsx             # Shared UI components
│           ├── Card
│           ├── StatCard
│           ├── Badge
│           ├── LoadingSpinner
│           └── ErrorAlert
│
├── services/
│   └── api.ts                    # Axios API client
│
├── store/
│   └── appStore.ts               # Zustand global state
│
├── styles/
│   └── globals.css               # Tailwind config & globals
│
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running (see backend README)
- Recent browser (Chrome, Firefox, Safari, Edge)

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd frontend

npm install
# or
pnpm install
# or
yarn install
```

### 2. Environment Setup

Create `.env.local` at the project root:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

> **Note:** Use `NEXT_PUBLIC_` prefix to expose variables to browser

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production

```bash
npm run build
npm start
```

---

## Environment Variables

Create `.env.local` file in the frontend root:

| Variable                 | Type   | Default                      | Description                      |
| ------------------------ | ------ | ---------------------------- | -------------------------------- |
| `NEXT_PUBLIC_API_URL`    | string | `http://localhost:8000/api/v1` | Backend API base URL           |

> Environment variables prefixed with `NEXT_PUBLIC_` are exposed to the browser

---

## Running the Application

### Development Mode

```bash
npm run dev
```

Features:
- Fast Refresh (live code reloads)
- Type checking
- Source maps for debugging
- Run on `http://localhost:3000`

### Production Build

```bash
npm run build    # Compile optimized bundle
npm start        # Start production server
```

### Linting

```bash
npm run lint     # ESLint
```

---

## Architecture

### Component Hierarchy

```
<Layout>
  ├─ <Navigation />
  └─ <main>
      └─ <Page>
          ├─ <Card />
          ├─ <StatCard />
          ├─ <LoadingSpinner />
          ├─ <ErrorAlert />
          ├─ <Badge />
          └─ <Recharts Charts />
```

### Data Flow

```
User Action (search, filter)
    ↓
Event Handler (onClick, onChange)
    ↓
API Call (services/api.ts → Axios)
    ↓
State Update (Zustand store)
    ↓
Component Re-render
    ↓
UI Update
```

### State Management with Zustand

```typescript
// Global state
const useStore = create((set) => ({
  isLoading: false,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
```

Local state (React hooks) for page-specific data:
- Search terms
- Filter selections
- Form inputs
- Pagination

---

## API Integration

### API Client Setup (services/api.ts)

```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error.response?.data?.message || 'API Error');
  }
);
```

### Available Endpoints

**Recommendations:**
```typescript
api.clientRecommendations(clientId, topK)
api.productRecommendations(productId, topK)
api.getTopProducts(method, limit)
```

**Customers:**
```typescript
api.getCustomers(limit)
api.getSegments(limit)
api.getSegmentCustomers(segmentId, limit)
api.getTopCustomers(limit)
```

**Analytics:**
```typescript
api.getCategories()
api.getGraphStats()
```

**Admin:**
```typescript
api.runAlgorithms(limit)
api.getAlgorithmStatus()
```

---

## State Management

### Zustand Store

Located in `store/appStore.ts`:

```typescript
interface AppState {
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}
```

### Usage in Components

```typescript
import { useStore } from '@/store/appStore';

export default function MyComponent() {
  const { isLoading, error, setLoading, setError } = useStore();
  
  useEffect(() => {
    setLoading(true);
    fetchData()
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  
  return <div>Content</div>;
}
```

---

## Styling & Design

### Tailwind CSS Configuration

Located in `tailwind.config.js`:

```typescript
theme: {
  colors: {
    primary: '#3b82f6',      // Blue
    accent: '#10b981',       // Green
    secondary: '#6b7280',    // Gray
  },
  spacing: {
    // Extend with custom values
  },
}
```

### Color Palette

| Name      | Value       | Use Case           |
| --------- | ----------- | ------------------ |
| Primary   | `#3b82f6`   | Buttons, highlights |
| Accent    | `#10b981`   | Success, positive   |
| Secondary | `#6b7280`   | Neutral, disabled   |
| Dark      | `#0f172a`   | Background         |
| Light     | `#f1f5f9`   | Light backgrounds  |

### Responsive Design

Built-in breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

Example:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
  {/* 1 col on mobile, 2 on tablet, 4 on desktop */}
</div>
```

---

## Development Guide

### Adding a New Page

1. Create file in `app/your-page/page.tsx`
2. Use `'use client'` directive at top (required for Next.js 13+)
3. Follow component structure:

```typescript
'use client';

import React, { useEffect, useState } from 'react';
import { Card, LoadingSpinner, ErrorAlert } from '@/components/ui';
import * as api from '@/services/api';

export default function YourPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await api.yourEndpoint();
        setData(res.data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-8">
      {error && <ErrorAlert message={error} />}
      {/* Your content */}
    </div>
  );
}
```

### Adding a New Component

1. Create in `components/YourComponent.tsx`
2. Export from `components/index.ts` (if UI component)
3. Use TypeScript interfaces:

```typescript
interface YourComponentProps {
  title: string;
  value: number;
  variant?: 'primary' | 'secondary';
}

export function YourComponent({ title, value, variant = 'primary' }: YourComponentProps) {
  return <div className={`variant-${variant}`}>{title}: {value}</div>;
}
```

### Type Safety

Always use TypeScript interfaces:

```typescript
interface Customer {
  client_id: string;
  name: string;
  purchases: number;
}

interface ApiResponse<T> {
  data: T;
  status: number;
}
```

---

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

Follow prompts. Automatic deploys on git push.

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t recsys-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000/api/v1 recsys-frontend
```

### Traditional Server

```bash
npm run build
npm start
# Runs on http://localhost:3000
```

Then use nginx/Apache as reverse proxy.

---

## Troubleshooting

### Blank Page / No Content

**Check:**
1. Browser console for errors (F12)
2. Network tab for failed API calls
3. Verify `NEXT_PUBLIC_API_URL` is correct
4. Ensure backend is running

**Fix:**
```bash
# Check API connectivity
curl http://localhost:8000/api/v1/health

# Restart frontend
npm run dev
```

### API Connection Error

**Problem:** "Failed to fetch from API"

**Solutions:**
1. Verify backend is running: `http://localhost:8000/docs` should load
2. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Check CORS settings in backend
4. Verify firewall isn't blocking connections

### Styling Not Applied

**Problem:** Tailwind classes not working

**Solutions:**
1. Restart dev server: `Ctrl+C` then `npm run dev`
2. Check `tailwind.config.js` has correct content paths
3. Rebuild: `npm run build`
4. Clear Next.js cache: `rm -rf .next/`

### State Not Updating

**Problem:** Component doesn't re-render after state change

**Solutions:**
1. Verify using `useStore` hook properly
2. Check for missing `useEffect` dependencies
3. Ensure `setError(null)` is called to clear old errors
4. Check browser React DevTools for state

---

## Performance Tips

### Optimization Techniques

1. **Code Splitting**: Automatic with Next.js App Router
2. **Image Optimization**: Use Next.js `<Image>` component
3. **Caching**: API responses cached for 5 minutes
4. **Lazy Loading**: Components load on-demand
5. **Memoization**: Use `React.memo()` for expensive renders

### Bundle Size

Check bundle size:
```bash
npm install --save-dev webpack-bundle-analyzer
# Add script to package.json and run
```

Target:
- JS bundle: < 200KB gzipped
- Initial load: < 3 seconds
- Lighthouse score: > 90

---

## Contributing

### Code Guidelines

1. **TypeScript First**: No `any` types unless absolutely necessary
2. **Component Props**: Always define interfaces
3. **Error Handling**: Always catch and display errors to users
4. **Accessibility**: Use semantic HTML (`<button>`, `<input>`, `<label>`)
5. **Comments**: Document complex logic

### Git Workflow

```bash
git checkout -b feature/your-feature
# Make changes
git add .
git commit -m "feat: description of changes"
git push origin feature/your-feature
# Create Pull Request
```

### Testing

```bash
npm test              # Run Jest tests
npm run test:watch   # Watch mode
npm run test:coverage # Coverage report
```

---

## Support & Documentation

- **API Docs**: Backend Swagger UI at `http://localhost:8000/docs`
- **Full Docs**: See [FRONTEND_DOCUMENTATION.md](./FRONTEND_DOCUMENTATION.md)
- **Backend Docs**: See [BACKEND_DOCUMENTATION.md](../BACKEND_DOCUMENTATION.md)

---

## License

MIT License - See LICENSE file for details

## Authors

Built with ❤️ for modern recommendation systems

Last Updated: March 2026
- **HTTP Client**: Axios
- **Backend API**: FastAPI (Python)

## 📦 Installation

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Setup

```bash
# Install dependencies
npm install

# Configure environment
# Update .env.local with your API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev

# Build for production
npm run build
npm run start
```

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js app directory
│   ├── layout.tsx               # Root layout with sidebar
│   ├── page.tsx                 # Dashboard
│   ├── recommendations/         # Recommendation search
│   ├── customers/               # Customer segments & insights
│   ├── analytics/               # Category & graph analytics
│   ├── graph/                   # Network visualization
│   └── admin/                   # Algorithm control panel
├── components/
│   ├── Layout.tsx               # Main layout with navigation
│   └── ui/                      # Reusable UI components (Card, Button, etc.)
├── services/
│   └── api.ts                   # API client & endpoints
├── store/
│   └── appStore.ts              # Global state (Zustand)
├── styles/
│   └── globals.css              # Global styles & utilities
├── tailwind.config.js           # Tailwind configuration
├── tsconfig.json                # TypeScript configuration
└── .env.local                   # Environment variables
```

## 🎨 Design System

### Colors
- **Primary**: Cyan (#0ea5e9)
- **Accent**: Purple (#a855f7)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Danger**: Red (#ef4444)

### Components
- **Glass UI**: Semi-transparent glass-morphism cards
- **Gradient Text**: Eye-catching gradient text effects
- **Animations**: Fade-in, slide-up, pulse-glow effects
- **Responsive**: Mobile-first responsive design

## 🔌 API Integration

All endpoints are through the FastAPI backend:

```bash
# Recommendations
GET /recommendations/client/{client_id}
GET /recommendations/product/{product_id}
GET /recommendations/top
GET /recommendations/clients/similar-all

# Customers
GET /customers/segments
GET /customers/segments/{id}
GET /customers/top

# Analytics
GET /analytics/categories
GET /analytics/graph-stats

# Algorithms
POST /algorithms/run_all
GET /algorithms/status
```

## 🌐 Navigation

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/` | System overview & metrics |
| Recommendations | `/recommendations` | Find product recommendations |
| Customers | `/customers` | View segments & top customers |
| Analytics | `/analytics` | Category & graph analytics |
| Graph Network | `/graph` | Network statistics & visualization |
| Admin | `/admin` | Algorithm control & cache management |

## 🚀 Running the Full Stack

### Terminal 1: Backend API
```bash
cd ../
python main.py
# or
uvicorn main:app --reload
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

### Access the Application
- UI: `http://localhost:3000`
- API Docs: `http://localhost:8000/docs`

## 📊 Data Flow

```
Frontend (Next.js/React)
         ↓
    Axios API Client
         ↓
    FastAPI Backend
         ↓
    Neo4j Database + GDS
```

## 🔒 Performance Optimizations

- **Server-Side Rendering**: Next.js SSR for fast initial load
- **Caching**: 5-minute TTL cache on all algorithms
- **Image Optimization**: Built-in Next.js image optimization
- **Code Splitting**: Automatic route-based code splitting
- **State Management**: Efficient global state with Zustand

## 🐛 Troubleshooting

### API Connection Issues
- Ensure backend is running on `http://localhost:8000`
- Check `.env.local` for correct API URL
- Verify CORS is enabled in FastAPI

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

### Type Errors
```bash
# Check TypeScript
npx tsc --noEmit
```

## 📝 License

This project is part of the Graph-Based Product Recommendation System.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- TypeScript strict mode compliance
- Responsive design on all screen sizes
- Consistent with design system
- API error handling

## 📧 Support

For issues or questions, please open an issue on the project repository.
