# FinanceAgents Frontend (BankerAI UI)

A Next.js web UI for the FinanceAgents backend: a chat page that sends questions to `POST /query` and renders each agent's summary, plus demo analysis and settings pages.

## Connecting to the backend

The chat page posts to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`, the LangChain implementation). Start one backend from its own directory, e.g.

```bash
cd ../langchain_agents && env $(cat ../env.all) python src/main.py
```

then copy `.env.example` to `.env.local` and adjust the port if you run a different implementation:

| Backend | Port |
|---|---|
| langchain_agents | 8000 |
| crewai_agents, llamaindex_agents | 8001 |
| ag2_agents | 8002 |

The backend replies with `{"response": {AgentName: {"summary": "..."}, "FinalSummary": {...}}}`, which the chat renders one block per agent.

## Features

### 🤖 Dashboard - Intelligent Chat
- ChatGPT-like chat interface
- Live answers from the FinanceAgents backend (per-agent summaries + final summary)
- Message history
- Keyboard shortcut support (Enter to send)

### 📊 Analysis - Data Analysis (static demo data)
- **Stock Price Trend**: Display stock price changes
- **Industry Revenue Analysis**: Bar chart showing revenue comparison across industries
- **Portfolio Distribution**: Pie chart showing asset allocation
- **Volume Analysis**: Display trading volume changes
- **Key Metrics Cards**: Total assets, monthly return, risk level, positions

### ⚙️ Settings - Personal Settings (UI only, not persisted)
- **Profile Management**: Name, email, phone, language settings
- **Notification Settings**: Email, push, SMS notification toggles
- **Security Settings**: Change password, two-factor authentication, login history
- **Appearance Settings**: Dark mode toggle

## Tech Stack

- **Framework**: Next.js 15.1.8 with App Router
- **UI Library**: React 19 + TypeScript
- **Styles**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Build Tool**: Turbopack

## Getting Started

### Install dependencies
```bash
npm install
```

### Start the development server
```bash
npm run dev
```

The app will start at http://localhost:3000

### Build for production
```bash
npm run build
```

### Start the production server
```bash
npm start
```

## Project Structure

```
src/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Layout component
│   └── globals.css       # Global styles
├── components/
│   ├── Sidebar.tsx       # Sidebar navigation
│   ├── Dashboard.tsx     # Chat interface
│   ├── Analysis.tsx      # Data analysis page
│   ├── Settings.tsx      # Settings page
│   └── ...              # Other components
```

## Usage

1. **Dashboard page**: Enter your question in the input box, AI will reply automatically
2. **Analysis page**: View various financial data charts and key metrics
3. **Settings page**: Manage profile, notifications, and security settings

## Development Notes

- TypeScript for type safety
- Responsive design, mobile-friendly
- Component-based development for easy maintenance and extension
- Modern UI design with Tailwind CSS

## License

MIT License
