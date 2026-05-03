# MolDiscovery Frontend

AI-powered catalyst and enzyme discovery platform frontend built with Next.js 14.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: Axios
- **Charts**: Recharts
- **3D Visualization**: Three.js

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your API configuration:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_API_KEY=your-api-key
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home/Dashboard
│   ├── discovery/         # Discovery wizard
│   ├── experiments/       # Experiment logger
│   ├── models/            # Model health dashboard
│   └── projects/          # Project management
├── components/            # React components
│   ├── ui/               # UI primitives (buttons, etc.)
│   └── ...               # Feature components
├── services/             # API client
└── lib/                  # Utilities
```

## Features

- **Discovery Wizard**: Multi-step workflow for catalyst/enzyme discovery
- **Experiment Logger**: Log and track experimental results
- **Model Health**: Monitor ML model performance
- **Project Management**: Organize discovery campaigns
- **3D Visualization**: Interactive molecular structures
- **Dark Mode**: Built-in theme switching

## API Integration

The frontend communicates with the FastAPI backend via REST API. All API calls are centralized in `src/services/api.ts`.

## Development Notes

- Uses Next.js App Router (not Pages Router)
- All pages are client components (`'use client'`)
- Environment variables must be prefixed with `NEXT_PUBLIC_`
- Tailwind CSS with custom design tokens
- TypeScript strict mode enabled
