# FinanceAgents Frontend

A Next.js chat UI for the FinanceAgents backends. Type a question, the page posts it to `POST /query`, and the reply is rendered as markdown: the comprehensive summary on top, then one collapsible card per agent (Reddit sentiment, internal filings, market data, SEC filings).

The Analysis and Settings tabs are UI demos with static data; only the Chat tab talks to the backend.

## Run it

Requires **Node 18 or newer** (`node --version`). `node_modules` and `.next` are gitignored, so a fresh clone has no `next` binary until you install.

1. Start any one backend from its own directory. All four listen on port 8000.

   ```bash
   cd ../langchain_agents            # or crewai_agents / llamaindex_agents / ag2_agents
   env $(cat ../env.all) python src/main.py
   ```

2. Install and start the UI:

   ```bash
   cd frontend
   npm ci              # first time, or after package.json changes
   npm run dev
   ```

3. Open <http://localhost:3000>, pick the Chat tab, and ask e.g. `Tell me about Tesla stock` or `NFLX`. A full answer takes 20 to 60 seconds; the three bouncing dots show while the backend works.

`npm run dev` uses Turbopack with hot reload. For a production build:

```bash
npm run build
npm start           # serves the build on port 3000
```

### Pointing at a different backend

The backend URL is read from `NEXT_PUBLIC_API_URL` at startup and defaults to `http://localhost:8000`. To change it, copy `.env.example` to `.env.local`, edit the value, and restart `npm run dev`. `.env.local` is gitignored.

```env
NEXT_PUBLIC_API_URL=http://192.168.1.20:8000
```

### "Request failed, please try again later"

The page shows this whenever the request to the backend fails. Check, in order:

1. A backend is running: `curl -s http://localhost:8000/docs` should return HTML.
2. `NEXT_PUBLIC_API_URL` matches where it runs, and the dev server was restarted after changing it.
3. The browser's developer console for the actual error (connection refused, CORS, 500).

## What the backend returns

```json
{
  "response": {
    "RedditAgent":  {"summary": "### ...markdown..."},
    "FinanceAgent": {"summary": "..."},
    "YahooAgent":   {"summary": "..."},
    "SecAgent":     {"summary": "..."},
    "FinalSummary": {"summary": "..."}
  }
}
```

`AgentResponse.tsx` maps each key to a label, icon, and colour. `FinalSummary` renders first and expanded; the others render collapsed. Unknown keys still render, labelled by their key. A non-financial question comes back with only `GeneralAgent`, which renders expanded.

## Project structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # tab switcher (Chat / Analysis / Settings)
│   │   ├── layout.tsx            # loads Geist fonts, global CSS
│   │   └── globals.css
│   └── components/
│       ├── Dashboard.tsx         # chat page: history list, input, axios call to /query
│       ├── AgentResponse.tsx     # renders one backend reply as markdown cards
│       ├── Sidebar.tsx
│       ├── Analysis.tsx          # static demo charts (Recharts)
│       ├── Settings.tsx          # static demo settings
│       └── ...                   # unused helper components kept from the original UI
├── .env.example                  # NEXT_PUBLIC_API_URL
├── package.json
├── tailwind.config.ts            # typography plugin, Geist font family
├── next.config.ts
└── Dockerfile                    # builds and serves on port 3000 (standalone; backend URL baked in at build)
```

## Stack

| | |
|---|---|
| Framework | Next.js 15 (App Router, Turbopack) |
| UI | React 19, TypeScript, Tailwind CSS 3 with `@tailwindcss/typography` |
| Markdown | `react-markdown` + `remark-gfm` |
| Charts | Recharts (Analysis tab) |
| Icons | Lucide React |
| HTTP | axios |

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | dev server with hot reload |
| `npm run build` | production build (also type-checks and lints) |
| `npm start` | serve the production build |
| `npm run lint` | ESLint |

## Docker

```bash
docker build -t financeagents-frontend .
docker run -p 3000:3000 financeagents-frontend
```

The image is built with the default backend URL `http://localhost:8000`. `NEXT_PUBLIC_*` values are inlined at build time, so to target another backend add `ENV NEXT_PUBLIC_API_URL=...` to the `Dockerfile` before the `npm run build` step and rebuild.
