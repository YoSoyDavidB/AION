# AION Frontend

Modern React frontend for AION - AI Personal Assistant with Long-Term Memory.

## Tech Stack

- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI + Tailwind)
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod
- **Graph Visualization**: React Flow
- **Charts**: Recharts
- **Markdown**: react-markdown
- **Icons**: Lucide React

## Quick Start

### Prerequisites

- Node.js 18+
- npm 9+

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Environment Variables

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_DEFAULT_USER_ID=david
```

## Project Structure

```
src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── badge.tsx
│   ├── chat/                  # Chat interface components
│   ├── dashboard/             # Dashboard components
│   ├── memories/              # Memory management components
│   ├── knowledge-graph/       # Graph visualization components
│   ├── documents/             # Document management components
│   └── layout/                # Layout components (Sidebar, Header)
├── pages/                     # Page components
├── lib/
│   ├── api/                   # API client
│   │   ├── client.ts          # Axios instance
│   │   ├── chat.ts            # Chat API
│   │   ├── memories.ts        # Memories API
│   │   └── documents.ts       # Documents API
│   ├── types/                 # TypeScript types
│   │   ├── chat.ts
│   │   ├── memory.ts
│   │   ├── document.ts
│   │   └── graph.ts
│   └── utils.ts               # Utility functions
├── hooks/                     # Custom React hooks
├── store/                     # Zustand stores
├── App.tsx                    # Main app component
├── main.tsx                   # Entry point
└── index.css                  # Global styles
```

## Features (Planned)

### ✅ Implemented

- Project setup with Vite + React + TypeScript
- Tailwind CSS configuration
- shadcn/ui components (Button, Card, Input, Badge)
- API client with Axios
- TypeScript types for all API endpoints
- Environment configuration

### 🚧 In Progress

- Layout base (Sidebar, Header, Routes)
- Chat Interface

### 📋 To Do

- Memory Dashboard
- Knowledge Graph Viewer
- Document Manager
- Analytics Dashboard

## Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint code
npm run lint
```

## API Integration

The frontend connects to the AION backend API running on `http://localhost:8000`.

### API Endpoints Used

- `POST /api/v1/chat` - Send chat messages
- `GET /api/v1/conversations` - Get conversations
- `POST /api/v1/memories` - Create memories
- `GET /api/v1/memories` - Get memories
- `POST /api/v1/memories/search` - Search memories
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents` - Get documents

## Development Guidelines

### Adding New Components

```typescript
// Use shadcn/ui components
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

// Use TypeScript for type safety
import type { ChatMessage } from "@/lib/types/chat"
```

### API Calls

```typescript
// Use the API client
import { chatApi } from "@/lib/api/chat"

// Make API calls
const response = await chatApi.sendMessage({
  user_id: "david",
  message: "Hello AION!",
  use_tools: true,
})
```

### State Management

```typescript
// Use Zustand for UI state
import { create } from "zustand"

interface ChatStore {
  messages: ChatMessage[]
  addMessage: (message: ChatMessage) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
}))
```

## Styling

We use Tailwind CSS with custom design tokens defined in `index.css`.

### Color Scheme

- Light mode: Clean, professional design
- Dark mode: Fully supported with dark variants

### Responsive Design

All components are mobile-first and fully responsive.

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure TypeScript types are correct
4. Test your changes
5. Submit a pull request

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.

---

**Built with ❤️ using modern React best practices**
