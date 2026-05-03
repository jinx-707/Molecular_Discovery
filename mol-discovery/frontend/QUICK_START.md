# Quick Start Guide

## Start Development Server

```bash
cd mol-discovery/frontend
npm run dev
```

Open http://localhost:3000

## Available Pages

- **/** - Dashboard (home page)
- **/discovery** - Start a new discovery run
- **/experiments** - Log experimental results
- **/models** - View model health and trigger retraining
- **/projects** - Manage discovery projects

## Environment Variables

Edit `.env.local` to configure:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_API_KEY=your-api-key
```

## Common Commands

```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Run tests
npm test
```

## Project Structure

```
src/
├── app/           # Pages (Next.js App Router)
├── components/    # React components
├── services/      # API client
└── lib/          # Utilities
```

## Making Changes

1. Edit files in `src/`
2. Changes auto-reload in browser
3. Check console for errors
4. Build before deploying: `npm run build`

## Troubleshooting

**Port already in use?**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Dependencies issues?**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Build errors?**
```bash
rm -rf .next
npm run build
```

## Need Help?

- Check `README.md` for detailed docs
- Check `FRONTEND_SETUP_COMPLETE.md` for what was fixed
- Check Next.js docs: https://nextjs.org/docs
